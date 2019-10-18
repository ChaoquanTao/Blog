---
title: Java中的Lock
date: 2019-10-16 10:05:07
updated: 2019-10-16 10:05:07
tags: Lock
categories: Java
---

Lock是JUC包中的一个接口，是在`synchronized`关键字之后出现的，用来提供锁的功能，本文主要讨论Lock接口以及其实现类，以及为什么有了synchronized关键字了还要有Lock.

先来看下它的继承关系

![lock.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7zut7fhc7j30co03ldfv.jpg)

我们会主要讨论圈出来的三个实现类

再来看下Lock接口的成员

![lock_member.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7zuvgi6t8j307304rwec.jpg)

其中`lock()`,`tryLock()`,`tryLock(ong, TimeUnit)`以及`lockInterruptibly()`用来加锁，`unlock()`用来解锁。需要注意的是如果使用`lockInterruptibly()`方法来获取锁的话，如果线程没有获取成功而进入等待队列，那么这个线程是可以响应中断的，相比只下，使用`synchronized`关键字获取锁时如果进入等待队列，线程是不能响应中断的。



`Lock`接口只是定义了实现锁的一系列约定，比如`lock()`,`unLock()`以及`tryLock()`等，具体的实现都是交给它的实现类去做的，比如`ReentrantLock`,`ReentrantReadWriteLock.ReadLock`和`ReentrantReadWriteLock.WriteLock`等。而这些实现类能够实现锁功能的关键，在于它们都聚合了一个AQS的实现类，AQS是一个抽象类，通过模板方法模式，提供了一系列状态同步的方法。

对`ReentrantLock`而言，维护的是重入次数state. 它有个内部类Sync，实现了AQS,然后用表示公平锁的类`FairSync`和表示非公平锁的类`NonFairSync`继承`Sync`类，这样就实现了公平锁和非公平锁。需要注意的是，`ReentrantLock`默认是非公平锁，但是我们可以通过构造方法的参数来指定锁的类型，同时，`ReentrantLock`是独占锁，也就是说，它的内部类并没有实现AQS的共享式获取和释放锁的方法。

对`ReentrantReadWriteLock`而言，维护的是多个线程的读次数和一个线程的写次数。 它和`ReentrantLock`类似，但是更为复杂，有个内部类`Sync`实现了`AQS`, 然后又使用`FairSync`和`NonFairSync`继承`Sync`. 然后在内部类`ReadLock`和`WriteLock`中聚合`Sync`.所以`ReadLock`和`WriteLock`就有锁的功能了。需要注意的是，读锁是共享锁，写锁是独占锁。

![rwlock.jpg](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g81ihye5phj30k10lmwjq.jpg)

### ReentrantLock

`ReentrantLock`，顾名思义，可重入锁，意思是：当一个线程获取该锁后，后续线程再次需要访问该锁锁住的内容时，可以直接访问。在[这篇]( [https://inewbie.top/2019/09/17/Java%E4%B8%AD%E7%9A%84ReentryLock/](https://inewbie.top/2019/09/17/Java中的ReentryLock/) )文章里已经介绍过了ReentrantLock,这里再来简单介绍下。

`ReentrantLock`里面有三个内部类`Sync`,`NonfairSync`和`FairSync`，其中`NonfairSync`和`FairSync`继承自`Sync`,分别用来实现非公平锁和公平锁。也就是说，`ReentrantLock`内部是实现了公平锁和非公平锁的。

而且ReentrantLock默认是非公平锁，我们可以通过带布尔参数的构造方法来设置它为公平锁。



