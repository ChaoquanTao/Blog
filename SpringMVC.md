---
title: SpringMVC
date: 2018-07-04 21:54:14
categories: 后端
---

### IDEA搭建一个小型SpringMVC Demo

用IDEA创建Spring项目，其本身就已经为我们做好了很多工作，这里需要注意的有两点：

1. 在 dispatcher-servlet中需要做相关配置，
2. 需要把有些jar包在编译后放到运行时环境中



标注在方法参数上的@ModelAttribute说明了该方法参数的值将由model中取得。如果model中找不到，那么该参数会先被实例化，然后被添加到model中。在model中存在以后，请求中所有名称匹配的参数都会填充到该参数中。 



关于复选框的传值，最好还是用数组形式，用List总是出问题（还没搞清楚原因），但是如果复选框不选的话，会有空指针错误，这个问题我们在前端或者后端加点判断就可以了。



### JdbcTemplate Class

JdbcTemplate Class的实例一旦被创建就是线程安全的，所以你可以配置一个JdbcTemplate类的实例然后安全的将其注入到多个DAO中。

一种常见的做法就是在Spring 配置文件中配置一个DataSource,然后将这个共享的DataSource注入到你的DAO中，那么JdbcTemplate就在DataSource的setter中被创建了

### Configuring Data Source

首先在我们的数据库TEST中创建一个学生表。

```
create table Student{
    id int not null auto_increment ,
    name varchar(20) not null ,
    age int not null ,
    primary key (id)
}
```

然后为Jdbc Template提供一个DataSource 以便它能够将自己接入DataBase

```
<bean id = "dataSource" 
   class = "org.springframework.jdbc.datasource.DriverManagerDataSource">
   <property name = "driverClassName" value = "com.mysql.jdbc.Driver"/>
   <property name = "url" value = "jdbc:mysql://localhost:3306/TEST"/>
   <property name = "username" value = "root"/>
   <property name = "password" value = "password"/>
</bean>
```

### Data Access Object(DAO)

DAO意味数据接入对象， 常用于和数据库交互。DAO提供了读写数据库的方法，应该把它置为一个接口然后让其他部分实现它。

### Executing SQL statements

```
//Quering for an integer
String SQL = "select count(*) from Student";
int rowCount = jdbcTemplateObject.queryForInt( SQL );

//Qurering for a long
String SQL = "select count(*) from Student";
long rowCount = jdbcTemplateObject.queryForLong( SQL );

//A simple query using a bind variable
String SQL = "select age from Student where id = ?";
int age = jdbcTemplateObject.queryForInt(SQL, new Object[]{10});

//Quering for a String
String SQL = "select name from Student where id = ?";
String name = jdbcTemplateObject.queryForObject(SQL, new Object[]{10}, String.class);

//Quering and returning an object
String SQL = "select * from Student where id = ?";
Student student = jdbcTemplateObject.queryForObject(
   SQL, new Object[]{10}, new StudentMapper());

public class StudentMapper implements RowMapper<Student> {
   public Student mapRow(ResultSet rs, int rowNum) throws SQLException {
      Student student = new Student();
      student.setID(rs.getInt("id"));
      student.setName(rs.getString("name"));
      student.setAge(rs.getInt("age"));
      
      return student;
   }
}

//Quering and returning mutiple objects
String SQL = "select * from Student";
List<Student> students = jdbcTemplateObject.query(
   SQL, new StudentMapper());

public class StudentMapper implements RowMapper<Student> {
   public Student mapRow(ResultSet rs, int rowNum) throws SQLException {
      Student student = new Student();
      student.setID(rs.getInt("id"));
      student.setName(rs.getString("name"));
      student.setAge(rs.getInt("age"));
      
      return student;
   }
}

//Inserting a row into the table
String SQL = "insert into Student (name, age) values (?, ?)";
jdbcTemplateObject.update( SQL, new Object[]{"Zara", 11} );

//Updating a row into the table
String SQL = "update Student set name = ? where id = ?";
jdbcTemplateObject.update( SQL, new Object[]{"Zara", 10} );

//Deleting a row from the table
String SQL = "delete Student where id = ?";
jdbcTemplateObject.update( SQL, new Object[]{20} );
```

