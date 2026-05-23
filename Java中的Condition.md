---
title: Java中的Condition
date: 2019-11-12 13:26:50
updated: 2019-11-12 13:26:50
tags: Lock
categories: Java
---

> 前面的文章中，我们了解了Java中的`Lock`接口，以及相关的实现类`ReentrantLock`、`ReentrantReadWriteLock`。它们都是通过聚合一个`AQS`来实现的。同时讨论了为什么有了`Synchronized`关键字之后还要有`Lock`。
>
> 我们知道`Synchronized`关键字是`Monitor`机制在Java中的一种具体实现，每个对象都有`wait()`、`notify()`和`notifyAll()`方法来进行线程通信。
>
> 那么问题来了，在提出了`Lock`之后，我们使用`Lock`加锁的时候有没有类似的一组监视器方法呢？这就是我们今天要讨论的`Condition`接口。`Condition`接口和`Object`类的监视器方法有相同又有不同。	



#### 定义

先来看下`Condition`接口里定义的方法：

![M1DemT.png](https://s2.ax1x.com/2019/11/12/M1DemT.png)

是不是和`Object`中定义的方法很类似。



#### 使用

`ConditionObject`类实现了`Condition`接口，作为一个AQS的内部类，所以它的创建依靠于`Lock`对象，通过`newCondition()`方法创建它。

使用也十分简单，但是记得使用时要加锁。

```java
Lock lock = new ReentrantLock() ;
Condition condition = lock.newCondition();

//线程A
lock.lock();
try {
    condition.await();
} catch (InterruptedException e) {
    e.printStackTrace();
}finally {
    lock.unlock();
}

//线程B
lock.lock();
try{
    condition.signal();
}catch(InterruptedException e){
    e.printStackTrace();
}finally{
    lock.unlock();
}
```



> 阻塞队列就是使用`Condition`来实现生产者和消费者的通信的



#### 实现

`Condition`作为`AQS`的内部类被实现，所以它是可以共享一些`AQS`的资源的。

`Condition`的实现有三个关键点：等待队列、等待和通知。



##### 同步队列和等待队列

同步队列：线程获取同步状态失败时会进入的队列，首节点表示获取同步状态成功的节点。

等待队列：存放调用了`Condition.await()`方法的线程节点。



##### `await()`

当线程执行`Condition.await()`时，线程节点从同步队列中被移除，加入对应`Condition`的等待队列中。



##### `signal()`

当线程执行`Condition.signal()`时，对应`Condition`等待队列中的首节点被移除，转而加入的同步队列中。



> 需要注意的是，对于同一个`Lock`，等待队列是可以有多个的。
>
> 同时可以发现，对于一个线程节点，要么在同步队列中，要么在等待队列中。