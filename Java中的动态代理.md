---
title: Java中的动态代理
date: 2020-02-16 17:41:44
tags: 动态代理
categories: Java
---

> 最近在看Spring中的AOP, 其实现主要是靠动态代理，所以打算先了解一下动态代理。

要说动态代理，需要先知道什么是代理，既然是动态代理，那么有没有静态代理，区别又在哪里。



何为代理，最直观的，我们fq时会用到小飞机或者其他的正向代理，说白了就是让代理代替我们去做某件事，在设计模式中专门有一个代理模式，我们可以先来看下代理模式的类图。

![3po3FJ.png](https://s2.ax1x.com/2020/02/16/3po3FJ.png)

其中ProxyImage就是代理对象，代理了RealImage, 它们实现了共同的接口，同时ProxyImage聚合了RealImage, 通过在ProxyImage的display方法中调用RealImage的display,达到代理的作用。



这样的代理我们也可以称之为静态代理，为什么这么说呢？因为这种代理关系是代码被编译成字节码时就存在的，而动态代理则不一样，它的代理关系是运行期动态创建的。说到运行期、动态，你想到了什么？反射。没错，其实动态代理就是用到了反射。



Java中常用的动态代理技术有JDK动态代理以及CGLIB动态代理。



基于JDK的动态代理核心有两个方法需要掌握：

首先要实现动态代理，代理需要继承`InvacationHandler`类，在代理类中实现代理对象和被代理对象的绑定，用的是`Proxy.newProxyInstance()`方法，然后需要重写一个`invoke()`方法，举一个廖雪峰大佬网站的例子

```Java
public class Main {
    public static void main(String[] args) {
        InvocationHandler handler = new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                System.out.println(method);
                if (method.getName().equals("morning")) {
                    System.out.println("Good morning, " + args[0]);
                }
                return null;
            }
        };mornin
        Hello hello = (Hello) Proxy.newProxyInstance(
            Hello.class.getClassLoader(), // 传入ClassLoader
            new Class[] { Hello.class }, // 传入要实现的接口
            handler); // 传入处理调用方法的InvocationHandler
        hello.morning("Bob");
    }
}

interface Hello {
    void morning(String name);
}

```

代码中生成了代理hello, 可以看到它和被代理对象是同一类型的，当执行代理对象的`morning()`方法时，就会调用`handler`的`invoke`方法，当然了，在`invoke`方法里我们一方面调用了被代理对象的morning方法，一方面加入我们自己的逻辑。