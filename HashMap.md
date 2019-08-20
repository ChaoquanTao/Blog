---
title: HashMap
date: 2019-07-09 20:44:30
updated: 2019-07-09 20:44:30
tags:
categories: Java
---

### `HashMap`

`HashMap`的底层实现是数组+链表，也就是数据结构中的邻接表，它的存取不用多说。

需要注意的是，`HashMap`和其他集合类一样，也有扩容的操作，当entries的数量超过容量阈值时，会自动扩容。所谓扩容，就是把里面的元素移植到一个更大的`HashMap`中，里面所有的元素都要进行以此重新hash.

但是，`HashMap`不是线程安全的，当在扩容的过程中有多个线程一起操作时，很有可能会造成链表首位相连，形成死循环。所以就有了`ConcurrentHashMap`



### `ConcurrentHashMap`

`ConcurrentHashMap`的设计思想就是使用分段锁的技术，说白了，它把一个打的`HashMap`分成几个小的`HashMap`,然后对每个小段进行加锁。那么就存在一个问题，要划分多少个段，每个段里有多少个桶？这个在构造函数里有一个并发级别的参数来控制。

关于`ConcurrentHashMap`的分段，它其实是借鉴了操作系统中内存的分段分页机制。得到一个`key`的`hash`值，然后根据段的个数和每个段中桶的个数，高几位用来定位段，低几位定位段中桶的位置。

`ConcurrentHashMap`的`rehash()`操作其实是对某个段进行`rehash()`

