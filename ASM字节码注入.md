---
title: ASM字节码
date: 2020-08-30 13:00:00
categories: Java
tags: ASM
---

> 写这篇文章是因为在开水团实习的时候的一个项目用到了这个技术，在这里重新做下总结和梳理。

#### 什么是ASM

ASM是一个字节码操作框架，使用它可以动态地修改class文件，或者让类被加载到虚拟机之前修改一些行为。

#### ASM有什么用

一言以蔽之，AOP.  说到AOP，可能会想到Spring的JDK动态代理Proxy或者CGLIB.  这里JDK动态代理底层使用反射实现，众所周知反射的性能比较差。而CGLIB, 其实ASM和CGLIB是有关系的。

#### 怎么用

ASM提供了两种API：基于事件触发的Core API和基于对象的Tree API,  其区别就在于解析class文件的方式不同。下面会主要介绍Core API.

先列出主要知识点：

+ Core API有三个核心类：`ClassReader`,`ClassWriter`,`ClassVisitor`.
+ 整体使用了Visitor模式。

首先, `ClassReader`, 听名字就知道是用来读取Class文件的，当然并不是简单的读文件操作啦，它还会分析class文件的结构之类的，给它分析的明明白白的放到内存里。

然后，这个`ClassReader`会作为`Visitor`模式中的被访问者，开辟一个`accept`接口，放进来一个`ClassVisitor`，进行一些visit操作。这里需要注意的一个点是，`visit`方法里面具体的visit顺序ASM已经固定好了，我们只需要按照自己的需求去覆盖一些visit方法即可。它的一个时序图如下：

