---
title: 聊一聊限流之guava限流器
date: 2022-10-22 18:00:00
categories: Java
---

### 前言

限流是微服务应用中一个老生常谈的话题，当A调B时，为了防止A的流量过大把B打垮，需要为B配置限流，限制上游应用对B的调用频率。关于限流算法，有漏铜算法、令牌桶算法、计数器算法、滑动窗口算法，本文不再赘述。本文主要讲解guava中的限流算法。

### 用法

guava限流算法实现的是令牌桶算法，依赖于包

```java
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
    <version>31.0-jre</version>
</dependency>
```

#### 赊账机制，将阻塞时间延后

```java
public static void main(String[] args) {
    RateLimiter rateLimiter = RateLimiter.create(1); //创建一个限流器，每秒允许获取一个令牌
    while (true){
        System.out.println("get token in "+rateLimiter.acquire()+"s"); //rateLimiter.acquire返回距离上次获取限流器等待的时间
    }
}
```

输出：

```
get token in 0.0s   //第一次获取令牌不用等待。
get token in 0.997387s
get token in 0.992418s
get token in 0.996242s
get token in 1.000031s
```

可以看到，在第一次获取令牌的时候，限流器并没有等待一秒，而是直接获取，反倒是从第二次获取令牌的时候才开始等待，这也是guava令牌桶算法的特点之一：赊账，将当前请求本应阻塞的时间顺延给下一个请求处理。这是一个很妙的设计，试想一下，如果面对下面的情况，第一个请求不用等100s，而是立即通过，反倒是第二个请求需要等100s后才能通过，很巧妙地将阻塞时间延后了，至于会不会有第二个请求、第二个请求要请求几个令牌，那都是100s后的事情了，这种赊账机制提升了限流器对于当前请求的处理速度。

```java
public static void main(String[] args) {
    RateLimiter rateLimiter = RateLimiter.create(1);
    while (true){
        System.out.println("get token in "+rateLimiter.acquire(100)+"s");
    }
}
```



#### 令牌累积，应对突发流量

guava限流器会将当前没有用完的令牌囤积下来，以便应对未来的突发流量。默认会积攒一秒的令牌量，对于下述代码，

```java
public static void main(String[] args) {
    RateLimiter rateLimiter = RateLimiter.create(1);
    while (true){
        System.out.println("get token in "+rateLimiter.acquire(1)+"s");
    }
}
```

输出

```
get token in 0.0s
get token in 0.997302s
get token in 0.993367s
get token in 0.995367s
get token in 0.995384s
```

即每隔一秒才能获取一个令牌，但是如果限流器启动后当前线程sleep一秒再获取令牌时，此时前六条请求（前五条用累积的令牌，第六条赊账）不用阻塞，能够立即获得令牌，原因就在于限流器积攒了这一秒的令牌。 即对于下述代码：

```java
 public static void main(String[] args) throws InterruptedException {
        RateLimiter rateLimiter = RateLimiter.create(5);
        Thread.sleep(1000);
        while (true){
            System.out.println("get token in "+rateLimiter.acquire(1)+"s");
        }
    }
```

输出：

```
get token in 0.0s
get token in 0.0s
get token in 0.0s
get token in 0.0s
get token in 0.0s
get token in 0.0s
get token in 0.194899s
```



### 原理

在了解guava令牌桶算法的原理之前，我们先来思考下，如果让我们来实现令牌桶算法，需要怎么写？

所谓令牌桶算法，就是以固定的速率往一个桶里放令牌，当有请求来时，就从桶里取令牌，如果桶空了，就阻塞请求，直到桶里有令牌为止。按照令牌桶算法的思想，最直观的实现思路就是生产者消费者模型，专门起一个生产令牌的线程，以固定速率往集合（桶）里生产令牌。但如果这么做的话就会有些复杂，涉及到一些线程安全的操作。

guava令牌桶的实现就比较巧妙了，将多线程的令牌操作换算成单线程的时间操作。由于生产令牌的速率是固定的，所以只要知道生产令牌的起止时间，就能算出这段时间里生产了多少令牌，每次当有请求到来时，计算下迄今一共存了多少令牌，如果令牌够用，则通过请求，更新剩余令牌数，否则，先赊账让当前请求通过，然后计算下次请求应该阻塞的最早时间。

