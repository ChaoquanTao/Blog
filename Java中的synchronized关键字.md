---
title: Java中的synchronized关键字
date: 2019-09-13 16:51:50
updated: 2019-09-13 16:51:50
tags: 关键字
categories: Java
---

本文主要从两个方面讲解synchronized关键字，第一个是用法，第二个是原理，即为什么synchronized关键字能够保持线程同步。

## 用法

synchronized的修饰对象主要有以下两种：

1. 修饰一个代码块。
   1. `synchronized(this|object) {}`:获得对象级的锁。当**多个线程**访问**同一对象内的同步代码块**时，只能互斥访问
   2. `synchronized(类.class) {}`:获得类级别的锁。当**多个线程**访问**由这个类定义的所有对象的的同步方法**时，只能互斥访问。
2. 修饰一个方法。

   1. 修饰非静态方法。获得对象级的锁，当**多个线程**访问**同一对象的同步方法**时，只能互斥访问。
   2. 修饰静态方法。获得类级的锁，当**多个线程**访问**由这个类定义的所有对象的的同步方法**时，只能互斥访问。



### 修饰代码块

#### 获取对象锁

1. 多个线程访问同一对象的同步代码块

```java
class SynTest implements Runnable {

    @Override
    public void run() {
        synchronized (this) {
            for (int i = 0; i < 5; i++) {
                System.out.println(Thread.currentThread().getName() + " " + i);
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }
}

public class Test {
    public static void main(String[] args) {
        //定义对象
        SynTest synTest = new SynTest();

        //两个thread传入的是同一对象
        Thread thread1 = new Thread(synTest);
        Thread thread2 = new Thread(synTest);

        thread1.start();
        thread2.start();
    }
}

```

输出：

```java
Thread-0 0
Thread-0 1
Thread-0 2
Thread-0 3
Thread-0 4
Thread-1 0
Thread-1 1
Thread-1 2
Thread-1 3
Thread-1 4
```

可以看到对于同一对象的同步代码块，同一时间只能有一个线程去访问。

2. 多个线程访问不同对象的同步代码块

我们稍微修改以下上述代码，分别定义两个SyntTest对象

```java
public class Test {
    public static void main(String[] args) {
        //定义两个对象
        SynTest synTest1 = new SynTest();
        SynTest synTest2 = new SynTest();

        //两个thread传入的是不同对象
        Thread thread1 = new Thread(synTest1);
        Thread thread2 = new Thread(synTest2);

        thread1.start();
        thread2.start();


    }

}
```

输出：

```java
Thread-0 0
Thread-1 0
Thread-1 1
Thread-0 1
Thread-0 2
Thread-1 2
Thread-0 3
Thread-1 3
Thread-1 4
Thread-0 4
```

可以看到，我们获取到的是对象级的锁，而两个线程访问的是两个对象里不同的同步方法，所以不存在同步问题。



3. 多个线程访问同一对象的同步代码块和非同步代码块



```java
class SynTest implements Runnable {

    void print1() {
        synchronized (this) {
            System.out.println("this is thread1");
            try {
                Thread.sleep(10000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    void print2() {
        System.out.println("this is thread2");
    }

    @Override
    public void run() {
        if(Thread.currentThread().getName().equals("thread1")){
            print1();
        }else {
            print2();
        }
    }
}

public class Test {
    public static void main(String[] args) {
        SynTest synTest = new SynTest();

        //两个thread传入的是同一对象
        Thread thread1 = new Thread(synTest, "thread1");
        Thread thread2 = new Thread(synTest, "thread2");

        thread1.start();
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        thread2.start();
    }

}
```

我们让thread1在synchronized代码段中停留十秒钟，如果有阻塞，那么这段时间thread2应该是不会有输出的，得等到thread1输出完它才输出。而事实是：

```java
this is thread2
this is thread1
```

说明不同线程执行同一对象的同步代码段和非同步代码段是互相不受干扰的。

需要注意的是，上面的代码中synchronized修饰的都是this，意味这访问同步代码段的线程持有了这个对象的锁，那么括号里的对象可以换成其他的Object吗，答案是可以的。严格来讲，对于代码块的使用场景是这样的：这接下来的一块代码里，可能会并发修改某个对象的问题，那么我们应该给这个对象加锁，也就是括号里应该写的是这个对象。但事实是，你可以随便指定一个对象包含的变量，都可以起到加锁的作用，比如：

