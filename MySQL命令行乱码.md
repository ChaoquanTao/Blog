---
titile: mysql命令行乱码
categories: mysql
date: 2021-09-21 10:00:00
---

一直用的都是mysql ui客户端，比如navicate等，今天用命令行连接的时候，发现查询中文乱码，所以这里排查一下。



首先用`show variables like 'char%';`命令查看数据库的编码方式

