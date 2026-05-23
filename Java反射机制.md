---
title: Java反射机制
date: 2019-07-11 15:26:23
updated: 2019-07-11 15:26:23
tags: 反射
categories: Java
---

写这篇文章主要想讲两个问题：

1. 什么是反射
2. 反射存在的意义
3. 反射能做哪些事

### 什么是反射

反射，简单的来讲，是一种在程序运行时生成对象的技术。为什么说是运行时呢，相比我们平时写代码时创建对象，比如：

```
public static void main(){
    Object obj = new Object();
}
```

我们创建对象的代码是事先写好的，那么程序在编译的时候，也就是`.java`文件被编译成`.class`文件的时候，这个对象就已经在`class`文件中了。而反射讲的是，这个对象在编译器是不存在，在程序运行的时候，因为某种需求，它才被创建出来。

### 反射存在的意义

学习一种技术，更重要的是要明白它存在的意义。那么为什么要有反射呢？

反射一个最大的用途就是用在各大框架中，如`Spring`,`Struts2` 现在的各种框架都是配置型的。下面的`xml`是`Stucts2`中的一个配置文件。当后台收到这个`login`请求后，经过各种过滤器，最后它会和这个配置文件对应，这个配置文件里面描述了当收到这种请求后我要调用哪个类（这里就是	`org.ScZyhSoft.test.action.SimpleLoginAction`类），以及类中的哪个方法（这里就是`execute`方法）。但这个类其实配置文件只写了一个类名，也就是说等到真正这个请求到了，需要用到这个类的时候它才被创建，这里创建的技术就是反射。

```
<action name="login"
               class="org.ScZyhSoft.test.action.SimpleLoginAction"
               method="execute">
           <result>/shop/shop-index.jsp</result>
           <result name="error">login.jsp</result>
       </action>
```

### 反射能做哪些事

#### 创建实例

使用反射创建实例，首先要获得`Class`对象，你可以认为它就是我们所写的类的对象类型。这句话可能有点绕，俗话说“万事万物皆对象”（当然除了基本数据类型），所以类本身也是对象，它是`Class`类的对象，获取`Class`对象有三种方法：

1. `Class.forName()`

   比如`Class.forName(org.ScZyhSoft.test.action.SimpleLoginAction)`

2.  直接获取某个对象的`class`属性

   如`Class<?> klass = obj.class`

3. 调用某个对象的`getClass()`方法

   如`Class<?> klass = obj.getClass()`

获取`Class`对象之后，就可以使用`Class`对象来创建实例了

1. 对于默认构造函数的对象，我们可以

```java
Class<?> c = String.class;
Object str = c.newInstance();
```

2. 对于带参的构造函数，我们可以

```java
//获取String所对应的Class对象
Class<?> c = String.class;
//获取String类带一个String参数的构造器
Constructor constructor = c.getConstructor(String.class);
//根据构造器创建实例
Object obj = constructor.newInstance("23333");
```

#### 获取方法和成员变量

获取某个Class对象的方法集合，主要有以下几个方法：

- `getDeclaredMethods` 方法返回类或接口声明的所有方法，包括公共、保护、默认（包）访问和私有方法，但不包括继承的方法。

```java
public Method[] getDeclaredMethods() throws SecurityException
```

- `getMethods` 方法返回某个类的所有公用（public）方法，包括其继承类的公用方法。

```java
public Method[] getMethods() throws SecurityException
```

- `getMethod` 方法返回一个特定的方法，public的，其中第一个参数为方法名称，后面的参数为方法的参数对应Class的对象。

```java
public Method getMethod(String name, Class<?>... parameterTypes)
```



`getDeclaredField`：所有已声明的成员变量，不问访问权限，但不能得到其父类的成员变量

`getFileds`：访问公有的成员变量，包括继承的公用方法

`getField(String name)` 获取指定的变量（public）

#### 调用方法

`invoke()`