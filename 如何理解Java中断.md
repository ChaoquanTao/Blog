---
title: 【基本功】如何理解Java线程中断
categories: Java
tags: 中断
date: 2023-03-12 09:00:00
---

### 什么是线程中断

从广义上讲，就是中断一个正在工作或sleep的线程，从代码上讲，  所谓的线程中断，就是设置某个线程的中断标志位，当我想要中断某个线程的时候，就将这个线程的中断标志位设置为true, **但是至于是否响应中断，全凭JVM或这个线程自己决定**。

### 为什么要有中断

 一种常见的用途是用于线程池的`shutdown`方法, 如果你去查看`ThreadPoolExecutor`的`shutdown`方法方法，就会发现其底层就是通过线程中断来终止掉正在工作的线程的。🌰：

```java
public void shutdown() {
        final ReentrantLock mainLock = this.mainLock;
        mainLock.lock();
        try {
            checkShutdownAccess();
            advanceRunState(SHUTDOWN);
            interruptIdleWorkers(); //在这里中断线程
            onShutdown(); 
        } finally {
            mainLock.unlock();
        }
        tryTerminate();
    }
```



```java
private void interruptIdleWorkers(boolean onlyOne) {
        final ReentrantLock mainLock = this.mainLock;
        mainLock.lock();
        try {
            for (Worker w : workers) {
                Thread t = w.thread;
                if (!t.isInterrupted() && w.tryLock()) {
                    try {
                        t.interrupt(); //通过调用Thread.interrupt方法来中断正在工作的线程
                    } catch (SecurityException ignore) {
                    } finally {
                        w.unlock();
                    }
                }
                if (onlyOne)
                    break;
            }
        } finally {
            mainLock.unlock();
        }
    }
```



### 如何中断

和线程中断相关的一共有三个方法，分别是：

+ 静态方法`Thread.isInterrupted`

+ `Thread.interrupt`: 

+ 静态方法`Thread.interrupted`

  

#### `Thread.isInterrupted`

该方法是`Thread`类的一个静态方法，返回当前线程的中断标志位状态。



#### `Thread.interrupt`

这个方法是Thread的一个成员方法，它会设置当前线程的中断标志位为true, 至于当前线程是否响应中断，和当前线程的执行内容有关。

所谓能够响应中断，是指:

1. 如果在线程里调用了`Object.wait()`相关重载方法，`Thread.join()`相关重载方法，以及`Thread.sleep()`相关重载方法，则当前线程的中断标志位会被清空，并抛出一个`InterruptedException`异常

   ```java
   public static void main(String[] args) throws InterruptedException {
           Thread t = new Thread(() -> {
               while (!Thread.currentThread().isInterrupted()){
                   try {
                       System.out.println("in loop");
                       Thread.sleep(2000);
                   } catch (InterruptedException e) {
                       System.out.println("after interrupted: " + Thread.currentThread().isInterrupted());
                   }
               }
           });
   
           t.start();
           Thread.sleep(1000);
           t.interrupt();
       }
   ```

   对于上述代码，`Thread.currentThread().isInterrupted()`用于查看当前线程的中断标志位。初始时由于线程未被中断，`Thread.currentThread().isInterrupted()`返回`false`, 所以能够进入到`while`循环中，当执行`t.interrupt()`时，线程t会抛出`InterruptedException`并清空标志位，所以`Thread.currentThread().isInterrupted()`依然返回`false`, 从而`while`循环能够一直进行下去。

   所以上述代码输出:

   ```java
   in loop
   after interrupted: false
   in loop
   in loop
   ...
   ```

   相反，如果我们只中断线程，但是不对中断标志位做任何响应的话，那么目标线程还是会正常运行:

   ```java
   public static void main(String[] args) throws InterruptedException {
           Thread t = new Thread(() -> {
               while (true){
                   boolean interrupted = Thread.currentThread().isInterrupted();
                   System.out.println("in loop, flag is: "+ interrupted);
               }
           });
   
           t.start();
           Thread.sleep(1000L);
           t.interrupt();
       }
   ```

   输出：

   ```java
   ...
   in loop, flag is: false
   in loop, flag is: false
   in loop, flag is: true
   in loop, flag is: true
   ...  
   ```

   

