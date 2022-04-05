---
title: Netty学习笔记之服务端建立新连接
categories: Java
tags: Netty
---

### 前情提要

在**Netty学习笔记之服务端启动**一文中，我们了解了`eventloop`的基本功能，知道了它的一生其实就是个死循环，再循环里处理`IO`事件和`taskQueue`里面的任务；同时我们也了解到，在服务端启动之初(准确的来讲是在`channel`注册完成之后调用`handlerAdded`的时候)会给`pipeline`里添加一个特殊的`handler`：ServerBootstrapAcceptor，有了这两点之后，让我们看下`Netty`服务端启动后是如何利用`reactor`模型建立新连接的。

### 正文

当客户端启动并给服务端发送消息后，服务端的`eventloop`就会监听到对应事件：

#### `NioEventLoop.run`

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
                        processSelectedKeys(); //这里就会支棱起来
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
            // Always handle shutdown even if the loop processing threw an exception.
         ...
        }
    }
```



#### `NioEventLoop.processSelectedKey`

```java
private void processSelectedKey(SelectionKey k, AbstractNioChannel ch) {
        final AbstractNioChannel.NioUnsafe unsafe = ch.unsafe();
				...
        try {
         
						....
            // Also check for readOps of 0 to workaround possible JDK bug which may otherwise lead
            // to a spin loop
            if ((readyOps & (SelectionKey.OP_READ | SelectionKey.OP_ACCEPT)) != 0 || readyOps == 0) {
                unsafe.read(); //调用了这里
            }
        } catch (CancelledKeyException ignored) {
            unsafe.close(unsafe.voidPromise());
        }
    }
```



#### `NioMessageUnsafe.read`

```java
public void read() {
           ...
            boolean closed = false;
            Throwable exception = null;
            try {
               ...
                int size = readBuf.size();
                for (int i = 0; i < size; i ++) {
                    readPending = false;
                    pipeline.fireChannelRead(readBuf.get(i)); //这里
                }
              ...
            } finally {
                // Check if there is a readPending which was not processed yet.
              ...
            }
        }
    }
```

最终调用了`pipeline.fireChannelRead(readBuf.get(i))`, 在服务端启动一文中我们也讲到了`pipeline`的传播，像这种`firexxx`的都是从`head`往后传播的，所以最终会传播到`ServerBootstrapAcceptor`里，调用`ServerBootstrapAcceptor`的`channelRead`,而这里，就是重头戏了。

#### `ServerBootstrapAcceptor.channelRead`

<img src="http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h0yyrpyhfej316w0qedss.jpg" alt="image" style="zoom:50%;" />

这里有几个点需要注意下：

+ 代码①：这里的`Channel`是`SockerChannel`，而不是`ServerSocketChannel`，即是客户端的`Channel`.

+ 代码②：`childHandler`就是我们在`boostrap`里配的`ChannelInitializer`，等到`channel`真正注册后回调`initChannel`方法，把`MyServerHandler`添加到`pipeline`，见下图，**这里的处理和服务端启动一文中`doResigter`一节中的代码②是一个道理，归根到底就是因为我们想给`pipeline`添加`handler`，但是`Channel`还没注册好，所以采取的一种妥协的方式，即先给`pipeline`注册一个`ChannelInitializer`类型的`Handler`，等到`Channel`真正注册好之后，再去回调这个特殊`Handler`的`initChannel`方法。**

  这里也可以解释`bootstrap`的`handler`和`childHanlder`的区别：前者对应`ServerSocketChannel`，后者对应`SockerChannel`.

​		<img src="http://tva4.sinaimg.cn/large/006ImZ0Ogy1h0yyux1a8kj3172100dwp.jpg" alt="image" style="zoom:50%;" />

+ 代码③：这里就是将`channel`注册到`eventloop`上，和我们在服务端启动一文中看到的`serversocketChannel`的注册差不多，但是有细微区别，主要体现在

  + 服务端启动时的注册是将`serversocketChannel`注册到`bossGroup`里的`eventloop`.而`childChannel`注册时是要注册到`workerGroup`里。

  + 在注册环节，由于当前线程是`bossGroup`的线程，所以一定会走`else`的逻辑, 将注册的任务提交到`childChannel`自己的`eventloop`

    <img src="http://tva1.sinaimg.cn/large/006ImZ0Ogy1h0yz5wlab7j319611uwxn.jpg" alt="image" style="zoom:50%;" />