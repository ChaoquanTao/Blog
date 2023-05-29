---
title: 聊一聊linux中的tc命令
date: 2023-05-25 21:00:00
categories: Linux
---

>最近杂事太多，又是组织架构调整，又是换工作，最近终于有空能写下这边文章了。

tc (Traffic Controll) 作为linux中的流量控制工具，功能非常强大，可以对网络流量的速率、延迟、带宽等进行控制。本文主要介绍tc命令的结构和使用，多数内容来自于对参考文章的翻译和整理，并增加了一些解释和说明，帮助大家在工作中能够快速理解和使用该命令。



## 什么是tc命令?

一言以蔽之，tc是linux中的一个流量控制工具，它能够控制指定类型的网络包以指定的速率和指定的顺序从指定网卡进来或出去。



## tc命令有什么用

基于tc命令的强大能力，我们可以做很多有趣的事，比如我们可以对网络带宽按照流量类型进行限速，可以帮助我们限制特定应用程序或网络接口的带宽使用；在实际的开发过程中，可以使用tc命令去模拟一些网络延迟、网络丢包的故障，以此验证我们的系统能否应对网络抖动。



## tc的原理

> 这部分的内容比较生硬，如果大家看着比较懵的话，可以先看下一节如何使用的部分，然后带着疑问来看这一节。

tc在逻辑上是一个树状结构，主要由以下队列(qdisc)，类别(class)，过滤器(filter)构成，其中队列和类别可以附着过滤器，用于对当前队列中的流量进行过滤和匹配，并将命中的流量发往下一级，大致结构如下：

