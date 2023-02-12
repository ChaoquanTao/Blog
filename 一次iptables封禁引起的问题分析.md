---
title: 一次由ip封禁引起的问题分析
date: 2023-02-10 22:00:00
tag: 网络
categories: 网络
---

### 问题背景

​       前两天有同事咨询：机器A上有个业务客户端，机器B上为服务端，服务端要定期探活客户端，当客户端访问不通时服务端应当摘除这个客户端节点。现在要验证下当客户端访问不通时服务端能否正常摘除节点，于是使用了iptables的ip封禁功能。在机器A上封禁机器B的ip后，在封禁期间服务B无法请求服务A，但是当取消机器A上的ip封禁后，服务B尽然收到了来自服务A的响应！

​     遇到这个问题我的第一反应是服务B是不是有什么重试机制，由于服务A访问不通所以多重试了几次，收到的响应其实是重试后的响应。在得到业务同学否定的回答后，我开始怀疑是否是tcp层做了重试。



### 问题复现

#### 先封禁，再建连

准备两台机器A和B, ip分别为：10.48.22.221（对应下文dev01）和10.171.170.104(对应下文test02). 笔者当时使用的iptables命令如下，含义是拒绝来自ip的包和发向ip的包：

```
iptables -I INPUT -s xxxx -j REJECT
iptables -I OUTPUT -d xxx -j REJECT
```

第一步：添加规则

在dev01上添加上述两条规则

![](http://cdn.cindafeng.com/%E6%96%87%E7%AB%A0iptables%E5%B0%81%E7%A6%81/1.png)



使用iptables -L查看，可以发现添加成功

第二步：dev01监听端口

使用`nc -l 1234`在dev01上监听1234端口

![](http://cdn.cindafeng.com/ip-forbidden/2.png)

使用`netstat -apn|grep 1234`查看1234端口，发现已经处于监听状态

![](http://cdn.cindafeng.com/ip-forbidden/3.png)



第三步骤：test02发起连接

在test02机器上使用`nc 10.171.170.104 1234`向dev01发起连接

![](http://cdn.cindafeng.com/ip-forbidden/4.png)

在dev01上使用`tcpdump host 10.48.22.221`命令进行抓包

![](http://cdn.cindafeng.com/ip-forbidden/6.png)

可以看到，dev01收到了test02的SYNC包（三次握手的第一次握手），但是由于dev01没有发送响应包，所以test01会进行重试，重试几次后，自动停止建连，在test02上使用`netstat -apnc|grep 1234`命令查看的结果也能验证这一点

![](http://cdn.cindafeng.com/ip-forbidden/7.png)



至此，可以得到

**结论一**：**在TCP建立连接阶段，使用**

```
iptables -I INPUT -s xxxx -j REJECT
iptables -I OUTPUT -d xxx -j REJECT
```

**是可以阻止TCP建立连接的。**



#### 先建连，再封禁

既然先封禁、再建连是符合我们预期的，那本文开始提到的问题：封禁取消后发送端会收到响应包，有没有可能是基于已经建立好的TCP连接进行封禁的呢？

先清除之前在dev01上建立的规则：

![](http://cdn.cindafeng.com/ip-forbidden/8.png)



使用`nc -l 1234`在dev01上监听端口，

![](http://cdn.cindafeng.com/ip-forbidden/9.png)

使用`nc 10.171.170.104 1234`在test02上发起连接：

![](http://cdn.cindafeng.com/ip-forbidden/10.png)

可以看到TCP连接已经建立

![](http://cdn.cindafeng.com/ip-forbidden/11.png)



在dev01上写入规则：

![](http://cdn.cindafeng.com/ip-forbidden/12.png)

在test2上发送数据包

![](http://cdn.cindafeng.com/ip-forbidden/13.png)

可以发现，由于没有收到ack, test2一直在尝试发送同一个数据包



此时，如果删除dev1上的规则，会怎样呢？

![](http://cdn.cindafeng.com/ip-forbidden/14.png)

果然，test2收到来自dev1的ack.

至此，我们得到

**结论二**：**在已建立TCP连接后，使用**

```
iptables -I INPUT -s xxxx -j REJECT
iptables -I OUTPUT -d xxx -j REJECT
```

**不会断开已有连接，发送端会不断重试，如果通信恢复，发送端会收到之前的ack.**



### 如何解决

目前已经知道了问题所在，那如何解决呢？查看iptables相关命令可以发现，iptables命令可以指定协议，并且对于TCP命令可以指定参数，比如默认的`--reject-with icmp-port-unreachable`，也可以显式为TCP协议添加参数`--reject-with tcp-reset`. 从名字就可以看出，tcp-reset会使当前已建立的TCP连接立即重置，看起来应该可以解决建连后ip封禁不生效的问题，接下来就测试一下吧。



#### 先封禁，再建连

在dev01上使用命令

```
iptables -I INPUT -p tcp -s 10.48.22.221 -j REJECT --reject-with tcp-reset
iptables -I OUTPUT -p tcp -d 10.48.22.221 -j REJECT --reject-with tcp-reset
```

dev01监听1234端口，test02发起连接，效果同上，test02会不断重试SYNC包。

看来该命令对于未建连的TCP是生效的。



#### 先建连，再封禁

建连后同样使用命令

```
iptables -I INPUT -p tcp -s 10.48.22.221 -j REJECT --reject-with tcp-reset
iptables -I OUTPUT -p tcp -d 10.48.22.221 -j REJECT --reject-with tcp-reset
```

在dev01上封禁test02,然后test02尝试发送数据包，诡异的事情出现了，test02并没有如我们所期望的那样收到dev01的RESET响应

![](http://cdn.cindafeng.com/ip-forbidden/15.png)

难道说是iptables的OUTPUT策略吧reset包给拦截了？

在建连之后只给dev01写入一条INPUT策略试下：

![](http://cdn.cindafeng.com/ip-forbidden/16.png)

果然，这时候test发送数据包后立即收到了RESET包

![](http://cdn.cindafeng.com/ip-forbidden/17.png)



至此，我们得到

**结论三**：**对于已建连的TCP，使用命令**

```
iptables -I INPUT -p tcp -s 10.48.22.221 -j REJECT --reject-with tcp-reset
```

**可以使TCP连接立即断开。**

**结论四**：**iptables OUTPUT策略和INPUT策略会互相影响，由INPUT导致的响应包会被OUTPUT策略给拦截。**



### 总结一下

本文主要介绍了使用iptables命令进行ip封禁的排查之路，之中会涉及到很多网络知识，希望对各位小伙伴有所帮助。

