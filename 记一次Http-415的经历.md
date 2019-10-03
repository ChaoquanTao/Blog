---
title: 记一次Http 415的经历
date: 2019-10-01 13:45:19
updated: 2019-10-01 13:45:19
tags: RequestBody
categories: 后端
---

### 问题重现：

> 使用`spring mvc`实现一个简单的登录功能，前后端分离，使用`nginx`反向代理实现跨域请求

这个问题困扰了我一天多，从最开始检查`nginx`配置到检查表单提交再到查看http请求头再到检查后端spring相关配置以及注解的问题，最后终于找到问题。整个过程中除了415当然还蹦出了其他各种错误，如400，405，500，不过415错误一直断断续续贯穿始终。下面来复盘一下整个过程。



从实际生产角度考虑，我需要实现一个前后端分离的系统，由于静态资源和后端服务可能不在同一个端口，甚至不在同一个服务器，所以必然存在跨域的问题，跨域是由于浏览器的**同源策略**导致的，为了保证其安全性，这里暂不去讨论同源策略是什么。解决跨域的方法很多，但大多数都是要修改前端代码或者后端代码，这是很不优雅的，所以我选择了使用`nginx`的反向代理功能来实现这一需求，将静态资源放在`nginx`上。

### nginx排查

部分`nginx`配置：

```
 listen       8800;
        server_name  localhost;
        #charset koi8-r;
        #access_log  logs/host.access.log  main;
		location /api/ {
			proxy_pass http://localhost:8080/;
		}
	    location / {
            root   E:\SimpleMall-Admin-Web;
            index  login.html;
        }
```

静态资源`url`: localhost:8800

后端服务：localhost:8080

请求`url`: `/api/login` 

刚开始一直以为是`nginx`配置有问题，因为我看到请求的`url`一直都是`localhost:8800/api/login`，我当时以为发起请求后应该是`localhost:8080/login`，以为会有个跳转的动作，后来我发现是自己对反向代理理解有误，这个代理过程对用户透明，所以我们是看不到`url`的变化的。



### ajax 表单提交

然后检查ajax提交表单过程

为什么使用ajax呢？因为这是个前后端分离的系统，所以页面应该跳到哪里这些事后端应该是不知道的，它只需要根据请求返回一些`json`就可以了。

然后发现，表单提交这有我不知道的东西：

关于提交按钮的两种写法：

写法一：

```html
<input id="commit" type="submit" onclick="login()" />
```

写法二：

```html
<input id="commit" type="button" onclick="login()" />
```

当然还可以写成button标签的形式，不过提交作用和第一种写法是一样的。

对于这两种写法，如果我们没有写这个`onclick`事件，

对于写法一：我们点击这个按钮他会自动提交整个form,即使form里面action也没写它也会提交，方法默认为GET,且会刷新整个页面，除非把form的`onsubmit`事件设置成返回false.

对于写法二：必须我们自己写这个`onclick`事件后它才会提交.

但是如果我们都写了`onclick`事件，那么他俩在请求上是没有区别的。

因为我们都自己实现了`onclick`事件，所以下面选其一，使用第二种方式。



我们在`js`里面使用ajax来实现提交的动作：

```javascript
 function login(){
    var usn = $("#userName").val();
    var pwd = $("#passWord").val();
    var datas = {"userName":usn,"passWord":pwd}
    $.ajax({
            //几个参数需要注意一下
                type: "POST",//方法类型
                dataType: "text",//预期服务器返回的数据类型
                url: "/api/login" ,//url
                data: datas,
                success: function (result) {
                    alert(result)
                    console.log(result);//打印服务端返回的数据(调试用)
                    if (result.resultCode == 200) {
                        alert("SUCCESS");
                    }
                },
                error : function() {
                    alert("异常！");
                }
            });
  }
```

同时在后端使用`@RequestBody`注解来解析。

```java
@Controller
public class AdminController {
    @RequestMapping(value = "/login",method = RequestMethod.POST,consumes = "application/json")
    public @ResponseBody String login(@RequestBody  Administrator  administrator){
        String userName = administrator.getUserName();
        String passWord = administrator.getPassWord();
        System.out.println(userName+"================"+passWord);
        return "dddddd" ;
    }
}
```

1. data 为js对象，无`ContentType`

