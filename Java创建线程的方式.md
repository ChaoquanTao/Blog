---
title: Java创建线程的方式
date: 2019-11-11 14:34:02
updated: 2019-11-11 14:34:02
tags: 多线程
categories: 多线程
---

#### 继承`Thread`类

继承`Thread`类，重写`run()`方法。

```java
public class ExtendThread extends Thread {
    @Override
    public void run() {
        super.run();
        System.out.println("this is  sub thread extends from Thread");
    }

    public static void main(String[] args) {
        new ExtendThread().start();
    }
}
```

java中是单继承，如果使用这种方式的话，每个类即是一个线程。



#### 实现`Runnable`接口

重写`run()`方法。

```java
public class RunnableThread implements Runnable {
    @Override
    public void run() {
        System.out.println("this is thread implements Runnable");
    }

    public static void main(String[] args) {
        Runnable runnable = new RunnableThread() ;

        new Thread(runnable).start();

    }
}

```



#### `Callable`+`Future`

先看下`Callable`接口的定义

```java
public interface Callable<V> {
    /**
     * Computes a result, or throws an exception if unable to do so.
     *
     * @return computed result
     * @throws Exception if unable to compute a result
     */
    V call() throws Exception;
}

```

再来看下`Future`

```java
public interface Future {
  boolean cancel(boolean mayInterruptIfRunning);
  boolean isCancelled();
  boolean isDone();
  V get() throws InterruptedException, ExecutionException;
  V get(long timeout, TimeUnit unit)
    throws InterruptedException, ExecutionException, TimeoutException;
}
```

我们一般配合线程池来使用，因为：

```java
` Future submit(Callable task);`` Future submit(Runnable task, T result);``Future submit(Runnable task);`
```

例子：

```java
public class CallableThread implements Callable<Integer> {
    @Override
    public Integer call() throws Exception {
        int sum = 0;
        for (int i=0; i<100; i++)
            sum += i ;
        return sum;
    }

    public static void main(String[] args) throws ExecutionException, InterruptedException {
        ExecutorService service = new ThreadPoolExecutor(5,10,60L,
                TimeUnit.SECONDS,new ArrayBlockingQueue(10));

        Future future = service.submit(new CallableThread()) ;

        System.out.println(future.get());

    }
}
```

上面实现`Runnable`接口已经比继承自`Thread`类的实现方法更为优雅了，但是这种方法还有一个问题，就是无法获得子线程的执行结果。这时候就需要`Callable`接口，它和`Runnable`接口效果差不多，唯一不同的是有返回值。这里配合`Future`来接收。



#### `Callable`+`FutureTask`

`FutureTask`

```java
public class FutureTask<V> implements RunnableFuture<V>
```

```java
public interface RunnableFuture<V> extends Runnable, Future<V>
```

例子：

```java
public class FutureTaskThread implements Callable<Integer> {
    @Override
    public Integer call() throws Exception {
        int sum = 0;
        for (int i=0; i<100; i++)
            sum += i ;
        return sum;
    }

    public static void main(String[] args) {
        FutureTask futureTask = new FutureTask(new FutureTaskThread()) ;
        ExecutorService service = new ThreadPoolExecutor(5,10,60L, TimeUnit.SECONDS,new ArrayBlockingQueue<>(10));

        service.submit(futureTask) ;

        try {
            System.out.println(futureTask.get());
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (ExecutionException e) {
            e.printStackTrace();
        }
    }
}
```

