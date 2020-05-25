---
title: Java中new对象时到底发生了什么
date: 2019-10-10 16:12:49
tags: JVM
categories: Java
---

Java中有许多创建对象的方式，比如使用new关键字，使用反射，使用序列化/反序列化，使用克隆，其内部原理也都不一样，本文主要讨论在使用new关键字创建对象的前前后后JVM都做了那些事。要讲清楚这个事情，需要了解一定的JVM内存模型，以及类加载机制。

###缘起

首先要明白，创建对象这是一个运行期的动作，在运行期前面，还有一个编译期。编译期就是将我们写的java文件编译成class文件的过程，运行期指的是JVM动态加载class文件并执行的过程。在讨论创建对象之前，首先要经过编译器，生成了需要的class文件。关于class文件的介绍可以查看[这篇]([https://inewbie.top/2019/09/04/%E8%B0%88%E4%B8%80%E8%B0%88Java%E5%B8%B8%E9%87%8F%E6%B1%A0%E4%B9%8Bclass%E5%B8%B8%E9%87%8F%E6%B1%A0/](https://inewbie.top/2019/09/04/谈一谈Java常量池之class常量池/))文章。



###使用new创建对象

这一过程涉及到许多类加载的知识。使用new关键字创建对象时，主要经过以下几个过程：

1. 虚拟机遇到new指令，到常量池定位到这个类的符号引用。
2. 检查符号引用代表的类是否被加载、解析、初始化过。
3. 虚拟机为对象分配内存。
4. 虚拟机将分配到的内存空间都初始化为零值。
6. 执行方法，成员变量进行初始化。

我们写一段简单的代码来帮助理解上述过程：

Father.java

```java
public class Father {
    private String privateFiled = "privateField" ;
    protected String protectedField = "protectedField" ;
    public String publicField = "publicField" ;

    private void privateMethod(){
    }
    
    protected void protectedMethod(){
    } 
    
    public void publicMethod(){       
    }
}
```

Son.java

```java
public class Son extends Father {
    private String name ;

    public void introduce(){
        System.out.println("I'm son");
    }
}
```

Test.java

```java
public class Test {
    public static void main(String[] args) {
        Father son = new Son();
    }
}
```



下面我们来逐一解释这几个过程。

####虚拟机遇到new指令，到常量池定位到这个类的符号引用

我们在Test.java中的main方法中使用new关键字创建Son对象，我们反编译一下Test.java：

常量池：

![8e0610edbae20825da41cee1f530514.png](http://ww1.sinaimg.cn/large/006ImZ0Oly1g7t7mz7mu4j30gs083glm.jpg)

指令：

![268c5d72fabd0afd821970260305284.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7t7epuby3j30is076a9z.jpg)

可以看到在main方法首先就是new指令，需要new一个Son对象，这时候JVM回去常量池中寻找这个类的符号引用。可以看到这个符号引用在常量池中索引为2，继续在常量池中查看第二个常量，发现它是一个class,并且class的名字存储在第15个常量，第15个常量是个字符串，内容是Son，由此就找到了需要创建的类的符号引用。

#### 检查符号引用代表的类是否被加载、解析、初始化过

上一步中我们已经知道了需要new出一个Son对象，这一步的目的就是检查代表Son的对应类有没有被初始化，这里其实是[类加载]([https://inewbie.top/2019/09/24/Java%E4%B8%AD%E7%9A%84%E7%B1%BB%E5%8A%A0%E8%BD%BD/](https://inewbie.top/2019/09/24/Java中的类加载/))的内容。也就是说，要想在运行期使用某个类，在此之前必须把这个类对应的class文件加载到内存，并对数据进行校验、解析和初始化，才能转换成可以被JVM直接使用的Java类型。如果这个类还没有被初始化，则执行类加载过程进行初始化。

#### 虚拟机为对象分配内存

好，经过上述步骤，我们和类相关的工作已经做完了，现在内存中也有了JVM可以用的java类型了，接下来就是准备对象相关事宜。

首先就是给对象分配内存，那么分配多少呢？其实对象的大小在类加载完成后就已经确定了， 这里要做的只不过是把人家需要的空间给分配出来就行。这里需要注意的是[对象的结构]([https://inewbie.top/2019/09/13/Java%E4%B8%AD%E7%9A%84synchronized%E5%85%B3%E9%94%AE%E5%AD%97/](https://inewbie.top/2019/09/13/Java中的synchronized关键字/))，有对象头、实例字段和对齐填充字段，所以分配的空间肯定是要比我们所能看到的空间大的。

1. 关于继承，是如何分配内存的

> 对于继承自父类的子类来说，在创建子类的时候，并不会创建父类，只不过是在调用自类的构造方法的时候会调用父类的构造方法进行成员变量的初始化，仅此而已。试想一下任何类都继承自Object类，如果每次创建自类的时候都要创建一个父类，那将会造成多少冗余。
>
> 那既然没有创建父类，我们讲的子类能访问继承自父类的非private的成员变量和方法又是哪来的呢？其实在分配内存的时候，JVM会给子类自身以及从父类继承下来的各种属性和方法都分配空间的，注意是各种。虽然官方文档里讲的是被private修饰的成员变量不会被继承，但是可以通过public的getter和setter来获得和修改，但是笔者认为，其实private变量也被继承下来了，只不过直接访问不到而已。

2. 分配内存时是如何保证线程安全的

   在分配内存的时候，都会给每个线程预先划分好一小块内存，叫做TLAB(Thread Local Allocation Buffer),这部分内存是本地线程独享的，以此来防止多个线程给同一块地址空间上分配对象。

3. 内存一定是分配在堆上吗

   逃逸分析、栈上分配、标量替换等技术使得不那么一定了。

4. 如果分配到堆上，分配到堆上的哪里

   看是小对象还是大对象。小对象分配到Eden,大对象放到Old Gen.

#### 虚拟机将分配到的内存空间都初始化为零值

需要注意的是，这里的初始化为零值并不是我们自己写的代码里的赋值操作，而是JVM自带的操作。



#### 执行方法，成员变量进行初始化

这里才是真正执行我们自己的构造方法，在构造方法里要先调用父类的构造方法，一直向上回溯一直到最根源，从最根源的父类构造方法开始依次向下调用。



> 需要注意的是，这里标题写的是成员变量初始化，而我内容写的是执行构造方法，但事实是，有些成员变量的初始化工作并不是写在构造方法里面的，那这是怎么回事呢？
>
> 实际上，如果我们对实例变量直接赋值或者使用实例代码块赋值，那么编译器会将其中的代码放到类的构造函数中去，并且这些代码会被放在对超类构造函数的调用语句之后(还记得吗？Java要求构造函数的第一条语句必须是超类构造函数的调用语句)，构造函数本身的代码之前。

下面这段代码

```java
public class Test2 {
    private int i = 1;
    private int j = i + 1;

    public Test2(int var){
        System.out.println(i);
        System.out.println(j);
        this.i = var;
        System.out.println(i);
        System.out.println(j);
    }

    {               // 实例代码块
        j += 3;

    }

    public static void main(String[] args) {
        new Test2(8);
    }
}

```

经过编译器优化后的构造函数就变成了

```java
public Test2(int var){
    	i = 1 ;
    	j = i + 1 ;
    	j += 3 ;
        System.out.println(i);
        System.out.println(j);
        this.i = var;
        System.out.println(i);
        System.out.println(j);
    }
```

所以输出应该是

```java
1
5
8
5
```



### 从`<clinit>()` `<init>()`的角度再次考虑

考虑两个概念：

+ 类初始化

  指的是类加载过程中的最后一个阶段。

+ 类实例化

  指的是创建对象的过程。

在Java中， 创建一个对象常常需要经历如下几个过程：**父类的类构造器<clinit>() -> 子类的类构造器<clinit>() -> 父类的成员变量和实例代码块 -> 父类的构造函数 -> 子类的成员变量和实例代码块 -> 子类的构造函数。**

**`<clinit>()`是什么**

` clinit`是class类构造器对静态变量，静态代码块进行初始化。由所有静态字段的赋值操作以及静态代码块按出现顺序构成。参考[这篇]( [https://inewbie.top/2019/09/24/Java%E4%B8%AD%E7%9A%84%E7%B1%BB%E5%8A%A0%E8%BD%BD/](https://inewbie.top/2019/09/24/Java中的类加载/) )文章

**`<init>()`是什么**

 `init`是instance实例构造器，对非静态变量解析初始化 。由所有实例变量的赋值，所有实例代码块以及构造函数里面的代码构成。其中实例变量的赋值以及实例代码块是放在最前面执行的。



下面以一个例子来说明`<clinit>()`和`<init>()`

考虑下面这段代码：

```java
public class StaticTest {
    public static void main(String[] args) {
        staticFunction();
    }

    static StaticTest st = new StaticTest();

    static {   //静态代码块
        System.out.println("1");
    }

    {       // 实例代码块
        System.out.println("2");
    }

    StaticTest() {    // 实例构造器
        System.out.println("3");
        System.out.println("a=" + a + ",b=" + b);
    }

    public static void staticFunction() {   // 静态方法
        System.out.println("4");
    }

    int a = 110;    // 实例变量
    static int b = 112;     // 静态变量
}/* Output: 
        2
        3
        a=110,b=0
        1
        4
 *///:~

```



我们来分析一下，`staticFunction()`是个静态方法，对它的调用就用到了`invokestatic`指令，所以会进行类加载，涉及到加载、验证、准备、解析、初始化几个阶段，其中在初始化阶段会调用`<clinit>()`进行类变量的初始化，而`<clinit>()`由静态字段的赋值操作以及静态代码块按照出现顺序组成，所以`<clinit>()`内容大概是这样的：

```java
 static StaticTest st = new StaticTest();
 static {   //静态代码块
        System.out.println("1");
 }
 static int b = 112;
```

注意！请看我的手法！在这里神奇的事情发生了，我们说上面这段代码是`<clinit>()`的内容，也就是类加载过程中初始化阶段的内容，但是！你会发现在类初始化的时候已经混进来了类实例化的操作，也就是说，这个类可能还没有创建好呢但是就已经开始进行实例化了，并且实例化的代码还放在了`<clinit>()`代码的开头，可以这样做吗？答案是可以的，但是这样就会造成一个问题，你在实例化代码时执行构造函数里面的内容时，里面的静态变量其实都还没有被来得及赋值。我们先将上述代码进一步细化, 将静态变量`st`的赋值分解为两个操作：创建对象和赋值。

```java
int a = 110;
System.out.println("2");// 实例代码块
System.out.println("3");//实例构造器
System.out.println("a=" + a + ",b=" + b);//实例构造器

给静态变量st赋值
    
System.out.println("1"); //静态代码块
static int b = 112;
```

这个就是完整的`<clinit>()`的内容了，可以看出，在初始化阶段，输出：

```java
2
3
a=110,b=0
1
```

初始化结束，调用`staticFunction()`,输出

```java
4
```

所以，最后输出为：

```java
2
3
a=110,b=0
1
4
```



在程序最后的一行，增加以下代码行：

```java
static StaticTest st1 = new StaticTest();
```

那么，此时程序的输出又是什么呢？

加入这行代码后，`<clinit>()`内容变为：

```java
int a = 110;
System.out.println("2");// 实例代码块
System.out.println("3");//实例构造器
System.out.println("a=" + a + ",b=" + b);//实例构造器

给静态变量st赋值
    
System.out.println("1"); //静态代码块
static int b = 112;

int a = 110;
System.out.println("2");// 实例代码块
System.out.println("3");//实例构造器
System.out.println("a=" + a + ",b=" + b);//实例构造器
给静态变量st1赋值
```

所以初始化阶段输出为：

```java
2
3
a=110,b=0
1
2
3
a=110,b=112
```

初始化结束，调用`staticFunction()`,输出

```java
4
```

所以，最后输出为：

```java
2
3
a=110,b=0
1
2
3
a=110,b=112
4
```



### 总结

好，我们来总结一下创建对象的过程:

要new出一个对象，首先是需要这个对象的类型信息的，也就是对应的类，如果内存中还没有这个类型信息的话，JVM要先执行类加载过程，将class文件加载进内存，并且经过准备阶段、解析阶段以及初始化阶段，最后变成能被JVM使用的类型（加载进来的东西都放在方法区，也就是说方法区放的是类信息）。如我们前面所说，万事万物皆对象，其实class文件在被载入内存初始化后也是个类，叫做Class类，所以话句话说，要new一个对象，首先要看内存中有没有这个对象对应的Class类。然后就是分配内存（这里要注意继承情况下内存是如何分配的）、初始化零值以及执行构造方法。



### 参考

[深入理解Java对象的创建过程：类的初始化与实例化](https://blog.csdn.net/justloveyou_/article/details/72466416)

[JVM类生命周期概述：加载时机与加载过程](https://blog.csdn.net/justloveyou_/article/details/72466105)

[万万没想到，JVM内存结构的面试题可以问的这么难？](https://www.hollischuang.com/archives/3875)