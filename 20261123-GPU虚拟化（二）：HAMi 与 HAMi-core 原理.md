---
date: 2026-11-23
tags:
  - GPU
  - GPU虚拟化
  - HAMi
  - HAMi-core
  - Kubernetes
  - LD_PRELOAD
categories: 云原生
title: GPU虚拟化（二）：HAMi 与 HAMi-core 原理
---

## 一、承接上篇：在 Kubernetes 里，我们需要怎样的 GPU 切分？

上一篇我们聊了 NVIDIA MIG。它像给大平层砌承重墙一样，在硬件层面把一张大 GPU 物理隔开，性能几乎零损耗、隔离性拉满。

但一旦把视角放到真实的 **Kubernetes 集群**里，MIG 的短板就非常明显了：

- 集群里大量存量卡是 **T4、V100、A10、L40**，根本不支持 MIG；
- 业务需求五花八门：有人只要 **2GB 显存**跑 Embedding，有人要 **12GB 显存 + 30% 算力**跑小模型，固定规格的 MIG 切不出这么细的粒度；
- 静态预切分在 K8s 里极易产生规格碎片——整张卡空着，却因为规格对不上导致 Pod 一直 Pending。

于是问题变成了：**能不能不依赖特殊硬件，在软件层面把任意一张 GPU 按需切分，并且无缝融入 Kubernetes 的调度体系？**

答案就是 CNCF 开源项目 **HAMi**（Heterogeneous AI Computing Virtualization Middleware，异构 AI 算力虚拟化中间件）以及它最核心的底层组件 **HAMi-core**。

---

## 二、理清架构：HAMi 和 HAMi-core 是什么关系？

很多人容易把 **HAMi** 和 **HAMi-core** 混为一谈，其实它们是**整体与底层核心模块**的关系：

- **HAMi** 是整套 Kubernetes 异构算力管理平台（Go 语言为主），相当于“**大管家**”，负责集群里的资源上报、调度选卡、账本管理、容器注入；
- **HAMi-core** 是 HAMi 旗下的底层 C/C++ 核心库（独立仓库，编译产物就是 **`libvgpu.so`**），相当于装在每个业务容器里的“**门禁**”，专门通过 `LD_PRELOAD` 实现 NVIDIA GPU 的软件层隔离。

```mermaid
flowchart TB
    subgraph HAMi["HAMi 整体架构（Kubernetes 侧）"]
        direction TB
        Sched["调度层<br/>HAMi Scheduler / 对接 Volcano Scheduler<br/>（维护全局显存/算力账本，决定 Pod 落到哪张物理卡）"]
        DP["节点设备插件层（Device Plugin DaemonSet）<br/>（发现节点 GPU、上报资源、启动容器时挂载设备并注入隔离库）"]
        Sched -->|"选卡结果写入 Pod Annotation"| DP
    end

    subgraph Iso["容器内隔离层（底层具体实现，可按需选择）"]
        direction LR
        Core["HAMi-core (libvgpu.so)<br/>软件切分：LD_PRELOAD 拦截 CUDA/NVML"]
        DMIG["Dynamic MIG<br/>硬件切分：按 Pod 请求动态创建/回收 MIG 实例"]
        Other["异构卡适配<br/>昇腾 / 寒武纪 / 海光等"]
    end

    DP --> Core
    DP --> DMIG
    DP --> Other
```

这里顺带解开一个常见疑惑：**为什么说 HAMi 既能做软件切分，又能管 MIG？**

因为 HAMi 本身是一个上层调度与管理框架。在节点上：
- 如果卡不支持 MIG，或者你想按 MB / 1% 任意细粒度切分，就用 **HAMi-core 模式**（软件切分）；
- 如果节点上是 A100/H100 且你想要硬件强隔离，HAMi 也支持 **Dynamic MIG 模式**——平时不提前把卡切死，等 Pod 来了，HAMi 根据 Pod 申请的规格**自动调用接口动态切出一个 MIG 实例**给它，Pod 结束后自动回收，顺手解决了上篇提到的静态 MIG 碎片痛点。

