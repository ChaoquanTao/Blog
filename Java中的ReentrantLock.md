---
title: Java中的ReentrantLock
date: 2019-09-17 14:56:35
updated: 2019-09-17 14:56:35
tags: ReentrantLock
categories: Java
---

ReentrantLock, 从名字来看，可重入锁，今天来看下它的具体实现。

它的继承关系如下：

![n5V010.png](https://s2.ax1x.com/2019/09/17/n5V010.png)

以及还有三个内部类：`Sync`,  `NonfairSync `, `FairSync`.其中后两个都继承自Sync，而Sync又继承自[AQS]( [https://inewbie.top/2019/10/17/Java%E4%B8%AD%E7%9A%84AQS/](https://inewbie.top/2019/10/17/Java中的AQS/) )

可以看出，`ReentryLock`是在自己内部实现了公平锁和非公平锁的。

可以看到，`ReentryLock`继承的Lock接口实现了`lock`,`tryLock`, `unLock`等方法, 这也是本文讨论的重点。



先来从整体上把握一下`ReentrantLock`, `ReentrantLock`之所以能有锁的功能，是因为它聚合了AQS类（当然这也是AQS类设计的初衷，AQS通过模板方式模式实现，设计者希望我们自己设计的状态同步组件重写具体的细节类，然后将这个状态同步组件聚合到我们的锁里面），`ReentrantLock`也正是这么做的。

`ReentrantLock`的设计逻辑是这样的：

在AQS中，有模板方法和需要重写的细节方法。模板方法负责搭建获取锁和释放锁的框架，细节方法延迟到子类中去实现。

![aqs.jpg](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g81gruisynj30hc0iawiz.jpg)

上图AQS类中，蓝色方法为模板方法，绿色方法为可能需要覆盖的方法，即在蓝色方法中调用了绿色方法。Sync继承自AQS, 而`NonfairSync`和`FairSync`继承了Sync,相当于最终要在公平锁和非公平锁中实现细节方法。可以看到，共享式的获取锁和释放锁是没有被实现的，所以说，`ReentrantLock`是独占锁。



我们来看下Sync的定义。

![n5eNzq.png](https://s2.ax1x.com/2019/09/17/n5eNzq.png)

![n5efOK.png](https://s2.ax1x.com/2019/09/17/n5efOK.png)

这里`Sync`继承自AQS, 用来实现状态同步。



我们看下`NonfairSync`的实现

![n5mJ0O.png](https://s2.ax1x.com/2019/09/17/n5mJ0O.png)

它实现了父类的lock方法，首先通过CAS设置线程持有锁的状态，如果修改成功，则锁属于当前线程，否则，调用`acquire()`方法. `acquire()`方法在AQS类中实现，

```java
public final void acquire(int arg) {
        if (!tryAcquire(arg) &&
            acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
            selfInterrupt();
    }
```

如果使用`tryAcquire()`获取锁失败，则把这个线程加入等待队列中。（`tryAcquire()`又是在`NonFairSync`中实现的，有点绕，它的实现又调用了父类Sync中的`nonfairTryAcquire()`方法）

![n5K039.png](https://s2.ax1x.com/2019/09/17/n5K039.png)



公平锁`FairSync`

![1568705713770](C:\Users\Arrow\AppData\Roaming\Typora\typora-user-images\1568705713770.png)

可以看到，相比于非公平锁的lock方法，公平锁的lock方法一开始执行就是排队，即acquire()方法，而非公平锁的lock方法上来二话不说就是先插队，即通过CAS改变自身持有该锁的状态

对于`tryAcquire()`方法，公平锁的判断条件里多了一个自己是否在队列首的判断。