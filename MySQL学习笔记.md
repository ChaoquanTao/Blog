---
title: MySQL学习笔记
date: 2017-12-13 18:54:49
categories: 数据库
---

###MySQL逻辑架构

![ZojTTx.jpg](https://s2.ax1x.com/2019/07/15/ZojTTx.jpg)



### redo log & bin log

MySQL的每次数据更改都不会立即写入磁盘的，因为这是一个大量IO的过程，耗时耗力，一个可取的操作时我先把当前的操作记录在日志里，等到~~夜深人静~~操作系统空闲的时候，在通过日志把相关的修改持久化。

所以，机智的MySQL设计者们就提出了一个叫做WAL(write ahead logging)的技术。

每当对数据库进行修改操作时，会先在redo log中添加一行记录“需要在哪个数据页上做什么修改”，并且把这行记录的状态设置为prepare状态，等到事务提交后，再把redo log中的这行记录的状态设置为commit.

#### redo log记录方式

redo log是InnoDB所有的，它的大小是固定的，可以通过特定参数来配置日志文件的数量和每个日志文件的大小。

它采用循环写的方式，如下图：

![Z7wXLt.jpg](https://s2.ax1x.com/2019/07/16/Z7wXLt.jpg)

其中write pos表示当前打算写的位置，write pos和check point之间的空间表示空闲空间，因为是循环写，所以必然存在一个写满的问题，写满了，就要擦除，然后继续写，所以它是不能保存过去的所有时刻的状态。

有了这个redo log,就可以保证数据库异常重启后，我们仍然可以根据redo log里面的记录进行恢复，我们把这个能力叫做crash-safe.

那么问题来了，既然都有了redo log，为什么还要bin log呢？

根据上述分析，我们知道：

1. redo log是InnoDB引擎特有的，其他引擎没有
2. redo log容量有限，所以不会保存太多的历史记录。

基于上述两条，我们又有了bin log, 那它们有什么区别呢？

1. bin log是属于server层的，所以它对于所有存储引擎都能用
2. bin log是通过追加方式写入的，所以旧的记录不会被擦除
3. redo log记录的是物理修改，比如某个页面的某个值修改为啥，而bin log记录的逻辑操作，你可以认为它记录了一条SQL语句
4. 

有了这两个日志后，这两份日志需要保证逻辑一致（我也不知道为啥，先记着吧），而这个保证是通过一个叫做两阶段提交的方式来实现的：

[![Z7sGge.png](https://s2.ax1x.com/2019/07/16/Z7sGge.png)](https://imgchr.com/i/Z7sGge)

它的大意是这样的，当有一个数据库的修改时，先将修改后的值放到内存，然后在redo log里面记录一哈，此时的状态是prepare, 然后在bin log里面再记录一哈，最后提交事务，将redo log里面的状态设置为commit. 等到夜深人静的时候，就可以通过redo里面这些状态为commit的字段来修改数据库了。