完成了和数据库的连接。



附上两篇参考教程

[introduce](http://www.tutorialspoint.com/spring/spring_jdbc_framework.htm)

[example](https://www.tutorialspoint.com/spring/calling_stored_procedure.htm)

​     

参考上述example，我们完成了基于Spring对数据库的增删改查，





遇到的问题：

1. 各方面配置好后每次启动服务器页面总显示`The origin server did not find a current representation for the target resource or is not willing to disclose that one exists.`

    

   历经千辛万苦我发现，再dispatcher-servlet里面需要做一个关于扫面的配置`<context:component-scan base-package="control"/>`，否则我们的Controller是不能被扫描到的。

   

2. 在做表单提交时，页面报出错误`java.lang.IllegalStateException: Neither BindingResult nor plain target object for bean name 'command' available as request attribute`，下面是我的理解

    

   ​	这是个关于`modelattribute`的问题,`springMVC`的form标签会渲染成一个html的form标签，并且给内部标签暴露出一个绑定路径。它把命令对象(command object)放在`PageContext`中，这样这些表单的内部标签就能与我们的命令对象建立联系。

   ​	通俗的讲，spring的表单标签能够实现与bean对象的一个绑定(通过path指定属性)，那么就有一个问题，假如bean对象很多，表单怎么知道是和哪个bean建立的联系呢，这时候就要扯出我们的command object了，`command object`也叫做`model attribute`,它的名字通过属性标签中的`modelAttribute`或`commandName`来指定的，方式如下：

   ```
   <form:form modelAttribute="some-example-name">
   <form:form commandName="some-example-name">
   ```

   `commandAttribute`的默认名是`command`,它通常是一个对象，或者POJO对象或者POJO的集合，而我所遇见的问题原因其实有点奇怪，第一次我是这样写的

   `return new ModelAndView("student","command",new Student()) ;`

   它报错了，其中第一个参数是`ViewName`,第二个参数是`ModelName`（也就是我们上面说的`command ojbect `的name）,第三个参数是`Model`，其实我也不知道为啥报错了。

   后来我改成了这样

   ```
   modelMap.addAttribute("command",new Student()) ;
   ```

   因为我们知道它默认的名字是command所以我们这里就没有加第一`attributename`参数，它还是错的

   直到我改成最标准的形式

   ```
   modelMap.addAttribute("command",new Student()) ;
   ```

   

3. `IOException parsing XML document from class path resource [WEB-INF/applicationContext.xml]; nested exception is java.io.FileNotFoundException: class path resource [WEB-INF/applicationContext.xml] cannot be opened because it does not exist`

   

   因为`DataDource`以及`JDBCTemplate`我们是在xml文件中配置的，所以我们需要在Controller中通过引入上下文的方式来获得`JdbcTemplate`,具体见代码

   ```
    ApplicationContext context = new ClassPathXmlApplicationContext("applicationContext.xml") ;
    StudentJDBCTemplate studentJDBCTemplate = (StudentJDBCTemplate) context.getBean("studentJDBCTemplate");
   ```

   然后就出现了上述错误，大概意思是找不到这个applicationContext.xml文件，后来发现，它是在WEB-INF文件夹下的，而我们新生成的out文件下，其实是没有这个路径的，也就是说它和class文件不在同一目录下，所以访问不到，解决办法是将其拷贝到同一目录下。

   




### 一直遇到的问题

1. controller不同

   配置时各种失误导致，没有扫描包，或者后缀检查配置有问题

2. 奇怪的415错误

   @RequestBody

   该注解常用来处理Content-Type: 不是`application/x-www-form-urlencoded`编码的内容，例如application/json, application/xml等



​	那么表单格式的内容用什么解析？

两个问题：为什么我们请求的数据成为了表单格式？表单格式如何解析？

表单提交默认就是`application/x-www-form-urlencoded`格式的

表单type时button还是submit提交时貌似有很大不同

+ 点击type=submit的按钮，触发表单的onsubmit事件，然后提交表单
+ 点击type=button的按钮，也可以提交表单

RequestBody注解如何运作