---
title: java学习笔记
date: 2018-03-14 14:57:25
categories: java
tags: java基础
---

### 继承与覆盖

+ 当通过一个父类的引用指向一个子类的对象后，将只能通过这个父类的引用访问那些父类中定义了的属性和方法。Java平台的执行规则是： **在编译的时候，可以调用哪些方法，访问哪些属性，是引用类型决定的；在程序运行的时候，具体访问哪个属性，执行哪个方法，是对象的类型决定的。**

  也就是说，如果子类中有这个方法f1而父类中没有，那么指向子类的父类引用是不能调用子类的这个方法f1的,只有当子类和父类拥有一样的方法（继承或者覆盖得到）时，指向子类的父类引用才可以调用这个方法，并且调用的是子类的方法。

+ 使用覆盖的几条规则
  + 子类必须把这个方法从父类中继承过来，这个与方法的访问控制符有关系；
  + 子类方法的访问控制符的访问权限应比父类中的更宽松或者相同
  + 子类方法返回值类型必须能赋值给父类方法返回值类型

+ 当继承被引入到重载的参数中时，决定函数重载的哪个方法被调用的是实参。这里的实参指的是引用的类型，而不是引用指向的对象的类型

+ 对于静态方法，Java会根据引用的类型而非引用指向的对象的类型来决定调用哪个静态方法

+ 变量的覆盖，变量的值取决于引用类型而不是引用指向的对象类型

### 接口     

+ 程序使用接口可以很好的避免对外部类的依赖性，因为对外只需要一个接口，任何实现了该接口的对象都可以作为参数传递过去。


+ 保存接口的文件名也要和接口名相同

+ ```
  public abstract insterface 接口名{
      public static final int r =1;
      public abstract 返回值 方法名();
  }

  ```
  也可以简单写为

  ```
  public interface 接口名{
      int r =1 ;
      返回值 方法名()
  }
  ```
### 抽象类

+ 接口是抽象的，必须通过类实现它才能用，除了抽象的接口之外，还有抽象的类，其声明方法类似

  ```
  public abstract class Person{
      private String name ;
      public Person(String name){
  		this.name = name ;
  	}
  	...
  	public abstract void introduceSelf();
  }
  ```

  + 抽象类首先是一个类
  + 抽象类中可以没有抽象方法
  + 一个类如果继承了抽象类，要么自己实现父类中的抽象方法，要么将自己也声明为抽象类
  + 类也可以通过接口来获得抽象方法

+ 为什么要有抽象类

  + 从语法上讲，是为了让子类强制覆盖父类中的某些类（有点像c++中的虚函数？）
  + 从业务上讲，如果有一个父类的方法不应该被调用（因为调用它没有实际意义的情况），此时应该用抽象类。

### 内部类

+ 成员内部类

  定义在类中的类，与类中其他成员是同一重量级

  + 静态成员内部类
    + 是类范畴中的元素，其中不含指向外部类对象的元素，所以不能在静态成员内部类中使用外部类中的非静态成员
    + 静态成员只能访问静态成员
  + 非静态成员内部类
    + 内部类可以访问外部类的所有属性和方法，因为它们本来就是同一级别的
    + 内部类中定义了一个指向外部类的引用
    + 外部类的代码也可以访问内部类的对象中的变量

+ 局部内部类

  定义在类中方法中的类，与方法中的局部变量是同一级别的。

  可以使用其所在方法中的final变量

  不能包含静态成员

  + 静态方法中的局部内部类
    + 受静态方法限制，只能访问静态变量和方法中的`final`变量
  + 非静态方法中的局部内部类
    + 隐含有指向外部类的引用

+ 匿名内部类

  + 没有名字

  + 不能添加构造方法

  + 没有修饰符

  + 通过接口来使用匿名类

  + 通过抽象类来使用匿名类

 ### 

### Java异常

+ 异常抛出

+ 异常传递

  + 从某个方法中的某个`throw`语句传递到调用这个方法的地方，一直到`main`方法
  + 异常必须被传递出去或者处理掉
  + 抛出异常位置后面的代码不会被执行

