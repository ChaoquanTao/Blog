---
title: java多线程
date: 2019-01-20 12:56:25
tags: java多线程
categories: Java
---

### Threadlocal

`ThreadLocal`是一个支持泛型的类，它为每个线程提供局部变量，这种变量是其他线程访问不到的，实现了线程的数据隔离。

线程间隔离，方法间共享

#### 内部方法

##### set

```
 public void set(T value) {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
    }
```

获取当前线程，获取当前线程的`ThreadLocalMap`,然后存储键值对。这里需要注意Thread中是由一个类型为`ThreadLocalMap`的变量`threadLocals`,其中`ThreadLocalMap`就是一个定制的`hashmap`.

##### get

```
public T get() {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null) {
            ThreadLocalMap.Entry e = map.getEntry(this);
            if (e != null) {
                @SuppressWarnings("unchecked")
                T result = (T)e.value;
                return result;
            }
        }
        return setInitialValue();
    }
    
 private T setInitialValue() {
        T value = initialValue();
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
        return value;
    }
    
protected T initialValue() {
        return null;
    }

```

##### remove

```
 public void remove() {
         ThreadLocalMap m = getMap(Thread.currentThread());
         if (m != null)
             m.remove(this);
     }
```

正常来讲，`ThreadLocal`对象会在每个线程里面 创建一个变量副本，线程间是不可互相访问这些变量的，但是在有些情况下，我们需要在子线程中也能访问父线程中的变量，这时候可以使用`InheritableThreadLocals`类，当父线程创建子线程时，父线程中`inheritalbeThreadLocals`变量里的本地变量复制一份保存到子线程的`inheritableThreadLocals`变量里面，

但是复制过来以后，他们也是互相独立的副本了，修改起来互不相干。

#### 总结

`ThreadLocal`类通过操作Thread类里面的`ThreadLocalMap`类型的变量，来实现线程私有变量的访问。真正私有变量是放在这个定制的`hashmap`里被维护的。



### Java线程中断

会有这种情况，由于某种需求你需要一个子线程去执行某些任务，但是这个任务可能在中途由于其他因素需要被中断或者中止，对于这种情况，就需要用到java的线程中断的方法了。

#### interrupt()方法

准确的讲，`interrupt()`方法并不是真正的中断线程，它的真正作用是修改线程中的标志位，然后我们根据标志位，手动的去中断这个线程（后面会讲到可能是根据标志位也可能是根据线程抛出的异常去手中断线程）。

```
public void interrupt() {
        if (this != Thread.currentThread())
            checkAccess();

        synchronized (blockerLock) {
            Interruptible b = blocker;
            if (b != null) {
                interrupt0();           // Just to set the interrupt flag
                b.interrupt(this);
                return;
            }
        }
        interrupt0();
    }
```

这里我贴了一段源码，如果没猜错的话，这个`interrupt0()`方法就是用来修改标志位的。



interrupt()方法可以用来中断线程，根据所要中断的线程是阻塞的或者是非阻塞的，做法不同。

1. 如果要中断的线程是被`wait(),sleep(),join()`方法阻塞，那么中断状态会被清除并且抛出一个`InterruptedException`异常。

   什么意思呢？上文中我们讲到`interrupt()`方法其实修改的是线程的中断标志位，而非真正中断线程。在这里可以看到，如果要中断的线程是被这些方法阻塞的，当我们调用`interrupt()`方法时，虽然标志位会被修改，但是我们是察觉不到的，因为它又会被clear掉，也就是被重新置为`false`,所以在这种情况下，我们要去中断线程的话，就得`catch`这个异常，然后在`catch`中操作了。

2. 如果要中断的线程是通过`InterruptibleChannel`被I/O操作阻塞的话，标志位会被修改为true,同时会抛出`ClosedByInterruption`异常。

   对于这种情况我没有进行尝试，但是从字面意思来看，我们应该既可以从标志位入手去中断线程也可以从异常入手去做。

3. 如果线程被`Selector`阻塞，那么通过interrupt()中断它时；线程的中断标记会被设置为true，并且它会立即从选择操作中返回

