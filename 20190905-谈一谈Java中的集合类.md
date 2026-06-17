---
title: 谈一谈Java中的集合类之总述
date: 2019-09-05 14:40:08
updated: 2019-09-05 14:40:08
tags: 集合类
categories: Java
---

`本文涉及集合类知识以及面试常问知识点`

### OverView

集合类分为`List`,`Map`,`Set`. 先上张图

![nBge00.jpg](https://s2.ax1x.com/2019/09/12/nBge00.jpg)

### Map

包括`HashMap`, `LinkedHashMap`, `HashTable`, `TreeMap` 和 `WeakHashMap`, `ConcurrentHashMap`

1. HashMap

不是线程安全，最多允许一条键为null的记录

2. LinkedHashMap

保存了记录的插入顺序

3. ConcurrentHashMap

线程安全

4. HashTable

线程安全，键和值都不能为空

5. TreeMap

有排序功能

### List

包括`ArrayList`, `LinkedList`, `Vector` 和 `stack`



### Set

包括`HashSet` , `TreeSet`



### 常见问题

1. `HashMap` 和 `ConcurrentHashMap`比较
2. `HashTable`实现原理，为什么线程安全
3. `TreeMap`实现原理