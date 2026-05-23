---
title: Tomcat Session管理
date: 2021-06-06 14:00:00
categories: Java
---

>Hey what's up guys. 有好长一段时间没写博客了，最近也是来上海一个多月难得的一个周末，所以写点东西吧。

关于session cookie相关的内容在校招时也被经常问到，但是最近感觉对这块的理解还是不够深入，所以再学习一下。



众所周知session用于会话管理，一般情况下，http request的header里的cookies字段里会带个sessionID, 服务端收到请求后，从cookie中拿出sessionID, 然后根据这个sessionID从服务端存储的session中拿出对应的session, 然后这个session里面一般会存储用户名、会话过期时间等。



流程是这么个流程，但是我之前一直忽略了一点，服务端的session是怎么存储的？因为考虑到服务端的扩展性，session有时候会被存储到redis或者mysql中，所以我一直以为session的管理需要开发者自己去做，后来发现，其实tomact有自己的会话管理功能。



而事实是，Tomcat内部有个`Manager`接口，这个接口的实现类负责管理`session`,具体来说，负责`session`的增删改查。`Manager`底下有`StandarManager`和`PersistanceManagerBase`两种实现，一种将`session`存在内存，一种则是持久化。当然`StandardManager`为了保证可靠性，也会将`session`存到文件中，只不过没有第二种存到数据库那么专业和高效罢了。