理清整体架构后，最核心的问题就落到了 `libvgpu.so`（HAMi-core）身上：它是如何在不改一行 PyTorch 代码的前提下，拦住容器里的 CUDA 调用的？这就需要了解两个很基础的 Linux 底层概念：**动态链接器（`ld.so`）** 和 **`LD_PRELOAD`**。

---

## 三、底层原理：动态链接器（`ld.so`）与 `LD_PRELOAD`

### 3.1 什么是动态链接器（`ld.so`）？

我们平时写的程序（比如 `python`），里面会调用大量公共函数——比如打印日志用的 `printf`、申请内存用的 `malloc`，或者操作显卡用的 CUDA 函数 `cuMemAlloc`。

编译程序时，处理这些公共库有两种方式：

- **静态链接**：编译时把所有依赖库的代码全部复制打包进可执行文件。优点是独立性强，缺点是文件巨大，且多个进程无法共享同一份库代码。
- **动态链接（Linux 默认方式）**：编译时**不复制库代码**，只在可执行文件里留一张“依赖清单”（需要哪些 `.so` 共享库、要调用哪些函数名），等程序真正启动时再去加载系统里的 `.so` 文件。

正因为库代码不在可执行文件里，程序运行前必须有一个“搬运工 + 接线员”先把库装进来——这个角色就是 **动态链接器（`ld.so`）**（在 64 位 x86 Linux 上，它通常是 `/lib64/ld-linux-x86-64.so.2`）。

当你敲下 `python train.py` 时，幕后其实发生了这 4 步：

1. **内核先唤醒 `ld.so`**：Linux 内核发现这个程序是动态链接的，不会直接运行它的 `main()`，而是先把 `ld.so` 跑起来。
2. **加载 `.so` 库**：`ld.so` 读取程序的依赖清单（用 `ldd /bin/ls` 就能看到这张清单），按顺序把需要的 `.so`（如 `libc.so`、`libcuda.so`）映射到内存。
   > 日常开发中遇到 `error while loading shared libraries: libxxx.so: cannot open shared object file`，就是 `ld.so` 在这一步找不到库文件报的错。
3. **符号解析（接线）**：程序里只写了“我要调 `cuMemAlloc`”，但不知道它在内存哪个地址。`ld.so` 就按加载顺序去 `.so` 里查表，把找到的**第一个**同名函数的内存地址填进程序里。
4. **交出控制权**：线全部接好后，`ld.so` 跳转到程序的 `main()`，你的程序才正式开始执行。

### 3.2 什么是 `LD_PRELOAD`？

注意上面第 3 步里一个极其关键的规则：**`ld.so` 查找函数地址时是“先到先得”的**。

而 **`LD_PRELOAD`** 就是 Linux 动态链接器提供的一个环境变量（也可以通过 `/etc/ld.so.preload` 文件全局配置），作用非常霸道：

> **强制让 `ld.so` 在加载任何其他共享库之前，先把我指定的 `.so` 库排在最前面加载。**

这意味着什么？

假设程序原本要调用官方 `libcuda.so` 里的 `cuMemAlloc()` 来申请显存。现在 HAMi-core 编译出的 `libvgpu.so` 里也定义一个**一模一样名字**的 `cuMemAlloc()`，并在容器启动时设置 `LD_PRELOAD=/path/to/libvgpu.so`。

程序启动时，`ld.so` 先加载了 `libvgpu.so`，再加载 `libcuda.so`。等接线时，`ld.so` 第一个找到的就是 `libvgpu.so` 里的 `cuMemAlloc()`！

```mermaid
flowchart LR
    subgraph Normal["正常情况（无 LD_PRELOAD）"]
        A1["PyTorch"] -->|"调用 cuMemAlloc()"| B1["官方 libcuda.so"] --> C1["GPU 驱动分配显存"]
    end

    subgraph Preload["设置 LD_PRELOAD=libvgpu.so 后"]
        A2["PyTorch"] -->|"调用 cuMemAlloc()"| Hook["libvgpu.so 的 cuMemAlloc()<br/>（先被拦截检查配额）"]
        Hook -->|"超过配额"| Deny["直接返回 OOM 错误"]
        Hook -->|"未超配额<br/>dlsym(RTLD_NEXT)"| B2["官方 libcuda.so"] --> C2["GPU 驱动分配显存"]
    end
```

