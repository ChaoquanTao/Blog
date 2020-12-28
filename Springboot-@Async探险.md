---
title: Springboot @Async探险
date: 2020-12-02 17:30:00
tags: async
categories: Java
---

#### 从业务说起，用到了`@Async`

在主线程中接收数据，进行数据拼接，然后存库，最后返回http 200, 由于客户端有失败重试机制，且失败次数多了之后会不再请求，所以为了避免由于存库导致的阻塞，项目中使用`@async`进行异步处理。

#### 出现了意料之外的问题

项目上线后发现，一段时间之后客户端停止请求服务端了（这里其实是客户端的自动推送功能被关了）查看日志发现是使用了`@async`的子线程抛了异常，导致没有正常返回http 200给客户端。

这就奇了怪了，`@async`是异步处理，理论上讲，在`@async`中出现异常不应该会影响到主线程返回http 200啊。因此笔者进行了进一步的验证。

#### `@Async`探秘

##### 是否是子线程的验证

起初我的代码是这样写的（springboot下的test文件下的）

```java
@Slf4j
@RunWith(SpringRunner.class)
@SpringBootTest
public class AsyncTest {
    @Test
    public void test(){
        log.info("before:{}",Thread.currentThread().getName());
        asyncTest();
        log.info("after");
    }

    @Async("asyncTaskExecutor")
    public void asyncTest(){
        log.info("sub:{}",Thread.currentThread().getName());
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
```

但是输出就很奇怪了：

```java
before:"main"
sub:"main"
after
```

加了`async`注解，但是似乎并没有开启子线程？

通过查找资料得知，原来**使用`async`注解的方法不能和主线程的方法在一个类中**，这里的原因笔者会稍后解释，于是修改代码：

`AsyncTest`

```java
@Slf4j
@RunWith(SpringRunner.class)
@SpringBootTest
public class AsyncTest {
    @Autowired
    AnotherTest anotherTest;
    
    @Test
    public void test(){
        log.info("before:{}",Thread.currentThread().getName());
        anotherTest.asyncTest();
        log.info("after");
    }
}
```



`AnotherTest`

```java
@Slf4j
@Service
public class AnotherTest {
    @Async("asyncTaskExecutor")
    public void asyncTest(){
        log.info("sub:{}",Thread.currentThread().getName());
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
```

再次执行，一样的输出？？？小小的脑袋有大大的疑惑。后来找到原因，需要在`SpringBootApplication`所在类使用`@EnableAsync`开启`async`功能，像这样：

```
@SpringBootApplication
@EnableAsync
@MapperScan("com.aier.camerawater.mapper")
public class CamerawaterApplication {

public static void main(String[] args) {        		SpringApplication.run(CamerawaterApplication.class, args);
    }
}
```

再次运行，输出是对了：

```java
before:"main"
after
sub:"async-task-thread-pool-1"
```

但是在输出的后面跟了个`InterruptException`:

```java
2020-12-02 19:10:33.960 INFO  com.aier.camerawater.AsyncTest - before:"main"
2020-12-02 19:10:33.971 INFO  com.aier.camerawater.AsyncTest - after
2020-12-02 19:10:33.980 INFO  com.aier.camerawater.AnotherTest - sub:"async-task-thread-pool-1"
2020-12-02 19:10:33.986 INFO  org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor - Shutting down ExecutorService 'asyncTaskExecutor'java.lang.InterruptedException: sleep interrupted

	at java.lang.Thread.sleep(Native Method)
	at com.aier.camerawater.AnotherTest.asyncTest(AnotherTest.java:14)
	at com.aier.camerawater.AnotherTest$$FastClassBySpringCGLIB$$437e206d.invoke(<generated>)
	at org.springframework.cglib.proxy.MethodProxy.invoke(MethodProxy.java:218)
	at org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.invokeJoinpoint(CglibAopProxy.java:771)
	at org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:163)
	at org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:749)
	at org.springframework.aop.interceptor.AsyncExecutionInterceptor.lambda$invoke$0(AsyncExecutionInterceptor.java:115)
	at java.util.concurrent.FutureTask.run(FutureTask.java:266)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)

Process finished with exit code 0
```

[![DIrmT0.png](https://s3.ax1x.com/2020/12/02/DIrmT0.png)](https://imgchr.com/i/DIrmT0)

再次愣住，众所周知，出现`InterruptException`的原因之一就是当线程`sleep`的时候被中断就会抛出这个异常，具体可以参考笔者的[这篇](http://123.56.245.109/2019/01/20/Blog/java%E5%A4%9A%E7%BA%BF%E7%A8%8B/#interrupt-%E6%96%B9%E6%B3%95)文章。那么问题来了，我们的代码中也没有interrupt的相关操作啊。但是冷静观察一下你就会发现，在抛出异常的上面，还有这么一行：

```java
org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor - Shutting down ExecutorService 'asyncTaskExecutor'java.lang.InterruptedException: sleep interrupted
```

也就是说，是由于主线程先结束的，然后这时候线程池打算shutdown了，于是就interrupt了我们的子线程。换句话说就是，这个线程池是跟着主线程走的，主线程结束它就结束。

[![DIc8C6.png](https://s3.ax1x.com/2020/12/02/DIc8C6.png)](https://imgchr.com/i/DIc8C6)

这似乎和我们平时用的线程池不太一样啊，平时使用也没见它这么猴急，还没等子线程结束就匆匆shutdown啊。在网上阅读了一些文章后发现，似乎问题不是出在线程池上，而是单元测试！还记得笔者在文章开始的时候说过这个测试代码是写在`springboot`的test文件夹下吗，也就是单元测试的位置，目测是在单元测试中，当主线程执行完之后，主线程所在bean就被回收了，不只是线程池，换成原生的线程创建方法都会有这么个问题。



那么怎么解决呢？严格来讲，这种情况只有在单元测试时才出现，所以不用太在意，但是如果非要解决，也是有办法的：

```java
        asyncTaskExecutor.setWaitForTasksToCompleteOnShutdown(true);
```

加上这句，线程池就会等task都执行完才会shutdown了。



下面来讲上面的遗留问题：使用`@async`时，为什么异步方法不能和调用它的方法属于同一个类？

其实要回答这个问题，最好的办法就是去理解和实现spring中的依赖注入，然后手写一个注解，下面给出参考自[这篇](https://juejin.cn/post/6844903855931523085)文章的回答：

spring 在扫描bean的时候会扫描方法上是否包含`@Async`注解，如果包含，spring会为这个bean动态地生成一个子类（即代理类，proxy），代理类是继承原来那个bean的。此时，当这个有注解的方法被调用的时候，实际上是由代理类来调用的，代理类在调用时增加异步作用。然而，如果这个有注解的方法是被同一个类中的其他方法调用的，那么该方法的调用并没有通过代理类，而是直接通过原来的那个 bean 也就是 this. method，所以就没有增加异步作用，我们看到的现象就是`@Async`注解无效。

