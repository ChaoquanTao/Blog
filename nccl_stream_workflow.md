# NCCL + GPU 队列 + Stream 的工作流程

> 记录一次 DDP 训练排障中，对 CUDA stream / GPU 队列 / NCCL 执行模型工作流程的理解。

## 0. 核心图像：GPU 是"异步的干活机器"，靠队列组织任务

CPU 说"去算这个" → **立刻返回**，不等结果。那"先算 A 再算 B"怎么保证？靠**队列**。这个队列就叫 **Stream**。

```
stream = 一条 FIFO 队列（先进先出）
GPU 从队列头一个个取任务执行
```

### Stream 三条铁律

| 规则 | 含义 |
|---|---|
| 同一条 stream **内有序** | A 入队早于 B → A 一定先执行完 |
| 不同 stream **间并行** | 硬件能重叠就重叠（拷贝和计算、多条 stream 同时跑） |
| 入队是**异步** | CPU 塞完就往下走；要结果得显式同步 |

### 同步的两种方式

- `stream.synchronize()` —— 等这条队列全空（粗暴，阻塞）
- `event`（路标）—— 在队列某点插一个标记，另一条 stream `wait_event` 它（精确、不阻塞整体）

> PyTorch 每个 device 有一个"当前 stream"（`current_stream`），前向/反向默认都塞进这条。

## 1. NCCL 比普通 CUDA 多了哪几层

NCCL 干的事：把"多卡/多机的集合操作（all-reduce、broadcast…）"做快。它在 stream 模型上**加了三样东西**：

```
                       ┌─────────────────────────────────────────┐
  一个 collective  →    │ Communicator（通信器，懒创建）              │
                       │   记得：组成员、拓扑(NVLink/PCIe/IB)、buffer │
                       ├─────────────────────────────────────────┤
                       │ 切成 n 条 Channel                          │
                       │   每条 channel = 一条独立 CUDA stream      │
                       ├─────────────────────────────────────────┤
                       │ Proxy 线程（CPU）                          │
                       │   专门驱动跨节点网络(IB/RoCE)的收发         │
                       └─────────────────────────────────────────┘
```

- **Communicator**：每个 rank 建一个；**第一次真正通信时才建**（`ncclCommInitRank`：bootstrap 交换、拓扑探测、分配 buffer、建 stream）。异常场景下 `invalid resource handle` 常爆在"建它 + 第一次 launch kernel"这里。
- **Channel**：把一个大 all-reduce **切成 n 份并行跑**，每份绑定一条自己的 stream，多通道 = 更高并行度（受带宽限制）。
- **两种执行路径**：同节点的卡走 **NVLink/PCIe，直接 launch GPU kernel** 互读显存；跨节点走 **Proxy 线程 → 网卡 DMA**，GPU kernel 靠显存里的 flag 和 proxy 握手。

## 2. 一次 all-reduce 的完整工作流程（带时序）

以 DDP 反向梯度同步为例：

```
CPU 主线程                 PyTorch DDP / PG-NCCL              NCCL 内部                    GPU / 网卡
   │
   │ loss.backward()
   ├──────────────▶ bucket 攒满 → all_reduce(bucket, 当前stream)
   │                     │
   │                     │ ① 在当前stream上 record event E1（"本地数据到齐了"）
   │                     │ ② NCCL内部stream  wait_event E1
   │                     │ ③ ncclAllReduce(comm, 内部stream)
   │                     ├──────────────────────────────▶ 把活拆到 n 条 channel-stream
   │                     │                                  ├─ ch0 stream: [拷贝/规约 kernel] ─NVLink→ 对端
   │                     │                                  ├─ ch1 stream: [...]
   │                     │                                  └─ proxy线程: 跨节点 IB 收发
   │                     │                                        （kernel 在 GPU 上原地等待，
   │                     │                                          直到所有 rank 数据到齐、规约完成）
   │                     │ ④ 完成后 内部stream record event E2
   │  ◀──────────────────┤ ⑤ 当前stream wait_event E2
   │  主线程继续（全程异步） ▼
```

### 关键点

- **入队即返回**：`all_reduce()` 调完 CPU 不阻塞；真正的等待发生在 **GPU kernel 内部**（kernel 自己会卡到 collective 达成）。
- **用 event 交接**：用户 stream ⇄ NCCL 内部 stream 之间靠 event 串接——既保证"后续算子看到规约后的结果"（正确性），又允许**通信和计算重叠**（这就是 DDP 能把通信藏进反向传播空隙的原理）。
- **多个 collective 可 `ncclGroupStart/End` 打包**一起提交，减少开销、避免死锁。

## 3. 三层"队列"别混淆

```
你的算子     ──塞进──▶  用户 stream（当前 stream）
                              │ event 交接
                              ▼
NCCL 的活     ──塞进──▶  NCCL 的 n 条 channel-stream（内部）
                              │  加上
                              ▼
跨节点数据   ──驱动于──▶  Proxy 线程的发送/接收队列（CPU 侧，网卡）
```

- **stream**：软件层面的"有序队列"（用户 / NCCL 各有）。
- **channel**：NCCL 把一条 collective 拆成的并行单元，每个绑定一条 stream。
- **proxy**：网卡的"搬运工线程"，负责真正把字节发出去 / 收进来。

## 4. 一句话总结

**Stream 是 GPU 的"有序工作队列"；NCCL 在它之上加了 communicator（懒建的通信器）+ 多条 channel-stream（把集合操作切分并行）+ proxy 线程（驱动网络），用户 stream 和 NCCL 内部 stream 之间用 event 交接——于是通信既正确、又能和计算重叠。** 而这整套"队列 + stream + kernel launch"机制，第一次搭起来就是第一个 collective（如 mmengine `setup_env` 的 `broadcast`），所以 CUDA 环境一坏，错误精确爆在那里。

## 5. 观察手段

```bash
# 看 communicator / channel / proxy 建立全过程
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,NET,GRAPH python tools/train.py ...

# 看 stream / kernel / 通信在时间轴上的重叠（最直观）
nsys profile -o prof python tools/train.py ...

# 看动态链接最终解析到哪个 libcudart / libnccl（排查版本混搭）
LD_DEBUG=libs python -c "import torch" 2>&1 | grep -iE "libcudart|libnccl|libcuda\.so"
```

