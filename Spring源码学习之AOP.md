---
title: Spring源码学习之AOP
date: 2020-03-21 12:35:04
updated: 2020-03-21 13:00:00
categoris: 框架
tag: Spring
categories: Spring
---

> 经过供应链大佬的预面试，觉得自己在Spring这一块掌握地还是有些浅，痛定思痛，再次阅读源码。



在上一篇文章中我们已经分析了Spring IOC的一个大概过程，那么AOP又是在什么时候发生的呢？（这篇文章不讲动态代理，不讲切面切点通知，只讲代码流程。）



###  缘起

Spring AOP很关键的一步就是创建AOP 代理，那么这一动作是何时发生的呢？

众所周知（不知道也没关系），创建代理对象有一种专门的类叫`ProxyCreator`, 那么如果是基于注解创建的话，这个类叫做`AnnotationAwareAspectJAutoProxyCreator`, 如果去看它的继承关系你会发现，它实现了`BeanPostProcessor`接口，这个接口我们在上篇文章中也提到了：`Bean`的实例化主要经过三个方法：`createBeanInstance`,`populateBean`,`initializeBean`.其中最后一个方法就是用来处理各种回调，其中就包括`BeanPostProcessor`,那我们就接着上一节讲的`BeanPostProcessor`的回调来继续讲。



### 开始

先到`BeanPostProcessor`的后置处理这里，

`AbstractAutowireCapableBeanFactory`  1633行

```java
if (mbd == null || !mbd.isSynthetic()) {
			wrappedBean = applyBeanPostProcessorsAfterInitialization(wrappedBean, beanName);
		}
```



`applyBeanPostProcessorsAfterInitialization`:

```java
public Object applyBeanPostProcessorsAfterInitialization(Object existingBean, String beanName)
			throws BeansException {

		Object result = existingBean;
		for (BeanPostProcessor beanProcessor : getBeanPostProcessors()) {
			result = beanProcessor.postProcessAfterInitialization(result, beanName);
			if (result == null) {
				return result;
			}
		}
		return result;
	}
```



进入到`AbstactAutoProxyCreator`,已经发现了`ProxyCreator`的影子了有木有？：

```java
public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
		if (bean != null) {
			Object cacheKey = getCacheKey(bean.getClass(), beanName);
			if (!this.earlyProxyReferences.contains(cacheKey)) {
				return wrapIfNecessary(bean, beanName, cacheKey);
			}
		}
		return bean;
	}
```



`wrapIfNecessary()`:

我就只截取关键代码啦

![8WYcDJ.png](https://s1.ax1x.com/2020/03/21/8WYcDJ.png)

这里的意思就是说，如果我们这个Bean有Advice或者Advisor的话，那么我们就开始创建代理，很容易理解有木有？



`createProxy()`:

这里代码略多，我就不贴了，它的核心逻辑就是先获取并设置一个代理工厂，然后从代理工厂里获取代理，方法的最后一句是这样的：

```java
return proxyFactory.getProxy(getProxyClassLoader());
```



来到Class `ProxyFactory`:

```java
public Object getProxy(ClassLoader classLoader) {
		return createAopProxy().getProxy(classLoader);
	}
```

从名字就可以看出来，创建`AopProxy`



`createAopProxy()`:

```java
protected final synchronized AopProxy createAopProxy() {
		if (!this.active) {
			activate();
		}
		return getAopProxyFactory().createAopProxy(this);
	}
```



`createAopProxy()`:

![8WNJTs.png](https://s1.ax1x.com/2020/03/21/8WNJTs.png)

从这里就可以看出，根据`targetClass`有没有接口之类的，决定用Jdk动态代理还是`Cglib`.



至此，`createProxy()`已经完成，我们再回到上面`ProxyFactory`的`getProxy()`方法：

```java
public Object getProxy(ClassLoader classLoader) {
		return createAopProxy().getProxy(classLoader);
	}
```

继续看下`jdk`代理的`getProxy()`做了什么：

![8WjNLt.png](https://s1.ax1x.com/2020/03/21/8WjNLt.png)

来到了熟悉的`jdk`动态代理有木有。众所周知第三个参数是`InvocationHandler`接口的实现类，这里用了`this`, 说明这个类自己实现了`InvocationHandler`接口，我们来看下它复写的`invoke()`方法。这个方法就厉害了，它涉及到拦截器调用链的执行，我这里只截取了部分核心代码。

![8fArf1.png](https://s1.ax1x.com/2020/03/21/8fArf1.png)

首先它会去获得当前方法的一个拦截器链，获得之后，如果这个chain不为空，我们就把这个拦截器链创建成一个method invocation，然后去执行。那么这个`proceed()`就是一个责任链模式的执行过程。



### 总结

关于Spring的AOP, 我们要知道这么几个问题，

1. 首先AOP从什么时候开始的，答案是`BeanPostProcessor`,也就是说，Spring AOP 会在 IOC 容器创建 bean 实例的最后对 bean 进行处理。其实就是在这一步进行代理增强。
2. AOP分为两步，`createProxy`和`getProxy`. 其中`createProxy`有`jdk`和`cglib`两种方法。而`getProxy`是我们最需要注意的。以`jdk`动态代理为例，它的invoke方法里包含了以责任链模式对拦截器的调用。





