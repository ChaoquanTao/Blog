---
title: 浅谈Go语言中的Channel
date: 2026-05-03 12:00:00
categories: Go
---

#### 1. 根本问题：并发程序如何安全地共享数据？

并发的本质矛盾是：多个执行流（goroutine）需要**协作**，但同时访问共享内存会导致数据竞争。

解决思路有两条：

- **共享内存 + 锁**：大家都能访问，但要抢锁（mutex）
- **消息传递**：数据的所有权随消息转移，不共享

Go 选择了后者，并将其哲学浓缩为一句话：

> *"Don't communicate by sharing memory; share memory by communicating."*

Channel 就是这个哲学的具体实现。

------

#### 2. 最小模型：channel 需要什么？

从第一性原理出发，一个"安全的数据传递管道"至少需要：



```
发送方  ──[数据]──▶  [ 缓冲区? ]  ──▶  接收方
```

| 需求                  | 对应机制                    |
| --------------------- | --------------------------- |
| 存放数据              | 环形缓冲队列（ring buffer） |
| 多方竞争访问时互斥    | 内部 mutex                  |
| 没数据时接收方等待    | recvq 等待队列              |
| 缓冲满时发送方等待    | sendq 等待队列              |
| goroutine 的挂起/唤醒 | Go runtime 调度器           |

------

#### 3. 数据结构：`hchan`

channel 的底层结构体（`runtime/chan.go`）：



go

```go
type hchan struct {
    qcount   uint           // 缓冲区当前元素数
    dataqsiz uint           // 缓冲区容量（make 时指定）
    buf      unsafe.Pointer // 指向环形缓冲区
    elemsize uint16         // 每个元素的大小
    closed   uint32         // 是否已关闭
    elemtype *_type         // 元素类型（用于 GC）

    sendx uint  // 下一个写入位置（send index）
    recvx uint  // 下一个读取位置（recv index）

    recvq waitq // 等待接收的 goroutine 队列
    sendq waitq // 等待发送的 goroutine 队列

    lock mutex  // 保护以上所有字段
}
```

环形缓冲区的工作方式：



```
buf: [ _ | A | B | C | _ | _ ]
           ↑               ↑
         recvx           sendx
         (读出)          (写入)
```

`sendx` 和 `recvx` 自动取模，实现循环复用，无需移动数据。

------

#### 4. 三条核心路径

##### 路径一：发送（`ch <- v`）



```
发送数据
   │
   ├─ recvq 有等待的 goroutine？
   │      └─ YES → 直接把数据拷贝给它，唤醒它（zero-copy 快路径）
   │
   ├─ 缓冲区有空位？
   │      └─ YES → 写入 buf[sendx]，sendx++，返回
   │
   └─ 都不满足 → 把自己（sudog）加入 sendq，挂起当前 goroutine
```

##### 路径二：接收（`v := <-ch`）



```
接收数据
   │
   ├─ sendq 有等待的 goroutine？
   │      ├─ 无缓冲 ch → 直接从它拷贝数据，唤醒它
   │      └─ 有缓冲 ch → 取 buf 头部，把 sendq 头部的数据补入 buf 尾部
   │
   ├─ 缓冲区有数据？
   │      └─ YES → 读取 buf[recvx]，recvx++，返回
   │
   └─ 都不满足 → 把自己加入 recvq，挂起当前 goroutine
```

##### 路径三：关闭（`close(ch)`）



```
close(ch)
   │
   ├─ 设置 closed = 1
   ├─ 唤醒所有 recvq 中的 goroutine（返回零值 + false）
   └─ 唤醒所有 sendq 中的 goroutine（panic：send on closed channel）
```

------

#### 5. goroutine 的挂起与唤醒

这是 channel 能"阻塞"的关键。Go 用 `sudog`（sudo goroutine）结构记录等待状态：



go

```go
type sudog struct {
    g       *g            // 被挂起的 goroutine
    elem    unsafe.Pointer // 数据指针（发送的值 或 接收的目标地址）
    next    *sudog
    prev    *sudog
    ...
}
```

挂起时：调用 `gopark()`，将 goroutine 状态从 `_Grunning` 改为 `_Gwaiting`，让出 P（处理器），调度器去运行其他 goroutine。

唤醒时：调用 `goready()`，将 goroutine 重新放入运行队列。

**这是用户态调度，不涉及操作系统线程挂起，成本极低。**

------

#### 6. 无缓冲 vs 有缓冲：本质区别



```
无缓冲 make(chan T)
   发送方必须等到接收方就位才能继续
   → 强同步，像"握手"

有缓冲 make(chan T, N)
   发送方最多可以"甩出" N 个值就走
   → 弱同步，像"邮箱"
```

无缓冲 channel 的直接拷贝路径（发送方 → 接收方栈，跳过 buf）是一个重要优化，避免了一次内存分配。

------

#### 7. `select` 的实现原理

`select` 本质是"多路 channel 的竞争等待"：

1. **随机打乱** case 顺序（防饥饿）
2. **加锁所有涉及的 channel**（按地址排序，防死锁）
3. 依次检查是否有 case 可以立即执行
4. 若都不行，把自己注册到**每一个** channel 的等待队列
5. 任意一个 channel 就绪后，从其他 channel 的等待队列中移除自己

------