---
title: 同步与异步，阻塞与非阻塞
date: 2019-12-20 22:13:46
updated: 2019-12-20 22:13:46
tags: IO模型
categories: OS
---

> 同步与异步，阻塞与非阻塞这几个词可以说是很常见了，但是网络上关于它们的解释却又众说纷纭，其中一个主要原因就是我们是在脱离了上下文在谈论这个问题，所以本文主要是基于Network IO来讨论。

在《UNIX网络编程：套接字联网API》一书中，一共比较了五种IO模型：

+ 阻塞式IO (blocking IO)
+ 非阻塞式IO (non-blocking IO)
+ IO多路复用（IO multiplexing）
+ 信号驱动式IO ()
+ 异步IO (asynchronous IO)

在正式开始讨论这五种IO模型之前，让我们先明确一件事：一个IO操作通常包括两个阶段：

1. 等待数据准备好
2. 从内核向进程复制数据

对应到Socket 的输入操作时，就是首先等待数据从网络中到达，然后将数据从内核缓冲区复制到进程缓冲区 （看不懂没关系，下面有图的）。



#### 阻塞式IO

开局一张图：

![AcroRd32_FAT9QJ8uGD.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga451qpoikj30p40dcdhb.jpg)

这里`recvfrom`是一个系统调用，当应用进程调用了这个系统调用后，当前进程从用户态切换到内核态，然后内核开始IO的第一阶段：等待数据。当数据准备好之后（比如从网络上接收到了完整的数据包），此时数据是在内核缓冲区的，然后操作系统会把数据从内核缓冲区复制到用户空间，并返回成功指示。

需要注意的是，在等待数据和拷贝数据阶段，应用进程都在阻塞。



#### 非阻塞式IO

继续上图：

![AcroRd32_3DYB0dlHhK.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga45h5qzymj30su0exgob.jpg)

我们把非阻塞式IO和上面的阻塞式IO对比来看。对于阻塞式IO，在等待数据阶段，如果数据还没准备好，内核这边也不吭声，应用进程在那死等 （即阻塞应用进程），直到返回结果。

而非阻塞式则不一样，当内核态这边收到这个系统调用后，如果数据还没准备好，它会先返回给应用进程一个错误信息，告诉应用进程数据还没准备好，应用进程知道后，可以先转去做其他事情，待会儿再来询问一下 （我们称之为轮询，polling），如此反复，直到有一回数据准备好了，这时候操作系统将数据从内核复制到用户空间，并且在此期间，应用进程是阻塞的。

所以对于非阻塞式IO来说，在数据准备阶段，应用进程不阻塞，在数据拷贝阶段，仍然阻塞。



#### IO多路复用

IO multiplexing, 有些地方也叫 event driven IO. 其核心在于：使用单个进程就可可以同时处理多个网络连接的IO，它主要是基于`select`函数或者`poll`函数来实现的。

![AcroRd32_W5THNghti5.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga463h690qj30ro0emdig.jpg)

基本原理是这样的：一个`select`函数它可以负责监控多个`socket`，准确的来说，我们可以调用`select`告知内核我们对哪些描述符（读、写或异常）感兴趣，然后`select`回去轮询我们感兴趣的这些事件，当其中的一个或者多个事件发生时，它就会告诉通知一下应用进程说：“嗨，你感兴趣的某某某出现了”。然后引用进程此时再发起系统调用`recvfrom`，此时就没有数据准备阶段了，而是直接数据拷贝，在此过程中应用进程依然阻塞。

> 可以看到的是，相比于阻塞式IO，这里的多路复用似乎性能更差，因为它有两个系统调用（select, `recvfrom`）而阻塞式IO只有一个（`recvfrom`）.

> 多路复用的优势不是说处理单个连接能有多快，而是可以单进程处理多个连接。



#### 信号驱动式IO

我们也可以使用信号，让内核在描述符就绪时就发送`SIGIO`信号通知我们，这种模型称之为信号驱动式IO。

![AcroRd32_syDKV3Mefv.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga46f1kwetj30sx0fsjtm.jpg)

首先我们需要开启套接字的信号驱动式IO功能，并通过`sigaction`系统调用安装一个信号处理函数。该系统调用立即返回，应用进程继续工作 (即没有被阻塞)，当数据准备好后，内核发送`SIGIO`到应用进程。然后应用进程再调用`recvfrom`读取数据。

它的优势在于在等待数据期间应用进程不被阻塞。



#### 异步IO

上面介绍的几种IO模型中，在第二个数据拷贝阶段都是阻塞的。异步IO则不然，它的工作机制是：告诉内核去完成某个动作，然后内核完成后再去告知应用进程。在这整个过程中，应用进程都是没有被阻塞的。

![AcroRd32_IqXmkVJ2j9.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga4c1jw7mgj30ro0gv408.jpg)



### 各种IO模型比较

下图对比了上述五种IO模型的对比。可以看出，对于前四种，在第二阶段都是阻塞的，而异步IO则不同，它全程无阻塞。

![AcroRd32_AGbGX6kjYK.png](http://ww1.sinaimg.cn/large/005UcYzagy1ga4c2mqz9mj30v10h40vq.jpg)



#### 同步IO？ 异步IO？

我们先看下POSIX对同步IO和异步IO的定义：

>A synchronous I/O operation causes the requesting process to be blocked until that I/O operation completes;
>An asynchronous I/O operation does not cause the requesting process to be blocked;

翻译过来就是说：

同步IO：导致请求进程阻塞，直到IO操作完成

异步IO：不会造成请求进程阻塞



按照这个定义，那么上面的五种IO模型中，哪几个在IO操作的时候会应用进程会被阻塞呢？

前四种都是。（这里需要注意，这里指的是IO操作，即`recvfrom`这一系统调用，在数据从内核复制到用户空间这一过程中，前四种都是阻塞的，除了异步IO模型）



### 总结

让我们来总结一下上面提到的几种IO模型：

+ 阻塞式IO：全程死等
+ 非阻塞式IO: 应用进程不断轮询直到数据准备好，然后进行数据拷贝，在此期间应用进程阻塞
+ 多路复用IO: 其实它也是一种轮询，与非阻塞式IO不同的是：
  + 非阻塞式IO中是应用进程主动轮询，而多路复用IO中是通过`select`系统调用让内核去轮询的，轮询期间应用进程被`select`系统调用阻塞
  + 多路复用IO中`select`可以同时关注多个socket的IO，从而实现了单进程管理多个socket IO
+ 信号驱动式IO：数据准备过程中不阻塞，数据拷贝过程中阻塞。
+ 异步IO：全程不阻塞，内核完成任务后告知应用进程一声就好。

> 这里讲的同步异步，阻塞非阻塞只是针对Socket IO来讲的，如果换个背景，定义可能会有所不同。