[![dbcyrR.png](https://s1.ax1x.com/2020/08/30/dbcyrR.png)](https://imgchr.com/i/dbcyrR)

而`ClassWriter`是`ClassVisitor`抽象类的一个实现类，剋把最终修改的字节码以byte数组的形式返回。

下面通过具体的例子来看下ASM是如何操作的。

先来一个测试类：

```java
public class Test1 {
    private int a;
    public void method(){}
}
```

再来一手`javac Test1.java`, 编译得到`Test1.class`.

现在开始ASM秀。

##### 1. 访问类的方法和字段

```java
package asm;

import jdk.internal.org.objectweb.asm.*;

import java.io.*;

import static jdk.internal.org.objectweb.asm.Opcodes.ASM5;

public class Main1 {
    public static void main(String[] args) {
        try {
            new Main1().visitMethodAndField();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    public void visitMethodAndField() throws IOException {
        //先读class文件
        byte[] classBytes = toByteArray("E:\\IntelliJidea\\workspace\\Test2\\src\\asm\\Test1.class");
        ClassReader cr = new ClassReader(classBytes);
        ClassWriter cw = new ClassWriter(0);
        ClassVisitor cv = new ClassVisitor(ASM5,cw) {
            @Override
            public FieldVisitor visitField(int i, String s, String s1, String s2, Object o) {
                System.out.println("field:"+s);
                return super.visitField(i, s, s1, s2, o);
            }

            @Override
            public MethodVisitor visitMethod(int i, String s, String s1, String s2, String[] strings) {
                System.out.println("method:"+s);
                return super.visitMethod(i, s, s1, s2, strings);
            }
        };
        cr.accept(cv, ClassReader.SKIP_CODE | ClassReader.SKIP_DEBUG);

    }

    public byte[] toByteArray(String filename) throws IOException {

        File f = new File(filename);
        if (!f.exists()) {
            throw new FileNotFoundException(filename);
        }

        ByteArrayOutputStream bos = new ByteArrayOutputStream((int) f.length());
        BufferedInputStream in = null;
        try {
            in = new BufferedInputStream(new FileInputStream(f));
            int buf_size = 1024;
            byte[] buffer = new byte[buf_size];
            int len = 0;
            while (-1 != (len = in.read(buffer, 0, buf_size))) {
                bos.write(buffer, 0, len);
            }
            return bos.toByteArray();
        } catch (IOException e) {
            e.printStackTrace();
            throw e;
        } finally {
            try {
                in.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
            bos.close();
        }
    }
}

```

输出：

```java
field:a
method:<init>
method:method
```

几个需要注意的点：

+ `ClassWriter`构造函数的参数，这里是一个标志位，可以用来标志是否修改这个类的默认行为，必须是0或者`COMPUTE_MAXS`或者`COMPUTE_FRAMES`:

  `COMPUTE_MAXS`: 一个标志位用来自动计算stack size的最大值和方法局部变量的最大值。如果这个标志位被设置，那么`visitMethod()`返回的对象`MethodVisitor`的方法`visitMaxs`的参数将会被忽略。

  `COMPUTE_FRAMES:` 用来计算stack map frames的标志位。

+ `ClassVisitor`的第一个参数，表示ASM版本。

+ 这个`init`是我们的构造方法。

+ 上面的代码也实锤了这个`ClassVisitor`是一个抽象类，我们实现它的时候，需要复写的方法有：

![dbfMcD.png](https://s1.ax1x.com/2020/08/30/dbfMcD.png)



##### 2. 添加字段或方法

```java
package asm;

import jdk.internal.org.objectweb.asm.*;

import java.io.File;
import java.io.IOException;

import static jdk.internal.org.objectweb.asm.Opcodes.ASM5;

public class Main2 {

    public void addField() throws IOException {
        byte[] classBytes = ByteUtil.toByteArray("E:\\IntelliJidea\\workspace\\Test2\\src\\asm\\Test1.class");
        ClassReader cr = new ClassReader(classBytes);
        ClassWriter cw = new ClassWriter(0);
        ClassVisitor cv = new ClassVisitor(ASM5,cw) {
            @Override
            public void visitEnd() {
                super.visitEnd();
                FieldVisitor fv = cv.visitField(Opcodes.ACC_PUBLIC,"str","Ljava/lang/String;",null,null);
                if(fv!=null)
                    fv.visitEnd();
            }
        };
        cr.accept(cv, ClassReader.SKIP_CODE | ClassReader.SKIP_DEBUG);
        byte[] classModifyed = cw.toByteArray();
        ByteUtil.byteArray2File(new File("E:\\IntelliJidea\\workspace\\Test2\\src\\asm\\ModifiedTest1.class"),classModifyed);
    }

    public static void main(String[] args) {
        try {
            new Main2().addField();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }


}

```

最后`javap ModifiedTest1.class`:

```java
public class asm.Test1 {
  public java.lang.String str;
  public asm.Test1();
  public void method();
}

```

几个需要注意的点：

这里我们添加方法是使用了`visiteEnd()`方法，从前面的时序图可以看出，它是最后一个`visit`方法，用以告诉ASM visit结束。

还需要注意的是这里使用了责任链模式。

新增方法操作类似，不再赘述。



##### 3. 删除方法和字段

删除操作比较简单，只需要在`visiteMethod`或者`visiteField`中返回null即可。

同样以`Test1.class`为例，我们删除方法`method`.

```java
package asm;

import jdk.internal.org.objectweb.asm.*;

import java.io.File;
import java.io.IOException;

import static jdk.internal.org.objectweb.asm.Opcodes.ASM5;

public class Main3 {

    public void removeMethod() throws IOException {
        byte[] classBytes = ByteUtil.toByteArray("E:\\IntelliJidea\\workspace\\Test2\\src\\asm\\Test1.class");
        ClassReader cr = new ClassReader(classBytes);
        ClassWriter cw = new ClassWriter(0);
        ClassVisitor cv = new ClassVisitor(ASM5,cw){
            @Override
            public MethodVisitor visitMethod(int i, String s, String s1, String s2, String[] strings) {
                if(s.equals("method"))
                    return null;
                return super.visitMethod(i, s, s1, s2, strings);
            }
        };
        cr.accept(cv, ClassReader.SKIP_CODE | ClassReader.SKIP_DEBUG);
        byte[] classModifyed = cw.toByteArray();
        ByteUtil.byteArray2File(new File("E:\\IntelliJidea\\workspace\\Test2\\src\\asm\\RemovedMethodTest1.class"),classModifyed);

    }

    public static void main(String[] args) {
        try {
            new Main3().removeMethod();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }


}

```

通过`javap`查看，发现已删除。



##### 4. 修改方法内容

