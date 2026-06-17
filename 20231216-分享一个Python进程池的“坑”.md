---
title: 分享一个Python进程池的“坑”
date: 2023-12-16 12:00:00
categories: Python
---

### 背景

最近线上运行的一个python任务负责处理一批数据，为提高处理效率，使用了python进程池，并会打印log。最近发现，任务时常会出现夯住的情况，当查看现场时发现，夯住时通常会有几个子进程打印了相关错误日志，然后整个任务就停滞在那里了。

### 原因

夯住的原因正是由于一行不起眼的log导致，简而言之，**Python的logging模块在写文件模式下，是不支持多进程的，强行使用可能会导致死锁**。

#### 问题复现

可以用下面的代码来描述我们遇到的问题

```
import logging
from threading import Thread
from queue import Queue
from logging.handlers import QueueListener, QueueHandler
from multiprocessing import Pool

def setup_logging():
    # log的时候会写到一个队列里，然后有一个单独的线程从这个队列里去获取日志信息并写到文件里
    _log_queue = Queue()
    QueueListener(
        _log_queue, logging.FileHandler("out.log")).start()
    logging.getLogger().addHandler(QueueHandler(_log_queue))

    # 父进程里起一个单独的线程来写日志
    def write_logs():
        while True:
            logging.info("hello, I just did something")
    Thread(target=write_logs).start()

def runs_in_subprocess():
    print("About to log...")
    logging.info("hello, I did something")
    print("...logged")

if __name__ == '__main__':
    setup_logging()

    # 让一个进程池在死循环里执行，增加触发死锁的几率
    while True:
        with Pool() as pool:
            pool.apply(runs_in_subprocess)
```

我们在linux上执行该代码：

```
About to log...
...logged
About to log...
...logged
About to log...
```

发现程序输出几行之后就卡住了。

#### 问题出在了哪里

python的进程池是基于`fork`实现的，当我们只使用`fork()`创建子进程而不是用`execve()`来替换进程上下时，需要注意一个问题：`fork()`出来的子进程会和父进程共享内存空间，**除了父进程所拥有的线程**。

对于代码

```
from threading import Thread, enumerate
from os import fork
from time import sleep

# Start a thread:
Thread(target=lambda: sleep(60)).start()

if fork():
    print("The parent process has {} threads".format(
        len(enumerate())))
else:
    print("The child process has {} threads".format(
        len(enumerate())))
```

输出:

```
The parent process has 2 threads
The child process has 1 threads
```

可以发现，父进程中的子线程并没有被fork到子进程中，而这正是导致死锁的原因:

- 当父进程中的线程要向队列中写log时，它需要获取锁
- 如果恰好在获取锁后进行了`fork`操作，那这个锁也会被带到子进程中，同时这个锁的状态是占用中
- 这时候子进程要写日志的话，也需要获取锁，但是由于锁是占用状态，导致永远也无法获取，至此，死锁产生。

### 如何解决

#### 使用多进程共享队列

出现上述死锁的原因之一在于在fork子进程的时候，把队列和锁的状态都给`fork`过来了，那要避免死锁，一种方案就是使用进程共享的队列。

```
import logging
import multiprocessing
from logging.handlers import QueueListener
from time import sleep


def listener_configurer():
    root = logging.getLogger()
    h = logging.handlers.RotatingFileHandler('out.log', 'a', 300, 10)
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    h.setFormatter(f)
    root.addHandler(h)

# 从队列获取元素，并写日志
def listener_process(queue, configurer):
    configurer()
    while False:
        try:
            record = queue.get()
            if record is None:  
                break
            logger = logging.getLogger(record.name)
            logger.handle(record) 
        except Exception:
            import sys, traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

# 业务进程的日志配置，使用queueHandler, 将要写的日志塞入队列
def worker_configurer(queue):
    h = logging.handlers.QueueHandler(queue)  
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)


def runs_in_subprocess(queue, configurer):
    configurer(queue)
    print("About to log...")
    logging.debug("hello, I did something: %s", multiprocessing.current_process().name)
    print("...logged, %s",queue.qsize())


if __name__ == '__main__':
    queue = multiprocessing.Queue(-1)
    listener = multiprocessing.Process(target=listener_process,
                                       args=(queue, listener_configurer))
    listener.start()
    
    #父进程也持续写日志
    worker_configurer(queue)
    def write_logs():
        while True:
            logging.debug("in main process, I just did something")
    Thread(target=write_logs).start()

    while True:
        multiprocessing.Process(target=runs_in_subprocess,
                       args=(queue, worker_configurer)).start()
        sleep(2)
```

在上面代码中，我们设置了一个进程间共享的队列，将每个子进程的写日志操作转换为向队列添加元素，然后由单独的另一个进程将日志写入文件。和文章开始处的问题代码相比，虽然都使用了队列，但此处用的是进程共享队列，不会随着`fork`子进程而出现多个拷贝，更不会出现给子进程拷贝了一个已经占用了的锁的情况。

#### spawn

出现死锁的另外一层原因是我们只进行了`fork`, 但是没有进行`execve`, 即子进程仍然和父进程享有同样的内存空间导致，因此另一种解决方法是在fork后紧跟着执行`execve`调用，对应于python中的`spawn`操作，修改后的代码如下：

```
if __name__ == '__main__':
    setup_logging()

    while True:
        # 使用spawn类型的启动
        with get_context("spawn").Pool() as pool:
            pool.apply(runs_in_subprocess)
```

使用`spawn`方法时，父进程会启动一个新的 Python 解释器进程。 子进程将只继承那些运行进程对象的 `run()`方法所必须的资源，来自父进程的非必需文件描述符和句柄将不会被继承，因此使用此方法启动进程会比较慢，但是安全。

### 参考

https://pythonspeed.com/articles/python-multiprocessing/

https://docs.python.org/3/howto/logging-cookbook.html#using-logging-in-multiple-modules

https://stackoverflow.com/questions/24509650/deadlock-with-logging-multiprocess-multithread-python-script

https://docs.python.org/zh-tw/3/library/multiprocessing.html