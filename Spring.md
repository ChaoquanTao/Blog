---
title: Spring
date: 2018-04-15 16:27:20
tags: Spring
categories: JavaWeb
---

### 初探Spring

类似于Struts2, Spring也是通过xml配置文件来对类进行操作的

在Struts2中，对于表单的提交，通过将表单中标签的name属性设置为Bean中对应的属性，通过配置struts.xml可以让框架自己去调用对应的setter，这里也是类似，只不过设置的是applicationContext.xml,这个配置文件将会告诉容器如何操作具体的类。 看一段代码：

bean包中

接口`IPerson`及其实现类

```
package com.bean;

public interface IPerson {
    public void say();
}

```

```
package com.bean;

public class ChineseImp implements IPerson {
    private String name ;
    private int age ;
    @Override
    public void say() {
        System.out.println("I'm Chinese,my name is"+this.name+" my age is "+this.age);
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }
}

```

```
package com.bean;

import java.sql.SQLOutput;

public class AmericanImp implements IPerson {
    private String name ;
    private int age ;
    @Override
    public void say() {
        System.out.println("I'm American,my name is "+this.name+" my age is"+this.age);
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }
}

```

`applicationContext.xml`

```
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
    <bean id="chinese" class="com.bean.ChineseImp">
        <property name="name">
            <value>taochaoquan</value>
        </property>
        <property name="age">
            <value>23</value>
        </property>
    </bean>

    <bean id="american" class="com.bean.AmericanImp">
        <property name="name">
            <value>Arrow</value>
        </property>
        <property name="age">
            <value>12</value>
        </property>
    </bean>
</beans>
```

emmmm内容浅显易懂，就不详述了

测试类

```
package com.spring;

import com.bean.IPerson;
import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;

public class Test {
    public static void main(String[] args) {
        //创建Spring容器
        ApplicationContext context = new ClassPathXmlApplicationContext("applicationContext.xml");
        IPerson p1 = (IPerson) context.getBean("chinese");
        p1.say();
        IPerson p2 = (IPerson) context.getBean("american");
        p2.say();
    }
}

```

输出

```
I'm Chinese,my name istaochaoquan my age is 23
I'm American,my name is Arrow my age is12
```



控制反转和依赖注入

​	传统的设计模式：假如调用者A需要调用被调用者B，那么它就需要new出一个B，这样的话，A,B之间的耦合度就会比较高，假如说后期需求发生了变化，需要往B中添加属性，那么就得修改项目中调用了B处的相关代码。

​	使用依赖注入：假如说A需要调用B，Spring容器会自动将B的实例注入到A中，相当于此时A拥有了B，当项目需求变更时，我们只需要修改Spring的配置文件而无需修改代码

下面用一个例子来说明6

有一个User类

```
package bean;

public class User {
    private String username ;
    private String password ;

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }
}

```

用接口UserDao来模拟持久层

```
package dao;

import bean.User;

public interface UserDao {
    public void save(User user);
}

```

```
package dao;

import bean.User;

public class UserDaoImp implements UserDao {
    @Override
    public void save(User user) {
        System.out.println("user has been saved in database");
    }
}

```

服务层

```
package service;

import bean.User;

public interface UserService {
    public void add( User user);

}

```

```
package service;

import bean.User;
import dao.UserDao;

public class UserServiceImp implements UserService {
    private UserDao userDao ;

    public UserDao getUserDao() {
        return userDao;
    }

    public void setUserDao(UserDao userDao) {
        this.userDao = userDao;
    }

    @Override
    public void add(User user) {
        userDao.save(user);
    }
}

```

测试类

```
package main;

import bean.User;
import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;
import service.UserServiceImp;

public class Test {
    public static void main(String[] args) {
        ApplicationContext context = new ClassPathXmlApplicationContext("beans.xml");
        UserServiceImp usi = (UserServiceImp) context.getBean("userService") ;
        User user = new User();
        user.setUsername("tao");
        user.setPassword("123");
        usi.add(user);
    }
}

```

大概业务逻辑如下：有一个新的用户user，我们想把它加到用户列表中，`UserServiceImp`类中提供了add()方法，我们可以看到，add方法内部其实是调用了UserDao的save方法，那么问题来了，当Test类中的usi.add()传入user后，应当需要一个UserDao的实例来执行save方法，而在我们的代码中并没有看到new出的实例。其实这个操作就是Spring容器帮我们做的，请看下面的配置文件

beans.xml

```
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
    <bean id="udi" class="dao.UserDaoImp"></bean>
    <bean id="userService" class="service.UserServiceImp">
        <property name="userDao">
            <ref bean="udi"/>
        </property>
    </bean>
</beans>
```

这里其实就是把被依赖的UserDao的实例注入了UserServiceImp的实例中，也就是我们所说的依赖注入。

对于上面的业务逻辑，如果 我们不使用依赖注入，应该是这样的，1.创建UserServiceImp实例，2.创建UserDao实例，3.通过UserServiceImp的setter方法，建立两者依赖，

可以看出，依赖注入帮我们完成了第二步和第三步，很好的解耦了他们的依赖性









### Spring MVC

配置`DispatcherServlet`

大概完成了一个简单demo,我只想说，最后部署的时候并不用加项目名称来访问，直接`localhost:8008/welcome`就可以了。

#### 注解

+ `@PathVariable`

  当使用@RequestMapping URI tempalte样式映射时，即someUrl/{paramId},这时的paramId可通过@PathVariable注解将其绑定到方法参数上

  ```
  @Controller  
  @RequestMapping("/owners/{ownerId}")  
  public class RelativePathUriTemplateController {  

    @RequestMapping("/pets/{petId}")  
    public void findPet(@PathVariable String ownerId, @PathVariable String petId, Model model) {      
      // implementation omitted  
    }  
  }  
  ```

  假如使用@PathVariable注解时参数名和URI template中的不一致，可以这样`@PathVarible("name")`其中name为URI template中的变量名

+ `@RequestHeader`

  把request header中的某些字段绑定到参数上

+ `@CookieValue`

  把Request header中关于cookie的值绑定到参数上

+ `@RequestParam和@RequestBody`

+ `@SessionAttribute`和`@ModelAttribute`

  绑定HttpSession中的attribute对象的值,

  @ModelAttribute注解有两个用法，一个是用于方法上，一个是用于参数上。**用于方法上时，被其注释的方法会在Controller每个方法执行前被执行，因此通常用来在处理@RequestMapping之前为请求绑定需要从后台查询的model；**用于参数上时，用来通过名称对应把相应名称的值绑定到注解的参数bean上

+ 

总的来说，注解就是实现了请求的相关值与方法参数的绑定。



请求参数名和java类的属性相匹配

测试SpringMVC



HttpRequest --> DispatcherServlet --> Handler Mapping --> Controller --> Model and View --> DispatherServlet --> View Resolver  --> Model 



