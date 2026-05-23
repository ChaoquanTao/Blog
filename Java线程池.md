---
title: Java线程池
date: 2019-11-07 20:44:46
updated: 2019-11-07 20:44:46
tags: 线程池
categories: 多线程
---

### 什么是线程池

线程池，和连接池、常量池一样，是一种池化思想。大概意思是预先把线程都创建好，放到一个池子里，用的时候就去拿，用完了再给下一个任务用，以达到一种资源的高效利用。

### 为什么要有线程池

为什么要有线程池？和这个问题相对应的一个问题是不用线程池行不行？答案是可以的。比如我们在想使用多线程的时候直接new一个Thread也是可以的，那么这两种方式有什么区别呢？每用一次new一次这样性能是很差的，而且用一次，new一次，很麻烦，而且这些线程之间很难统一管理。如果使用线程池，我们可以将这些线程重复利用，避免重复创建，浪费系统资源，同时方便我们统一管理，比如并发数量，定时执行等。

### 设计思想

了解了什么是线程池以及为什么要有线程池之后，我们来看下在Java中是如何设计线程池的。

首先线程池线程池，既然是个池子，那也就是个容器，所以我们需要个容器来装这些线程，在Java中这个容器（池子）是`HashSet`.



线程池的设计中有三个主要模块：

+ 核心池（core pool）
+ 最大池(maximum pool)
+ 队列（BlockingQueue）



大概思想是这样的，当需要创建一个线程时，我先检查池子中已有的线程（Worker）数量是否大于核心池数量，如果没有，继续在核心池里创建线程（Worker）.

如果核心池已经满了，那再有新的线程需要执行，我先把它放到一个队列里候着。

如果队列也满了，现在考虑往最大池里创建线程（Worker）。关于core pool和maximum pool的关系是这样的，core pool相当于公司的正式员工，maximum pool相当于临时工。当有顾客来时，先仅着正式员工用，正式员工不够了，让顾客先在大厅休息一哈，如果大厅也满了，再让临时工也工作起来。

如果maximum pool也满了，则执行拒绝策略。



我们通过一个流程图来展示下它的执行过程：

![MAvrPU.jpg](https://s2.ax1x.com/2019/11/07/MAvrPU.jpg)





### 源码分析

接下来我们从源码角度更细致地分析一下上述过程。

首先看构造函数

![MAxDeI.png](https://s2.ax1x.com/2019/11/07/MAxDeI.png)

`corePoolSize`: 核心线程数。

`maximumPoolSize`: 最大线程数

`workQueue`: worker数量达到核心线程数后要加入的队列

`keepAliveTime`:  临时工的最大存活时间，如果临时工超过这个时间还没有工作，就会被销毁。

`threadFactory`: 用来创建线程的工厂。

`handler`:  线程池拒绝策略。



再来看下关于线程池状态和线程数量的相关定义：

![MES2rj.png](https://s2.ax1x.com/2019/11/07/MES2rj.png)

使用原子变量`ctl`的高三位表示线程状态，低29位标识线程池中的线程数量。



再来看下线程池中最重要的方法`execute()`:

![ME9S7n.png](https://s2.ax1x.com/2019/11/07/ME9S7n.png)

其实注释已经讲的很清楚了，这里三个框分别代表上面一节中的加入核心池，加入队列以及加入最大池。需要注意的是，在加入队列的时候，是进行了一个double check的，也就是说在将任务加入队列后重新判断线程池是否在运行，如果不在运行则执行拒绝策略，如果在运行但是worker数量为零则新增非核心线程。另外一个点就是何时执行拒绝策略？两种情况：线程池shutdown或者线程池满。



再来看下`addWorker()`方法干了些啥：

<img src="https://s2.ax1x.com/2019/11/07/MEi48P.png" alt="MEi48P.png" style="zoom:80%;" />



### 使用

常见有两种创建方式

1. 使用`ThreadPoolExecutor()`创建

   ```java
   ExecutorService executorService = new ThreadPoolExecutor(5,10,60L,TimeUnit.SECONDS, new ArrayBlockingQueu(10))
   ```

   提交任务时：

   ```java
   executorService.execute(new Runnable(){
       //省略若干行代码
   })
   ```

   

2. 使用`Executor`框架创建

```java
ExecutorService executorService1 = Executors.newFixedThreadPool(5);
```



但是，《阿里巴巴开发手册》中有这样的规定：

![ME5CdJ.png](https://s2.ax1x.com/2019/11/08/ME5CdJ.png)

我们以`FixedThreadPool`为例来看下

![MEIy4A.png](https://s2.ax1x.com/2019/11/08/MEIy4A.png)

这里的队列用的是`LinkedBlockingQueue<>`， 没有初始化容量，则默认的就是`Integer.MAX_VALUE`，因此如果不断的向队列中塞任务的话，就有可能导致OOM.