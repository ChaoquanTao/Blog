---
title: Python学习笔记
date: 2018-10-13 15:33:11
categories: 机器学习
comments: true
updated: 2020-05-31 12:35:04
---



###  语句

+ while循环，for循环，if语句 不需要括号，后面需要加冒号

+ 定义函数语句 ： 

`def fun(a,b):`
   ​    注：参数可以设置为默认值


   + 定义全局变量： 定义在函数外部或者用内部global修饰
<!-- more -->

###  模块安装

 sd

### 函数

+ 默认参数  函数可以有默认参数，但是默认参数必须指向不变对象

+ 可变参数  

  意味着可以传入任意多个参数，在调用时自动组装成一个tuple,在参数前面加个*号，在一个list或者tuple前面加个 *号，意味着将list或tuple元素拆解成多个可变参数传入

+ 关键字参数

  关键字参数允许传入任意个含参数名的参数，这些关键字参数在函数内部自动组装成一个dict

  ```
  def person(name,age,**kw):
  	print('name',name,'age',age,'other',kw)
  person('Jack',24,**{'city':'Beijing','job':'Engineer'})
  >>> name Jack age 24 other {'job': 'Engineer', 'city': 'Beijing'}
  ```

+ 命名关键字参数

  顾名思义，限制关键字参数的名字，比如说我只允许传入city和job关键字，那么

  ```
  person(name,age,*,city,job)
  ```

  果函数定义中已经有了一个可变参数，后面跟着的命名关键字参数就不再需要一个特殊分隔符`*`了

  ```
  person(name,age,*args,city,job)
  ```
### 高级特性

+ 切片

  ```
  l=list(range(0,100,1))
  L[0:3]表示取出索引0到索引2的所有元素
  l[:10] //取出前十个元素
  l[-10:] //取出后十个元素
  l[:10:2] //前十个数每两个取一个
  ```

  

+ 列表生成式

  ```
  [x*x for x in range(1,11)]
  d = {'x':'A','y':'B','z':'C'}
  [k+'='+v for k,v in d.items()]
  ```

  

+ 生成器

  一边循环一遍计算的机制

  + 定义方法一

  ```
  >>> l = [x*x for x in range(1,11)]
  >>> l
  [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
  >>> g = (x*x for x in range(1,11))
  >>> g
  <generator object <genexpr> at 0x000001EF9005A5C8>
  ```

  相比于列表生成器，唯一的不同就是()

  + 定义方法二

    yield关键字，以斐波那契数列为例

    ```
    >>> def fib(max):
    	n,a,b = 0,0,1
    	while n<max:
    		yield b
    		a,b = b,a+b
    		n=n+1
    	return 'done'
    >>> for i in fib(6):
    	print(i)

    	
    1
    1
    2
    3
    5
    8
    ```

    如果把这里的yield换成print，那fib()就是个函数，这里yield关键字的作用是，生成器每次执行到这里返回，下次执行时接着这里执行

+ `Interable`   `Interator`

  可以作用于for循环的成为`Interable`

  可以被`next()`函数调用并不断返回下一个值的叫做`Interator`

  可以用`isInstance()`判断一个对象是否是`Interator`对象

  `Interator`的计算是惰性的，只有需要下一个值时它才会计算

+ 

### 函数式编程

允许将函数作为一个参数传给函数

#### 高阶函数

+ map/reduce

  + map 

     `map(function,Interator)`,map将function作用于`Interator`的每个元素，生成一个新的`Interator`

  ```
  >>> map(abs,[-1,-2,-3,-4])
  <map object at 0x000001EF9006C518>
  >>> r = map(abs,[-1,-2,-3,-4])
  >>> r
  <map object at 0x000001EF9006C278>
  >>> list(r)
  [1, 2, 3, 4]
  ```

  也就是一种映射

  + reduce

    `reduce(function,Interator)`，reduce可以认为是一种归纳或者迭代

    ```
    >>> from functools import reduce
    >>> reduce(add,[1,2,3,4])
    10
    ```

    

+ filter

  同样接收两个参数

+ sorted

  `sorted([...],key=function)`先按照key所指的函数对list处理，对处理后的结果排序，然后把排序好的结果映射到原来的list并返回

