---
title: oracle填坑
date: 2018-01-10 19:32:55
tags:  数据库
categories: 数据库
---

使用dbca来创建数据库，这个过程选择了高级选项，需要留意用户名和密码，这个在后来用sql  developer连接时用得到



在用sql developer连接时，应该是可以选择管理员账户的（不过我还没搞清楚），并且注意选择一般账户的话底下那个选项就不能用sysdba哦



关于找不到模块的问题，貌似需要把js文件放到oracledb模块下编译

在基于oracledb 用node 运行js文件时提示说用户名或密码无效，事实是我杠杆用这个用户名登陆了sqldeveloper,导致js文件代码连不上

在用sqldeveloper连接oracle时出现了下面错误

`sql developer ORA-12505, TNS:listener does not currently know of SID given in connect descriptor`

大概意思就是 没有监听到这个SID,于是乎打开listener.ora文件，把这个SID相应的加进去就好了，