---
title: Spring IoC 容器的实现(一)
date: 2019-11-02 20:04:31
updated: 2019-11-02 20:04:31
tags: Spring
categories: 框架
---

本文开门见山，直接讨论Spring `IoC`容器的初始化过程。

关于Spring容器，有一个最基本的接口，叫做`BeanFacotory`, 它提供了容器最基本的一些特性。所有的容器都是基于它的。还有一个较为高级一点的容器接口，叫做`ApplicationContext`，它在`BeanFactory`的基础上，又提供了其他一些高级特性，比如访问资源。		



本文以`ApplicationContext`的一个具体实现类`FileSystemXmlApplicationContext`为例，探究spring容器的初始化过程。先来看下它的主要代码。



显示构造函数：

```java
public FileSystemXmlApplicationContext(String[] configLocations, boolean refresh, ApplicationContext parent)
			throws BeansException {

		super(parent);
		setConfigLocations(configLocations);
		if (refresh) {
			refresh();
		}
	}
```

这里的`refresh()`方法标志着容器初始化的启动，也是我们后面分析的重点。

还有一个方法

```java
protected Resource getResourceByPath(String path) {
		if (path != null && path.startsWith("/")) {
			path = path.substring(1);
		}
		return new FileSystemResource(path);
	}
```

它会在启动容器的过程中调用。



先看下`FileSystemXmlApplicationContext`的继承关系

[![KLBqzt.md.png](https://s2.ax1x.com/2019/11/02/KLBqzt.md.png)](https://imgchr.com/i/KLBqzt)



下面正式分析`BeanDefinition`的`Resource`定位



`refresh()`方法在`AbstractApplicationContext`中实现：

![KLRWQJ.png](https://s2.ax1x.com/2019/11/02/KLRWQJ.png)

代码虽长，其实只做了两件事：框出来的部分创建容器，剩余部分对创建好的容器进行一系列设置。继续来看创建容器的部分：

![KLWxc4.md.png](https://s2.ax1x.com/2019/11/02/KLWxc4.md.png)

这里的`refreshBeanFactory()`是个抽象方法，在`AbstractRefreshableApplicationContext`中实现。



**`AbstractRefreshableApplicationContext`**

![KLhRSS.png](https://s2.ax1x.com/2019/11/02/KLhRSS.png)



继续来看`createBeanFactory()`

```java
protected DefaultListableBeanFactory createBeanFactory() {
		return new DefaultListableBeanFactory(getInternalParentBeanFactory());
	}
```

返回一个`DefaultListableBeanFactory`容器



再看`loadBeanDefinitions()`, 它同样是个抽象方法，它在`AbstractXmlApplicationContext`中实现

![KL4ukt.png](https://s2.ax1x.com/2019/11/02/KL4ukt.png)

它先创建一个reader，然后通过这个reader加载`BeanDefinition`,继续看它的重载方法

![KL4v38.png](https://s2.ax1x.com/2019/11/02/KL4v38.png)



对于xml的上下文来说，它走的应该是第二个if, 里面调用了`XmlBeanDefinitionReader` 的`loadBeanDefinitions()`方法，继续看

![KL52rQ.png](https://s2.ax1x.com/2019/11/02/KL52rQ.png)



继续看它的重载方法

![KLIzwj.png](https://s2.ax1x.com/2019/11/02/KLIzwj.png)



继续来看具体是如何获取资源的：

`ResourceLoader`是个接口，这里使用了`DefaultResourceLoader`类实现的方法

![KLTpuD.png](https://s2.ax1x.com/2019/11/02/KLTpuD.png)





好，到此整个分析过程差不多结束了，重新梳理一下：

在`BeanDefiniton`的`Resource`定位中，始于`FileSystemXmlApplicationContext`的`refresh()`方法，这里是容器初始化的开端，同时也是定位资源的开端。

这里的`refresh()`方法来自父类`AbstractApplicationContext`, 这个方法里面获得了容器并对容器进行了一系列操作。

这里获得容器的方`obtainFreshBeanFactory()`使用了模板方法模式，里面的模板方法`refreshBeanFactory()`交由具体子类实现，在这里是由子类`AbstractRefreshableApplicationContext`实现。

在`AbstractRefreshableApplicationContext`的`refreshBeanFactory()`中，创建了容器，并进行`BeanDefinition`的加载。

这个加载方法`loadBeanDefinitons()`同样是模板方法，涉及一系列的调用。具体它是通过一个`BeanDefinitonReader`来加载`BeanDefinition`的，加载的过程中就涉及到对各种形式location的解析。解析完之后差不多就真正完成了对resource的定位了。



总的来说，做了两件事。目的是初始化容器，首先你得有个容器，比如桶，其次你得有水，那么就得找到水在哪，上面主要描述的就是一个找水的过程。

起源于refresh,但是要找到水，还需要靠`Reader`

相当于下面这个过程

```java
ClassPahtResource res = new ClassPathResouce("bean.xml") ;
DefaultListableBeanFactory factory = new DefaultListableBeanFactory();
XmlBeanDefinitionReader reader = new XmlBeanDefinionReader(factory);
reader.loadBeanDifinition(res) ;
```



使用IoC容器时，需要以下几个步骤（即初始化容器的步骤）：

1. 创建抽象资源，包括Ioc配置文件，Beandefiniton
2. 创建BeanFactory
3. 创建reader,读取BeanDefinition并回传给BeanFactory,完成载入和注册。





画一个调用的关系图就能更好的理解这个过程了。

​	











### 参考

《Spring技术内幕》