### 文件读写

 写文件：
```
	file = open("filename","openMethod")
	file.write()
	file.close()
```

 读文件：
 ```
	file = open()
	context = file.read()
	//其他形式file.readline()或file.readlines()
	file.close()
 ```
###  class 类
 定义：
 ```
	class Calculator :
		name = 'Good Calculator'
		price = 18
		def __init__(self,name,price)
		def add(self,x,y):
			return x+y
 ```
 声明：
	`calcu = Calculator();`

 注：

 + 与java不同的是python定义方法时必然有一个self参数，相当于java中的this,且在方法中使用属性时需要用 self.name
 + 函数init()相当于构造函数，用于初始化属性，也是最先执行的方法，比较奇怪的是它这里并没有像java中那样和类名同名
 + 属性必须初始值，不然会报错

### 元组，列表，字典，集合

 + 元组   tuple = (...)     圆括号,相比于列表，元组一旦初始化就不可改变
 + 列表   list= [...]  方括号
 ```
	list.append(element) #追加
	list.insert(index,element)	#插入
	list.remove(element)	#删除第一次出现的该元素
	list[-1] #表示最后一个元素
	list[0:3]	#从第0个元素到第三个元素（不包括第三个）
	list.index(element)	#返回第一次出现该元素的索引
	list.count(element)	#返回list中该元素的个数
	list.sort()	#对list进行升序排序并覆盖原来的list
	list.sort(reverse=True)	#对list降序排序
 ```
 + + 多维列表
 ```
	multi_dim_list = [[1,2,3],[4,5,6],[7,8,9]]
	print(multi_dim_list[0])
	print(multi_dim_list[0][2])
 ```
 + 字典

无序的容器，可存储任意类型对象，每个元素分别又由键：值构成，键必须唯一，值可不唯一，且类型可多样，键类型也可多样。无论是添加还是删除元素，都是通过键来索引值
```
	d = {1:'a',2:'b'}
	print(d)
	print(d[1])
	del d[1]
	print(d)
	d[3]='c'
	print(d)
	d[4] = {1:3,2:4}
	d[5] = ['a','b','c']
	print(d)
	d['a']= 1
	print(d)
```
+ 集合

  set可以看成数学意义上的无序和无重复元素的集合，set里存放的是不可重复的键

###  模块

    1. import模块
    + import time
    + import time as t  自己重新定义模块名
    + from time import time,localtime  只import自己想要的功能
    + from time import *  import该模块所有功能

### try语句
```
	try:
		.....
	except Exception as e:
		....
	else:
		....
```
###  map zip lambda

 - zip

   将两个list用于纵向的合并,如：
```
   	a=[1,2,3] , b=[4,5,6]
   	print(list(zip(a,b)))
```
   输出：
   `[(1, 4), (2, 5), (3, 6)]`

 - lambda

   lambda用于定义一个简单的函数，简化代码,如：
   ```
   	res = lambda x,y : x+y
   	print(res(2,5))
   ```
   输出：
   `7`

 - map

   用于绑定函数与参数，如：
   `list(map(fun,1,2))`
   注：参数须为列表形式

### copy & deepcopy

 a = list[1,2,3] , 如果 b = a , 则a和b指向的是同一内存空间，这时候如果用 b = copy.copy(a)  (因为copy是一个模块，所以需要先引入这个模块import copy), 则会开辟新的内存空间，如果输出 id(a) == id(b) ,则是false.但是需要注意这里的copy是浅复制(shallow copy),也就是说只会复制list中的一层到新的内存空间，如果list是这种形式：a = list[1,2,[3,4]],那么执行copy后前两个元素 会被复制到新的内存空间，而第三个元素则被共享，这时候就需要deepcopy发挥作用了，使用它则是完完全全的复制



### 冒号的用法

把冒号放在数组中，主要起到分片的作用，

```
>>> a = 'hello'
>>> a[1:3]
'el'
>>> a[::]
'hello'
>>> a[:]
'hello'
>>> a[:1]
'h'
>>> a[1:]
'ello'
>>> a[-1]
'o'
>>> 
```