![](http://cdn.inewbie.top/tc/tc.png)

### qdisc

qdisc (queue discipline)即队列，linux网络中每个进入网卡的流量都会进入一个队列，队列分为有类别的队列 (classful qdiscs)和无类别的队列 (classless qdiscs)，有类别的队列下可以添加一个类别 (class)，这个类别上可以挂载过滤器 (filter)；无类别队列顾名思义，里面不能添加分类，是一种比较简单的队列。tc默认的队列的fifo (先进先出队列)。

> 我们在使用中会常看到root qdisc, 其指的是出站(egress)的根队列，tc的大多数配置也都是在出站队列里配的，而非入站(ingress)队列，这是因为入站队列能够配置的规则有限，不如出站队列的配置灵活。



#### qdisc分类

qdisc分类如下，每种队列的适用场景不同，下面是这些队列一般性的定义：

1. **pfifo (Packet First-In, First-Out)**: 使用简单的FIFO排队算法进行数据包调度，按照先到先服务的原则进行处理。
2. **bfifo (Byte First-In, First-Out)**: 类似于pfifo，但按照数据包的字节数进行调度和处理。
3. **sfq (Stochastic Fairness Queueing)**: 使用随机公平队列调度算法，将数据包分配到多个小队列中，以实现公平的带宽共享。
4. **tbf (Token Bucket Filter)**: 使用令牌桶算法对数据包进行调度和控制，限制传输速率和突发传输量。
5. **htb (Hierarchical Token Bucket)**: 提供层次化的流量控制和优先级管理，可以创建多个子队列和子类别，并为每个子队列应用不同的流量控制策略。
6. **prio (Priority Queueing)**: 允许用户为不同的数据流设置不同的优先级，数据包按照优先级进行排队和发送。
7. **red (Random Early Detection)**: 使用随机早期检测算法对数据包进行调度，以避免网络拥塞和数据包丢失。
8. **cbq (Class-Based Queueing)**: 提供基于类别的队列调度和流量管理，可以根据不同的类别设置不同的带宽限制和优先级。



### class

class即类别，类别是以递归的结构依附于队列存在的，即队列下可以添加类别，而类别下又可以添加子类别或队列。每个类别会包含一个或多个过滤器 (filter)，这些过滤器可以用于筛选哪些流量可以进入哪些子类别或子队列。



### filter

filter即过滤器，filter可以依附于class或qdisc，用以过滤哪些流量可以进入下一阶段。作为一个filter：

+ 必须包含一个classifier
+ 可以包含一个policer



#### classifier

classifier即过滤器，用以确定要将数据包发往哪个类别。最常见的就是u32过滤器，可以认为classifier是filter的一部分，用来识别流量包的一些特征属性。



#### policer

也是filter的一部分。可以限制网络包入队的速率，可以用于丢弃(drop)网络包。



### handle

用于标识class或classful qdisc,  由major number和minor number组成：

+ major number: 可以随便命名
+ Minor numner: 如果为0，表示当前handle未qdisc，其他非0数字表示当前handle为class，同一父节点下的class的minor number相同。

​	> ffff:0表示入站队列

```
 										root 1:
                      |
                    _1:1_
                   /  |  \
                  /   |   \
                 /    |    \
               10:   11:   12:
              /   \       /   \
           10:1  10:2   12:1  12:2
```

对于上述结构，root 1: 表示根队列，根队列下有一个类别1:1，类别下有三个队列10:，11:, 12:，队列10:下有10:1和10:2两个类别，队列12:下有12:1和12:2两个类别。

## 如何使用

经历上面这些生硬的概念后，下面我们从实战出发，看下tc命令的使用。

### case 1: 添加一个队列

```
tc qdisc add    \   ①
>  dev eth0     \   ②
>  root         \   ③
>  handle 1:0   \   ④
>  htb              ⑤
```

1. `tc qdisc add`: 添加一个队列调度器规则。
2. `dev eth0`: 指定要应用该规则的网络接口，这里是以太网接口eth0。
3. `root`: 指定该规则为根（root）队列，即出站队列egress，表示它是队列调度器的顶层队列。
4. `handle 1:0`: 指定队列的处理标识符（handle），这里是1:0。该标识符用于唯一标识该队列，第一个数字可以随意指定，第二个数字为0表示队列，也可以简写为1:。
5. `htb`: 指定队列调度器的类型为"Hierarchical Token Bucket"（层次令牌桶）类型，它是一种流量调度算法。



### case 2: 添加一个简单class

```shell
tc class add    \     ①
>    dev eth0     \   ②
>    parent 1:1   \   ③
>    classid 1:6  \   ④
>    htb          \   ⑤
>    rate 256kbit \   ⑥
>    ceil 512kbit     :seven
```

1. `tc class add`: 添加一个类别规则。
2. `dev eth0`: 指定要应用该规则的网络接口，这里是以太网接口eth0。
3. `parent 1:1`: 指定父类别的标识符，该类别是1:1，由于minor number非0，表示parent也是个class。
4. `classid 1:6`: 指定当前类别的标识符，该类别是1:6。
5. `htb`: 指定类别的类型为"Hierarchical Token Bucket"（层次令牌桶）类型，它是一种流量控制算法。
6. `rate 256kbit`: 设置类别的最大传输速率为256 kbit/s，表示流量在该类别中的传输速率不会超过该值。
7. `ceil 512kbit`: 设置类别的上限传输速率为512 kbit/s，表示流量在该类别中可以突发性地达到该值，但不会持续超过该值。



### case 3: 添加一个优先级队列

```
# tc qdisc add dev eth0 root handle 1: prio 
## 创建优先级队列时会默认创建 1:1, 1:2, 1:3三个类别
  
# tc qdisc add dev eth0 parent 1:1 handle 10: sfq
# tc qdisc add dev eth0 parent 1:2 handle 20: tbf rate 20kbit buffer 1600 limit 3000
# tc qdisc add dev eth0 parent 1:3 handle 30: sfq      
```

上面的命令创建的队列结构为:

```
root 1: prio
       /   |   \
     1:1  1:2  1:3
      |    |    |
     10:  20:  30:
     sfq  tbf  sfq
band  0    1    2
```



对于上述配置，不免会有一个疑问，已经配置了优先级队列，但是当有网络包来临时，应当如何判断当前网络包的优先级呢？这里其实就涉及到filter了，需要为根队列配置filter，根据filter的过滤结果将数据包发往下一级队列或类别。



### case 4: 为队列添加filter (classifier方式)

```
# tc qdisc add dev eth0 root handle 10: prio                         （1）
# tc filter add dev eth0 protocol ip parent 10: prio 1 u32 match \   （2）
  ip dport 22 0xffff flowid 10:1																		 
# tc filter add dev eth0 protocol ip parent 10: prio 1 u32 match \   （3）
  ip sport 80 0xffff flowid 10:1
# tc filter add dev eth0 protocol ip parent 10: prio 2 flowid 10:2   （4）
```

解释如下：

（1）创建了一个根队列（root qdisc）并将其标识符设置为10:

（2）添加了一个过滤器规则，该规则应用于根队列的子类别10:1。它使用prio优先级为1，并使用u32分类器来检查目标端口是否为22的IP数据包。如果匹配成功，该数据包将被发送到flowid为10:1的子类别进行进一步处理

   (3) 添加了另一个过滤器规则，也应用于根队列的子类别10:1。它使用prio优先级为1，并使用u32分类器来检查源端口是否为80的IP数据包。如果匹配成功，该数据包将被发送到flowid为10:1的子类别进行进一步处理

 （4）添加了第三个过滤器规则，应用于根队列的子类别10:2。它使用prio优先级为2，并将所有不符合第二条和第三条过滤器郭泽的数据包发送到flowid为10:2的子类别中进行处理。

上面的prio 1或prio 2决定了数据包被过滤器处理的顺序，因为prio 1的优先级高于prio 2, 所以当数据包来临时，prio 1的过滤器会先对数据包进行匹配，如果匹配不上，才会轮到prio 2所指的过滤器进行处理。



### case 5: 为队列添加filter (policer方式)

```shell
# tc filter add               \ 							  (1)
>                  dev eth0                 \  （2）
>                  parent 1:0               \   (3)
>                  protocol ip              \  (4)
>                  prio 5                   \  (5)
>                  u32                      \  (6)
>                  match ip port 22 0xffff  \  (7)
>                  match ip tos 0x10 0xff   \  (8)
>                  flowid 1:6               \  (9)
>                  police                   \  (10)
>                  rate 32000bps            \  (11)
>                  burst 10240              \  (12)
>                  mpu 0                    \  (13)
>                  action drop/continue        (14)
      
```

1. `tc filter add`: 添加一个过滤器规则。
2. `dev eth0`: 指定要应用该规则的网络接口，这里是以太网接口eth0。
3. `parent 1:0`: 指定父类别的标识符，该类别是1:0。这表示该过滤器规则将应用于标识符为1:0的父类别。
4. `protocol ip`: 指定过滤器规则的协议为IP协议，这意味着该规则将应用于IP数据包。
5. `prio 5`: 设置过滤器规则的优先级为5。优先级越高的规则将首先匹配和处理数据包。
6. `u32`: 指定过滤器匹配规则的类型为u32，表示使用32位的匹配规则。
7. `match ip port 22 0xffff`: 设置匹配规则，仅匹配目标端口号为22（SSH端口）的数据包。
8. `match ip tos 0x10 0xff`: 设置匹配规则，仅匹配TOS（Type of Service）字段为0x10的数据包。
9. `flowid 1:6`: 指定匹配的数据包将被发送到标识符为1:6的类别。
10. `police`: 启用流量控制（policing）机制，用于限制匹配的数据包的传输速率。
11. `rate 32000bps`: 设置流量控制的传输速率为32000 bps（比特每秒），即限制匹配的数据包的传输速率。
12. `burst 10240`: 设置允许的最大突发传输量为10240字节，表示数据包可以在短时间内突发性地达到该大小。
13. `mpu 0`: 设置最小传输单元（Minimum Packet Unit）为0，表示不进行进一步的分片处理。
14. `action drop/continue`: 指定匹配的数据包将被丢弃或继续处理，这取决于具体的配置需求。



## 写在最后

tc命令强大，并且复杂， 光是其中的队列类型就有很多可以探究的地方，要以一篇文章总结tc的所有用法也不现实。本文旨在为读者提供一个tc的快速入门，帮助读者能够快速了解tc命令，希望对大家有用。



## 参考文章

https://tldp.org/HOWTO/html_single/Traffic-Control-HOWTO/#software

https://tldp.org/HOWTO/Adv-Routing-HOWTO/index.html