4. 如果不属于前面所说的情况，那么通过interrupt()中断线程时，它的中断标记会被设置为“true”



上面的操作都提到了标志位，那么标志位怎么获得呢？

+ `interrupted()`:静态方法，调用它时，标志位会被清除。这意味着如果你连着调用两次这个方法，那么第二次结果肯定是false.
+ `isInterrupted()`：非静态方法，调用它时，标志位不会被清楚。



下面是一个例子，相关说明已经写在了注释里

```

import static java.lang.Thread.sleep;

public class ThreadTest {


    public static void main(String[] args) throws InterruptedException {

        Thread t1 = new MyThread1();
        Thread t2 = new MyThread2();
        t1.start();
        t2.start();

        System.out.println("after two minutes thread one interrupt");
        try {
            sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        t1.interrupt();
        t2.interrupt();


        Thread.sleep(3000);
        System.out.println("in main " + t1.getName() + " " + t1.getState() + " " + t1.isInterrupted());

        System.out.println("in main " + t1.getName() + " " + t2.getState() + " " + t2.isInterrupted() );
    }
}

/**
 * 非阻塞型线程，通过判断标志位来实现线程中止
 */
class MyThread1 extends Thread {
    @Override
    public void run() {

        for (; ; ) {
            System.out.println("in "+getName());

            if (isInterrupted()) {
                /**
                 * 下面调用了一次interrupted()方法，标志位被清除，所以再次调用isInterrupted()方法时为false
                 */
                System.out.println(getName() + " " + getState() + " " + interrupted()+" "+isInterrupted() );
                break;
            }

        }
    }
}

/**
 * 阻塞型线程，通过异常来终止
 */
class MyThread2 extends Thread {
    @Override
    public void run() {
        try {
            for (; ; ) {
                System.out.println("in "+getName());
                sleep(500);
            }
        } catch (InterruptedException e) {
            System.out.println(getName() + " " + getState() + " " + isInterrupted());
            e.printStackTrace();
        }
    }
}

```

### Java线程池

我们通常使用的一种创建线程池的方式：

```
ExecuttorService executorService = new ThreadPoolExecutor(1,1,60,TimeUnit.SECONDS,new ArrayBlockingQueue<>(10));
```

它的构造函数是这样的：

```
public ThreadPoolExecutor(int corePoolSize,
                              int maximumPoolSize,
                              long keepAliveTime,
                              TimeUnit unit,
                              BlockingQueue<Runnable> workQueue,
                              RejectedExecutionHandler handler)
```

其中：

 `corePoolSize`: 核心线程数量

`maximumPoolSize`:最大线程数数量

`keepAliveTime`:那些超过核心线程数数量的的线程如果在这个时间内没有被执行，就会被回收。

`unit`:上一个参数的时间单位。

`workQueue`:用来存储等待执行的任务。

`hander`:拒绝任务处理时的策略。



看`ThreadPoolExecutor`的定义，可以发现它继承了`AbstractExecutorService`

```
public class ThreadPoolExecutor extends AbstractExecutorService
```

再来看下`AbstractExecutorService`的定义:

```
public abstract class AbstractExecutorService implements ExecutorService
```

它实现了`ExecutorService`接口

再来看下`ExecutorService`接口

```
public interface ExecutorService extends Executor
```

它实现了`Executor`接口：

```
public interface Executor{
    void execute(Runnable command)
}
```



我们来画下它们的类图

