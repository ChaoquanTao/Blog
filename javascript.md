---
title: javascript
date: 2018-01-05 13:02:17
tags: 前端
---

### 函数

+ 匿名函数是将函数值赋给变量`var abs = function(x){...}`


+ 把自己的代码全部放入唯一的名字空间`MYAPP`中，会大大减少全局变量冲突的可能。
+ 解构赋值
+ JavaScript的函数其实都指向某个变量。既然变量可以指向函数，函数的参数能接收变量，那么一个函数就可以接收另一个函数作为参数，这种函数就称之为高阶函数。

  ​常用的有：map/reduce,filter,sort;

  ​数组对象具有一个map函数，可以进行批量操作

+ 返回闭包时牢记的一点就是：返回函数不要引用任何循环变量，或者后续会发生变化的变量。

+ JavaScript的原型链和Java的Class区别就在，它没有“Class”的概念，所有对象都是实例，所谓继承关系不过是把一个对象的原型指向另一个对象而已。

+ JavaScript的原型继承实现方式就是：

  1. 定义新的构造函数，并在内部用`call()`调用希望“继承”的构造函数，并绑定`this`；

  2. 借助中间函数`F`实现原型链继承，最好通过封装的`inherits`函数完成；

  3. 继续在新的构造函数的原型上定义新方法。

### DOM

+ `document`对象表示当前页面。由于HTML在浏览器中以DOM形式表示为树形结构`document`对象就是整个DOM树的根节点.
+ html文档被解析后就是一颗DOM树，在操作一个DOM节点前，首先要获得这个节点，方法有`document.getElementById()`和`document.getElementsByTagName()`

ORM技术：Object-Relational Mapping

+ 要DOM做什么？

  可以操作html文档

+ ​



### BOM对象

浏览器对象模型

+ 对象：

  + Navigator:获取浏览器的信息

  + Screen: 获取屏幕信息

  + location: 请求的`url`地址

    `href`属性: 获取当前请求地址，设置新的地址

  + History: 请求的`url`的历史记录

    ```
    histtory.back()
    history.go(-1)
    history.forward()
    histoty.go(1)
    ```

    ​

  + Window： 窗口对象，顶层对象，所有`bom`对象都是在Window里面操作的

    ```
    window.alert()
    window.confirm("...")  //确认框，有返回值true false
    window.prompt(text,defalutText)   //输入的对话框
    window.open(URL,name,feature,replace) //打开一个窗口
    window.close()  //关闭窗口
    ```

    ​

  + ​