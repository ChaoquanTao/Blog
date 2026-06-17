---
title: Java中的final关键字
date: 2019-10-11 15:54:43
updated: 2019-10-11 15:54:43
tags: 关键字
categories: Java
---

### 用法

#### 修饰变量

修饰基本类型：基本类型的值不可被改变

修饰引用：引用的指向不能被改变

被final修饰的基本类型和String类型会在编译器被放到常量池

#### 修饰方法

方法不可被覆盖

#### 修饰类

类不可被继承



### 原理

我们反编译如下代码：

```java
public final class Tiger  {
    private final String name ="tiget" ;
    private final int a = 1;


    public final void run(){
        System.out.println("tiger is running");
    }
}
```



得到：

<img src="http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7uchin2fgj30ll0kht9c.jpg" alt="7f26f50ff199d5bba671d34a3115a01.png" style="zoom:80%;" />

<img src="http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7ucij5ni5j30mo0eqdg2.jpg" alt="22ceb20e2a54fb5ca9e545e3b62b34d.png" style="zoom:80%;" />

