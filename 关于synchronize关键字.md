---
title: 关于synchronized关键字
date: 2019-07-04 14:45:10
updated: 2019-07-04 14:45:10
tags:
categories: java
---

`synchronized`关键字可以用来修饰方法，也可以用来修饰代码块，但是底层的实现有所不同。对于同步方法，JVM采用`ACC_SYNCHRONIZED`标记符来实现同步。 对于同步代码块。JVM采用`monitorenter`、`monitorexit`两个指令来实现同步。

Q1: `synchronized`关键字如何实现原子性？

​	通过`moniterenter`和`moniterexit`两个指令保证代码块在同一时间内只能被同一线程访问。

Q2: `synchronized`关键字如何实现可见性？

​	对于`sybchronized`关键字，有一条规定是这样的，在对代码块解锁前，需要先把里面的变量同步到主存中，以此来保证可见性。