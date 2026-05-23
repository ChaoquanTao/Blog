---
title: 从建造者模式看自限定泛型
categories: Java
tags: 泛型
date: 2022-05-22 21:00:00
---

### 基本用法

Java提供了泛型，可以在编译期做一些类型检查。以集合类`List`为例，如果我们这样用：

```java
public class GenericApp {
    public static void main(String[] args) {
        List list = new ArrayList();
        list.add(1);
        list.add("a");
      
       for (Object value : list) {
            System.out.println((int)value);
        }
    }
}

```

虽然也不会报错，但是由于这个list什么类型都能添加，在运行期如果要获取其中元素并做一些强制类型转换的话，一定会报错。



有了泛型，可以帮助我们在编译器就发现程序的一些问题：

```java
public class GenericApp {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add("a");
    }
}
```

上述代码在编译器就会报错，因为泛型限制了当前`list`只能添加整型。



需要注意的是，泛型只存在于编译期，编译完成之后会进行类型擦除, 将上述代码编译后再反编译，你会看到list的元素类型其实是Object

![image](http://tvax2.sinaimg.cn/large/006ImZ0Ogy1h2p4j0ms3dj31ak0ey784.jpg)

当然了，如果使用的是有上限通配符的泛型，那反编译后泛型会被替换成上界的类型。



### 自限定类型

在Java泛型中，有一种比较奇特的用法，叫自限定泛型（Self Bounded Generic）。写法是这样的:

```java
class SelfBounded<T extends SelfBounded<T>>{}
```

这种自限定泛型初次看起来可能会比较懵逼，SelfBounded接收的一个泛型参数，并且这个泛型的上界是它自己？看起来有点递归调用的意思？

先说结论：

> 它的作用常常体现在**继承**中，用于限定子类中泛型的类型上界，当父类的某个方法想要返回的子类的类型，可以采用自限定类型这种方式

下面我们通过一个建造者模式的例子来加深对它的理解。



#### 实现一个建造者模式

有一个披萨类，是个抽象类，具体实现有芝士披萨和牛肉披萨，这两种披萨都有一些共有特征，比如都可以往上面加一些小料（topping），同时各自又有一些特性，比如芝士披萨需要指定尺寸，而牛肉披萨需要指定是否加酱料。

我们使用`Builder`模式来实现这个需求，首先将共有属性抽象到父`Builder`里

```java
public abstract class Pizza {

    public static abstract class Builder {
        abstract Pizza build();

        public Builder addTopping(Topping topping){
            System.out.println("topping added");
            return this;
        }
    }
}
```



芝士披萨

```java
public class CheesePizza extends Pizza {
    private String size;
    
    public CheesePizza(){}
    
    public CheesePizza(CheesePizzaBuilder builder){
        CheesePizza cheesePizza = new CheesePizza();
        cheesePizza.size = builder.size;
    }

    public static Builder builder(){
        return new CheesePizzaBuilder();
    }


    public static class CheesePizzaBuilder extends Builder {
        private String size;

        @Override
        Pizza build() {
            return new CheesePizza(this);
        }

        public CheesePizzaBuilder size(String size){
            this.size = size;
            return this;
        }
    }
}
```



测试类：

```java
public class PizzaApp {
    public static void main(String[] args) {
        Pizza cheesePizza = CheesePizza.builder().size("small").addTopping(new Topping()).build();
    }
}
```

这时候问题就出现了，`CheesePizza`的`builder()`方法返回`Builder`类，`Builder`类是没有`size`方法的，因为`size`是子类`CheesePizzaBuilder`特有的。

![image](http://tvax4.sinaimg.cn/large/006ImZ0Ogy1h2pltbno0sj306v04d3yj.jpg)

这好办，我把`CheesePizza`的`builder()`方法返回具体子类不就好了？也不是不能用，但是不优雅，这个改动意味着每次`build`时必选先调用子类`Builder`中的特有方法，如`size`, 然后才能调用父`Builder`的`addTopping`方法，这样好吗？这样不好，很不优雅。



#### 带泛型的建造者模式

冷静分析上面的问题，你就会发现根因在于父`Builder`的`addTopping`方法返回的类型和子`Builder`的`size`方法返回的类型不一致。理论上，既然是子`Builder`进行`build`, 我们自然希望子`Builder`里的每个方法都能返回子`Builder`，这样既能调用子`Builder`自己的独有的方法，也能调用父`Builder`的方法。所以，我们可以这么改造:

`Pizza`类

```java
public abstract class Pizza {

    public static abstract class Builder<T> {
        public Builder(){}

        abstract Pizza build();

        public T addTopping(Topping topping){ // 这里做了改变
            System.out.println("topping added");
            return self();
        }

        protected abstract T self();
    }
}
```



`CheesePizza`类

```java
public class CheesePizza extends Pizza {
    ...
    public static class CheesePizzaBuilder extends Builder<CheesePizzaBuilder> {
        private String size;

        public CheesePizzaBuilder(){}

        @Override
        Pizza build() {
            return new CheesePizza(this);
        }

        @Override
        protected CheesePizzaBuilder self() { //这里做了改变
            return this;
        }

        public CheesePizzaBuilder size(String size){
            this.size = size;
            return this;
        }
    }
}
```

考虑到`Builder`中的每个具体的`build`方法（如`size`）都应该返回具体的`Builder`, 我们为父`Builder`加入了泛型，该泛型表示的是具体的`Builder`, 并在`addTopping`后返回该泛型。如此一来，我们就可以快乐的`build`了。



##### 还能再优化吗

从上面的讨论可以知道，我们引入的泛型其实是有上界的，泛型`T`一定是继承自`Builder`的，所以我们可以更精简一下：

```java
public abstract class Pizza {

    public static abstract class Builder<T extends Builder<T>> { //这里做了修改
        public Builder(){}

        abstract Pizza build();

        public T addTopping(Topping topping){
            System.out.println("topping added");
            return self();
        }

        protected abstract T self();
    }
}
```

子类中的写法保持不变：

```java
public static class CheesePizzaBuilder extends Builder<CheesePizzaBuilder> {}
```



那这时候就出现了我们前文提到的自限定泛型，它在这里的语义是：传给`Builder`的泛型一定是一个继承自`Builder`的类型。这么做有什么好处呢？它可以在编译器尽可能地帮我们检查出一些错误，如果这时候子类的`Builder`接收了一个非继承自`Builder`的类型，那么编译器就会直接报错。



#### 总结一下

这篇文章主要介绍了自限定泛型，并通过建造者模式加深了对它的理解。自限定泛型，常用于传入的类型参数需要和类本身继承自同一父类的场景，说白了，它的作用常常体现在**继承**中，用于限定子类中泛型的类型上界，**当父类的某个方法想要返回的子类的类型**，可以采用自限定类型这种方式，加强编译期校验。

如果你要问只用个泛型，不要自我限定行不行，答案是也行，只不过前者更“细”，前者会在编译器做更多的类型校验。















