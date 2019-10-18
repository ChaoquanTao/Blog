---
title: Java中的ReentrantReadWriteLock
date: 2019-10-17 21:59:10
updated: 2019-10-17 21:59:10
tags: ReentrantReadWriteLock
categories: Java
---

  `ReentrantReadWriteLock`

看下它的类图

<img src="http://ww1.sinaimg.cn/large/006ImZ0Ogy1g80yg0yrbmj30b10njgme.jpg" alt="rwlock.png" style="zoom:80%;" />

可以看到`ReentrantReadWriteLock`实现了`ReadWriteLock`接口。`ReadWriteLock`就是读写锁的意思，那么问题来了，为什么要有个读写锁呢？为什么要把读锁和写锁分开呢？这里就是出于对性能的考虑了，多个线程之间，可以同时读，但是不可以同时写或者一个读一个写，所以分开之后，读锁和写锁各司其职，可以提高效率。

和`ReentrantLock`锁的实现方法一样，`ReentrantReadWriteLock`也是通过聚合了AQS的实现类来来实加锁和释放锁的功能的。



在`ReentrantReadWriteLock`里面有三个比较重要的内部类，`Sync`,`ReadLock`和`WriteLock`.

其中`Sync`同样继承自AQS，用来做线程同步，它作为成员变量参与到了`ReadLock`和`WriteLock`的定义中。

然后`ReadLock`和`WriteLock`作为静态内部类，都继承自`Lock`接口，在里面实现各自的加锁解锁功能。



写锁的获取（可重入）

其实注释已经写的很清楚了，

1. 如果读数量非零或者写数量非零，或者锁的拥有者是其他线程，则获取锁失败。
2. 如果总的状态数（读数量和写数量的总和）大于阈值，则获取锁失败。
3. 否则获取锁成功，更新状态

简言之，如果锁被读线程（无论是不是当前线程）或者其他写线程占用，则获取写锁失败

![rrw_tryacq.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g81jvgkn8vj30p60hl40d.jpg)

写锁的释放

![rrw_tryrelease.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g81jy2d104j30f205rglz.jpg)



读锁的获取



