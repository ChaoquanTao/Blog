---
title: Spring思考与总结
date: 2020-03-19 22:44:20
tag: Spring
categories: 框架
---

> 更新于2020-10-01

从IoC的角度来说，spring是个容器，这个容器就是BeanFactory, 当然你说它是ApplicationContext也没有问题。容器是用来装东西的，装的东西就是我们定义的bean, 不过spring对它进行了封装，叫做BeanDefinition.

所以spring初始化的过程中，首先会做这么几件事情：

1. 创建容器
2. 创建beandefinition
3. 向容器里注册beandefinition

***

Spring是容器，最基本的容器是BeanFactory, 然后ApplicationContext又继承自它，但其实不能认为ApplicationContext是BeanFactory的实现类，因为事实是ApplicationContext内部持有了一个实例化的BeanFactory(DefaultListableBeanFactory).



refresh方法是整个容器启动的核心。方法主要有以下几个功能：

+ obtainFreshBeanFactory(): 创建容器，加载注册Bean.

+ prepareBeanFactory(): 设置类加载器，添加BeanPostProcessor

+ finishBeanFactoryInitialization(beanFactory)：初始化所有的Singleton Beans

  + createBeanInstance: 实例化bean

  + populateBean: 属性设置，处理依赖

  + initializeBean: 处理各种回调

    + 检查aware相关接口（aware接口是为了让bean可以获取到框架自身的一些对象）
    + BeanPostProcessor前置处理
    + 如果实现InitializeBean, 调用afterPropertiesSet()
    + BeanPostProcessor后置处理‘

    [![8c8Lut.jpg](https://s1.ax1x.com/2020/03/20/8c8Lut.jpg)](https://imgchr.com/i/8c8Lut)

    

BeanDefinition是Bean装载进容器中的一种表示，里面具体有是否是单例，它的依赖，是否懒加载，类名称，等等。