打个比方，这就像在电话线路中间串了一个**接线员**：程序以为自己在直接给 CUDA 打电话，其实请求先经过了 `libvgpu.so` 检查——合规就转接给真正的 CUDA（通过 `dlsym(RTLD_NEXT, ...)` 找到下一个库里的原函数），超标就直接挂断。

**最妙的地方在于：整个过程对业务代码完全透明、零侵入。** PyTorch、TensorFlow、业务镜像一行代码都不用改。

---

## 四、一个 vGPU Pod 在 K8s 里是怎么跑起来的？

假设你的 Kubernetes 集群里有一台装有 **1 张 80GB A100** 的节点，已经部署好了 HAMi（或 Volcano + HAMi Device Plugin）。现在两个开发者分别提交了 Pod A（要 10GB 显存、20% 算力）和 Pod B（要 15GB 显存、30% 算力）。

完整流程如下：

```mermaid
sequenceDiagram
    participant User as 开发者
    participant Sched as 调度器 (HAMi / Volcano)
    participant Kubelet as 节点 Kubelet
    participant DP as HAMi Device Plugin
    participant Pod as 业务容器 (PyTorch + libvgpu.so)

    User->>Sched: 提交 Pod A（1 vGPU, 10GB 显存, 20% 算力）
    Sched->>Sched: 查账：Node-1 的 GPU-0 剩余 80GB/100%，够用！
    Sched->>Kubelet: 绑定到 Node-1，并将选中的 GPU-0 写入 Pod Annotation
    Kubelet->>DP: 调用 Allocate() 准备设备
    DP-->>Kubelet: 返回 GPU-0 设备 + 挂载 libvgpu.so + 设置 LD_PRELOAD 与限额环境变量
    Kubelet->>Pod: 启动容器
    Pod->>Pod: 运行 PyTorch，CUDA 调用被 libvgpu.so 实时拦截与限流
```

拆解成 4 个关键步骤：

### 第 1 步：Pod 按需申请资源

开发者不再写 `nvidia.com/gpu: 1`，而是直接声明自己需要的显存和算力（不同接入方式资源名略有差异，以下是 HAMi / Volcano 的典型写法）：

```yaml
resources:
  limits:
    nvidia.com/gpu: 1          # 申请 1 块 vGPU（Volcano 下为 volcano.sh/vgpu-number）
    nvidia.com/gpumem: 10000   # 显存上限 10000 MB（约 10GB）
    nvidia.com/gpucores: 20    # 算力上限 20%
```

### 第 2 步：调度器记账与选卡

调度器手里维护着集群里**每一张物理 GPU** 的实时账本：
- 给 Pod A 分配 GPU-0 后，账本扣减为剩余 `70GB / 80%`；
- 紧接着 Pod B 来了，账本依然够用，于是也调度到**同一张物理 GPU-0**，账本扣减为剩余 `55GB / 50%`。
- 调度器会把“具体选了哪张物理卡（UUID）”写进 Pod 的 Annotation 里。

### 第 3 步：Device Plugin 注入“门禁”

容器启动前，kubelet 调用节点上的 HAMi Device Plugin：
- 插件读取 Pod Annotation，把对应的物理 GPU-0 挂载进容器；
- **最关键的一步**：插件把宿主机上的 `libvgpu.so`（HAMi-core）挂载进容器，通过 `LD_PRELOAD`（或 `/etc/ld.so.preload`）使其生效，并注入环境变量告知该容器的配额（`10GB` 显存、`20%` 算力）。

### 第 4 步：容器运行期，HAMi-core 接管三大核心能力

容器启动后，PyTorch 跑起来，HAMi-core 就在幕后默默干三件事：

