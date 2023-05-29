---
title: 如何在Java中优雅地使用异常
categories: Java
tags: 异常
date: 2023-03-05 12:00:00
---

> 本文会简单介绍Java异常的分类， 以及在使用异常过程中的一些注意事项。



### 异常的分类

Java异常是JVM应对错误的一种方式，无论是编译时错误、运行时错误、还是JVM内部错误，它的分类如下：

![](http://cdn.inewbie.top/exception/exception.jpg)

Java的`Exception`和`Error`都继承自`Throwable`,` Exeception`包括`CheckedExeception`和`UncheckedException`，其中`CheckedException`是一些在编译期就能发现的异常，JVM要求开发者必须显式地捕获或抛出该异常, 如`IOExcetion`, `FileNotFoundException`, `ClassNotFoundException`。而`UnCheckedException`为运行时异常，在编译器无法发现，JVM也就不要求开发者必须做处理。

> 有两种比较容易混淆的异常和错误需要注意下：`ClassNotFoundException`,` NoClassDefFoundError`。如上文所说，`ClassNotFoundException`发生在编译期，通常是由于找不到该类文件导致，比如虽然在pom文件里引用了该jar包，编译器也确实没提示报错，但是由于当前的类加载器不加载这个jar包所在path的类文件，就会报这个错，比如调用`Class.forName`或`Classloader.loadClass`时，就可能会报这个异常。而`NoClassDefFoundError`发生在运行期，由于运行时找不到对应的类文件导致，比如你以`provided`方式引入某个jar包，编译时ok, 但运行时可能就会报错。



### 异常的使用

由于Java异常有一定的性能损耗，在这里和大家分享几点异常的使用原则

 **1、应当捕获什么粒度的异常？**

​	抛开场景谈这个问题毫无意义，看到网上有些文章说不应当捕获`Throwable`类，笔者不认同这种说法。在一些业务场景中，对于下游抛出的不同异常应当有不同的处理逻辑，这时捕获的异常应当越具体越好，比如：

```Java
try{
	//biz code
}catch(ExeptionA a){
	//do something
}catch(ExceptionB b){
	//do something else
}
```



也有些场景，比如你的代码相对于主逻辑是个旁路分支，这时你应当在自己代码的最外层一把梭捕获所有`Exception`和`Error`, 避免旁路逻辑抛出什么预期外的异常而影响主逻辑。，即你应当去捕获 `Throwable`:

```Java
try{
	//旁路逻辑
}catch(Throwable t){
	//无论抛出什么异常，都不应当影响主流程
}
```



**2、尽量使异常堆栈简短**

​		异常堆栈的解析有一定的性能损耗，过长的异常栈也会给日志打印带来压力，所以，在明确知道你的异常会发生在什么位置时，应当使异常栈尽可能的浅，而对应的做法就是应当将捕获的异常重新定义再抛出：

```java
//代码一，直接抛出原异常，会使异常栈比较深
try{
  //biz code
}catch(Exeception e){
  throw e;
}

//代码二，捕获并重新定义异常，异常栈会从重新定义的地方开始计算
try{
  //biz code
}catch(Exception e){
  throw new RuntimeException("error msg here")
}
```



**3、将异常定义为静态成员变量，避免重复创建对象**

异常本身也是一个对象，既然是对象，那创建和回收就会有性能损耗，试想一下，在高并发情况下，刚好有一段代码有bug, 频繁地抛出异常，频繁地创建`Exception`新对象就有可能造成频繁地`young GC`.

```java
try{
  
}catch(Exception e){
  throw new Exception(); //在这里频繁地创建并抛出异常
}
```

所以，**在明确知道当前逻辑会抛出或应当抛出什么异常的情况下，**将异常定义为静态变量，可以帮助降低系统性能开销。举个🌰：

```java
if(/**不是会员**/){
  throw BizException.ExceptionA;
}

public BizException{
  public static BizException ExceptionA = new BizException("不是会员!");
}
```



### 写在最后

开发不规范，上线两行泪。了解一下异常的使用技巧可以帮助我们规避一些开发风险 🫡

