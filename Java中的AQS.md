---
title: Java中的AQS
date: 2019-10-17 13:47:12
updated: 2019-10-17 13:47:12
tags: AQS
categories: Java
---

`AbstractQueuedSynchronizer`  简写`AQS`, 队列同步器，是用来构建锁或者其他同步组件的基础框架，`Lock`接口的实现，如`ReentrantLock`等都有它的身影，都是通过它来实现线程同步的。从名字可以看出，首先它是个同步器，其次它里面还有个队列。



 AQS使用了模板方法模式，这意味着AQS类里面大体有两种方法：需要被子类重写的涉及到具体细节的方法和模板方法，而模板方法就大致刻画了这个方法的整体功能。

看下AQS提供的需要重写的方法

### 需要重写的方法

#### 独占式

`boolean tryAcquire(int arg)`

```java
protected boolean tryAcquire(int arg) {
        throw new UnsupportedOperationException();
    }
```

独占式获取的具体操作。通过CAS设置state



`boolean tryRelease(int arg)`

```java
protected boolean tryRelease(int arg) {
        throw new UnsupportedOperationException();
    }
```

独占式释放的具体操作。当前线程释放同步状态，队列中接下来的线程则有机会获得同步状态。



#### 共享式

`int tryAcquireShared(int arg)`

```java
protected int tryAcquireShared(int arg) {
        throw new UnsupportedOperationException();
    }
```

共享式获取同步状态。



`boolean tryReleaseShared(int arg)`

```java
protected boolean tryReleaseShared(int arg) {
        throw new UnsupportedOperationException();
    }
```

共享式释放同步状态



#### 番外

`boolean isHeldExclusively()`

```java
protected boolean isHeldExclusively() {
        throw new UnsupportedOperationException();
    }
```

同步器是否被当前线程独占



而模板方法又分为两类：共享式的锁操作和独占式的锁操作，所谓共享式，指的是多个线程可以同时获取同步状态，独占式指的是同一时间只能有一个线程获取同步状态，其他未获取到同步状态的线程只能排队。

下面我们来看下AQS提供的模板方法：

### 模板方法

#### 独占式

`void acquire(int arg)`

```java
public final void acquire(int arg) {
        if (!tryAcquire(arg) &&
            acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
            selfInterrupt();
    }
```

独占式获取同步状态，不成功则进入同步队列等待，如果进入队列也失败了，则中断自己。



`void acquireInterruptibly(int arg)`

```java
public final void acquireInterruptibly(int arg)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        if (!tryAcquire(arg))
            doAcquireInterruptibly(arg);
    }
```

作用和`acquire()`差不多，唯一不同的是它能够响应中断。



`boolean tryAcquireNanos(int arg, long nanosTimeout)`

```java
public final boolean tryAcquireNanos(int arg, long nanosTimeout)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        return tryAcquire(arg) ||
            doAcquireNanos(arg, nanosTimeout);
    }
```

增加了超时限制，如果一段时间后还没获得同步状态，则返回false.



`boolean release(int arg)`

```java
 public final boolean release(int arg) {
        if (tryRelease(arg)) {
            Node h = head;
            if (h != null && h.waitStatus != 0)
                unparkSuccessor(h);
            return true;
        }
        return false;
    }
```

独占式释放同步状态，唤醒队列中的下一个线程。



#### 共享式

`void acquireShared(int arg)`

```java
public final void acquireShared(int arg) {
        if (tryAcquireShared(arg) < 0)
            doAcquireShared(arg);
    }
```

共享式获取同步状态，如果失败，加入队列。



`void acquireSharedInterruptibly(int arg)`

```java
public final void acquireSharedInterruptibly(int arg)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        if (tryAcquireShared(arg) < 0)
            doAcquireSharedInterruptibly(arg);
    }
```

共享式获取同步状态，且响应中断。



`boolean tryAcquireSharedNanos(int arg, long nanosTimeout)`

```java
public final boolean tryAcquireSharedNanos(int arg, long nanosTimeout)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        return tryAcquireShared(arg) >= 0 ||
            doAcquireSharedNanos(arg, nanosTimeout);
    }
```

共享式获取同步状态，且有超时限制



`boolean releaseShared(int arg)`

```java
public final boolean releaseShared(int arg) {
        if (tryReleaseShared(arg)) {
            doReleaseShared();
            return true;
        }
        return false;
    }
```

共享式释放同步状态。



#### 番外

`Collection<Thread> getQueuedThreads()`

```java
public final Collection<Thread> getQueuedThreads() {
        ArrayList<Thread> list = new ArrayList<Thread>();
        for (Node p = tail; p != null; p = p.prev) {
            Thread t = p.thread;
            if (t != null)
                list.add(t);
        }
        return list;
    }
```

查询线程中的队列集合。



通过上述分析可以看到，通过模板模式的设计，当用户自己想要实现一个同步器时，只需要继承自AQS, 实现那些需要被覆盖的方法，然后对外提供一些接口就行了，就像`ReentrantLock`一样，它的`lock()`,`tryLock()`,`release()`等方法都是调用同步器的`acquire()`,`tryAcquire()`和`release()`方法，对实现者友好，更对用户友好。

