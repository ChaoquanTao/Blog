---
title: Java集合类之HashMap
date: 2019-07-09 20:44:30
updated: 2019-07-09 20:44:30
tags: HashMap
categories: Java
---

### OverView



### `HashMap`

#### 1. jdk 1.7

链表

#### 2. jdk 1.8

红黑树

`HashMap`的底层实现是数组+链表，也就是数据结构中的邻接表，它的存取不用多说。

需要注意的是，`HashMap`和其他集合类一样，也有扩容的操作，当entries的数量超过容量阈值时，会自动扩容。所谓扩容，就是把里面的元素移植到一个更大的`HashMap`中，里面所有的元素都要进行以此重新hash.

但是，`HashMap`不是线程安全的，当在扩容的过程中有多个线程一起操作时，很有可能会造成链表首位相连，形成死循环。

同时jdk1.8针对jdk1.7中链表过长进行了优化，当链表过长的时候，它会被调整成红黑树，以此减少遍历链表查询时间。



### `ConcurrentHashMap`

#### 1. jdk 1.7

分段锁

桶中装链表

#### 2. jdk 1.8

CAS+自旋锁

桶中装红黑树

`ConcurrentHashMap`的设计思想就是使用分段锁的技术，说白了，它把一个打的`HashMap`分成几个小的`HashMap`,然后对每个小段进行加锁。那么就存在一个问题，要划分多少个段，每个段里有多少个桶？这个在构造函数里有一个并发级别的参数来控制。

关于`ConcurrentHashMap`的分段，它其实是借鉴了操作系统中内存的分段分页机制。得到一个`key`的`hash`值，然后根据段的个数和每个段中桶的个数，高几位用来定位段，低几位定位段中桶的位置。



`ConcurrentHashMap`的`rehash()`操作其实是对某个段进行`rehash()`



Segment继承自`ReentryLock`，每个`HashEntry`里面的字段被修饰，读不需要加锁，写加分段锁

万一一个线程正在读时另一个线程来写呢

如何真正保证线程安全的？

#### 推荐阅读

[Map 综述（三）：彻头彻尾理解 ConcurrentHashMap](<https://blog.csdn.net/justloveyou_/article/details/72783008>)（jdk 1.6）

[HashMap? ConcurrentHashMap? 相信看完这篇没人能难住你！](<https://juejin.im/post/5b551e8df265da0f84562403>) (jdk1.7 jdk 1.8)



