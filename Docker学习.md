---
title: Docker笔记
category: 容器
date: 2021-11-13 15:00:00
---

常见命令

+ `docker image ls`查看镜像列表
+ `docker ps` 查看正在运行的容器
+ docker run -p 8888:80 -tid blog-20220502 /bin/bash 启动容器
+ 进入运行中的容器：`docker exec -ti {containerId} /bin/bash`
  + -t 为docker分配一个伪终端并绑定到容器的标准输入上
  + -i 是让容器的标准输入保持打开状态
+ `docker stop/start/restart constainerId`
+ 我在别人的容器里进行了修改，如何保存成新的镜像？先将之前的container停掉,然后`docker commit oldContainerId newImage`, 注意，是**containerId**
+ 

