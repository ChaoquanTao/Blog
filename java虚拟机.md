---
title: java虚拟机
date: 2019-03-04 21:43:50
tags: Java虚拟机
categories: Java
---

### Java内存模型

#### java运行时数据区域

##### 程序计数器

线程私有的

##### Java虚拟机栈

线程私有，存放局部变量，返回值地址等

##### 本地方法栈

线程私有，存放局部变量，返回值地址等

##### Java堆

线程共享区域，几乎所有的对象实例都在这里分配内存。

##### 方法区

存储已被虚拟机加载的**类信息，常量，静态变量，即时编译器编译后的代码**等数据。

##### 运行时常量池

是方法区的一部分，用于存放**编译期生成的各种字面变量和符号引用**

##### 直接内存

NIO使用Native函数 库直接分配堆外内存，然后通过一个存储在Java堆中的DirectByBuffer对象作为这块内存的引用进行操作。由于这样做避免了在Java堆和Native堆中来回复制数据，所以可以显著提高性能。



#### 内存模型

工作内存和主内存

##### volatile

当一个变量被volitile关键字修饰时，它有两层语义：

+ 可见性：一个线程对这个变量的更改会立即刷新到主内存中
+ 禁止指令重排序：保证了有序性。
+ 但是它不保证原子性，它能保证修改被立即写到主存，但是不能保证读到的值被立即修改，也就是原子性。对于非原子性的操作，比如自增操作，如果一个线程读入了变量的值，然后被阻塞，这时候这个线程其实是没有修改变量值的，那么也就不会使得其他线程缓存无效，这时候其他线程也读入这个值得时候，读入得其实是旧值。问题得根源就在于，volatile只能保证修改时立即可见，但是不能保证这个操作是原子性的，比如自增操作。如何解决这个问题呢？可以使用synchronized关键字。

使用volatile关键字，可以使得其他线程中对被修饰变量的拷贝无效，迫使它再次从主存中重新读取。

volatile关键字禁止指令重排序有两层意思：

　　1）当程序执行到volatile变量的读操作或者写操作时，在其前面的操作的更改肯定全部已经进行，且结果已经对后面的操作可见；在其后面的操作肯定还没有进行；

　　2）在进行指令优化时，volatile语句相当于一个屏障，它所处的位置是禁止指令重排序的，但是它前面和后面的代码块是可以分别指令重排序的。

然后推荐一篇很不错的博客：