2. 如果当前线程阻塞在`InterruptibleChannel`类型的IO操作上，则会将当前线程中断标志位置为true并抛出一个`ClosedByInterruptException`

   🌰：

   ```java
   public static void main(String[] args) throws IOException, InterruptedException {
   
           Thread t = new Thread(() -> {
               try {
                   SocketChannel sc = SocketChannel.open(new InetSocketAddress("localhost", 8080));
                   sc.read(ByteBuffer.allocate(1));
               } catch (ClosedByInterruptException e) {
                   System.out.println("thread is interrupted, and the flag is:" + Thread.currentThread().isInterrupted());
               } catch (IOException e) {
                   throw new RuntimeException(e);
               }
           });
   
           t.start();
           Thread.sleep(1000);
           t.interrupt();
       }
   ```

   上述代码代码会打开一个`SocketChannel`并阻塞监听8080端口，如果此时中断当前线程，则会将线程中断标志位置为`true`并且抛出`ClosedByInterruptException`, 所以上述代码输出为：

   ```java
   thread is interrupted, and the flag is:true
   ```

   

3. 如果当前线程阻塞在NIO的`Selector`上，则会将线程中断标志位置为`true`并且立即从`select`动作中返回。🌰：

   ```java
   public static void main(String[] args) throws InterruptedException {
   
           Thread t = new Thread(() -> {
               try {
                   Selector selector = Selector.open();
                   ServerSocketChannel sc = ServerSocketChannel.open();
                   sc.socket().bind(new InetSocketAddress(8080));
                   sc.configureBlocking(false);
                   sc.register(selector, SelectionKey.OP_ACCEPT);
                   selector.select(); //如果没有被中断且没有感兴趣的事件发生，则会一直阻塞在这里
                   System.out.println("如果走到了这里，说明线程被中断或者有感兴趣的事件发生");
               } catch (IOException e) {
                   throw new RuntimeException(e);
               }
           });
   
           t.start();
           Thread.sleep(1000L);
     			t.interrupt();
       }
   ```

   上述代码中，我们使用NIO的方式开启了一个server, 并监听8080端口，由于没有感兴趣的事件发生，server的代码会一直阻塞在` selector.select()`，此时如果中断当前线程，则`select`方法会立即返回，并打印下第11的输出。

   > ps: 可以看到第三点和第四点讲的都是NIO的中断响应，为什么没有讲到BIO呢，因为BIO是不会对中断抛出异常或立即返回的(虽然也会设置中断标志位为true, 但是在代码行为上不会有任何变化)，对于下述代码，服务端会阻塞在第12行`serverSocket.accept`上，当我们执行`t.interrupt()`后，虽然在主线程第23行的打印中可以看到线程t的标志位已经为`true`，但是`ServerSocket`依然阻塞，不会有任何改变。
   >
   > ```java
   > public static void main(String[] args) throws InterruptedException {
   >         Thread t = new Thread(() -> {
   >             ServerSocket serverSocket = null;
   >             try {
   >                 serverSocket = new ServerSocket(83);
   >             } catch (IOException e) {
   >                 throw new RuntimeException(e);
   >             }
   > 
   >             try {
   >                 while (true) {
   >                     Socket socket = serverSocket.accept();
   >                 }
   >             } catch (IOException e) {
   >                 throw new RuntimeException(e);
   >             }
   >         });
   > 
   >         t.start();
   > 
   >         Thread.sleep(1000L);
   >         t.interrupt();
   >         System.out.println(t.isInterrupted());
   >     }
   > ```

4. 对于非上述几种类型，则只会将中断标志位设置为true. 

小小总结一下，`Thread.interrupt`的本质是将线程中断标志位设置为`true`, 对于一些特殊的方法，如`sleep`,`wait`等，会抛出`InterruptedException`并清空中断标志位，对于其他操作，要么抛异常，要么立即返回，要么do nothing, 但是不会清空标志位。但无论如何，至于是否要响应中断，其实是目标线程自身决定的。



#### `Thread.interrupted`

`interrupted`是`Thread`类的一个静态方法，它会返回当前线程的中断标志位并清空，这意味着，如果连续两次调用该方法，第二次一定返回的是`false`. 举个例子：

```java
public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            while (!Thread.currentThread().isInterrupted()){
                System.out.println("in loop, flag");
            }
            System.out.println("thread is interrupted, before invoker Thread.interrupted(): "+ Thread.currentThread().isInterrupted());
            System.out.println("after invoker Thread.interrupted(): "+Thread.interrupted());
            System.out.println("after invoke Thread.interrupted() again: "+Thread.interrupted());
        });

        t.start();
        Thread.sleep(1L);
        t.interrupt();
    }
```

输出：

```java
...
in loop, flag
thread is interrupted, before invoker Thread.interrupted(): true
after invoker Thread.interrupted(): true
after invoke Thread.interrupted() again: false
```

当线程t被中断后，第一次调用`Thread.interrupted()`,返回`true`, 再次调用，返回`false`

### 写在最后

Java的线程中断给我们提供了一种去改变目标线程状态的方式，和`Thread.stop`相比，中断更加温柔，它给目标线程提供了一个终止的机会，但是至于是否真的要终止，其实是由目标线程自身决定的，由目标线程自身决定是否对中断标志位的变更进行响应。





























