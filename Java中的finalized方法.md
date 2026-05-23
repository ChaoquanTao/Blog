---
title: Java中的finalized方法
date: 2019-10-27 15:31:44
updated: 2019-10-27 15:31:44
tags: finalize
categories: Java
---

### finalize是什么

`finalize()`是定义在Object类中的一个方法，用于垃圾回收。

### finalize原理

当JVM的GC打算回收某个对象时，如果这个对象覆盖了`finalize()`方法，并且`finalize()`方法没有被执行过，会把这个对象放在一个叫做F-Queue的队列中，稍后由一个由虚拟机自动建立的，低优先级的`Finalizer`线程去触发`finalize`的执行。稍后GC将对F-Queue中的对象进行第二次小规模标记，如果这个对象仍然不可达，那么就把它回收了，如果在`finalize()`方法中这个对象实现了自救——将自己与GC Root关联起来，那么它将会被移出队列，不会被回收。

需要注意以下几个问题：

> 1. `finalize()`只会被执行一次
> 2. 对象不一定被垃圾回收，所以对应的，finalize也不一定会被执行

### 为什么要有finalize

在JNI代码中做清理工作

 作为确保某些非内存资源(如Socket、文件等)释放的一个补充 

