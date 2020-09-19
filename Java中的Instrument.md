---
title: Java中的Instrumentation
date: 2020-09-04 22:00:00
categories: Java
tags: Instrument
---

#### 前言

在[之前]([http://123.56.245.109/2020/08/30/Blog/ASM%E5%AD%97%E8%8A%82%E7%A0%81%E6%B3%A8%E5%85%A5/](http://123.56.245.109/2020/08/30/Blog/ASM字节码注入/))的文章里我们介绍了ASM字节码框架，使用它可以动态的修改class文件。但是仔细一想，你会发现仅仅ASM并不能真正用于生产，为什么？假如你已经有一个在运行的系统了，现在想要做一些字节码修改的动作，难道我们要去修改源代码吗？麻烦不说，而且污染了本来的系统。



所以我们就考虑，有没有什么方法，可以实现动态的无污染的织入，这就要引入今天的主角，Instrument了。



#### 正文

Instrumentation是`Javaagent`的一种具体实现，那`javaagent`又是什么？如果你在终端里输入`java`(当然前提是你已经安装了jdk),  你会看到这么几个参数：

![wA3cNR.png](https://s1.ax1x.com/2020/09/04/wA3cNR.png)

其中，`-javaagent`就是我们所说的，jdk提供的`Instrument`允许我们在jvm启动或者运行时，动态地拦截要加载的类，并对其进行修改。无论是启动时还是运行时，其大致原理都是把我们的修改代码封装成一个Jar包，然后想办法让目标jvm进程加载。

##### instrumentation介绍

先上一张图：

![wIAOln.png](https://s1.ax1x.com/2020/09/19/wIAOln.png)

instrumentation是什么？jdk中的一个接口，我们看看这个接口提供了哪些方法：

![wIERNF.png](https://s1.ax1x.com/2020/09/19/wIERNF.png)

这里我也框出来了常用的几个方法，可以看到这几个方法基本都和`ClassFileTransformer`这个接口有关，那我们继续看下`ClassFileTransformer`的介绍。

其实从名字可以大概看出，`ClassFileTransformer`是对class文件进行转换的，再通俗点，就是用来修改字节码的。`ClassFileTransformer`这个接口只有一个方法`transform`:

```java
byte[]
    transform(  ClassLoader         loader,
                String              className,
                Class<?>            classBeingRedefined,
                ProtectionDomain    protectionDomain,
                byte[]              classfileBuffer)
```

其中`loader`参数是加载这个类的类加载器，`classfileBuffer`就是载入内存中的class文件。可以看到这个方法返回值是个字节数组，如果返回null, 则表示对class文件不做处理，否则就用返回的字节数组代替原来的类。



当我们使用`addTransformer`给`instrumentation`添加`ClassFileTransformer`后，后续所有JVM加载类的时候都会被`ClassFileTransformer`的`transform`方法拦截。



上面大概介绍了`instrumentation`和`ClassFileTransformer`，下面的部分会介绍这两个东西如何结合起来使用。如上文所说，`instrumentation`的原理大概是：**把我们的修改代码封装成一个Jar包（即agent），然后想办法让目标jvm进程加载。**那就涉及到一个问题：目标jvm何时加载？java agent提供了两种手段，分别是在jvm启动时加载和jvm运行时加载。



##### JVM启动时加载instrument agent

主要用到了`premain()`方法， 从名字也可以看出，premain其实就是在main函数之前执行，所以也就是会在main函数执行之前拦截类的加载，并做一些改造，premain函数如下：

```java
 public static void premain(String agentArgs, Instrumentation inst)
```

其中第一个参数agentArgs是agent启动时的参数，第二个参数就是我们的主角，instrumentation. 一般的一个操作流程是使用instrumentation的addTransformer方法添加一个`ClassFileTransformer`, 而这个`ClassFileTransformer`里面的`transform`方法一般就是我们施展拳脚的地方，在这里可以对字节码进行修改等操作。下面的代码实现了一个简单的Agent

```java
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;

public class PreMainAgent {
    public static void premain(String agentArgs, Instrumentation inst){
        System.out.println("agent args: "+agentArgs);
        inst.addTransformer(new MyTransformer(),true);
    }

    static class MyTransformer implements ClassFileTransformer{

        @Override
        public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined, ProtectionDomain protectionDomain, byte[] classfileBuffer) throws IllegalClassFormatException {
            System.out.println("premain load class: "+className);
            return classfileBuffer;
        }
    }
}

```

然后我们需要把这个agent打包成jar包，这里我使用maven打包，通过配置pom.xml文件，核心内容如下：

```java
 <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.1.0</version>
        <configuration>
            <archive>
                <!--自动添加META-INF/MANIFEST.MF -->
                <manifest>
                    <addClasspath>true</addClasspath>
                </manifest>
                <manifestEntries>
                    <Premain-Class>PreMainAgent</Premain-Class>
                    <Agent-Class>PreMainAgent</Agent-Class>
                    <Can-Redefine-Classes>true</Can-Redefine-Classes>
                    <Can-Retransform-Classes>true</Can-Retransform-Classes>
                </manifestEntries>
            </archive>
        </configuration>
    </plugin>
```

使用`mvn package`打包成Jar包，打包后的文件在/target目录下。

完成上述操作后，我们再单独建一个项目，来测试我们的agent,

```
public class Test {
    public static void main(String[] args) {
        System.out.println("main start");
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("main end");
    }
}
```

如果是在idea里运行的话，我们需要在`add configuration`里面配置一下：

![wIK6xg.png](https://s1.ax1x.com/2020/09/19/wIK6xg.png)

主要就是关注下这个javaagent参数就行，然后运行，走起，输出如下：

```java
agent args: null
premain load class: java/util/concurrent/ConcurrentHashMap$ForwardingNode
premain load class: java/util/jar/Attributes
premain load class: java/util/jar/Manifest$FastInputStream
...(此处省略若干)
main start
premain load class: java/net/URI
...（此处省略若干）
premain load class: sun/nio/cs/US_ASCII$Decoder
main end
premain load class: java/lang/Shutdown
premain load class: java/lang/Shutdown$Lock

Process finished with exit code 0

```

至此，流程走通。



那么这种jvm启动时就加载agent的方式有没有什么问题呢？首先好处肯定是有的，因为此时agent加载的时候大部分类还没加载，这个时候可以实现对新加载的类的进行字节码修改。但是！如果premain方法执行失败或者抛异常，那么jvm进程会被终止，这就有点难以接受了。（这段话摘自占小狼的博客）

![wIQcHs.png](https://s1.ax1x.com/2020/09/19/wIQcHs.png)

因此，在jdk1.6中，又提出了另一种方法。



##### JVM运行时加载instrument agent

主要用到了`agentmain()`方法，

##### instrument原理



##### 使用instrument有什么问题

TODO:

+ 类隔离
+ 反射