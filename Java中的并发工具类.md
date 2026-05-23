---
title: Java中的并发工具类
date: 2019-12-02 11:28:28
updated: 2019-12-02 11:28:28
tags: 并发
categories: Java
---

#### `CountDownLatch`

多线程的使用中往往有这样的场景：某个线程需要等到其他线程执行完毕后才能继续执行，即线程的“等待其他线程”的功能（注意这里说的不是`wait()`）。这时候就可以用`CountDownLatch`类来实现，当然了，`Thread.join()`方法也具有这个功能，只不过相比之下，`CountDownLatch`功能更加丰富。

通过一个例子来看下：

```java
import java.util.concurrent.CountDownLatch;

public class CountDownLatchTest {

    static CountDownLatch cdl = new CountDownLatch(3) ;

    public static void main(String[] args) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                System.out.println(Thread.currentThread().getName()+" is running");
                cdl.countDown();
            }
        }).start();

        new Thread(new Runnable() {
            @Override
            public void run() {
                System.out.println(Thread.currentThread().getName()+" is running");
                cdl.countDown();
            }
        }).start();

        new Thread(new Runnable() {
            @Override
            public void run() {
                System.out.println(Thread.currentThread().getName()+" is running");
                cdl.countDown();
            }
        }).start();

        try {
            cdl.await();
            System.out.println("sub thread executed");
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
       
    }
}
```

在上面的代码中，我们新建了三个子线程，现在想要等到三个子线程都执行完毕了输出一句`sub thread executed`. 我们使用了`CountDownLatch`来实现这个功能。

```java
static CountDownLatch cdl = new CountDownLatch(3) ;
```

这句话设置`CountDownLatch`计数器的值为3，表示对三个线程进行计数。

```java
cdl.countDown();
```

在每个线程里执行这句话，将计数器的值减一。

```java
cdl.await();
```

在主线程中使用`await()`方法等待计数器值为0的时候就开始执行后续代码。

> 所以需要注意一个问题，如果我们设置计数器值为3，但是在子线程中只执行力两次`coutDown()`，那么主线程中的`await()`方法后面的内容永远也不会被执行到。



#### `CyclicBarrier`

`CyclicBarrier`用于让一组线程都到达某个状态后然后统一同时开始继续执行。从名字来看，`CyclicBarrier`就是可以循环利用的屏障，所以它的作用也就是在线程执行中插入一个屏障，当所有的线程都执行到屏障这里后，才能统一继续往下执行。

通过下面的代码来看：

```java
public class CyclicBarrierTest {
    static  int THREAD_COUNT =3 ;

    public static void main(String[] args) {
        CyclicBarrier cyclicBarrier = new CyclicBarrier(3);

        for (int i = 0; i < THREAD_COUNT; i++) {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    System.out.println(Thread.currentThread().getName() + " 到达屏障前");
                    try {
                        cyclicBarrier.await();
                        System.out.println(Thread.currentThread().getName() + " 到达屏障后");

                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    } catch (BrokenBarrierException e) {
                        e.printStackTrace();
                    }
                }
            }).start();
        }

    }
}

```

创建了三个线程，同时`CyclicBarrier`的计数器为3，在每个线程的执行代码中插入一句：

```java
cyclicBarrier.await();
```

那么该代码后续的内容需要等到所有线程都执行到屏障这里才能继续执行。

执行结果：

```java
Thread-1 到达屏障前
Thread-0 到达屏障前
Thread-2 到达屏障前
Thread-2 到达屏障后
Thread-1 到达屏障后
Thread-0 到达屏障后
```



> `CyclicBarrier`相比于`CountDownLatch`，区别之一在于它可以循环利用，这也是它名字里`cyclic`的意义所在，`CyclicBarrier`的计数器可以通过`reset()`重置。