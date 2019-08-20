---
title: java_mongo_db学习笔记
date: 2018-03-19 15:25:02
tags: 编程语言
---

### 数据导入

+ 之前的数据是在Oracle里面，所以这里需要将oracle中的表导入`Mongodb`中、

  + 先将Oracle中数据表导出为`tsv`格式

  + Mongo提供`mongoimport`命令进行导入

    ` mongoimport --db busi_run --type tsv --headerline --ignoreBlanks --file G:\毕设\data\busi100.tsv`

    这里`headerline`选项会将文件第一行作为字段名

    ​

  + ​

+ ​