```java
class Test implements Runnable
{
   private byte[] lock = new byte[0];  // 特殊的instance变量
   public void method()
   {
      synchronized(lock) {
         // todo 同步代码块
      }
   }

   public void run() {

   }
}
```

至于是为什么，我们在原理部分会讲到。

#### 获取类锁

1. 不同线程访问同一个类不同实例的同步代码块

   ```JAVA
   class SynTest implements Runnable {
   
       @Override
       public void run() {
           synchronized (SynTest.class) {
               for (int i = 0; i < 5; i++) {
                   System.out.println(Thread.currentThread().getName() + " " + i);
                   try {
                       Thread.sleep(1000);
                   } catch (InterruptedException e) {
                       e.printStackTrace();
                   }
               }
           }
       }
   }
   
   public class Test {
       public static void main(String[] args) {
           //定义对象
           SynTest synTest1 = new SynTest();
           SynTest synTest2 = new SynTest();
   
           //两个thread传入的是不同对象
           Thread thread1 = new Thread(synTest1);
           Thread thread2 = new Thread(synTest2);
   
           thread1.start();
           thread2.start();
       }
   }
   ```

   输出：

   ```java
   Thread-0 0
   Thread-0 1
   Thread-0 2
   Thread-0 3
   Thread-0 4
   Thread-1 0
   Thread-1 1
   Thread-1 2
   Thread-1 3
   Thread-1 4
   ```

   可以看到，虽然两个线程传入的是不同的对象，但是因为我们的同步代码块修饰的是一个类而不是一个对象，所以只要是这个类定义的对象，在被线程访问时都需要获取锁。

   

### 修饰方法

修饰方法和修饰代码是差不多的，仍然分为获取对象锁和获取类锁，只不过粒度薛微大了点，这里就不赘述啦。

## 实现

给出下面一段代码，

```java
public class Test {

    public synchronized void synMethod(){
        System.out.println("this is a sync method");
    }

    public void method2(){
        synchronized (this){
            System.out.println("this is a sync block");
        }
    }

}
```

反编译后得到如下信息：

