---
title: Java泛型
date: 2019-10-31 09:40:05
updated: 2019-10-31 09:40:05
tags: 泛型
categories: Java
---

### 为什么要有泛型

它的一个主要目标是将运行时才能发现的错误转移到编译期。

### 泛型是什么

所谓泛型，就是将类型参数化，即把类型也作为一种参数。如何做到这点呢？通过解耦类或方法与所使用的类型之间的约束。

### 表面使用

#### 泛型类

```java
public class GenericsDemo <T> {
    private T var ;

    public void setVar(T v){
        var = v ;
    }

    public T getVar(){
        return var;
    }

    public static void main(String[] args) {
        GenericsDemo demo1 = new GenericsDemo();
        demo1.setVar("string");
        System.out.println(demo1.getVar());
        demo1.setVar(1);
        System.out.println(demo1.getVar());

        GenericsDemo<Integer> demo2 = new GenericsDemo<Integer>() ;
//        demo2.setVar("stirng");
        demo2.setVar(1);
        System.out.println(demo2.getVar());
    }

}

```

可以看出，虽然我们定义了泛型类，但是在使用它的时候是可以不传入泛型实参的，如果不传， 在泛型类中使用泛型的方法或成员变量定义的类型可以为任何的类型。 

#### 泛型接口

定义方式和泛型类相似

```java
public interface Generator<T> {
    T next() ;
}
```

需要注意的是当有个类实现这个泛型接口时的操作

1. 实现类和接口都没写泛型参数

   ```java
   public class FruitGenerator implements Generator {
   
       @Override
       public Object next() {
           return null;
       }
   }
   ```

   

2. 如果接口写了泛型参数，但是没有传入实参，则实现类也必须写上，不然会报错

   ```java
   public class FruitGenerator<T> implements Generator<T> {
   
       @Override
       public T next() {
           return null;
       }
   }
   ```

   

3. 如果接口写了泛型参数，且传入了实参，那么使用接口中泛型的地方都要换成传入的实参类型，但是这并不影响给这个实现类添加自己的泛型。

   ```java
   public class FruitGenerator<T> implements Generator<String> {
       private T  fruitVar ;
   
       @Override
       public String next() {
           return null;
       }
   }
   ```

   

#### 泛型方法

```java
public <T> T getData(T data){
    return data; 
}
```



#### 泛型通配符

通配符就是`?`,是一个**泛型实参**，以一个泛型类作为形参为例：

```java
import java.util.*;

public class Test {

    public static void main(String[] args) {
        List<String> name = new ArrayList<String>();
        List<Integer> age = new ArrayList<Integer>();
        List<Number> number = new ArrayList<Number>();

        name.add("icon");
        age.add(18);
        number.add(314);

        getData(name);
        getData(age);
        getData(number);

    }

    public static void getData(List<?> data) {
        System.out.println("data :" + data.get(0));
    }
}
```

我们在main里定义了三个list,每个list装入的类型都不一样，现在想用一个`getData()`方法来获取这三个list里面的值，这里的关键就在于`getData()`的形参怎么写了，如果给作为形参的list传入泛型实参，比如String,那么age和number这两个list就不能作为实参传进来了。怎么办呢？使用通配符，给形参的list加了通配符之后，就意味着海纳百川，不管实参是什么样的list都能传进来。

其实你也会发现，如果给形参list不加泛型也可以，因为到头来泛型都会被擦除掉。需要注意的是，这里的通配符`List<?>`，从逻辑上讲，它应该是其他`List<具体类型实参>`的父类。

当然了，通常也不会单独拿出来一个通配符来使用的，它一般都是配合上界或下界一起使用的。

### 内部原理

​	泛型只在编译器有效，在编译过程中，正确检验泛型结果后，**会将泛型相关信息擦除 ， 并且在对象进入和离开方法的边界处添加类型检查和类型转换的方法 **。



