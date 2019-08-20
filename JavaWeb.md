---
title: JavaWeb
date: 2018-04-08 15:06:43
tags: JavaWeb
categories: Java
---

### Servlet

[![kziovt.jpg](https://s2.ax1x.com/2019/03/08/kziovt.jpg)](https://imgchr.com/i/kziovt)

​						Tomcat各个组建之间的嵌套关系

今天在idea地下进行最基本的JavaWeb的部署，奈何一直404，在网上找了各种解决办法，最后发现，原来是我tomcat少配置了一步，在tomcat的deployment里面没有添加war包，在此记录一哈。



### 前后端交互

通过表单提交或者ajax,都是基于http协议，对于前端的多个请求，后端通过web.xml中的mapping来与servlet进行对应。

servlet属于controller层,controller层对数据库的操作需要用到service层，service层就是对查询结果（生数据）进行进一步加工的层，而dao层则是单纯的对数据库进行增删改查，得到生数据。



#### getParameter 和 getAttribute

getParameter是获取http请求中的数据，比如get或者post方法，返回值是字符串。是客户端向服务器请求的数据。

getAttribute之前必须先setAttribute



forward 服务器端跳转 使用forward时，request设置的属性依然能保留在下一个页面(setAttribute); 

response.senRedirect() 客户端跳转





getParameter得到的都是String类型的。或者是http://a.jsp? id=123中的123，或者是某个表单提交过去的数据。
getAttribute则可以是对象。

getParameter()是获取POST/GET传递的参数值；
getAttribute()是获取对象容器中的数据值；

getParameter：用于客户端重定向时，即点击了链接或提交按扭时传值用，即用于在用表单或url重定向传值时接收数据用。
getAttribute：用于服务器端重定向时，即在sevlet中使用了forward函数,或struts中使用了mapping.findForward。getAttribute只能收到程序用setAttribute传过来的值。
另外，可以用setAttribute,getAttribute发送接收对象.而getParameter显然只能传字符串。
setAttribute是应用服务器把这个对象放在该页面所对应的一块内存中去，当你的页面服务器重定向到另一个页面时，应用服务器会把这块内存拷贝另 一个页面所对应的内存中。这样getAttribute就能取得你所设下的值，当然这种方法可以传对象。session也一样，只是对象在内存中的生命周 期不一样而已。
getParameter只是应用服务器在分析你送上来的request页面的文本时，取得你设在表单或url重定向时的值。

转自：https://blog.csdn.net/oscar999/article/details/2859132



### ajax的使用

今天使用ajax进行前后端交互，然后发现ajax可以返回，但是总是在error里面，就去网上找了一哈答案，原来在写ajax的时候，有个dataType字段，这个其实是用来定义从后端传回来的值的类型，我以为是指的是从前端往后端的类型，所以写成了json,后面改成了text就好了。看来网上的一些回答，目测提交按钮的type如果是submit也会出问题，这个有时间了再记录吧。



### 文件上传/下载

+ 上传

  + `upload.jsp`

    ```
    <%@ page contentType="text/html;charset=utf-8" language="java" %>

    <html>
    <head>
        <title>FileUpload</title>
    </head>
    <body>
    <p> select the file you want to upload</p>
        <form action="accept.jsp" method="post" enctype="multipart/form-data">
            <input type="file" name="upfile">
            <br>
            <input type="submit" value="upload">
        </form>

    </body>
    </html>
    ```

    ​

  + `accept.jsp`

    ```
    <%@ page contentType="text/html;charset=utf-8" language="java" %>
    <html>
    <head>
        <title>FileAccept</title>
    </head>
    <body>
    <%
       request.setCharacterEncoding("GBK");
        BufferedReader bufferedReader = request.getReader();
        //创建输出流
        PrintWriter printWriter = new PrintWriter(new BufferedWriter(new FileWriter("G:/upload.txt")));
        
        String buffer ;
        while((buffer = bufferedReader.readLine())!=null){
            System.out.println(buffer);
            printWriter.write(buffer);
        }
        bufferedReader.close();
        printWriter.close();
        out.print("file upload complete");
    %>
    </body>
    </html>
    ```

    这里因为我传txt是`gbk`编码，所以在`accept.jsp`里面需要解码

    文件上传/下载的实质其实也就是基于`httprequest`和`httpresponse`的文件读写，当然也可以用字节读写，不过有效率问题

+ 下载

  +  `loadfile.jsp`

    ```
    <%@ page contentType="text/html;charset=UTF-8" language="java" %>
    <html>
    <head>
        <title>loadfile</title>
    </head>
    <body>
    <p>test..................</p>
        <%
            PrintWriter printWriter = response.getWriter() ;
            response.setHeader("Content-disposition","attachment;filename="+"download.txt");
            response.setContentType("application/txt");

            BufferedReader bufferedReader = new BufferedReader(new FileReader("G:/upload.txt"));
            String buffer;
            while((buffer=bufferedReader.readLine())!=null){
                printWriter.write(buffer);
            }
            out.print("download complete");
            printWriter.close();
            bufferedReader.close();
        %>
    </body>
    </html>
    ```

    这里对`response.setHeader()不太懂`，但目测是必不可少的

  + ​


+ ​