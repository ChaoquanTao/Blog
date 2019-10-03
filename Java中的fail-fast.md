---
title: Java中的fail fast
date: 2019-09-29 19:32:50
updated: 2019-09-29 19:32:50
tags: fail fast
categories: Java
---

不知道到大家在操作Java集合类的时候有没有遇到过`ConcurrentModificationException`异常，反正我是遇到过，今天就来聊一下这个异常的缘起缘灭。

### fail fast

上述异常都是由这个叫做fail fast的机制导致的，fail fast是Java集合类的一种异常检测机制，当多个线程并发修改一个集合类的结构时，就有可能触发上述异常。我们以`ArrayList`为例来探究一下。



`ArrayList`中有一个成员变量叫做`modCount`，jdk8文档里面是这么介绍它的：

> The number of times this list has been *structurally modified*. Structural modifications are those that change the size of the list, or otherwise perturb it in such a fashion that iterations in progress may yield incorrect results.
>
> This field is used by the iterator and list iterator implementation returned by the `iterator` and `listIterator` methods. If the value of this field changes unexpectedly, the iterator (or list iterator) will throw a `ConcurrentModificationException` in response to the `next`, `remove`, `previous`, `set` or `add` operations. This provides *fail-fast* behavior, rather than non-deterministic behavior in the face of concurrent modification during iteration.

大概意思就是说：它是用来记录这个list被结构性修改的次数，所谓结构性修改指的是那些让它的大小发生改变的操作。并且，这个字段是被iterator使用的。

#### iterator

我们再来看下iterator. 我们在集合类中一般是这样使用集合类的：

![uGedJI.png](https://s2.ax1x.com/2019/09/29/uGedJI.png)

可以发现，它这里有两种方法，一种是iterator,还有一种是`listIterator`，有iterator方法很好理解，是因为`ArrayList`实现了`Iterable`接口，而iterator方法就是这个接口里的方法

![uGmM7Q.png](https://s2.ax1x.com/2019/09/29/uGmM7Q.png)

`Iterable`接口

![uGmGpq.png](https://s2.ax1x.com/2019/09/29/uGmGpq.png)

这三个方法定义如下：

![uGKhEF.png](https://s2.ax1x.com/2019/09/29/uGKhEF.png)

可以看到，两个`listIterator()`方法返回的是一个`ListItr`对象，iterator方法返回的是一个`Itr`对象。我们来看下这两个对象有什么区别：

`Itr`对象

![uGMNG9.png](https://s2.ax1x.com/2019/09/29/uGMNG9.png)

`ListItr`对象

![uGMRxI.png](https://s2.ax1x.com/2019/09/29/uGMRxI.png)



看来这两个内部类在`AbstractList`中就有了，只不过在这里进行了优化。下面这张类图就很能说说明问题了：

<img src="https://s2.ax1x.com/2019/09/29/uGlP78.png" alt="uGlP78.png" style="zoom:80%;" />

可以看出，`ListItr`就相当于是专门给list做的一个iterator,提供了一些下标访问的方法，但是平时用的还是比较少。





好，看完了iterator,我们来正式看下`ConcurrentModificationException`是怎么肥四

#### `ConcurrentModificationException`

fail fast出现在哪里的，根据上述问的描述，出现在发生结构性修改的地方，好，我们看一下add(),remove()的代码：

![uGlx5F.png](https://s2.ax1x.com/2019/09/29/uGlx5F.png)

![uG1CvR.png](https://s2.ax1x.com/2019/09/29/uG1CvR.png)

可以看到，发生结构性修改的地方，都会有`modount++`的操作。可是这里也没有看到抛出异常的代码呀。别急，其实都藏在Iterator里面，这里以内部类`Itr`为例：

![uG3Eyn.png](https://s2.ax1x.com/2019/09/29/uG3Eyn.png)

请注意图中我圈出来的地方，这个内部类有个字段叫做`expectedModCount`，顾名思义就是期望被修改的次数，它被赋值成`modCount`，然后，对于这个内部类里面的每一个方法，都包含了一个叫做`checkForComodification()`的方法，这个方法做了什么呢？

![uG3tw6.png](https://s2.ax1x.com/2019/09/29/uG3tw6.png)

可以看到，它做的事情就是比较`modCount`和`expectModCount`是否相等，不等的话就抛出这个异常。在Itr类里面，只有一个地方修改了`expectedModCount`类：

![uG86gJ.png](https://s2.ax1x.com/2019/09/29/uG86gJ.png)

那么什么时候他俩才会不等呢？

这个内部类里面对`expectedModCount`初始化的值就是`modCount`的值，如果说要不等，那么可能有这么两种情况：

- 修改了`expectedModCount`，没有修改`modCount`
- 修改了`modCouont`，没有修改`expectedModCount`



其实看到这里，我们的疑惑大概也就解开了，在`Itr`类里面，对`expectedModCount`的修改只有上面那一处，而且还是将`modCount`赋值给他，这意味着，要发生这个异常，只能是我们在别处（Iterator以外的地方）对list进行了结构性修改，这时候只改了`modCount`，然后又使用`Itr`进行遍历操作，这时候这两个值就不相等了，这里推荐阅读H大的这篇文章，讲的很清楚：[为什么阿里巴巴禁止在 foreach 循环里进行元素的 remove/add 操作](https://www.hollischuang.com/archives/3304)



当然了，上述只是发生这个异常的一种原因啦，其实查看源代码你会发现其他地方也有这个异常，比如你使用多线程进行遍历或者修改的时候，因为数组越界也有可能触发这个异常。