+ 异常处理

  ```
  try{
      //可能会抛出异常的代码
  }catch(异常类型1 异常引用1){ //如果抛出的异常与此处的异常类型匹配，用异常引用指向try中的异常实例
  	//处理异常
  }catch(异常类型2 异常引用2){
      
  }finally{
      /*`finally`语句中的代码无论如何都会被执行，无论上面的catch过程是匹配到异常处理掉了还是将异常
         抛出，都会执行finally块，如果异常被处理掉了，那么接下来执行finally,如果异常没有被匹配，那么
         先执行finally,再抛出异常 */
      /*finally语句通常不被遇到，一种典型使用情况是用来释放资源*/
  }

  ```

  ```
  try{
  }finally{
      
  }
  ```

  关于异常的捕获，我们可以做的不仅仅是将其打印输出，也可以在`catch`语句里对异常进行修改

### Java多线程

+ 多线程

  ```
  public class UseRunnable {
      public static void main(String args[]) throws InterruptedException {
          //显示主线程的名字
          System.out.println("current thread name is: "+Thread.currentThread().getName());

          System.out.println("program will be executed after 5000 ms");
          //这里的Thread方法和currentThread方法一样，都是静态方法
          Thread.sleep(5000);

          MyRunnable runnable = new MyRunnable();
          Thread thread = new Thread(runnable);
          //这里也可以通过匿名类的方式实现Runnable
          /*
          * Thread thread = new Thread(new Runnable(){
          *       public void run(){
          *           System.out.println("this is my runnable in anther way")
          *       }
          * })
          * */

          thread.start();

          MyThread mythread = new MyThread();
          mythread.start();
      }
  }

  /*methond 1*/
  class MyRunnable implements Runnable{   //通过继承接口的方式来实现线程
      @Override
      public void run() {
          System.out.println("this is my runnable");
      }
  }

  /*其实我们也可以通过继承Thread类来实现
  *这样做有个显著的不好，java中类是单继承的，如果为了使用线程而去继承Thread类，
  * 那将不能继承其他类，所以还是实现接口的方式好一些*/

  /*method 2*/
  class MyThread extends  Thread{ //Thread类有一个参数为空的构造方法
      public void run(){
          System.out.println("this is my thread");
      }

  ```

  ​

+ synchronized关键字

  当某个方法只允许同一时间只被一个线程访问时，可以用synchronized关键字来修饰这个方法

  + `public synchronized static void func()`

    当synchronized修饰静态方法时，是类范畴内的同步。也就是说，加入某类有多个静态同步方法，那么当其中一个方法被第一个线程访问时，当第二个线程试图访问这个类中的任意一个静态同步方法时，它都会被挂起。但是不同类中的静态方法互不影响。

  + `public synchronized void func()`

    对象范畴的同步。也就是说，当某个线程访问该对象中的非静态同步方法时，如果另一线程试图访问同一个对象中的任意非静态同步方法时，它将被挂起

  + ​

  ​

+ wait()和notify()

  ```
  package top.iamnewbie;

  public class UseWaitAndNotify {
      public static void main(String[] args) {
          Object obj = new Object();
          Waiting waiting = new Waiting(obj);
          Notifier notifier = new Notifier(obj); //注意,这里使用同一对象初始化Waiting和Notifier

          //因为Waiting和Notifier都实现了Runnable接口，所以可以用他们来初始化Thread类
          Thread thread1 = new Thread(waiting,"线程1");
          Thread thread2 = new Thread(notifier,"线程2");
    
          //通过start函数来触发Runnable的run函数
          thread1.start();
          thread2.start();
      }
  }

  //它实现了Runnable接口，在Thread中将这个类的实例作为参数就可以创建线程
  class Waiting implements Runnable{
      private Object waitObj ;

      public Waiting(Object obj) {
          this.waitObj = obj;
      }
    
      @Override
      public void run() {
          System.out.println(Thread.currentThread().getName()+"将被挂起");
          synchronized (waitObj){
              try {
                  waitObj.wait();
              } catch (InterruptedException e) {
                  e.printStackTrace();
              }
    
          }
          System.out.println(Thread.currentThread().getName()+"被唤醒");
      }
  }

  class  Notifier implements Runnable{
      private Object notifyObj ;

      public Notifier(Object notifyObj) {
          this.notifyObj = notifyObj;
      }
    
      @Override
      public void run() {
          System.out.println("开始notify线程");
          try {
              Thread.sleep(5000);
          } catch (InterruptedException e) {
              e.printStackTrace();
          }
    
          synchronized (notifyObj){
              notifyObj.notify();
          }
          System.out.println("notify线程结束");
    
      }
  }
  ```

  同步代码块，语法如下

  ```
  synchronized(对象引用){
  	同步代码
  }
  ```

  如果有多个线程同时访问同步代码块，而且同步代码块中对象的引用指向的是同一对象，那么就只有一个线程能进入代码块执行。上面的例子中，两个类中都写了同步代码块，在执行的时候，可以发现，用的是同一个对象实例来初始化`Waiting`和`Notifier`,也就是说虽然同步代码块是在两个对象中，但是同步代码块中对象的引用指向的是同一个实例（这也是将两个线程联系起来的关键）。进入代码块时，给对象加锁，执行wait()方法时，去掉锁，此时线程1被挂起，同时`obj`对象也没有被加锁，这时候线程2就可以访问这个代码块了，使用过synchronized先加锁，执行notify后解锁

  通篇来看，正是因为初始化两个对象用了同一对象，这才让两个线程建立了关联。

