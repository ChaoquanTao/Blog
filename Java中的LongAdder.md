---
title: Java中的LongAdder
date: 2019-12-05 11:25:22
updated: 2019-12-05 11:25:22
tags: 并发
categories: Java
---

> 最近发现JUC包里除了`AtomicLong`外还有`LongAdder`，所以打算研究一下它俩的异同。

#### `AtomicLong`

`AtomicLong`是JUC包中的原子类，通过CAS来实现`long`类型的加减。

那么既然都有`AtomicLong`类了，为什么还要有一个`LongAdder`类？因为从名字来看，`LongAdder`也是用来操作`long`类型的。

#### `LongAdder`的设计思想

先翻译一段官方文档里的解释：

> `LongAdder`是通过多个变量一起来维护一个`long`型总和。什么意思呢？它主要是为了计算一些统计信息的，在多线程竞争的场景下，它给每个线程都分配一个变量，每个线程各自修改自己的变量，然后它有个`sum()`方法，可以计算所有变量的总和，通过这种方式来减少多线程之间的竞争。
>
> 当多个线程去更新一个公有的`sum`总和时，我们更偏向于用`LongAdder`而非`AtomicLong`. 这两个类特性相似，但是在多线程竞争激烈的场景，`LongAdder`具有更好的性能（这一点也可想而知，毕竟`AtomicLong`使用的是CAS）。	

上面的描述也就基本上解释了`LongAdder`的缘起缘灭了，它主要是为统计而生，而非那种细粒度的同步控制。



其实这个也就相当于一种分治，非中央集权而是分而治之，让每个线程维护自己的那个变量，最后综合统计一下。



#### 详情

我们在这里从源码角度讨论一下`LongAdder`.

先看下它的继承关系：

```java
public class LongAdder extends Striped64 implements Serializable
```

它最核心的一个方法就是`add()`方法了

```java
 /**
     * Adds the given value.
     *
     * @param x the value to add
     */
    public void add(long x) {
        Cell[] as; long b, v; int m; Cell a;
        if ((as = cells) != null || !casBase(b = base, b + x)) {
            boolean uncontended = true;
            if (as == null || (m = as.length - 1) < 0 ||
                (a = as[getProbe() & m]) == null ||
                !(uncontended = a.cas(v = a.value, v + x)))
                longAccumulate(x, null, uncontended);
        }
    }
```

看着很简单，但里面的逻辑判断却不少。先简单介绍下这里面的一些陌生类型和方法。

+ `Cell[]`：`Cell`类里面其实就是维护了一个变量，这个数组用来存在每个线程的自己维护的变量。具体细节是这样的：对每个线程计算`hash`，将得到的`hash`值作为`Cell`数组的下标。
+ `casBase()`：对`base`变量进行CAS,什么是`base`变量呢？当有竞争是使用`Cell[]`数组给每个线程维护一个变量，当没有竞争是`LongAdder`就只操作一个`base`变量就可以了。
+ `getProbe()`：得到当前线程对应的哈希值，再和数组长度进行与运算就得到了对应的下标（有没有一点`hashmap`的影子？）.

+ `longAccumulate()`：当基本的操作都失败时，执行这个方法。

为了方便理解代码逻辑，我画了一个流程图：

![QwURIS.jpg](https://s2.ax1x.com/2019/12/09/QwURIS.jpg)

 可以看到大概流程是先操作`Cell`数组，数组空的话再操作base,如果都没成功再考虑`longAccumulate`（），虽然我也没仔细研究`longAccumulate()`里的代码，但是大概可以猜到，它应该是上述未成功操作的`plus`版，操作逐渐升级。



> 这种设计思想可以学习一手