![](https://s2.ax1x.com/2019/04/16/AvdkUs.jpg)

可以看出，Executor是最顶层的接口。



解下来我们来看下`ThreadPoolExecutor`里面的一些变量和方法.

首先是`ctl`相关的：

```
private final AtomicInteger ctl = new AtomicInteger(ctlOf(RUNNING, 0));
    private static final int COUNT_BITS = Integer.SIZE - 3;
    private static final int COUNT_MASK = (1 << COUNT_BITS) - 1;

    // runState is stored in the high-order bits
    private static final int RUNNING    = -1 << COUNT_BITS;
    private static final int SHUTDOWN   =  0 << COUNT_BITS;
    private static final int STOP       =  1 << COUNT_BITS;
    private static final int TIDYING    =  2 << COUNT_BITS;
    private static final int TERMINATED =  3 << COUNT_BITS;

    // Packing and unpacking ctl
    private static int runStateOf(int c)     { return c & ~COUNT_MASK; }
    private static int workerCountOf(int c)  { return c & COUNT_MASK; }
    private static int ctlOf(int rs, int wc) { return rs | wc; }
```

`ctl`这个变量其实是个组合变量，用它来表示**线程数量**`workerCount`和线程**工作状态**`runState`。

从下面几行可以看出来，线程状态有五种，那么就需要三个比特位来表示，剩下的`Integer.SIZE-3`也就是29位用来表示线程数量，一共能表示$2^{29}-1$个线程。第三行则是通过位运算来计算掩码，掩码是长度为29 bit的1。

所以现在的情况是这样的，`ctl`一共有32位，高三位用来表示线程池运行状态，低29位用来表示线程数量。

下面看下这几个拆解`ctl`的方法：

```
    private static int runStateOf(int c)     { return c & ~COUNT_MASK; }
```

这个方法是为了获取运行状态。掩码是29个1，取非，29个0，与`ctl`与运算，得到`ctl`的高三位+29个0，正好和上面几行的`runState`的左移对应起来。



```
    private static int workerCountOf(int c)  { return c & COUNT_MASK; }
```

这个方法用来获取线程数量，与的结果就是`ctl`的低29位。



```
    private static int ctlOf(int rs, int wc) { return rs | wc; }
```

这个方法`runState`和`workerCount`来组合出一个`ctl`



再来看下`execute`方法：

它的代码如下：

```
public void execute(Runnable command) {
        if (command == null)
            throw new NullPointerException();
        int c = ctl.get();
        if (workerCountOf(c) < corePoolSize) {
            if (addWorker(command, true))
                return;
            c = ctl.get();
        }
        if (isRunning(c) && workQueue.offer(command)) {
            int recheck = ctl.get();
            if (! isRunning(recheck) && remove(command))
                reject(command);
            else if (workerCountOf(recheck) == 0)
                addWorker(null, false);
        }
        else if (!addWorker(command, false))
            reject(command);
    }
```

我们分批来看这块代码：

```
int c = ctl.get();
        if (workerCountOf(c) < corePoolSize) {
            if (addWorker(command, true))
                return;
            c = ctl.get();
        }
```

首先，获得当前线程数，如果小于`corePoolSize`，那么就添加新的线程去执行任务。如果添加线程成功了，直接return,否则，重新获得`ctl`的值，继续下面的判断。



```
if (isRunning(c) && workQueue.offer(command)) {
            int recheck = ctl.get();
            if (! isRunning(recheck) && remove(command))
                reject(command);
            else if (workerCountOf(recheck) == 0)
                addWorker(null, false);
        }
```

在执行这个代码块时我们需要注意，来到第二个代码块时，第一个代码块的判断条件可能是`workerCount`大于等于`corePoolSize`,也可能是`addWorker`失败。如果线程池`isRunning`,则尝试向`workQueue`中添加任务，如果添加成功，重新获得`ctl`值，double check 线程池是否running,如果此时线程池没有running，则remove掉当前任务，并且执行reject. 如果线程池在运行，或者remove失败，检查`workerCount`是否为0，如果为0则添加一个空的thread.



```
else if (!addWorker(command, false))
            reject(command);
```

如果添加核心线程失败，则直接拒绝。



这个可能看着有点迷，先看下里面的`addWorker`方法

//有空再写吧



这里推荐一篇讲的很仔细的博客：https://mp.weixin.qq.com/s/-89-CcDnSLBYy3THmcLEdQ



### Java中的锁

图片来自[美团技术团队博客](https://tech.meituan.com/2018/11/15/java-lock.html)

![](https://s2.ax1x.com/2019/05/06/EBNFgJ.png)

这些分类更多的是按照锁的特性和设计来分类的，并不是说真真正正的有这么多的锁。



下面我会介绍Java中的`synchronized` 、 `reentrylock`等锁，以及它们分别属于哪些类别。

