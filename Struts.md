---
title: Struts2
date: 2018-04-13 15:28:29
categories: JavaWeb
---

### Struts2

- IDEA下的环境部署及所见问题

  webApplication+ struts2+ 稍后通过maven来加载包

  dependency如下：

  ```
  <dependency>
              <groupId>org.apache.struts</groupId>
              <artifactId>struts2-core</artifactId>
              <version>2.5.14.1</version>
  </dependency>
  ```

  这里的版本号是自己去官网查的，第一波我只写了2.5,然后出现了下面的错误1，目测是不兼容，

  这里之所以没有用IDEA下载jar包的方式是因为目测最新版本它下载的jar包缺一个`javassist`，本地导的话也不方便，因为是编译好的

  用maven加载完之后需要将包加入运行时环境，也就是project structure中的artifact

  大概的步骤是这样的，如果选了默认的download jar,那么可能会出现download jar和maven jar冲突的情况，删除掉download的包就可以了，我是分别在artifacts和out中都删掉的，下面的错误二就属于这种情况

  ​

  下面写一下Struts的基本工作流程，个人觉得其实它就是为了让MVC架构更明显，耦合度更低才出现的产物

  ​

  ​

  错误1： ` Illegal char <:> at index 3: jar:file:\F:\IntelliJidea\utimate\workspace\UseStruts2_2\out\artifacts\UseStruts2_2_war_exploded\WEB-INF\lib\struts2-core-2.5.jar`

  兼容性问题，struts-core换成2.5.14就可以了

  错误2：` Unable to load configuration. - bean - jar:file:/F:/IntelliJidea/utimate/workspace/UseStruts2_2/out/artifacts/UseStruts2_2_war_exploded/WEB-INF/lib/struts2-core.jar!/struts-default.xml:73:72`

  包冲突，底下某一行的`caused by`其实有说明的

  错误3：浏览器显示`There is no Action mapped for namespace [/] and action name [list] associated with context path [].`

  查询`stackoverflow`发现,大概是struts.xml文件位置的问题，因为很明显发现，out文件夹下是没有这个文件的，想一想编译好的文件里都没有配置文件，它当然找不到了，这时候我就简单粗暴的把它拷贝到out里面的web-info下面了，因为反正xml文件不需要编译

- ​从表单提交看struts机制

  struts.xml

  ```
  <?xml version="1.0" encoding="UTF-8"?>

  <!DOCTYPE struts PUBLIC
          "-//Apache Software Foundation//DTD Struts Configuration 2.0//EN"
          "http://struts.apache.org/dtds/struts-2.0.dtd">

  <struts>
      <package name="default" extends="struts-default" namespace="/">
          <action name="reg" method="execute" class="Register">
              <result name="success">/success.jsp</result>
              <result name="input">/index.jsp</result>
          </action>
      </package>
  </struts>
  ```

  ​

  index.jsp

  ```
   <s:head></s:head>
   <s:form action="reg">
       <br/>
     <s:textfield name="person.firstname" label="firstname:"/>
     <s:textfield name="person.lastname" label="lastname:"/>
     <s:textfield name="person.age" label="age:"/>
     <s:submit/>
   </s:form>
  ```

  success.jsp

  ```
  <%@ taglib prefix="s" uri="/struts-tags" %>
  <%--
    Created by IntelliJ IDEA.
    User: Terry
    Date: 2018/4/12
    Time: 22:22
    To change this template use File | Settings | File Templates.
  --%>
  <%@ page contentType="text/html;charset=UTF-8" language="java" %>
  <html>
  <head>
      <title>Title</title>
  </head>
  <body>
  success!
  <s:property value="person.firstname"  />
  <s:property value="person.lastname"/>
  <s:property value="person.age"/>
  </body>
  </html>

  ```

  ​

  Person.java

  ```
  public class Person {
      private String firstname ;
      private String lastname ;
      private int age ;

      public String getFirstname() {
          return firstname;
      }

      public void setFirstname(String firstname) {
          this.firstname = firstname;
      }

      public String getLastname() {
          return lastname;
      }

      public void setLastname(String lastname) {
          this.lastname = lastname;
      }

      public int getAge() {
          return age;
      }

      public void setAge(int age) {
          this.age = age;
      }
  }
  ```

  Register.java

  ```
  import com.opensymphony.xwork2.ActionSupport;

  public class Register extends ActionSupport {
      Person person ;

      public Person getPerson() {
          return person;
      }

      public void setPerson(Person person) {
          this.person = person;
      }

      public String execute() throws Exception{
          return SUCCESS;
      }

      public void validate(){
          if(person.getFirstname().length()==0){
              addFieldError("person.firstname","first name is required");
          }
          if(person.getLastname().length()==0){
              addFieldError("person.lastname","lastname is required");
          }
          if(person.getAge()<18){
              addFieldError("person.age","children are not allowed here!");
          }
      }
  }

  ```

  //这里我们不讲配置文件相关过程

  `index.jsp`中这里每个`textfield`都有一个name属性，注意这个属性不是乱起的，每个输入框对应了一个Bean对象的一个属性，可以认为是struts它对输入框的name和Action中的person对象的属性实现了一个绑定，当输入表单点击提交后，struts会调用Person中对应的set方法来对属性实现赋值，这一切都发生在Action的execute方法之前。

  当跳转到成功页面时，同样可以访问到我们刚刚输入的值

  输入校验时，如果校验失败，返回的是`input`

  //几点想法  个人觉得这种直接访问属性的方式有悖于private修饰符存在的意义