### IO

来一张输入流和输出流的类层次图

![](https://ws1.sinaimg.cn/large/005UcYzagy1ftkxcjom5ij30n50nd45y.jpg)

+ 关于几个类

  + File类

    文件和文件夹都用File类来表示

  + `InputStream`和`OutputStream`

    Java中的输入流和输出流

  + `Writer`

    Abstract class for writing to character streams. The only methods that a subclass must implement are write(char[], int, int), flush(), and close(). Most subclasses, however, will override some of the methods defined here in order to provide higher efficiency, additional functionality, or both.

  + `PrintWriter`

    `Writer`的子类，将对象格式化打印到文件中

  + ​

+ 读写数据

  + 向文件中写数据（假设文件已存在）

    + `PrintWriter`

    ```
    PrintWriter printWriter = new PrintWriter(new FileOutputStream(filename));
    printWriter.write("write something");
    printWriter.close();
    ```

    	`PrintWriter()`接受的参数类型主要有

    ![](https://ws1.sinaimg.cn/large/005UcYzagy1fpvrurtcrcj30qf0gg0ts.jpg)

    这里看上去不关输出流什么事，但其实它已经蕴含在`PrintWriter`类里面了.

    + `BufferdWriter`

      ```
      BufferedWriter out=new BufferedWriter(new FileWriter(fileName));
      out.write("Hello BufferWriter");
      out.close();
      ```

      `BufferdWriter()`接受的参数类型

      ![](https://ws1.sinaimg.cn/large/005UcYzagy1fpvrwofyqzj30nr054t8t.jpg)

    + `FileWriter`

      ```
      FileWriter writer=new FileWriter(fileName,true);
      writer.write("write something");
      writer.close();
      ```

      `FileWriter()`接受的参数类型

      ![](https://ws1.sinaimg.cn/large/005UcYzagy1fpvryi3ajmj30un0a8gm4.jpg)

      ​

      ​

      总结一下，写文件的话一般用的就是Writer的子类，

  + 读文件

    ```
     fileReader = new FileReader(file1);
     bufferedReader1 = new BufferedReader(fileReader);
     while((content1=bufferedReader1.readLine()) != null){
            System.out.println(content1);
     }
     fileReader.close();
    ```

    ​

### Swing

+ 基本流程

  创建一个窗口`JFrame`,进行基础设置，获得Container对象，向里面添加其他组件·



### Java Collection Framework

![](https://ws1.sinaimg.cn/large/005UcYzagy1fv5utslrw5j30lr0ijjui.jpg)

#### 相互区别

`ArrayList`底层实现是数组，可以存储null, 没有进行同步措施，不是线程安全的，当数组容量不够时，需要扩容。



`LinkedList`同时实现了List和Deque接口，所以它既可以看作一个顺序容器，又可以看作队列，又可以看作栈。（我对Deque的理解就是双端队列Double end queue）,它的底层实现是一个双向链表。为了效率`LinkedList`同样没有实现同步，如果多个线程并发访问，可以用`Collection.synchronizedList()`方法对其进行包装。



Stack 类继承自Vector, Java已不推荐使用Stack, 而是推荐使用`ArrayDeque`（继承自Deque）,`ArrayDeque`不是线程安全的，需要手动同步，其中不允许放入null. `ArrayDeque`底层也是数组实现，作为双端队列，肯定需要判断队列是否满了，如果满了要进行扩容操作，虽然这个工作API内部就完成了，但是在看它的实现时，我的表情是这样的，![](https://ws1.sinaimg.cn/large/005UcYzagy1fv5x4qelgdj305n064dfs.jpg)

数据结构书上讲的判断队列满的方法是取模，这里它是这么实现的

```
public void addFirst(E e) {
    if (e == null)//不允许放入null
        throw new NullPointerException();
    elements[head = (head - 1) & (elements.length - 1)] = e;//2.下标是否越界
    if (head == tail)//1.空间是否够用
        doubleCapacity();//扩容
}
```

通过位运算来实现的，因为Array每次扩容都是按倍数增长，所以它的容量是2的次幂，那么用head-1来和length-1进行与运算，就可以求模了，想想通过位运算来求模肯定会节省很多时间啊。真的是![](https://ws1.sinaimg.cn/large/005UcYzagy1fv5x90s09xj308o08c3yk.jpg)



##### Vector 和 `ArrayList`

1. vector 是线程同步的，所以它也是线程安全的，而 `ArrayList` 是线程异步的，是不安全的。如果不考虑到线程的安全因素，一般用 `ArrayList` 效率比较高。

2. 如果集合中的元素的数目大于目前集合数组的长度时，vector 增长率为目前数组长度的100%,而 arraylist 增长率为目前数组长度的50%.如过在集合中使用数据量比较大的数据，用 vector 有一定的优势。

3. 如果查找一个指定位置的数据，vector 和 arraylist 使用的时间是相同的，都是0(1),这个时候使用 vector 和 arraylist 都可以。而如果移动一个指定位置的数据花费的时间为 0(n-i)n 为总长度，这个时候就应该考虑到使用 linklist,因为它移动一个指定位置的数据所花费的时间为 0(1),而查询一个指定位置的数据时花费的时间为 0(i)。

ArrayList 和 Vector 是采用数组方式存储数据，此数组元素数大于实际存储的数据以便增加和插入元素，都允许直接序号索引元素，但是插入数据要设计到数组元素移动 等内存操作，所以索引数据快插入数据慢，Vector 由于使用了 synchronized 方法（线程安全）所以性能上比ArrayList 要差，LinkedList 使用双向链表实现存储，按序号索引数据需要进行向前或向后遍历，但是插入数据时只需要记录本项的前后项即可，所以插入数度较快！

##### arraylist 和 linkedlist

1. ArrayList 是实现了基于动态数组的数据结构，LinkedList 基于链表的数据结构。 2.对于随机访问 get 和 set，ArrayList 觉得优于 LinkedList，因为 LinkedList 要移动指针。 3.对于新增和删除操作 add 和 remove，LinedList 比较占优势，因为 ArrayList 要移动数据。 这一点要看实际情况的。若只对单条数据插入或删除，ArrayList 的速度反而优于 LinkedList。但若是批量随机的插入删除数据，LinkedList 的速度大大优于 ArrayList. 因为 ArrayList 每插入一条数据，要移动插入点及之后的所有数据。

#### HashMap



### Java自动拆装箱

==比较的是对象应用，equals比较的是值

在Java 5中，在Integer的操作上引入了一个新功能来节省内存和提高性能。整型对象通过使用相同的对象引用实现了缓存和重用。

> 适用于整数值区间-128 至 +127。
>
>
>
> 只适用于自动装箱。使用构造函数创建对象不适用。



### Java中的String

#### 关于字符串常量池

考虑以下代码

```
String s1 = "taochq" ; （1）
String s2 = new String("taochq") ; （2）
String s3 = new String("taochq").intern() ; （3）
```

JVM为了提高性能和减少内存开销，在实例化字符串常量的时候进行了一些优化，字符串类维护了一个字符串常量池。

执行代码（1）的时候，jvm会检查常量池中有没有“taochq”这个字符串，没有则创建并返回引用（注意这个引用是指向字符串常量池的），有的话则直接返回它的引用。

执行（2）的时候，s2是在栈上，堆上会创建一个String对象，它指向字符串常量池中的"taochq",所以s2指向的是堆上的一个地址。

执行（3）的时候，因为调用了intern()方法，JVM会检查常量池中是否有相同的的字符串，如果有则直接返回引用（注意这里的引用也是指向字符串常量池的），如果没有则将字符串放入常量池并返回它的引用。



看到这里，你可能会觉得，代码（1）和代码（3）实现的效果差不多啊，为什么还要有`intern()`这个方法呢，其实是有区别的。要知道，常量池保存的是**已确定**的字符串，什么意思呢？就是说很多时候我们在程序中用到的字符串都是在编译器无法确定的，只有在运行时才知道这个字符串确切是啥，对于这种情况，使用intern进行定义，每次程序执行到这里的时候直接返回常量池中的字符串，可以减少堆上对象的创建。

而对于那种在编译器就能确定的常量，我们当然可以使用双引号字符串进行定义。



#### + 号拼接字符串

在java中，`+`并不是运算符重载，java是不支持运算符重载的，这只是java的一个语法糖，它的底层仍然是`stringbuilder`的`apend`操作。



#### concat

借助字符数组，最终还是new了一个新的String对象



##### `String` `StringBuffer` `StringBuilder`

它们内部都是通过数组来实现的，不同的是，String的内部数组是final修饰的，是不可改变的，`StringBuffer`和`StringBuilder`内部数组是可修改的。它俩有一个变量来指示数组中已经被占用的元素个数。它们的append方法是通过数组来实现的。

`StringBuffer`和`StringBuilder`最大的区别是`StringBuffer`是线程安全的。



#### 总结

如果在循环体内，使用`+`进行字符串拼接的话，会频繁的创建`StringBuilder`对象，不如直接用`StringBuilder`拼接来的快。



#### String的比较

`==`比较的事两个对象的引用是否相同，即两个对象是否是同一个对象而只是引用不同而已。

`equals()`方法比较的是字符串的值。



### `foreach`循环中的remove/add操作

最近在项目中使用`foreach`并且在里面对元素进行remove时常常发生并发修改异常,特此记录。

```
java.util.ConcurrentModificationException
```

#### 问题场景

```
List<String> list = new ArrayList<String>(){{
    add("this is");
    add("a foreach");
    add("example");
}}

for(String str: list){
    if(str.equals("a foreach)){
        list.remove(str);
    }
}
```

执行以上代码时，就会产生上述异常。

```
Exception in thread "main" java.util.ConcurrentModificationException
	at java.base/java.util.ArrayList$Itr.checkForComodification(ArrayList.java:937)
	at java.base/java.util.ArrayList$Itr.next(ArrayList.java:891)
	at Test.main(Test.java:12)
```





#### 问题分析

`foreach`循环其实是java提供给我们的语法糖，其本质还是借助while循环和iterator来实现的（iterator使用迭代器模式实现）。

之所以出现上述异常，是因为触发了java的fail-fast机制。fail-fast即快速失败机制，当多线程访问集合类并对其进行修改时，可能触发。其实单线程也是可以触发的，比如本例。

其实产生并发修改异常的原因很简单,`checkForComdification`的代码如下：

```
 final void checkForComodification() {
            if (modCount != expectedModCount)
                throw new ConcurrentModificationException();
        }
```

可以看出，抛出异常的原因是因为`modCount`和`expectedModCount`的值不一样，那这两个值代表着什么呢？

+ `modCount`是`AbstractList`中的成员变量，代表list被修改的次数

+ `expectedModCount` 是 `ArrayList`中的一个内部类——`Itr`中的成员变量。`expectedModCount`表示这个迭代器期望该集合被修改的次数。其值是在`ArrayList.iterator`方法被调用的时候初始化的。**只有通过迭代器对集合进行操作，该值才会改变**。

看到这里，其实问题已经明了了，`foreach`是用while+iterator实现的，但是上述代码中remove操作却用的是集合类自己的remove方法而不是iterator的remove,这样造成的结果就是`modCount`得到了修改但是`expectedModCount`却没有被修改，从而抛出异常。

### Java中的日志

阿里巴巴开发手册中有一条：【强制】应用中不可直接使用日志系统（Log4j、`Logback`）中的API，而应依赖使用日志框架SLF4J中的API，使用门面模式的日志框架，有利于维护和各个类的日志处理方式统一。



来看下Java中一些好的日志门面：

**SLF4J**(Simple Logging Facade for Java)

### Java中的引用

在JVM的文章中有写到。

+ 

#### 弱引用