[https://www.cnblogs.com/dolphin0520/p/3920373.html]: https://www.cnblogs.com/dolphin0520/p/3920373.html



##### 内存模型的特征

+ 原子性
+ 可见性
+ 有序性

sychronized关键字可以实现上述三种特性。

除了volatile之外，sychronized和final也可以实现可见性。



##### happens-before原则

先行发生（happens-before）原则指的是java内存模型中定义的两个操作之间的先序关系。如果A先行发生于B，那么A操作所产生的影响就能被B观察到，这里的影响包括内存中共享变量值的修改，发送消息，调用方法等。

happens-before原则是对指令执行顺序性的保障，如果两个操作可以有下面的原则推导出来，说明这两个操作是存在顺序性的，可以在编码中直接使用。否则，虚拟机可以对他们重排序。

+ **程序次序规则**：一个线程内，按照代码顺序，书写在前面的操作先行发生于书写在后面的操作。
+ **管程锁规定**：一个unlock操作先行发生于后面对同一个锁的lock操作。（后面指时间上的先后性）
+ **volatile变量规则**: 对一个volitle变量的写操作先行发生于后面对这个变量的读操作。（后面指时间上的先后性）
+ **线程启动规则：**Thread对象的start()方法先行发生于此线程的每一个动作。
+ **线程终止规则：**线程中的所有操作都先行发生于对此线程的终止检测。
+ **线程中断规则:** 对线程interrupt方法的调用先行发生于被中断线程的代码检测到中断事件的发生。
+ **对象终结操作：**一个对象的初始化完成先行发生于它的finalize方法的开始。
+ **传递性：**如果A先行发生于B，B先行发生于C，那就可以得出A先行发生于C

先行发生原则和时间上的先后发生其实是没有关系的。一个操作时间上的先发生不代表这个操作是“先行发生”。反过来，一个操作是“先行发生”也不代表它是时间上先发生的，因为会有指令重排序。

### GC

所回收的区域指的是堆和方法区。

关于GC的灵魂拷问：

#### 什么是垃圾

1. 引用计数算法（Reference Couting）

添加一个引用计数器，当一个对象被引用时，计数器加一；引用失效时，计数器减一。引用为零，则是垃圾。

缺点：无法解决对象循环引用的问题。

2. 可达性分析算法(Reachablity Analysis)

从一个叫做GC Root的对象作为起点，一直向下搜索，搜索走过的路径被称为Reference Chain, 那些不在这个引用链中的对象是不可达的，是垃圾。

那么问题来了，哪些对象被称为GC Root?

+ 虚拟机栈中引用的对象
+ 方法区中类静态属性引用的对象
+ 方法区中常量引用的对象
+ 本地方法栈中JNI引用的对象

#### 如何回收垃圾

1. 标记-清楚算法

会产生大量的内存碎片

2. 复制算法

我每次只用内存的一半，这一半用完后，把存活的对象挪到另一半，然后清理这一半。

缺点：只能用一半的空间，而且复制意味着修改对象的地址。

3. 标记-整理算法

可以认为是结合了上述两种方法的优点，先标记，然后把存活对象往一段移动，清理另一端。

缺点：内存变动频繁，需要整理所有存活对象的引用地址，效率比复制算法低。

4. 分代收集算法

集百家之长，对不同寿命的对象使用不同的算法收集。

将堆分为新生代和老年代，新生代对象朝生夕死，只有少量对象存活，所以我们采用复制算法。

#### 回收策略

Eden, from Survivor, to Survivor, Old 前三个都是新生代

对象首先都会被分配到Eden中，当Eden剩余空间不够用时，会触发一次Minor GC, 剩下的存活对象放到from Survivor, 如果from区不够，则放到Old.

继续新建对象，下一次Eden又不够用了，继续Minor GC，这次把Eden和from里面剩下的存活对象又放到to里面，如果不够放，继续放到Old.

##### 特例

除了上述所说，还有一些特殊情况：

1. 大对象直接进入Old.

因为它比较大，你放到新生代的话，频繁的Minor GC要移动一个大块头是个很麻烦的事

2. 长期存活对象进入Old.

有些对象一直在from区和to区来回蹦跶，我们给它一个年龄计数器，每蹦跶一次年龄加一，等到成年了就把它送到Old.这个年龄默认是15岁

3. 动态对象年龄判定

JVM并不是严格要求说只有成年才能被送到Old. 如果Survior中相同年龄的对象占用了一半或者以上的空间，那么这些对象以及比他们年长的都会被送到Old. 因为它们太占地方了。

##### 思考

1. 为什么要有Survivor区而不是直接Eden和Old.

为了在进入Old之间缓冲一哈，不然Old会被很快填满，而且进入Old的对象指不定没过多久就变成垃圾了。

2.  为什么要有两个Survivor区

这个其实是借鉴了复制算法的思想。两个Survivor来回倒腾，每次总有一个是空的，它可以很好的解决碎片化的问题。



#### 关于引用

1. 强引用（Strong Reference）

   常见的Objec obj = new Object()就是强引用。

   - 强引用所指的对象在任何时候都不会被系统回收。JVM宁愿抛出OOM异常，也不会回收强引用所指向的对象。

   - 强引用可能导致内存泄漏

2. 软引用（Soft Reference）

   软引用是除了强引用之外，最强的引用类型。

   在内存紧张的情况下，软引用会被回收。

3. 弱引用（Weak Reference）

   系统GC时，只要发现弱引用，就会被回收。

   弱引用和软引用都适合用来保存一些可有可无的缓存数据。

4. 虚引用（Phantom Reference）

   虚引用是四个里面最弱的，如果说软引用和弱引用是弟弟，那么虚引用就是弟中弟。

   一个对象持有虚引用，和没有持有几乎是一样的，因为虚引用随时可能会被GC回收，那么虚引用的作用在哪里呢？它主要用在垃圾回收过程中。虚引用必须和引用队列关联使用，当垃圾回收器准备回收一个对象时，如果发现它还有虚引用，就会把这个虚引用加入到与之 关联的引用队列中。程序可以通过判断引用队列中是否已经加入了虚引用，来了解被引用的对象是否将要被垃圾回收。如果程序发现某个虚引用已经被加入到引用队列，那么就可以在所引用的对象的内存被回收之前采取必要的行动。

#### 类加载机制

##### 类加载的生命周期

加载

验证

准备

解析

初始化

##### 各种类加载器

启动类加载器

拓展类加载器（ExtClassLoader）

系统类加载器（AppClassLoader）

自定义类加载器

##### 类初始化的时机

以下五种情况下会进行类的初始化

（1）

（2）

（3）

（4）

（5）

这五种情况称之为对类的主动引用，除这五种之外，所有引用类的方式都不会触发初始化，成为被动引用。