1. **显存硬限制**：拦截 `cuMemAlloc` 等显存分配与释放 API，并在容器内通过**共享内存账本**持续统计所有进程的累计显存用量。如果 Pod A 累计申请超过 10GB，即使物理卡还剩 55GB 空闲，`libvgpu.so` 也会直接返回 OOM，保护同卡上的 Pod B 不被挤爆。
2. **算力配额控制**：拦截 `cuLaunchKernel` 等 CUDA Kernel（计算核函数）的提交调用。`libvgpu.so` 会在很短的时间窗口内采样当前容器的算力使用占比，一旦超过 20%，就在 CPU 侧让后续 Kernel 提交短暂 `sleep` 排队，从而把平均算力平滑压在 20% 左右。
3. **视图虚拟化**：拦截 NVML 查询接口。当你在 Pod A 里敲 `nvidia-smi` 时，看到的显存总量就是 **10000 MiB**，而不是整张物理卡的 80GB，让容器觉得自己真的独占了一张 10GB 的小卡。

---

## 五、没有银弹：HAMi-core 的局限性

看完上面的原理，HAMi-core 听起来几乎完美：不挑卡型、按需切分、业务代码零侵入。但它的优势来自**基于 `LD_PRELOAD` 的用户态 API 劫持**，短板也同样源于此：

1. **软隔离：防不住故障波及，也挡不住“噪声邻居”**
   同卡上的所有容器共享同一张物理 GPU 和宿主机驱动：一旦某个容器触发严重的驱动或硬件异常，同卡上的其他容器可能会被连带牵连；同时缓存和显存带宽并没有切分，邻居密集读写时依然会影响你的任务速度。此外，拦截发生在用户态，权限管控不严时存在绕过风险，不适合完全不可信的公有云强隔离场景。
2. **算力限流是“事后拉平”，容易带来延迟抖动**
   HAMi-core 无法像硬件那样把算力切死，也不能打断正在执行的计算任务，只能通过时间窗口采样 + 在 CPU 侧让后续请求短暂 `sleep` 来拉平平均算力。如果某个任务提交了耗时很长的大计算，会先吃满整张卡再通过后续排队“还债”，因此对延迟敏感的在线推理容易出现耗时抖动。
3. **显存统计存在误差，需要预留缓冲余量**
   API 拦截主要统计业务主动申请的显存，但驱动为每个进程维护的上下文等底层开销很难 100% 精确统计。实际使用时通常需要给物理卡预留一点显存余量，避免出现“账本没超、物理卡却 OOM”的情况。
4. **强依赖动态链接与 CUDA 生态，有一定兼容性成本**
   因为靠 `LD_PRELOAD` 拦截 CUDA 接口，静态编译的程序会直接失效，非 CUDA 生态的调用也管不到；此外，当 CUDA 或 PyTorch 升级引入新的内存/计算接口时，HAMi-core 也需要同步跟进适配。

> 一句话概括：HAMi-core 是用“**隔离强度、延迟稳定性、以及一定的版本适配成本**”，换取了“**不挑卡型、任意细粒度切分、极高集群利用率**”。

---

## 六、总结：怎么选，以及更底层在做什么？

回头看这两篇聊到的两种切分路线，其实各有取舍：如果业务追求**硬件级强隔离**和稳定的尾延迟，手里又有 A100 / H100 这类高端卡，选 **MIG** 最稳妥；如果更看重**灵活性和集群利用率**，或者集群里主要是 T4、A10、L40 等不支持 MIG 的存量卡，那么软件层的 **vGPU 方案**会实用得多。

当然，两者在工程落地时并不是非此即彼的。像 **HAMi** 这样的上层框架，底层既支持用 `HAMi-core` 做软件 vGPU，也支持 **Dynamic MIG**（按 Pod 请求动态切分与回收 MIG 实例），一定程度上已经把 MIG 方案也覆盖进了同一套调度体系里。

另一方面，纯用户态的 API 拦截（`LD_PRELOAD`）本身存在一定的拦截开销和算力限流抖动，在多租户公有云场景下也更容易受到用户态绕过或 CUDA 版本变化的影响。这也是为什么不少云厂商会选择往下再走一步，自研**内核态拦截**的 GPU 虚拟化方案——比如阿里云的 **cGPU**、腾讯云的 **qGPU**，将显存管控与算力调度下沉到内核/驱动层，以换取更低的运行时损耗、更精准的隔离以及更高的安全性（相应的代价，则是与宿主机内核和驱动版本强绑定，研发与维护门槛更高）。


