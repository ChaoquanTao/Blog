---
layout: java
title: Java中的NIO
date: 2019-07-17 16:30:42
tags: IO
categories: Java
---

NIO(Non-Blocking IO，非阻塞同步IO)是Jdk 1.4后提出的新技术，为什么要提出这个技术呢？是为了解决什么问题呢？

要回答这个问题，就要从传统的阻塞式IO说起。

#### 何为同步异步，何为阻塞非阻塞

对IO来说，

+ 同步：API调用返回时就已经知道执行结果了
+ 异步：API调用返回时还不知道执行结果，需要过一会儿才能知道
+ 阻塞：当没有数据读或者写时，它就一直等啊等，等到有数据来
+ 非阻塞：能读多少是多少，然后返回，即使没有数据读，我也不等，直接返回

总结一下就是，同步异步，强调的是返回时有没有直到执行结果。而阻塞和非阻塞，强调的是何时返回，即死等还是立即返回。

#### 传统IO

1. ##### 单线程下的通信

我们举个简单例子，为了读取一个TCP连接的数据，

客户端：

```java
public class Client {
    public static void main(String[] args) throws IOException {
        String host = "127.0.0.1";
        int port = 8888 ;
        Socket socket = new Socket(host,port) ;
        OutputStream outputStream = socket.getOutputStream();
        outputStream.write(String.valueOf("hello server").getBytes());
    }
}
```

服务端

```java
public class Server {
    public static void main(String[] args) throws IOException {

        ServerSocket serverSocket = new ServerSocket(8888);
        while (true) {
            Socket socket = serverSocket.accept();
            //do something
            InputStream inputStream = socket.getInputStream();
            byte[] bytes = new byte[1024];
            int len = inputStream.read(bytes);
            System.out.println(new String(bytes, 0, len));
        }
    }
}
```

在这里，服务端的`serverSocket.accept()`就是一种同步阻塞的写法，服务端的线程一直阻塞在这里，占用着内存资源，直到有请求过来，才开始执行后续代码。当有多个请求到来时，服务端就一个一个挨个处理。很显然，这是很低效的，

2. ##### 多线程下的通信

为了提高服务端的效率，我们多开几个线程来处理服务端的请求。每次有新的连接来了我就重新创建一个线程，而不是排队等候那唯一一个线程，这样效率得到了提高。

服务端：

```java
public class MultiThreadServer {
    public static void main(String[] args) throws IOException {

        ServerSocket serverSocket = new ServerSocket(8888);
        while (true) {
            Socket socket = serverSocket.accept();
            //do something
            new Thread(new Runnable() {
                @Override
                public void run() {
                   
                    try {
                        System.out.println("sub thread:"+Thread.currentThread().getName());
                        InputStream inputStream = null;
                        inputStream = socket.getInputStream();

                        byte[] bytes = new byte[1024];
                        int len = 0;

                        len = inputStream.read(bytes);
                        System.out.println(new String(bytes, 0, len));
                    } catch (IOException e) {
                        e.printStackTrace();
                    }

                }
            }).start();

        }
    }
}
```



3. ##### 线程太多啦

再后来，业务庞大了，连接数多了起来，这么频繁的创建销毁线程也是很消耗系统资源的，于是，我们使用线程池进行服务端线程的创建与维护，方便统一管理和复用线程，提高资源利用率。在营业（接收并处理请求）之前我先创建好一系列线程，到时候有连接来了我就分配一个线程，用完了我再拿回来，性能薛微得到了一丝改善。

```java
public class ThreadPoolServer {
    public static void main(String[] args) throws IOException {
        ExecutorService service = new ThreadPoolExecutor(5, 10, 60L, TimeUnit.SECONDS, new ArrayBlockingQueue<>(10));
        ServerSocket serverSocket = new ServerSocket(8888);
        while (true) {
            Socket socket = serverSocket.accept();
            service.submit(new RequestHandler(socket));
        }
    }
}

class RequestHandler implements Runnable {
    private Socket socket;

    public RequestHandler(Socket socket) {
        this.socket = socket;
    }

    public RequestHandler() {
    }

    @Override
    public void run() {

        try {
            System.out.println("sub thread:" + Thread.currentThread().getName());
            InputStream inputStream = null;
            inputStream = socket.getInputStream();

            byte[] bytes = new byte[1024];
            int len = 0;

            len = inputStream.read(bytes);
            System.out.println(new String(bytes, 0, len));
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

}
```



