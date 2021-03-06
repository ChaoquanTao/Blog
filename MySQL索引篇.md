---
title: MySQL索引篇
date: 2019-11-06 16:47:54
updated: 2019-11-06 16:47:54
tags: MySQL
categories: 数据库
---

提到MySQL索引，都会讲到B树和B+树，今天来梳理一下。



最开始是二叉查找树，但是这种树不平衡，有时候会退化成一条链表，使得查找时间边长，于是就有了二叉平衡树。

理论上讲，二叉平衡树已经能满足一些查找需求了，为什么还要有B树呢？

因为数据库在磁盘中，而查找的时候需要读一部分数据到磁盘中，这就涉及到了IO，IO的时候是以磁盘块为单位读取的，或者说是以页为单位。我们使用树这种数据结构，一个磁盘块应该包含一个或者若干个节点，然后以节点为单位读入。那么AVL树有什么问题？它的每个节点太“瘦弱”了，只能装一个键值对，假如一个节点就是一个磁盘块的化，这就导致我们查询的时候增大IO次数。那么有什么对应办法呢？就是让每个节点“胖一点”，即让每个节点多装几个键值对。这就引出了B树。



B树突破了二叉，每个节点有多个键值对，这样一来，节点个数减少，我们查询的IO次数也会减少。



那还有没有优化的余地呢？上面我们讲到每个节点都含有多个键值对，为了更一步充分利用节点的空间，我们可以让非叶子节点只含有键，只有叶子节点才会包含数据，也就是键对应的值，这么一来，非叶子节点就能装更多的键了，树的高度和节点数就能更进一步被降低了。这种只用叶子节点保存数据的树就是B+树了。



不止如此，在B树的基础上，B+树的还用双向链表链接起了每个叶子节点，这样有什么好处呢？可以很方便的实现范围查询。



还有一个需要了解的是聚簇索引和非聚簇索引。

所谓聚簇索引，指的是以主键作为索引构建B+树，而且叶子节点存储数据的索引结构。



非聚簇索引，首先索引不是主键，其次它的叶子节点存放的不是数据而是索引对应的主键（需要注意的是这里`InnoDB`和`MyISAM`实现略有区别，`InnoDB`存放的是主键，而`MyISAM`存储的是文件地址，我们这里以`InnoDB`为主进行讲解）。也就是说，对于非聚簇索引，你首先需要根据索引找到主键，然后再根据主键进行聚簇索引查找，这一过程我们称之为**回表**。



所以这里我们就可以看到使用主键进行查询的好处：只需要查询一颗B+树（这里再加一点，对于每张表来说，每个索引就相当于一颗B+树）。



同时一些文章里也会提到，通常要求我们建表的时候选一个自增主键作为索引，为什么要这样要求呢？因为索引底层是由B+树实现的，自增主键可以使得我们再插入节点时减少业分裂，当当前页满时只需要再创建一个新页继续添加数据即可，不用对之前已有的页进行分裂。

那么就又有一个问题了，自增主键如何选？假如一个表里有身份证号，且能够保证它是自增的，我们可以用它做主键吗？可以是可以，但是要知道，普通索引的叶子节点是主键，你用身份证号做主键，这意味着叶子节点就很占空间了，肯定没有我们自己设置的自增主键划算。



联合索引，覆盖索引，最左匹配原则。

都说加索引可以提高查询效率，但是当我们查询时where后面有多个条件时，难道我们要为每一列都加个索引吗？其实不是的，一种更好的方法是可以加联合索引，并且联合索引是满足最左匹配原则的。什么意思呢，假如我们建立了联合索引`key(a,b,c)`，那么在今后的查询中，(a), (a,b), (a,b,c)这三种查询条件都是可以使用我们的联合索引来加快查询速度的。



覆盖索引主要是针对非聚簇索引和联合索引说的，指的是叶子节点中已经包含了我们要查询的列，这样就免的进行回表这一操作了。



总结：

其实可以看到，这些数据结构都不是凭空产生，一般都是为了满足某个需求才被人们创建。所以在某些程度上，知道一种技术为什么存在要比技术本身更为重要，否则永远只能是一个技术的学习者，而不是缔造者。