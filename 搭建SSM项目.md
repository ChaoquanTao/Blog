---
title: 搭建SSM项目
date: 2019-10-13 15:33:11
updated: 2019-10-13 15:33:11
tags: SSM
categories: 框架
---

最近在做一个基于SSM的系统，借此记录一下如何在IDEA下搭建一个SSM项目



SSM, 即Spring, Spring MVC 和Mybaits. 所以整体来讲它还是一个基于Spring MVC的，只不过后端使用了Spring和Mybaits.



我们先来看下对于一个SpirngMVC项目，它里面的配置文件有哪些

`web.xml`

这个是Web工程的配置文件，看下里面的的配置：

<img src="http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7wmnzpzzyj30uw0c9q4o.jpg" alt="362b4082424544ac35702266f68bf5e.png" style="zoom: 80%;" />



第一部分 `contextConfigLocation`，描述Spring MVC的Spring IoC文件的位置，这里默认是同目录下的`applicationContext.xml`，可以发现里面是空的。



第二部分`ContextLoaderListener`，起作用是在整个Web工程加入自定义的代码



第三部分配置`DispatcherServlet`,在里面配置name是`dispatcher`，说明还有一个专门的`dispatcher-servlet`文件，在同目录下也可以找到,关于这可以了解下Spring MVC的组件以及流程。



第四部分配置拦截器，这里`DispatcherServlet`会拦截所有以form结尾的请求。



ok,以上就是Spring MVC里面`web/WEB-INF/`下的三个配置文件的介绍



那么要建立一个SSM项目，在一个Spring MVC项目的基础上，还需要什么呢？

还需要两个配置文件：桥接spring和`mybatis`的配置文件以及关于`mybaits`自身的配置文件。

关于这两个文件，我们一般会在`src/main`下面创建一个resource文件夹，在里面放置`spring-mybaits.xml`和`mybaits-config.xml`.



再来看下这两个配置文件里应该放些啥

`spring-mybaits.xml`

![4dd3ae455d1c228b43d6df10adfbb03.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7wn9db33ij30wt0hg418.jpg)

第一部分`dataSource`，配置数据源，也就是数据库相关属性



第二部分配置`sqlSessionFactory`，关于这个你可能需要了解一下MyBaits的核心组件，它通过工厂模式来生产`sqlSession`, sqlSession可以获得我们下面要提到的mapper, 它里面配置它的dataSource属性和configLocation属性，其中这个configLocation属性就指向了mybaits自身的配置文件。



第三部分配置`MapperScannerConfigurer`, 从名字就可以看出，是一个关于mapper扫描器的配置，那它是干啥的呢？

首先说映射器mapper,它是mybaits里面很重要的一部分，它由一个接口和一个xml文件（或注解）组成，需要给出相关的SQL和映射规则。它负责发送SQL去执行，并返回结果。

所以要用mapper，我得先知道有哪些mapper,这些mapper都在哪里，所以需要扫描一下，这里做的事情就是关于扫描的配置。这个配置里面，`basePackage`告诉我们要去哪个包地下扫，`sqlSessionFactoryBeanName`，就是我们第二部分说的那个，`annotationClass`告诉我们只有被这个注解标注的时候，我们才去扫描。



`mybaits-config.xml`

![58fefb017f16bd0205251c01860ce6d.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7wo08yhcnj30jq0bbt9m.jpg)

第一部分 相关设置，这里先不重要



第二部分，给我们的pojo配置些别名，这个在写sql的时候会用到



第三部分，指定映射器的路径





好，讲到这里，关于配置文件的东西就介绍完了，但是！还记得我们在web里面讲的`contextConfigLocation`吗，它描述的是Spring IoC的位置，那么在这里，这个位置应该是啥呢？没错，是我们的`spring-mybaits.xml`，所以记得在`web.xml`里面记得修改一下。