4. ##### 线程池也扛不住了

业务持续增长，线程池也满足不了需求了，当线程数大于cpu核数的时候，必然会存在线程切换的问题，这很耗费资源，而且，对于每个线程内部，阻塞的情况还是存在的，这也就存在一个线程状态切换的问题，这也耗费资源。



> 基于这个背景，我们就在考虑，有没有什么方法，能够解决这个线程频繁上下文切换的问题？也就有了我们的NIO



#### NIO

关于NIO，网络上已经有很多相关介绍了，但是我想从一个不同的角度去刨析它。

在之前的[文章]([https://inewbie.top/2019/12/20/IO%E4%B8%AD%E7%9A%84%E5%90%8C%E6%AD%A5%E5%BC%82%E6%AD%A5%EF%BC%8C%E9%98%BB%E5%A1%9E%E9%9D%9E%E9%98%BB%E5%A1%9E/#more](https://inewbie.top/2019/12/20/IO中的同步异步，阻塞非阻塞/#more))中我们介绍了五种IO模型，其中有一种是 IO多路复用(IO multiplexing)，NIO的设计就用到了这一思想。

首先我们来大概了解下NIO是怎么工作的。

首先，它是非阻塞的，非阻塞意味着读或者写的时候，如果没有数据，就直接返回了。为了能够拿到数据，你可能就要不停的去调用read或者write去尝试看能不能拿到数据。这也是NIO需要解决的问题之一。

NIO有三个核心模块：

+ Buffer
+ Channel
+ Selector

下面我们会一一介绍。

##### Buffer

传统的BIO是面向流（Stream）的，即我们是向Stream读取或者写入数据的，并且这个Stream是单向的，即要么是输入流，要么是输出流。

NIO是面向缓冲区的，我们要输入的数据，首先得放到Buffer，然后由Buffer送到Channel中。



##### Channel

Channel意思即通道，它和传统的Stream类似，很大的一点不同在于：Channel是双向的，同一个Channel既可以拿来输入，也可以拿来输出，而不像Stream是有InputStream和OutputStream之分的。



##### Selector

Selector叫做选择器，也被叫做多路复用器，从他的名字就可以知道，它和我们之前介绍的IO multiplexing有很大关系。

NIO中利用Selector实现了多路复用，通过在Selector上注册多个事件（在我们这里对应的就是通道了），Selector去监听这多个事件是否有发生，如果有事件发生，则进行相应处理。它这样设计一个很大的好处是可以用单线程管理多个通道，如果你仔细读[这篇]([https://inewbie.top/2019/12/20/IO%E4%B8%AD%E7%9A%84%E5%90%8C%E6%AD%A5%E5%BC%82%E6%AD%A5%EF%BC%8C%E9%98%BB%E5%A1%9E%E9%9D%9E%E9%98%BB%E5%A1%9E/#more](https://inewbie.top/2019/12/20/IO中的同步异步，阻塞非阻塞/#more))文章，你会发现它们十分类似。

> 但是也有不同，在IO multiplexing中，应用进程是被select系统调用阻塞的，但是目测在NIO中，注册监听后当前线程并没有被阻塞，所以从这个角度讲，NIO更像是IO多路复用和信号驱动式IO的结合。



总结一下，它的设计思想是这样的：

+ 单线程实现

+ 提出了`Channel`的概念，每一个对磁盘或者文件的IO操作对应一个Channel，相当于Channel提供了我们和真正的文件或者磁盘操作的一个桥梁。

+ 我们通过Buffer和Channel交互，对于读操作，我们先把数据从Channel读到Buffer,然后再操作Buffer, 对于写操作，我们先把数据放到Buffer, 然后再写到Channel.
+ 为了在实现非阻塞的同时避免不停的调用read()或者write(), 实现了监听机制。具体是通过选择器Selector实现的，我们把每个Channel都绑定在一个Selector上，并且告诉Selector我对什么样的事件感兴趣，通过Selector进行监听，监听的过程中程序是阻塞的，当Channel感兴趣的事件发生时，Selector通知Channel,然后Channel开始它的表演。

所以，说白了，它的非阻塞同步，主要就是

1. 设置了监听
2. 把多线程的客户端请求映射成了单线程的多个channel, 然后selector监听，有感兴趣的事情发生之后就开始轮询每个channel.