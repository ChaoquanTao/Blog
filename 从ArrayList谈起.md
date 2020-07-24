---
title: 从ArrayList
date: 2020--07-21 23:00:00
categories: Java
---

>  ArrayList作为最常用的集合类之一，在此关于对它进行一个启发式的总结。

### 本质

其本质是个动态数组，所谓动态，就是可以再进行add操作的时候进行扩容。

说到动态数组，其实它应用的还是比较广泛的，比如redis的list的实现，也用到了动态数组的思想，只不过它的实现比ArrayList更灵活，不仅可以扩容，还可以缩容，关于redis动态数组可以参考[]()。

### 扩容

这也是面试常问的问题，要回答这个问题，我建议从ArrayList的构造方法看起。

常见的构造方法有

```java
public ArrayList() {
        this.elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA;
    }
```

```java
public ArrayList(int initialCapacity) {
        if (initialCapacity > 0) {
            this.elementData = new Object[initialCapacity];
        } else if (initialCapacity == 0) {
            this.elementData = EMPTY_ELEMENTDATA;
        } else {
            throw new IllegalArgumentException("Illegal Capacity: "+
                                               initialCapacity);
        }
    }
```



如果使用无参的构造函数创建ArrayList的话，它的默认大小其实是0，在`add`第一个元素的时候，会给它分配一个默认的大小：

```java
private static final int DEFAULT_CAPACITY = 10;
```

然后每次快满的时候，动态数组就会按照1.5倍的规模扩大：

![UjEvGR.png](https://s1.ax1x.com/2020/07/24/UjEvGR.png)



当使用带有参数的构造函数创建ArrayList的时候，则它的capacity就是当前参数（前提是当前参数合法）。

需要注意的是，这里HashMap有所不同，hashMap会根据所传参数计算出一个最接近这个参数的2的次幂作为capacity,其目的是为了方便扩容（具体细节参见[这篇]()文章）。



ArrayList的容量最大能有多大呢？

![Uj0EDK.png](https://s1.ax1x.com/2020/07/24/Uj0EDK.png)

从代码可知，最大为Integer.MAX_VALUE.