![](https://s2.ax1x.com/2019/09/17/n5cR3Q.png)

可以看到，对于synchronized修饰的方法，JVM使用ACC_SYNCHRONIZED标记符来实现同步。顺便一提，这个方法的标记符是作为符号引用放在常量池中的，参考[这篇]([https://inewbie.top/2019/09/04/%E8%B0%88%E4%B8%80%E8%B0%88Java%E5%B8%B8%E9%87%8F%E6%B1%A0%E4%B9%8Bclass%E5%B8%B8%E9%87%8F%E6%B1%A0/](https://inewbie.top/2019/09/04/谈一谈Java常量池之class常量池/))文章。

对于synchronized修饰的代码块，则是使用monitorenter和monitorexit两个指令来实现同步。

## 原理

好，讲完了synchronized的用法之后，我们再来考虑一下，synchronized是如何保持线程同步的，上文中一直讲到的获取锁，又是个什么操作呢。

先说两个结论：

+ synchronized基于monitor机制实现
+ 任何对象均可作为锁

至于原因，我们接下来解释。

要说明这个问题，首先我们要理解Monitor机制和Java的对象模型。

### Monitor

monitor，被翻译成监视器，或者管程。它是一种同步机制，在不同的语言里，有不同的实现。但是无论哪种语言实现，它的核心元素有以下四种：

- 监视者对象 (Monitor Object): 负责定义公共的接口方法，这些公共的接口方法会在多线程的环境下被调用执行。
- 同步方法：这些方法是监视者对象所定义。为了防止竞争条件，无论是否同时有多个线程并发调用同步方法，还是监视者对象含有多个同步方法，在任一时间内只有监视者对象的一个同步方法能够被执行。
- 监视锁 (Monitor Lock): 每一个监视者对象都会拥有一把监视锁。
- 监视条件 (Monitor Condition): 同步方法使用监视锁和监视条件来决定方法是否需要阻塞或重新执行。



从上面synchronized关键字的用法中可以看到，其实synchronized往往需要指定一个对象与之关联，即使它修饰非静态方法，关联的其实是this。这里关联的对象就是监视器对象monitor object, 并且我们在这个对象中定义了很多管理和唤醒线程的方法，比如wait, notify.

你是不是发现了什么，是的没错，在java实现的monitor机制中（我们上面讲了不同的语言对moitor有不同的实现），monitor object其实就是我们的java.lang.Object类定义的对象。

继续讲，这个监视器对象拥有一把锁，所以对于下面这个代码

```java
synchronized(obj){
    do something
}
```

任何线程想要访问这段临界区，都要先获取obj对象的锁。

我们上面讲的这些，在jvm内部都有具体的实现，是基于一种叫做ObjectMonitor的模式实现的。我们来看下它的大概原理：

![nyW3B4.png](https://s2.ax1x.com/2019/09/14/nyW3B4.png)

当一个线程需要获取 Object 的锁时，会被放入 EntrySet 中进行等待，如果该线程获取到了锁，成为当前锁的 owner。如果根据程序逻辑，一个已经获得了锁的线程缺少某些外部条件，而无法继续进行下去（例如生产者发现队列已满或者消费者发现队列为空），那么该线程可以通过调用 wait 方法将锁释放，进入 wait set 中阻塞进行等待，其它线程在这个时候有机会获得锁，去干其它的事情，从而使得之前不成立的外部条件成立，这样先前被阻塞的线程就可以重新进入 EntrySet 去竞争锁。这个外部条件在 monitor 机制中称为条件变量。



讲到这里也就大概解释了为什么我们上面说synchronized是基于monitor实现的了，要记住，monitor不是一个具体的东西，它是一种机制，或者说一种方法论，不同的语言有不同的实现，在java中，synchronized关键字就是monitor的具体实现。同时我们也可以看出，synchronized锁的不是别的，是对象，每个对象都只有一把锁，当被一个线程获取后，其他线程执行到这里也就只能等了。



那么怎么才算一个线程获取了锁呢，这些信息是存储在Java对象的对象头中的。

### Java对象模型

Java对象由三部分组成，对象头，实例数据，填充数据，如下图所示：

![nySQNq.jpg](https://s2.ax1x.com/2019/09/14/nySQNq.jpg)

实例数据就是我们自己coding时写的那部分，填充数据主要是为了字节对齐而设置的，就像网络中数据报格式一样。而和synchronized相关的玄机，都藏在对象头里了。

对象头由两部构成：mark word和class meta data address,如果对象是数组类型，还会有一部分来描述数组长度。

| 长度   | 内容                   | 说明                                      |
| ------ | ---------------------- | ----------------------------------------- |
| 1 Word | Mark Word              | 存储对象的hashcode,分代年龄和锁标记等信息 |
| 1 Word | Class Metadata Address | 存储指向对象类型数据的指针                |
| 1 Word | Array length           | 数组长度                                  |

可以看到，和锁相关的信息的都在Mark Word中，这也是我们重点分析的对象。顺便一提，Class Metadata Address指针指向存储对象类型信息的位置，那对象类型信息放在哪里呢，熟悉JVM内存结构的朋友应该知道，是放在方法区的。

下面我们重点研究Mark Word.

上面我们说到，mark word里面存储了相关的锁信息，那具体的结构是怎样的呢。

下图描述了32位虚拟机上，对象在不同状态下mark word里面的情况：

![ObjectHead](http://www.hollischuang.com/wp-content/uploads/2018/01/ObjectHead-1024x329.png)

其中轻量级锁和偏向锁是Java 6 对 synchronized 锁进行优化后新增加的。

**无锁**

无锁没有对资源进行锁定，所有的线程都能访问并修改同一个资源，但同时只有一个线程能修改成功。

无锁的特点就是修改操作在循环内进行，线程会不断的尝试修改共享资源。如果没有冲突就修改成功并退出，否则就会继续循环尝试。如果有多个线程修改同一个值，必定会有一个线程能修改成功，而其他修改失败的线程会不断重试直到修改成功。上面我们介绍的CAS原理及应用即是无锁的实现。无锁无法全面代替有锁，但无锁在某些场合下的性能是非常高的。

**偏向锁**

偏向锁是指一段同步代码一直被一个线程所访问，那么该线程会自动获取锁，降低获取锁的代价。

在大多数情况下，锁总是由同一线程多次获得，不存在多线程竞争，所以出现了偏向锁。其目标就是在只有一个线程执行同步代码块时能够提高性能。

当一个线程访问同步代码块并获取锁时，会在Mark Word里存储锁偏向的线程ID。在线程进入和退出同步块时不再通过CAS操作来加锁和解锁，而是检测Mark Word里是否存储着指向当前线程的偏向锁。引入偏向锁是为了在无多线程竞争的情况下尽量减少不必要的轻量级锁执行路径，因为轻量级锁的获取及释放依赖多次CAS原子指令，而偏向锁只需要在置换ThreadID的时候依赖一次CAS原子指令即可。

偏向锁只有遇到其他线程尝试竞争偏向锁时，持有偏向锁的线程才会释放锁，线程不会主动释放偏向锁。偏向锁的撤销，需要等待全局安全点（在这个时间点上没有字节码正在执行），它会首先暂停拥有偏向锁的线程，判断锁对象是否处于被锁定状态。撤销偏向锁后恢复到无锁（标志位为“01”）或轻量级锁（标志位为“00”）的状态。

偏向锁在JDK 6及以后的JVM里是默认启用的。可以通过JVM参数关闭偏向锁：-XX:-UseBiasedLocking=false，关闭之后程序默认会进入轻量级锁状态。

**轻量级锁**

是指当锁是偏向锁的时候，被另外的线程所访问，偏向锁就会升级为轻量级锁，其他线程会通过自旋的形式尝试获取锁，不会阻塞，从而提高性能。

在代码进入同步块的时候，如果同步对象锁状态为无锁状态（锁标志位为“01”状态，是否为偏向锁为“0”），虚拟机首先将在当前线程的栈帧中建立一个名为锁记录（Lock Record）的空间，用于存储锁对象目前的Mark Word的拷贝，然后拷贝对象头中的Mark Word复制到锁记录中。

拷贝成功后，虚拟机将使用CAS操作尝试将对象的Mark Word更新为指向Lock Record的指针，并将Lock Record里的owner指针指向对象的Mark Word。

如果这个更新动作成功了，那么这个线程就拥有了该对象的锁，并且对象Mark Word的锁标志位设置为“00”，表示此对象处于轻量级锁定状态。

如果轻量级锁的更新操作失败了，虚拟机首先会检查对象的Mark Word是否指向当前线程的栈帧，如果是就说明当前线程已经拥有了这个对象的锁，那就可以直接进入同步块继续执行，否则说明多个线程竞争锁。

若当前只有一个等待线程，则该线程通过自旋进行等待。但是当自旋超过一定的次数，或者一个线程在持有锁，一个在自旋，又有第三个来访时，轻量级锁升级为重量级锁。

**重量级锁**

升级为重量级锁时，锁标志的状态值变为“10”，此时Mark Word中存储的是指向重量级锁的指针，此时等待锁的线程都会进入阻塞状态。

整体的锁状态升级流程如下：

![img](https://awps-assets.meituan.net/mit-x/blog-images-bundle-2018b/8afdf6f2.png)

综上，偏向锁通过对比Mark Word解决加锁问题，避免执行CAS操作。而轻量级锁是通过用CAS操作和自旋来解决加锁问题，避免线程阻塞和唤醒而影响性能。重量级锁是将除了拥有锁的线程以外的线程都阻塞。

## 内存语义

以下内容涉及到Java内存模型。

### 可见性

可见性指的是一个线程对变量的修改能够立即被另一个线程看见。

为了保证可见性，对synchronized修饰的代码有这样一条规则：对一个变量解锁之前，必须先把此变量同步回主存中。这样解锁后，后续线程就可以访问到被修改后的值。

### 原子性

synchronized对要访问的代码段加锁，访问结束再释放锁，在此期间只有一个线程能访问代码块，可以实现原子性。

### 有序性

synchronized保证的有序性是多个线程之间的有序性，即**被加锁的内容要按照顺序被多个线程执行**。但是其内部的同步代码还是会发生重排序，只不过由于编译器和处理器都遵循as-if-serial语义，所以我们可以认为这些重排序在单线程内部可忽略。

## 参考

[探索 Java 同步机制](<https://www.ibm.com/developerworks/cn/java/j-lo-synchronized/index.html>)  

[Java 中的 Monitor 机制](<https://segmentfault.com/a/1190000016417017>) 

[不可不说的Java“锁”事](<https://tech.meituan.com/2018/11/15/java-lock.html>)

[既生synchronized，何生volatile](https://www.hollischuang.com/archives/3928)





