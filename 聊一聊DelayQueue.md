---
title: 聊一聊DelayQueue
date: 2022-07-06 23:00:00
categories: Java
---

> `DelayQueue`作为延时队列，有很多应用场景，今天主要来聊一下它的原理、优缺点以及应用场景。



#### 基本用法

`DelayQueue`的元素需要实现`Delayed`接口, 并覆盖`getDelay`方法和`compareTo`方法，其中`getDelay`方法会被**轮询调用**，以判断当前任务是否到达执行时间，`comparedTo`方法则是用来比较每个任务的先后关系。

基本用法如下：

```java
public class MyTask implements Delayed {
    private long curTime = System.currentTimeMillis();
    private long executeTime;
    private long delayTime;

    public MyTask(long time) {
        this.delayTime = time;
        this.executeTime = curTime + time;
    }

    public void execute() {
        System.out.println("execute task with delay " + delayTime);
    }

    @Override
    public long getDelay(TimeUnit unit) {
        return unit.convert(executeTime - System.currentTimeMillis(),TimeUnit.MILLISECONDS);
    }

    @Override
    public int compareTo(Delayed o) {
        return (int) (this.executeTime - ((MyTask) o).executeTime);
    }
}
```



测试类

```java
public class DelayQueueApp {
    public static void main(String[] args) {

        DelayQueue<MyTask> queue = new DelayQueue<>();
        queue.add(new MyTask(10_000));
        queue.add(new MyTask(15_000));
        queue.add(new MyTask(5_000));

        new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    try {
                        MyTask task = queue.take();
                        task.execute();
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
        }).start();
    }
}
```

我们给`queue`里添加三个元素，延迟分别是10ms, 15ms和5ms, 然后在子线程里从这个`queue`里取任务并执行，输出：

```java
execute task with delay 5000
execute task with delay 10000
execute task with delay 15000
```

可以看到任务是按照延迟时间排序出队的。



#### 原理

`DelayQueue`是基于优先级队列实现的，并且是线程安全的。先列出`DelayQueue`中几个比较重要的的概念：

+ 优先级队列`PriorityQueue`:`DelayQueue`的底层是优先级队列
+ Thread类型的leader变量
+ 可重入锁：用于控制入队和出队的线程安全

优先级队列和可重入锁这里不再赘述，关于`leader`变量需要着重说明下，**`DelayQueue`可能会有多个消费者线程**，然而一个任务节点最终只能被一个线程抢到，为了为了避免不必要的争抢，`DelayQueue`使用了“Leader-Follower”模式，说白了就是将消费者线程排队，每次只让`leader`线程去获取队首节点，这里就涉及到两个点：

1. 当队首元素发生变化时（比如后入队的元素优先级更高，成了队首元素），`leader`线程也应当跟着刷新，即`leader`线程总是致力于获取队首元素。
2. 当`leader`线程执行结束后，应当重新产生`leader`线程。

> 需要注意的是，Leader-Follower模式并不能减少awaitNanos的时间，它是用来避免不必要的线程状态切换的，如果不用Leader-Follower模式，也能实现该功能，但是会增加一些无意义的线程wakeup/sleep；如果使用Leader-Follower模式，只有leader线程会在指定时间后被唤醒，其他线程则是无限期等待，相比之下，后者更高效。



**入队方法**

```java
public boolean offer(E e) {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            q.offer(e);   //元素入队
          
          	/**如果当前是队首（有人会好奇为什么会有这个判断，这是因为当前是优先级队列，后入队的元素也可能是队首），
          		如果队首元素有变化，那leader线程也应当跟着变化，所以这里将leader置为null, 等待出队时重新选择
          	**/
            if (q.peek() == e) { 
                leader = null;
                available.signal();
            }
            return true;
        } finally {
            lock.unlock();
        }
    }
```

这里首先会加个可重入锁，然后给q添加元素，查看q的定义，可以看到它就是一个优先级队列。

```java
private final PriorityQueue<E> q = new PriorityQueue<E>();
```

这里有段代码需要注意下：

```java
if (q.peek() == e) {
    leader = null;
    available.signal();
}
```



**出队方法**

```java
public E take() throws InterruptedException {
    final ReentrantLock lock = this.lock;
    lock.lockInterruptibly();
    try {
      for (;;) {
        E first = q.peek();
        if (first == null)   //如果队空，则当前线程进入等待队列
          available.await();
        else {
          long delay = first.getDelay(NANOSECONDS);
          if (delay <= 0)		//如果队首元素已到期，则直接出队
            return q.poll();
          
          /**否则，说明当前线程要排队等候，这时候就要决定当前线程是leader线程还是follow线程，如果已经有leader了，那当前线程就只								能是follower了，默默加入等待队列即可。如果当前还没有等待队列，那就把当前线程作为leader线程，并让当前线程等待到剩余					时间**/
          first = null; // don't retain ref while waiting
          if (leader != null)
            available.await();
          else {
            Thread thisThread = Thread.currentThread();
            leader = thisThread;
            try {
              available.awaitNanos(delay);
            } finally {
              if (leader == thisThread)
                leader = null;
            }
          }
        }
      }
    } finally {
      // 如果队列不为空，并且没有Leader则从等待队列拿出一个线程，进行take操作。
      if (leader == null && q.peek() != null)
        available.signal();
      lock.unlock();
    }
  }
```



#### 应用

看到网上有些文章讲`DelayQueue`可以用来做淘宝下单后的定时取消订单功能，对此笔者持保留态度。`DelayQueue`作为延迟队列，单从技术角度来看确实可以，但是从系统设计角度看则有待商榷。用`DelayQueue`做订单取消功能，意味着在内存中维护待取消的订单信息，说明你的服务是有状态的，而有状态意味着：1、无法水平扩展；2、增加开发成本。举个🌰，假如当前这台服务器突然宕机，那队列里的任务都不会被执行；又比如面临大促时，当前服务器系统负载飙升，但是由于任务都集中在当前机器的`DelayQueue`里，即使加机器也无法解决。所以，面临一些比较重的计算任务时，需要考虑系统的可扩展性和可用性，单单依赖`DelayQueue`是不行的，一般大型公司都会有专门做定时任务的中间件，可以依赖这些中间件去实现，并将delayqueu作为一种降级策略，如果是对时间精确度要求较低的场景，也可以考虑将这些任务持久化到数据库中，然后定时去扫库。



#### 写在最后

无论如何，没有最牛逼的架构，只有最合适的架构，选型之前除了组件本身功能之外，也要考虑到系统特点，需要在开发成本、系统可用性要求等诸多因素中做权衡。