```javascript
$.ajax({
            //几个参数需要注意一下
                type: "POST",//方法类型
                dataType: "text",//预期服务器返回的数据类型
                url: "/api/login" ,//url
                data: datas,
                success: function (result) {
                    alert(result)
                    console.log(result);//打印服务端返回的数据(调试用)
                    if (result.resultCode == 200) {
                        alert("SUCCESS");
                    }
                },
                error : function() {
                    alert("异常！");
                }
            });
```



报错415，请求头如下：

![uUC8E9.png](https://s2.ax1x.com/2019/10/01/uUC8E9.png)

可以看到，请求头的Content-Type是默认的`application/x-www-form-urlencoded`形式，而`RequestBody`注解是按照Content-Type来寻找对应的转换器进行解析的，并且它无法解析这种形式（至于为什么不能我们后面再分析）。

所以我们修改`ContentType`

2. data为`js`对象，`ContentType`为`json`

```javascript
$.ajax({
            //几个参数需要注意一下
                type: "POST",//方法类型
                dataType: "text",//预期服务器返回的数据类型
                url: "/api/login" ,//url
                data: datas,
    			contentType: 'application/json;charset=utf-8',
                success: function (result) {
                    alert(result)
                    console.log(result);//打印服务端返回的数据(调试用)
                    if (result.resultCode == 200) {
                        alert("SUCCESS");
                    }
                },
                error : function() {
                    alert("异常！");
                }
            });
```

报错400，请求头

![](http://pyopearjz.bkt.clouddn.com/a247ec52bacd26c873563c09291fd29.png)

因缺思厅，`Content-Type`变成了`json`,而请求体变成了拼接形式，又发现报的是400错误，说明我们请求无效，这个无效通常有两种原因：

+ 前端提交数据的字段名称或者是字段类型和后台的实体类不一致，导致无法封装；
+ 前端提交的到后台的数据应该是json字符串类型，而前端没有将对象转化为字符串类型；

很明显，后端是按照ContentType来解析的，且RequenstBody是可以解析json类型的，那么问题就只能是出现在了第二种。可以发现，前一次和这一次我们传给data的都是一个`jacascript`对象，而不是一个`json`字符串，所以我们将js对象转成json字符串再试试。

3. data 为json字符串，ContentType为json

```javascript
 $.ajax({
            //几个参数需要注意一下
                type: "POST",//方法类型
                dataType: "text",//预期服务器返回的数据类型
                contentType: 'application/json;charset=utf-8',
                url: "/api/login" ,//url
                data: JSON.stringify(datas),
                success: function (result) {
                    alert(result)
                    console.log(result);//打印服务端返回的数据(调试用)
                    if (result.resultCode == 200) {
                        alert("SUCCESS");
                    }
                },
                error : function() {
                    alert("异常！");
                }
            });
```



返回200，访问成功

![](http://pyopearjz.bkt.clouddn.com/34f999b82782257c1d1530ec24207d8.png)

注意：此时还是要写Content Type的，不然就会415.



对于表单提交来说，当然也不是非用json传值不可，只是我觉得它比较方便，在这里也是可以直接将表单数据序列化然后传给后端的。

我们将前端改成这样：

```javascript
 $.ajax({
            //几个参数需要注意一下
                type: "POST",//方法类型
                dataType: "text",//预期服务器返回的数据类型
                url: "/api/login" ,//url
                data: $("form").serialize(),
                success: function (result) {
                    alert(result)
                    console.log(result);//打印服务端返回的数据(调试用)
                    if (result.resultCode == 200) {
                        alert("SUCCESS");
                    }
                },
                error : function() {
                    alert("异常！");
                }
            });
```

后端改成这样：

```java
public @ResponseBody String login(String userName,String passWord){
        System.out.println(userName+"================"+passWord);
        Administrator adm = new Administrator();

        return "ddddddddddddddd" ;
    }
```

然后就可以快乐的接收数据啦

![form-nonbody.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7isuun7myj30d507wjrh.jpg)

可以看出，因为数据格式是默认的这种模式，所以不能用RequestBody解析，只能这样挨个接收，很麻烦，所以这也是为啥我想用json的原因。



下面来分析一下@RequestBody到底干了啥

### RequestBody







讲到这里，大概能遇到的问题差不多都讲道理，然而困扰我最久的，以上都不是，而是：

![dd2e5c9651f7878f6b2ec5d9d7670e4.png](http://ww1.sinaimg.cn/large/006ImZ0Ogy1g7itfg38eij30h9047wed.jpg)

编译文件没有即使更新！我当时内心真是。。。