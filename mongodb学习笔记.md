---
title: mongodb学习笔记
date: 2018-01-02 09:41:25
categories: 数据库
---

1. 关系型数据库与MongoDB术语对比

| 关系型数据库 | MongoDB                 |
| ------ | ----------------------- |
| 表      | 集合                      |
| 行      | 文档                      |
| 列      | 字段                      |
| 表join  | 内嵌                      |
| 主键     | 主键（由MongoDB提供默认的key_id） |

2. 创建数据库

   ` use DATABASE_NAME`

3. 得到

4. 记一次在`mapreduce`里填的坑

   `mapreduce`最初是由谷歌提出的框架，但已在多种平台上实现。分为map和reduce两个阶段。

   map阶段通过emit函数对同一个key所对应的值进行映射，reduce阶段对每组映射结果进行化简。用官方文档的一张图来说明：

   ![](https://ws1.sinaimg.cn/large/005UcYzaly1fpn1zw63gvj30kg0hp75s.jpg)

   ​

5. ​

5. 问题合集

+ 在连接MongoDB的过程中，实际上应该用两次cmd,第一次是开启Mongo服务，第二次才是连接到数据库。先到安装目录下的bin文件夹下执行`mongod --dbpath "F:\mongodb\data\db"`启动服务器，然后重新打开命令行，输入`mongo`连接数据库

+ 在`node.js`操作`mongodb`时遇到如下错误

  `MongoNetworkError: connection destroyed, not possible to instantiate cursor`

  最后发现应该把`db.close()`写到回掉函数里面

+ `​mongodb`的在线调试端口默认28017



mongodb的访问控制问题： admin对于非系统集合其实是没有读权限的