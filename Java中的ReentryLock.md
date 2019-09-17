---
title: Java中的ReentryLock
date: 2019-09-17 14:56:35
updated: 2019-09-17 14:56:35
tags: ReentryLock
categories: Java
---

ReentryLock, 从名字来看，可重入锁，今天来看下它的具体实现。

它的继承关系如下：

![n5V010.png](https://s2.ax1x.com/2019/09/17/n5V010.png)

以及还有三个内部类：`Sync`,  `NonfairSync `, `FairSync`.其中后两个都继承自Sync

可以看出，`ReentryLock`是在自己内部实现了公平锁和非公平锁的。

可以看到，`ReentryLock`继承的Lock接口实现了`lock`,`tryLock`, `unLock`等方法, 这也是本文讨论的重点。



有个Sync类型的成员变量sync, 我们先来看下Sync的定义。

![n5eNzq.png](https://s2.ax1x.com/2019/09/17/n5eNzq.png)

![n5efOK.png](https://s2.ax1x.com/2019/09/17/n5efOK.png)

上文说到，`NonfairSync `, `FairSync`都继承自Sync, 所以lock方法是留给自类实现的。



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

如果使用`tryAcquire()`获取锁失败，则把这个线程假如等待队列中。（`tryAcquire()`又是在`NonFairSync`中实现的，有点绕，它的实现又调用了父类Sync中的`nonfairTryAcquire()`方法）

![n5K039.png](https://s2.ax1x.com/2019/09/17/n5K039.png)



公平锁`FairSync`

![1568705713770](C:\Users\Arrow\AppData\Roaming\Typora\typora-user-images\1568705713770.png)

可以看到，相比于非公平锁的lock方法，公平锁的lock方法一开始执行就是排队，即acquire()方法，而非公平锁的lock方法上来二话不说就是先插队，即通过CAS改变自身持有该锁的状态

对于`tryAcquire()`方法，公平锁的判断条件里多了一个自己是否在队列首的判断。