先来看下acquire方法：

```java
public double acquire(int permits) {
  long microsToWait = reserve(permits); //返回获取目标令牌数所需等待的时间
  stopwatch.sleepMicrosUninterruptibly(microsToWait);
  return 1.0 * microsToWait / SECONDS.toMicros(1L);
}
```

其中`reserve`方法返回获取目标令牌数所需等待的时间：

```java
final long reserve(int permits) {
  checkPermits(permits);
  synchronized (mutex()) {
    return reserveAndGetWaitLength(permits, stopwatch.readMicros());
  }
}
```

```java
final long reserveAndGetWaitLength(int permits, long nowMicros) {
  long momentAvailable = reserveEarliestAvailable(permits, nowMicros);
  return max(momentAvailable - nowMicros, 0);
}
```

接下来就是核心部分了：

```java
final long reserveEarliestAvailable(int requiredPermits, long nowMicros) {
   //刷新截止目前的令牌数 storedPermits 和下次能获取令牌的时间 nextFreeTicketMicros
  resync(nowMicros);
  //下次允许获取令牌的时间点
  long returnValue = nextFreeTicketMicros; 
  //得出需要花费的令牌数，比如需要5个，当前一共存了3个，则返回3；如需求3个，但存了5个，仍返回3
  double storedPermitsToSpend = min(requiredPermits, this.storedPermits);
  //除去已积攒的令牌，还需额外支付的令牌，比如需求5个，当前存了3个，则还需额外支付两个
  double freshPermits = requiredPermits - storedPermitsToSpend;
  //把要额外支付的令牌数换算成时间，比如还需额外支付两个，如果设置的qps是5，即每200ms生产一个令牌，那2个令牌就需要等待400ms
  long waitMicros =
      storedPermitsToWaitTime(this.storedPermits, storedPermitsToSpend)
          + (long) (freshPermits * stableIntervalMicros);
	//更新下次获取令牌的时间，
  //这里需要注意，这个方法的返回值是 returnValue，即更新前的 nextFreeTicketMicros，
  //也就是说当前请求需要阻塞的时间不变，而是将需要额外支付的时间交给下个请求，下个请求需要阻塞更久，也就是上文讲到的赊账机制
  this.nextFreeTicketMicros = LongMath.saturatedAdd(nextFreeTicketMicros, waitMicros);
  //更新已存储的令牌
  this.storedPermits -= storedPermitsToSpend;
  return returnValue;
}
```

同步nextFreeTicket

```java
void resync(long nowMicros) {
  // if nextFreeTicket is in the past, resync to now
  if (nowMicros > nextFreeTicketMicros) {
    double newPermits = (nowMicros - nextFreeTicketMicros) / coolDownIntervalMicros();
    storedPermits = min(maxPermits, storedPermits + newPermits);
    nextFreeTicketMicros = nowMicros;
  }
}
```

下面通过一个小🌰来解释一下，在下图中，假设限流器限流为5ps, 即每200ms一个请求，当第一个请求在限流器启动时（即0s）时到来，这时候会直接通过，并计算允许下次请求通过的时间，由于此时是请求两个令牌，所以`nextFreeTicket`为2*200ms=400ms，在0-400ms期间到来的请求都会阻塞到400ms才允许通过，并再次更新`nextFreeTicket`.

![ratemiliter](//tvax3.sinaimg.cn/large/008uWfc7gy1h7f9pdqfvpj30rd0dnwg0.jpg)



### 写在最后

这篇文章主要介绍了guava令牌桶算法的用法以及原理，文章只挑选了最核心的部分进行了介绍，关于guava ratelimiter, 除了文中介绍的应对突发流量的限流器外，还有平滑预热（warming up）限流，感兴趣的读者可以自行了解。

从工程角度讲，上述限流器是一种单机限流，即只能针对单台机器生效，但真实环境中一个应用更多是集群部署，需要针对整个集群限流，比如让整个集群的qps小于某个阈值，这就需要用到集群限流，比如阿里巴巴开源的sentinel。

