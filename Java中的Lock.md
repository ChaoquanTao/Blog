---
title: Java中的Lock
date: 2019-10-16 10:05:07
updated: 2019-10-16 10:05:07
tags: Lock
categories: Java
---

> Lock是JUC包中的一个接口，是在`synchronized`关键字之后出现的，用来提供锁的功能，本文主要讨论Lock接口以及其实现类，以及为什么有了synchronized关键字了还要有Lock.

`synchronized`作为内嵌的Java关键字，其可以隐式地获取和释放锁，它简化了同步的管理，同时也固化了锁的获取和释放，缺少灵活性。

在Java SE 5 之后，新增了`Lock`接口（以及相关实现类），相比于`Synchronized`关键字，它需要显式的获取和释放锁，同时增加了超时获取、响应中断等方法。



先来看下它的实现关系

![lock.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7zut7fhc7j30co03ldfv.jpg)

我们会主要讨论圈出来的三个实现类

再来看下Lock接口的成员

![lock_member.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7zuvgi6t8j307304rwec.jpg)

其中`lock()`,`tryLock()`,`tryLock(ong, TimeUnit)`以及`lockInterruptibly()`用来加锁，`unlock()`用来解锁。需要注意的是如果使用`lockInterruptibly()`方法来获取锁的话，如果线程没有获取成功而进入等待队列，那么这个线程是可以响应中断的，相比只下，使用`synchronized`关键字获取锁时如果进入等待队列，线程是不能响应中断的。



`Lock`接口只是定义了实现锁的一系列约定，比如`lock()`,`unLock()`以及`tryLock()`等，具体的实现都是交给它的实现类去做的，比如`ReentrantLock`,`ReentrantReadWriteLock.ReadLock`和`ReentrantReadWriteLock.WriteLock`等。而这些实现类能够实现锁功能的关键，在于它们都聚合了一个AQS的实现类，AQS是一个抽象类，通过模板方法模式，提供了一系列状态同步的方法。