- 拦截器

  拦截器运行于Action之前，通常以栈的形式存储，也就是说，假设当前有Interceptor1,Interceptor2,Interceptor三个拦截器，在strtuts.xml中注册好后，因为每个拦截器里有一个intercept方法，这个方法会调用invoke函数，来调用栈里的下一个拦截器，如果已经是最后一个拦截器，那么它会调用Action,然后紧接着以反过来的顺序执行invoke函数后面的内容

  struts.xml

  ```
  <?xml version="1.0" encoding="UTF-8"?>

  <!DOCTYPE struts PUBLIC
          "-//Apache Software Foundation//DTD Struts Configuration 2.0//EN"
          "http://struts.apache.org/dtds/struts-2.0.dtd">

  <struts>
      <package name="default" namespace="/" extends="struts-default">
          <interceptors>
              <interceptor name="firstInterceptor" class="Interceptor.MyInterceptor1"/>
              <interceptor name="secondInterceptor" class="Interceptor.MyInterceptor2"/>
              <interceptor-stack name="mystack">
                  <interceptor-ref name="firstInterceptor"/>
                  <interceptor-ref name="secondInterceptor"/>
              </interceptor-stack>
          </interceptors>

          <action name="fistAction" class="action.MyAction1">
              <result type="chain">secondAction</result>
              <interceptor-ref name="mystack"/>
          </action>
          <action name="secondAction" class="action.MyAction2">
              <result name="success">/success.jsp
              </result>
          </action>

      </package>
  </struts>
  ```

  MyInterceptor1.java

  ```
  package Interceptor;

  import com.opensymphony.xwork2.ActionInvocation;
  import com.opensymphony.xwork2.interceptor.Interceptor;

  public class MyInterceptor1 implements Interceptor {
      public void destroy() {

      }

      public void init() {

      }

      public String intercept(ActionInvocation actionInvocation) throws Exception {
          System.out.println("fist interceptor,before invoke the next interceptor or action");
          String res = actionInvocation.invoke();
          System.out.println("first interceptor,after invoker the next interceptor or action");
          return res ;
      }
  }

  ```

  MyInterceptor2.java

  ```
  package Interceptor;

  import com.opensymphony.xwork2.ActionInvocation;
  import com.opensymphony.xwork2.interceptor.Interceptor;

  public class MyInterceptor2 implements Interceptor {
      public void destroy() {

      }

      public void init() {

      }

      public String intercept(ActionInvocation actionInvocation) throws Exception {
          System.out.println("second interceptor,before invoke the next interceptor or action");
          String res = actionInvocation.invoke();
          System.out.println("second interceptor,after invoker the next interceptor or action");
          return res ;
      }
  }

  ```

  MyAction1.java

  ```
  package action;

  import com.opensymphony.xwork2.ActionSupport;

  public class MyAction1 extends ActionSupport {
      public String execute() throws Exception{
          System.out.println("this is first action");
          return SUCCESS ;
      }

  }

  ```

  MyAction2.java

  ```
  package action;

  import com.opensymphony.xwork2.ActionSupport;

  public class MyAction2 extends ActionSupport {
      @Override
      public String execute() throws Exception {
          System.out.println("this is the second action");
          return SUCCESS;

      }
  }

  ```

  index.html

  ```
  <%@ taglib prefix="s" uri="/struts-tags" %>
  <%--
    Created by IntelliJ IDEA.
    User: Terry
    Date: 2018/4/13
    Time: 11:25
    To change this template use File | Settings | File Templates.
  --%>
  <%@ page contentType="text/html;charset=UTF-8" language="java" %>
  <html>
    <head>
      <title>$Title$</title>
    </head>
    <body>
   <s:a action="firstAction">requst interceptor stack</s:a>
    </body>
  </html>

  ```

  ​

- ​