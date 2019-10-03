---
title: Nginx教程
date: 2019-09-27 20:10:02
updated: 2019-09-27 20:10:02
tags: Nginx
categories: 教程
---

### 前提

需要：

1. 编译器及相关工具：`gcc`编译器，make工具

由于命令`apt-get install gcc gcc-c++`报错`Couldn't find any package by regex 'gcc-c+`,

 所以我们可以直接装`apt-get -y install build-essential`



2. 模块依赖性： `pcre`库（正则表达式匹配的库），`zlib`库（压缩用的），`openssl`库（安全套接字库）

   这些都安装在`/usr/lcal/src`中

   这里我使用`wget`命令安装。以`pcre`为例：

```
wget ftp://ftp.pcre.org/pub/pcre/pcre2-10.33.tar.gz
tar -zxvf pcre2-10.33.tar.gz
cd pcre2-10.33
./Configure
make
make install
```

同样的方法安装 `zlib`,`openssl`



安装`nginx`:

```
wget http://nginx.org/download/nginx-1.16.1.tar.gz
tar -xzf nginx-1.16.1.tar.gz
./configure --with-pcre=../pcre2-10.33
make
make install
```

因为这里的安装需要上面的一些依赖库，我这里只加上`pcre`就可以了，具体情况可能和版本有关系，需要注意。

```
apt install nginx-core
apt install nginx-extras
apt install nginx-full
apt install nginx-light

```

装好的目录长这样：

```

CHANGES     LICENSE   README  conf       contrib  man   src
CHANGES.ru  Makefile  auto    configure  html     objs

```





错误集锦：

```
src/core/ngx_regex.h:15:10: fatal error: pcre.h: No such file or directory
```

pcre2换成`pcre`