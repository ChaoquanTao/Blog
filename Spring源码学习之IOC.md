---
title: Spring源码学习
date: 2020-03-18 18:46:22
---

> 今天面试被问到了Spring, 被面试官吊捶，痛定思痛，决定重新开始学习源码！

首先Spring容器的顶层容器接口是什么？`BeanFactory`和`ApplicationContext`, 其中`ApplicationContext`加了一些上下文的支持，更为高级一点。



以`ClassPathXmlApplicationContext`为例，容器初始化的入口方法在哪里呢？`refresh()`方法。

`refresh()`进来后有几处核心方法，我们来一一看下。



第一处 `obtainFreshBeanFactory()`: 这个方法又调用了`refreshBeanFactory()`,主要做了两件事情：创建容器，加载`BeanDefinition`，也就是我们常说的容器初始化三步走的第一步。

```java
DefaultListableBeanFactory beanFactory = createBeanFactory();
loadBeanDefinitions(beanFactory);
```

继续看下这个`loadBeanDefinition()`：

![8sGH7F.png](https://s1.ax1x.com/2020/03/19/8sGH7F.png)

可以看到里面的代码分为两部分，第一部分就是创建并设置一个读取器，用来读取资源文件，第二部分就是加载`BeanDefinition`,好，继续深入。

![8sYooF.png](https://s1.ax1x.com/2020/03/19/8sYooF.png)

这里的代码也是很言简意赅，主要就是看我们的资源文件是以什么形式存在的，从而决定加载的是Resource还是String. 调试了一手发现我们这个走的是第一种类型，好，继续看：

[![8sUp2d.png](https://s1.ax1x.com/2020/03/19/8sUp2d.png)](https://imgchr.com/i/8sUp2d)

代码依旧简单，我们来看最核心的这一行干了啥：

```java
@Override
	public int loadBeanDefinitions(Resource resource) throws BeanDefinitionStoreException {
		return loadBeanDefinitions(new EncodedResource(resource));
	}
```

继续深入`loadBeanDefinitions()`：

这个代码比较长，我就只截取最重要的部分进行说明了

![8sB9BR.png](https://s1.ax1x.com/2020/03/19/8sB9BR.png)

这个代码主要做的工作就是负责从xml里面装载`BeanDefinition`.

继续看`doLoadBeanDefinitions()`:

![8sBs8U.png](https://s1.ax1x.com/2020/03/19/8sBs8U.png)

这里把xml转化成document, 然后执行`registerBeanDefinitions()`方法。

继续看`registerBeanDefinitions()`:

[![8srDcF.png](https://s1.ax1x.com/2020/03/19/8srDcF.png)](https://imgchr.com/i/8srDcF)

代码依旧简单，主要分为两部分：首先创建一个Reader, 然后由reader进行注册。这两部分都很重要，我们一一来看：

创建Reader:

进行注册：

![8sW7kQ.png](https://s1.ax1x.com/2020/03/19/8sW7kQ.png)

代码简单，继续深入：

`doRegisterBeanDefinitions()`:

这里面最核心的一句：

`parseBeanDefinitions(root, this.delegate);`

继续深入：

`parseDefaultElement(ele, delegate);`

继续深入：

![8sfW4J.png](https://s1.ax1x.com/2020/03/19/8sfW4J.png)

这里就厉害了，根据不同的节点名字进行不同的操作，那我们主要是加载bean, 那么节点名肯定就是`BEAN_ELEMENT`了，继续深入：

![8sOaU1.png](https://s1.ax1x.com/2020/03/19/8sOaU1.png)

继续来看下是如何解析Element的：

解析的方法叫这个名字

`public BeanDefinitionHolder parseBeanDefinitionElement(Element ele, BeanDefinition containingBean)`

可以看到它返回了一个`BeanDefinitionHolder`, `BeanDefinitionHolder`是对`BeanDefinition的进一步封装`，不信我们可以来看这个方法的返回值：

`return new BeanDefinitionHolder(beanDefinition, beanName, aliasesArray);`

可以看到里面封装了`beanName`,`alias`以及`beanDefinition`,那么`beanDefinition`又是在哪里定义的?

这个方法里有这么一句代码：

```java
AbstractBeanDefinition beanDefinition = parseBeanDefinitionElement(ele, beanName, containingBean);

```

