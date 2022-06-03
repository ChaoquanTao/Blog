---
title: Netty学习笔记之服务启动
date: 2022-02-13 12:00:00
updated: 2022-02-13 12:00:00
tags: Netty
categories: Netty
---

### 前置知识

学习之前需要理清这么几个关键概念：

+ netty相关：EventLoop, EventLoopGroup, ChannelHandler, ChannelPipeline，ChannnelPromise, ChannelFuture
+ nio相关：channel, selector.

#### `Channel`与`Selector`

谈到nio, 那么channel和selector就是绕不开的话题，他们的关系如下：

![nio](http://tva2.sinaimg.cn/large/006ImZ0Ogy1h0nopjfconj30bf09rglt.jpg)

一个selector和一个线程对应，这也是nio的好处之一：用单线程处理多个客户端的连接；一个selector同时对应多个channel,每个channel将自己注册到selector上，注册的时候会携带自己感兴趣的事件。然后selector就去轮训这些事件，当有某个事件ready时，就去通知对应的channel.



#### `EventLoop`

翻译过来是事件循环器，其实就是用来处理各种io事件的，要具备这种能力，那么eventloop必须：

1. 具有一个selector
2. 具有自己的线程，在这个线程里可以对selector注册的事件进行遍历

所以,eventloop继承自了Executor,具有线程池的能力，同时含有一个selector.

<img src="http://tva1.sinaimg.cn/mw690/006ImZ0Ogy1h0nas3pud1j30pi10iwis.jpg" alt="image" style="zoom:50%;" />

每个`channel`都对应一个`eventloop`，在`netty`启动之时，会将`channel`注册到`eventloop`，然后`eventloop`就会开启死循环，去

1. 遍历`channel`感兴趣的事件
2. 作为`executor`去执行任务队列里的任务

上述两点便是`eventloop`的核心作用。我们已`AbstractChannel.register`来说明这个问题。

##### `AbstractChannel.register`

```java
public final void register(EventLoop eventLoop, final ChannelPromise promise) {
  ...
    if (eventLoop.inEventLoop()) {
      register0(promise);
    } else {
      try {
        eventLoop.execute(new Runnable() {
          @Override
          public void run() {
            register0(promise);
          }
        });
      } catch (Throwable t) {
        ...
      }
    }
}
```

在注册`channel`的时候，如果当前线程是`eventloop`线程，则直接注册，否则，将`register0`作为一个任务提交到`eventloop`的任务队列里，也就是`execute`方法。

##### `SingleThreadEventExecutor.execute`

<img src="http://tvax2.sinaimg.cn/large/006ImZ0Ogy1h0ypn36ciqj30ou0p8n3d.jpg" alt="image" style="zoom:50%;" />

`execute`方法也是言简意赅，如果当前线程是`eventloop`线程，则直接`addTask`，否则先开启一个线程，然后`addTask`.



##### ``SingleThreadEventExecutor.``doStartThread

```java
private void doStartThread() {
        assert thread == null;
        executor.execute(new Runnable() {
            @Override
            public void run() {
                thread = Thread.currentThread();
                if (interrupted) {
                    thread.interrupt();
                }

                boolean success = false;
                updateLastExecutionTime();
                try {
                    SingleThreadEventExecutor.this.run();
                    success = true;
                } catch (Throwable t) {
                    logger.warn("Unexpected exception from an event executor: ", t);
                } finally {
                 ...
            }
        });
    }

```

这里利用Jdk的`Executor.execute`开启一个线程，并在这个线程里开始了它的死循环，即`SingleThreadEventExecutor.this.run()`



##### `NioEventloop.run`

```java
protected void run() {
        for (;;) {
            try {
                switch (selectStrategy.calculateStrategy(selectNowSupplier, hasTasks())) {
                    case SelectStrategy.CONTINUE:
                        continue;
                    case SelectStrategy.SELECT:
                        select(wakenUp.getAndSet(false));
                        if (wakenUp.get()) {
                            selector.wakeup();
                        }
                        // fall through
                    default:
                }

                cancelledKeys = 0;
                needsToSelectAgain = false;
                final int ioRatio = this.ioRatio;
                if (ioRatio == 100) {
                    try {
                        processSelectedKeys();
                    } finally {
                        // Ensure we always run tasks.
                        runAllTasks();
                    }
                } else {
                    final long ioStartTime = System.nanoTime();
                    try {
                        processSelectedKeys();
                    } finally {
                        // Ensure we always run tasks.
                        final long ioTime = System.nanoTime() - ioStartTime;
                        runAllTasks(ioTime * (100 - ioRatio) / ioRatio);
                    }
                }
            } catch (Throwable t) {
                handleLoopException(t);
            }
           ...
        }
    }
```

这个`run`方法就是`EventLoop`的核心了，里面有两个比较关键的方法：

+ `processSelectedKeys`:查询已经就绪的事件并处理，说白了就是处理io事件
+ `runAllTasks`:处理任务队列里的任务，比如我们通过`eventloop.execute`提交的任务

​		<img src="http://tva3.sinaimg.cn/large/006ImZ0Ogy1h0yqc7rplaj312k0n010i.jpg" alt="image" style="zoom:50%;" />        

<img src="http://tvax1.sinaimg.cn/large/006ImZ0Ogy1h0yqcvzr2tj30xk0keq9t.jpg" alt="image" style="zoom:50%;" />

那么至此，`eventloop`的功能就大概清楚了，它就是在死循环里套死循环，去处理io事件和`taskQueue`. 当然了，里面还有一些小细节，比如：

+ 为了分配好处理io事件的时间和处理`taskQueue`的事件，使用了`ioratio`作为两者的时间比例。
+ 



#### `ChannelPipeline`

用张图来解释：

![image](http://tva3.sinaimg.cn/large/006ImZ0Ogy1h0wtxu3rssj30m60610vk.jpg)

每个channel都会对应一个channel pipeline, 而这个pipeline就是一个链表，每个节点类型为`ChannelHandlerContext`,内部包了一个`ChannelHandler`. 而`ChannelHandler`又分为`ChannelInboundHandler`和`ChannelOutboundHandler`, 分别用来处理入站事件和出站事件，差不多像这样：

<img src="http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h0wu5kfv4zj30zg15idna.jpg" alt="image" style="zoom:50%;" />



当有入站事件或者出站事件发生时，事件会以责任链模式经过`handler`.



#### `ChannelPromise`和` ChannelFuture`

netty扩展了jdk原生的future. 而promise则是对Netty future的进一步扩展。

<img src="http://tvax1.sinaimg.cn/mw690/006ImZ0Ogy1h0nckpjxpej30yo0ok0wt.jpg" alt="image" style="zoom:80%;" />

jdk原生future:

![image](http://tva1.sinaimg.cn/mw690/006ImZ0Ogy1h0ncmmnjlwj30hy082gmw.jpg)

netty的future:

<img src="http://tvax3.sinaimg.cn/mw690/006ImZ0Ogy1h0ncnj6s5vj30oa0l4wlb.jpg" alt="image" style="zoom:80%;" />

可以看到,netty扩展的future增加了一些监听器的`add`和`remove`的方法，以及一些同步方法，如`await`,`sysnc`.

再来看下promise：

![image](http://tvax4.sinaimg.cn/mw690/006ImZ0Ogy1h0ncq1ts1yj30ok0gc0y8.jpg)

多了一些设置状态的方法，如`setSuccess`,`setFailure`

##### 这些扩展意味着什么

netty的`future`可以`addListener`,`removeLisener`, `promise`可以`setSuccess`,`setFailure`,意味着异步操作时，如主线程调了eventloop的线程，只要将`promise`返回主线程，那么`promise`在eventloop线程里的任何动作都可以被主线程感知到，比jdk的`futrue`更加健壮了一些。



### 总览

一般的启动代码长这样：

![image](//tvax3.sinaimg.cn/mw690/006ImZ0Ogy1h0n90500mdj30zg0zs7k5.jpg)

真正的入口在`bind`这里，进去看看：

<img src="http://tva4.sinaimg.cn/large/006ImZ0Ogy1h0wuyeay80j31fa1404gf.jpg" alt="image" style="zoom:33%;" />

首先，`initAndRegister`,意思是初始化并注册，初始化什么？注册什么？这里其实是初始化一个channel, 并把eventloop的selector注册到channel上，注意这个方法的返回值，是个`future`,也就是说`initAndRegister`这个动作是异步进行的，如果注册完成了，即`regFuture.isDone()`,则进行`doBind0`操作，否则，添加一个监听器，等`initAndRegister`完成了会出发它，然后进行`doBind0`。



OK，大致来看，启动分为两个步骤，首先`initAndRegister`,然后进行`doBind0`。



#### `initAndRegister`

首先来看下这个`initAndRegister`究竟做了些啥。

<img src="http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h0xy4c5qloj31d60se15m.jpg" alt="image" style="zoom:40%;" />

这里`init`后面会讲。最终调用到的是**`AbstractChannel$AbstractUnsage.register`**

##### `AbstractChannel$AbstractUnsage.register`

<img src="/Users/chaoquantao/Library/Application Support/typora-user-images/image-20220326145847131.png" alt="image-20220326145847131" style="zoom:40%;" />

这个`register`方法有两个参数，`eventloop`是最初配置的`bossGroup`,`ChannelPromise`是对`Channel`的包装。这里要注意，注册的动作必须发生在`eventloop`的线程里，所以如果当前线程不是eventloop的线程的话，`eventloop`会起一个自己的线程去做这个事情。



继续看`register0`:

##### `register0`

<img src="http://tva1.sinaimg.cn/large/006ImZ0Ogy1h0np2uql8kj31b616qwtl.jpg" alt="image" style="zoom:40%;" />

`doResigter`就是真正的注册过程，在死循环里将channel注册到`eventloop`的`selector`里。

##### `doResigter`

<img src="http://tvax1.sinaimg.cn/large/006ImZ0Ogy1h0no9fhpi7j317s0nsdm6.jpg" alt="image" style="zoom:50%;" />

相比代码①，注册完成之后的②③④⑤更值得关注。

+ 代码②回调添加`handler`时候的`handlerAdded`方法

​		这里是有细节的，回到我们最初的server端代码：

​		<img src="/Users/chaoquantao/Library/Application Support/typora-user-images/image-20220404200516407.png" alt="image-20220404200516407" style="zoom:40%;" />

执行完代码②后，应该输出“HandlerAdded”. 但是这个handler是什么时候添加进`pipeline`的呢？是`serverBootStrap`的`handler()`方法吗，不是。回到`initAndRegister`处，

<img src="http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h0xy4c5qloj31d60se15m.jpg" alt="image" style="zoom:40%;" >abc</img>

看下这个`init`方法：

```java
@Override
    void init(Channel channel) throws Exception {
       ... //省略若干代码
        p.addLast(new ChannelInitializer<Channel>() {
            @Override
            public void initChannel(final Channel ch) throws Exception {
                final ChannelPipeline pipeline = ch.pipeline();
                ChannelHandler handler = config.handler();
                if (handler != null) {
                    pipeline.addLast(handler);
                }

                ch.eventLoop().execute(new Runnable() {
                    @Override
                    public void run() {
                        pipeline.addLast(new ServerBootstrapAcceptor(
                                ch, currentChildGroup, currentChildHandler, currentChildOptions, currentChildAttrs));
                    }
                });
            }
        });
    }
```

可以看到，在`init`的时候，`pipeline`就添加一个`handler`,即`ChannelInitializer`,并覆盖了`initChannel`方法,所以启动后`pipelie`里除了`head`和`tail`之外，还有一个叫做`ChannelInitializer`的`handler`,一共三个`handler`。再回到代码②，代码②的最终功能就是去调用`ChannelInitializer`的`initChannel`方法,而这个`initChannle`里面，才是把我们在`serverbootstrap`里定义的`handler`给加到`pipeline`里,并在添加之后回调`handlerAdded`方法。

<img src="http://tvax3.sinaimg.cn/large/006ImZ0Ogy1h0xz79wr5gj310c0kc122.jpg" alt="image" style="zoom:50%;" />

当这个`ChannelInitializer`完成的它的任务后，就被`remove`掉了，此时`pipeline`里就只有`head`,`tail`以及我们自己定义的`handler`了。



+ 代码③设置成功之后，我们上文里提到的`doBind`方法里的listener就会被出发，从而继续执行`doBind0`方法
+ 代码④执行添加handler时候的`channelRegistered`回调
+ 代码⑤首次注册的时候不是active,后面再讲

OK，至此，一个channel就初始化好了，并且注册了到了eventloop上



#### `doBind0`

书接上回`register0`的代码③，设置成功后，`doBind`方法里的`regFuture`添加的`listener`就被触发了，来到了`doBind0`环节。

<img src="http://tvax3.sinaimg.cn/large/006ImZ0Ogy1h0ww01j6yij31f20lsdob.jpg" alt="image" style="zoom:50%;" />

这里的`channel.bind()`也是比较有意思的，看似是`channel`的`bind`，其实最后调的是`pipeline`的`bind`.(插一嘴，`pipieline`在netty里相当核心，基于责任链模式，所有的事件都在`pipeline`里流动，后面会专门起一篇文章说这个事情。)

**`AbstractChannel.bind()`**

<img src="http://tvax3.sinaimg.cn/large/006ImZ0Ogy1h0xwsk5yjqj310y06en0g.jpg" alt="image" style="zoom:50%;" />

**`DefaultChannelPipeline.bind()`**

<img src="http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h0xwucggyfj313405c77s.jpg" alt="image" style="zoom:50%;" />

​		可以看到，`pipeline`的`bind`是从`tail`开始的，也就是说，它是从尾部向头部传播的，也就是说，`context`的类型应该是`outboundContenxt`

### 总结一下

服务端启动需要做这么几件事：初始化一个channel, 然后把这个channel注册到selector上，然后把在channel上绑定服务端地址。

整个过程中，`pipeline`贯穿全局，起着传递事件的作用。





