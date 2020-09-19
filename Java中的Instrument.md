---
title: Java中的Instrument
date: 2020-09-04 22:00:00
categories: Java
tags: Instrument
---

#### 前言

在[之前]([http://123.56.245.109/2020/08/30/Blog/ASM%E5%AD%97%E8%8A%82%E7%A0%81%E6%B3%A8%E5%85%A5/](http://123.56.245.109/2020/08/30/Blog/ASM字节码注入/))的文章里我们介绍了ASM字节码框架，使用它可以动态的修改class文件。但是仔细一想，你会发现仅仅ASM并不能真正用于生产，为什么？假如你已经有一个在运行的系统了，现在想要做一些字节码修改的动作，难道我们要去修改源代码吗？麻烦不说，而且污染了本来的系统。



所以我们就考虑，有没有什么方法，可以实现动态的无污染的织入，这就要引入今天的主角，Instrument了。



#### 正文

Instrument是`Javaagent`的一种具体实现，那`javaagent`又是什么？如果你在终端里输入`java`(当然前提是你已经安装了jdk),  你会看到这么几个参数：

![wA3cNR.png](https://s1.ax1x.com/2020/09/04/wA3cNR.png)

其中，`-javaagent`就是我们所说的，jdk提供的`Instrument`允许我们在jvm启动或者运行时，动态地拦截要加载的类，并对其进行修改。无论是启动时还是运行时，其大致原理都是把我们的修改代码封装成一个Jar包，然后想办法让目标jvm进程加载。

##### instrument介绍



##### 启动时加载instrument agent

主要用到了`premain()`方法

##### 运行时加载instrument agent

主要用到了`agentmain()`方法

##### instrument原理



##### 使用instrument有什么问题

TODO:

+ 类隔离
+ 反射