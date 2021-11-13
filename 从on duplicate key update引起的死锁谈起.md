---
title: 从duplicate key update谈起
categories: 数据库
date: 2021-08-26 22:00:00
---

>背景：有张表，表里有个唯一索引，为了防止在insert时候出现由于索引重复造成的错误，我就自以为很机智的使用了`duplicate key update`进行插入，它的作用就是，如果有这条记录，则更新，如果没有，则插入，而这正是噩梦的开始（造成了死锁）。
>
>
>
>刚好最新在读周志明老师的《凤凰架构》，读到了事务这一部分，那就都写下来吧，做个复盘。

### 1. 使用`insert on duplicate key update`时会用到哪些锁

关于mysql的锁，我在之前的文章里有做过介绍，所以这里就直接开始正片。



因为是insert, 所以是要加X锁的，既然要加X锁，肯定是有IX锁的（IX是mysql自动加的，之前的文章也做过介绍）。

同时，因为有唯一索引，如果这么草率地插入的话，万一有其他事务也刚好同时插入了具有相同唯一索引的记录怎么办，所以，还需要一个gap lock, 那gap的范围呢？当然是负无穷到正无穷啦。

所以总结下，加的锁有: IX, X, gap lock.



事情到这里位置似乎都还正常，那死锁是怎么产生的呢？源于并发，如果只有一个事务这么操作当然是没有问题的，但是如果有多个事务同时`insert on duplicate key update`就不好说了。



### 2. 场景复现

假如有个表，有这么几个字段，nodeId, parentId, relationship. 其中nodeId为自增主键，relationship为unique key.



