---
title: Linux supervise
categories: Linux
date: 2021-08-31 23:00:00
---

> 今天工作中遇到一个命令svc，可以用于优雅杀死进程。本着啥都不会的精神，刨根问题一哈。

背景:

一般而言生产环境中的服务都是有守护进程的：当它挂掉后，会有另外一个进程把它立马拉起来。

在指导这个东西以前，我都是通过cron+脚本的方式来达到这一目的的，但是缺点就是cron只能精确到分钟，不够细。



正餐：

linux中有个监控工具，叫`supervise`，它是`daemontools`里面的一个工具。

`daemontools`是什么？

它是一个linux工具包，http://cr.yp.to/daemontools.html。

`supervise`是什么？

`supervise`用来监控一个服务，当服务死掉时，可以立马将其拉起。要实现这个操作，`supervise`命令需要创建一个run文件。