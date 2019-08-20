---
title: windows下tensorflow anoconda安装
date: 
categories: 教程
---


之前已经装好anoconda，这里安装tensorflow

准备工作：Python3.5 或者Python3.6

很多操作指令[官方文档](https://tensorflow.google.cn/install/install_windows?hl=zh-cn)已经给出 

1. 打开cmd，输入

   `conda create -n tensorflow python=3.5`

   创建一个名为tensorflow的环境，（这里我第一次尝试并没有成功，将目录切换到Python底下才成功，估计是环境变量的问题），可能会显示要安装新的文件，点y即可。

2. 激活环境

   `activate tensorflow`

   这时你会发现命令行最开始会有(tensorflow)，说明已经激活

3. 安装tensorflow, 因为我安装的是cpu版本，所以命令如下：

   `pip install --ignore-installed --upgrade tensorflow`

4. 至此安装已经完成，如需检验是否安装成功，输入python,如果import tensorflow不报错，基本说明安装成功

---
 至此tensorflow的安装工作已经完成，那如何在anconda navigator中导入呢？

+ 方法一  UI界面中导入

   ![](https://ws1.sinaimg.cn/large/005UcYzaly1flnnyibtzcj30it02tglg.jpg)
   ​

     个人觉得这种方法很容易卡死，推荐第二种

+ 方法二 命令行下载

  首先activate 某环境，然后conda install xxx  (如spyder)




如果之前安装了别的python版本，因为anaconda里面自己带了python,如何给指定版本安装numpy?这里有两种方式：

   	1. activate conda环境，然后conda install numpy,这样会安装许多其他的包，很麻烦,不推荐
       2. py -3 -m pip install python 