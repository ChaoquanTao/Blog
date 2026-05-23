---
title: MySQL的锁
date: 2020-01-06 11:12:07
updated: 2020-01-06 11:12:07
tags: MySQL
categories: 数据库
---

先看锁的分类：

按照是否共享，可以分为：

+ 共享锁（读锁）
+ 排他锁（写锁）



按照锁的粒度，可以分为：

+ 表锁
+ 行锁



要谈锁，我认为是要结合事务隔离级别一起谈的，MySQL的事务隔离级别有：

+ Read Uncommitted
+ Read Committed
+ Repeatable Read
+ Serializable



`InnoDB`默认的是行锁，而且行锁是加给索引的，所以如果没有索引，那也就只能被迫全表扫描了。



单纯的说“要给什么语句加什么锁”，这句话本身是靠不住的，因为要给某个语句是否加锁，加什么锁，取决于很多因素，如：

+ 上下文，即事务的隔离级别
+ 这条语句本身的特性：这条语句是单纯的select,还是select for update, select lock in share mode，还是insert, update 或者delete，带有修改意味的语句一般会被加X锁，普通的语句加S锁或者不加
+ 执行时有没有用到索引，使用二级索引可能会需要回表，这时候对一级索引也要加锁，使用一级索引进行修改二级索引则二级索引也要加锁。



同一语句在不同的隔离级别下加锁情况也不一样。

在READ UNCOMMITTED 和 READ COMMITTED隔离级别下，因为不需要防止幻读的问题，所以加锁也都是一条记录一条记录的加，不存在范围锁（gap锁或者next-key lock）

但是在 REPEATABLE READ 下则不一样，因为需要防止幻读，加锁的时候不仅需要加锁自身，还要锁定一个范围。