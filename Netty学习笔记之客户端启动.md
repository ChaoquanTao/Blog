---
titie: Netty学习笔记之客户端启动
categories: Java
tags: Netty
---

在上一篇文章中，讨论了netty服务端启动的大概流程，这篇文章将会继续看下客户端启动流程。

### 总览

一般的客户端长这样，真正的入口要从`bootstrap.connect`看起。

<img src="http://tvax2.sinaimg.cn/large/006ImZ0Ogy1h0xhyutw28j31bm10yape.jpg" alt="image" style="zoom:40%;" />



### 分析

进入`connect`方法的最终调用在这里：

<img src="/Users/chaoquantao/Library/Application Support/typora-user-images/image-20220404105736798.png" alt="image-20220404105736798" style="zoom:33%;" />

如果已经看过服务端启动流程，会发现这里和服务端的代码神似，都是先`initAndRegister`,如果注册成功，则直接执行`doResolveAndConnect0`,否则就添加一个监听器，当监听器触发的时候执行`doResolveAndConnect0`. 事实上`initAndRegister`的逻辑都是一样的，因为都是走的都是`Bootstrap.initAndRegister()`. 我们只需要关注`doResolveAndConnect0`做了什么即可。



#### `doResolveAndConnect0`

<img src="/Users/chaoquantao/Library/Application Support/typora-user-images/image-20220404111042034.png" alt="image-20220404111042034" style="zoom:50%;" />

这里熟悉的异步操作又又又又来了：首先异步执行`resolver.resovle()`,并返回一个`future`,后续会根据`future`来判断`resolve`动作是否完成。如果它完成了，则执行`doConnect`，否则给`future`注册一个`listener`,等到`resovle`完成的时候会触发这个`listener`，进而执行`doConnect`.

<img src="http://tvax1.sinaimg.cn/large/006ImZ0Ogy1h0xs8mhp8yj31h80jq4ag.jpg" alt="image" style="zoom:40%;" />

最终的connect走的是`pipeline`的`connect`方法

<img src="http://tvax1.sinaimg.cn/large/006ImZ0Ogy1h0xsbvthbrj312y0600vg.jpg" alt="image" style="zoom:50%;" />

继续，

<img src="http://tvax3.sinaimg.cn/large/006ImZ0Ogy1h0xsd28w4dj315i06e41p.jpg" alt="image" style="zoom:50%;" />

这个`tail`是个`ChannelHandlerContext`,也就是`pipeline`的主要内容，

<img src="http://tvax1.sinaimg.cn/large/006ImZ0Ogy1h0xsdrrhglj312i064adl.jpg" alt="image" style="zoom:50%;" />



