---
title: 谈一谈Java常量池之class常量池
date: 2019-09-04 14:08:30
updated: 2019-09-04 14:08:30
tags: class文件
categories: Java
---

Java常量池分为字符串常量池，class常量池和运行时常量池。本文主要讲class常量池。

#### 什么是class常量池

顾名思义，class常量池就是class文件中对应的常量池，那什么是class文件呢，就是将java文件编译得到的字节码文件，jvm所处理的也正是这种字节码文件。而class常量池，指的就是这个字节码文件中对应的一部分内容。



#### class文件结构

为了进一步了解class文件，我们准备了一小段代码：

```java
public class Test {
    public static void main(String[] args) {
        String s = "hello world" ;
    }
}
```

使用`javac`进行编译,在十六进制下查看，得到：

![ed66adec53a9775ef5de3e366e0054e.png](http://ww1.sinaimg.cn/large/006ImZ0Oly1g7tcyi4g70j30dk07e3yr.jpg)

这就是我们编译得到的class文件。

前四个字节是魔数（magic number）,紧接着的四个字节是版本号，然后就是class常量池的入口了。

下图展示了完整的class文件格式：

类型 | 名称 | 数量 | 说明 
:-: | :-: | :-: | :-: 
u4 | magic | 1 | 魔数 
u2 | minor_version | 1 | 次版本号 
u2 | major_version | 1 | 主版本号 
u2 | constant_pool_count | 1 | 常量池中常量数量 
cp_info | constant_pool | constant_pool_count-1 | 常量池中的常量 
u2 | access_flag | 1 | 访问标志，用于标识**当前的类**或者接口的访问信息，如是类还是接口，访问类型等 
u2 | this_class | 1 | 类索引，确定这个类的全限定名，具体存放在常量池中，根据这个索引去查找 
u2 | super_class | 1 | 父类索引，作用同上 
u2 | interfaces_count | 1 | 当前类所实现的接口数量 
u2 | interfaces | interfaces_count | 接口索引集合，描述当前类所实现的接口，根据索引在常量池中查找 
u2 | fields_count | 1 |  
field_info | fields | fields_count | 字段表集合，用于描述类或者接口中申明的变量 
u2 | methods_count | 1 |  
method_info | methods | methods_count | 方法表集合，用于描述类或者接口中申明的方法 
u2 | attributes_count | 1 |  
attribute_info | attributes | attributes_count |  

可以看出class文件中只有两种数据类型：无符号数和表，对于每个表，开头总会先说它的数量，然后表中的每个字段都有自己的结构。

下面这个表描述了常量池中都有哪些表

| 类型                             | 标志 | 描述                   |
| -------------------------------- | ---- | ---------------------- |
| CONSTANT_utf8_info               | 1    | UTF-8编码的字符串      |
| CONSTANT_Integer_info            | 3    | 整形字面量             |
| CONSTANT_Float_info              | 4    | 浮点型字面量           |
| CONSTANT_Long_info               | ５   | 长整型字面量           |
| CONSTANT_Double_info             | ６   | 双精度浮点型字面量     |
| CONSTANT_Class_info              | ７   | 类或接口的符号引用     |
| CONSTANT_String_info             | ８   | 字符串类型字面量       |
| CONSTANT_Fieldref_info           | ９   | 字段的符号引用         |
| CONSTANT_Methodref_info          | １０ | 类中方法的符号引用     |
| CONSTANT_InterfaceMethodref_info | １１ | 接口中方法的符号引用   |
| CONSTANT_NameAndType_info        | １２ | 字段或方法的符号引用   |
| CONSTANT_MothodType_info         | １６ | 标志方法类型           |
| CONSTANT_MethodHandle_info       | １５ | 表示方法句柄           |
| CONSTANT_InvokeDynamic_info      | １８ | 表示一个动态方法调用点 |

要注意的是每个表结构都是不同的，那么这样就有一个问题了，既然表结构都有不同，那么jvm自己又是怎么认识这些表项的呢。这里就有一点class文件设计的技巧了：虽然每个表都不同，但是我可以给每个表设置一个开始标志或者结束标志呀。class文件使用的是前一种，每个表项，都是以一个一字节的tag位作为开始的，如上表所示，每个tag代表了不同的表结构，然后根据tag去查找对应的表结构，按照对应的表结构来解析接下来的内容。

#### class常量池里有啥

看完class文件结构，再来细看一下class常量池，从上面的表格可以看出，常量池也是一个表，开头先说它的数量，即里面有几个常量，然后才是常量池的内容。

>常量池中每一项又是一个表，且不同的详，表结构不同
>
>

我们使用`javap`命令来简单明了的看下class常量池：

![359b2d3d056ad2361f3aeec265d5573.png](http://ww1.sinaimg.cn/large/006ImZ0Oly1g7tcz46t7jj30h907ndfv.jpg)

上图展示了class常量池中的内容，常量池中主要存放两种常量：字面量（Literal）和符号引用（Symbolic References）.字面量指的就是一些字符串啊数字啊之类的东西，而符号引用包括以下三类常量：

+ 类和接口的全限定名（这个常量在类索引或者父类索引中就会用到）
+ 字段的名称和描述符 （这个在字段表集合中会被用到）
+ 方法的名称和描述符（这个在方法表集合中会被用到）



#### class常量池有啥用

可以这么理解，class常量池相当于是一个资源库，在JVM运行时，它会把需要的资源从class文件中加载进内存。而这些就是类加载的内容了，我们会在后面的文章中讲到。