---
title: MySQL之MVCC
date: 2020-01-05 20:53:07
updated: 2020-01-05 20:53:07
tags: MySQL
categories: 数据库
---

讨论MySQL的MVCC的同时还应该讨论MySQL中的锁，不过本文先就MVCC进行讨论。



MVCC叫做多版本并发控制，它主要是为了实现多个事务之间的隔离性而提出的一种更高效的方法，为什么说更高效呢，因为锁也可以实现，只不过相比之下比较低效。



MVCC的核心有三：

+ MySQL每一行记录的隐藏列之`DATA_TRX_ID`
+ MySQL每一行记录的隐藏列之``DATA_ROLL_PTR`
+ READ VIEW

我们下面一一进行解释。



MySQL的每一行记录都有两个隐藏列，`DATA_TRX_ID`和``DATA_ROLL_PTR`。其中`DATA_TRX_ID`表示修改该行的事务ID,而`DATA_ROLL_PTR`则指向该行的历史修改，它把所有的历史修改连成一个链表，像这样

![wpl4mV.png](https://s1.ax1x.com/2020/09/02/wpl4mV.png)

而Read View是什么呢？它也是一种数据结构，m_ids上面我们讲到不同的事务对同一行的操作形成了一个链表，那么我们在执行一条SQL时到底应该选择链表中的哪一条作为结果呢？Read View正是为了解决这个事情的。

Read View里存放了我们当前活跃的事务的集合，所谓当前活跃，指的是这些事务还未被提交，当在不同的隔离级别下执行SQL时，通过检查版本链中的事务ID和Read View中的事务ID大小就可以决定要选择版本链中的哪个节点作为执行结果了。

具体是这样的：

- 如果被访问版本的`trx_id`属性值小于`m_ids`列表中最小的事务id，表明生成该版本的事务在生成`ReadView`前已经提交，所以该版本可以被当前事务访问。

  

- 如果被访问版本的`trx_id`属性值大于`m_ids`列表中最大的事务id，表明生成该版本的事务在生成`ReadView`后才生成，所以该版本不可以被当前事务访问。

  

- 如果被访问版本的`trx_id`属性值在`m_ids`列表中最大的事务id和最小事务id之间，那就需要判断一下`trx_id`属性值是不是在`m_ids`列表中，如果在，说明创建`ReadView`时生成该版本的事务还是活跃的，该版本不可以被访问；如果不在，说明创建`ReadView`时生成该版本的事务已经被提交，该版本可以被访问。



还有两点需要注意的是：

+ Read View是与SQL绑定的，而并不是事务

+ 对于使用`READ UNCOMMITTED`隔离级别的事务来说，直接读取记录的最新版本就好了，对于使用`SERIALIZABLE`隔离级别的事务来说，使用加锁的方式来访问记录。所以MVCC只在可重复读和读已提交这两个隔离级别下工作。

> 本文转自公众号：我们都是小青蛙，作者小孩子4919

>

参考：

https://mp.weixin.qq.com/s/SCW_3AypO-rSolMcjCxVtA