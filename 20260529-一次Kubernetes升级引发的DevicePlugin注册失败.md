---
title: 一次Kubernetes升级引发的Device Plugin注册失败
date: 2026-05-29 12:00:00
categories: Kubernetes
---



最近把一个 Kubernetes 集群从旧版本升级到了新版本，集群里跑着一个自研的 device plugin（以 DaemonSet 形式部署）。升级前一切正常，升级后这个 DaemonSet 一启动就疯狂报错：

```
Set vendor name: example.com
Set resource name: cool-device
Set device number: 8
E  Device plugin register failed, err: rpc error: code = Unknown
   desc = failed to dial device plugin: context deadline exceeded
```

诡异的地方在于：**代码一行没改，镜像还是同一个**，只是集群版本变了。报错说的是"注册（register）失败"，错误内容却是"拨号（dial）超时"——到底是谁在向谁拨号？这篇文章就从 device plugin 的原理出发，把这个问题彻底讲清楚。

------

### 1. 什么是 Device Plugin

#### 1.1 它解决什么问题

Kubernetes 调度器天生只认识两种资源：CPU 和内存。你可以在 Pod 里写 `requests.cpu: 500m`、`requests.memory: 1Gi`，调度器据此把 Pod 放到合适的节点上。

但现实世界里节点上还有大量**异构设备**：GPU、RDMA 网卡、FPGA、TPU、各种加密卡……这些设备 Kubernetes 默认一无所知。如果想让 Pod 能声明 `requests: nvidia.com/gpu: 2`，就需要有人告诉 kubelet：

1. 这个节点上有哪些这种设备、有几个、健不健康；
2. 当某个 Pod 申请了这种设备，要怎么把设备真正"塞"进容器里（挂设备文件、设环境变量等）。

把硬件细节硬编码进 kubelet 显然不现实——厂商太多、设备太杂。于是 Kubernetes 提供了一个**扩展点**：Device Plugin 框架。kubelet 定义好一套 gRPC 接口，谁想接入自己的设备，就实现这套接口、注册进来即可。这是典型的"机制与策略分离"。

#### 1.2 基本架构

Device plugin 本质上是一个 gRPC server，通常以 DaemonSet 部署到每个节点，与该节点的 kubelet 通过节点本地的 **Unix domain socket** 通信。

```
        ┌────────────── Node ──────────────┐
        │                                   │
        │   ┌─────────────┐    gRPC over    │
        │   │   kubelet    │◀──unix socket──▶│   ┌──────────────────┐
        │   └─────────────┘                 │   │  device plugin   │
        │         ▲                          │   │   (DaemonSet)    │
        │         │ 上报 / 分配              │   └──────────────────┘
        │   /var/lib/kubelet/device-plugins/ │
        │     ├── kubelet.sock  (kubelet 监听)│
        │     └── cool.sock     (插件监听)    │
        └───────────────────────────────────┘
```

关键约定：

- kubelet 在 `/var/lib/kubelet/device-plugins/kubelet.sock` 上监听一个**注册服务**；
- 插件自己也在同目录下创建一个 socket（如 `cool.sock`）作为自己的 gRPC server；
- 因为要访问 kubelet 的 socket 目录，插件 Pod 通常需要 `hostPath` 挂载该目录，并以 `privileged` 运行。

#### 1.3 工作原理：四个接口 + 一次握手

device plugin 需要实现的核心 gRPC 接口只有四个：

| 接口 | 作用 |
| --- | --- |
| `GetDevicePluginOptions` | 声明插件能力（是否需要 PreStartContainer 等），一般返回空 |
| `ListAndWatch` | **流式接口**，持续向 kubelet 上报设备列表及健康状态 |
| `Allocate` | Pod 真正要用设备时被调用，返回需要注入容器的环境变量、设备文件、挂载等 |
| `GetPreferredAllocation` | 可选，给 kubelet 提供设备分配偏好 |

而插件接入 kubelet 的过程，是一次**双向握手**。注意这里有个容易忽略的细节：注册请求是插件主动发起的，但建立设备上报通道却是 **kubelet 反过来拨号连插件**。整个时序如下：

<svg xmlns="http://www.w3.org/2000/svg" width="640" height="380" font-family="monospace" font-size="13">
  <!-- lifelines -->
  <text x="120" y="24" text-anchor="middle" font-weight="bold">device plugin</text>
  <text x="500" y="24" text-anchor="middle" font-weight="bold">kubelet</text>
  <line x1="120" y1="34" x2="120" y2="360" stroke="#888" stroke-dasharray="4 3"/>
  <line x1="500" y1="34" x2="500" y2="360" stroke="#888" stroke-dasharray="4 3"/>
  <!-- step 1 -->
  <rect x="60" y="50" width="120" height="30" fill="#eef" stroke="#557"/>
  <text x="120" y="69" text-anchor="middle">① Start()</text>
  <text x="120" y="98" text-anchor="middle" fill="#555">listen cool.sock</text>
  <!-- step 2: register -->
  <line x1="120" y1="120" x2="500" y2="120" stroke="#333" marker-end="url(#arr)"/>
  <text x="310" y="113" text-anchor="middle">② Register(endpoint, resourceName)</text>
  <!-- step 3: dial back -->
  <line x1="500" y1="160" x2="120" y2="160" stroke="#c33" marker-end="url(#arr)"/>
  <text x="310" y="153" text-anchor="middle" fill="#c33">③ dial back → connect cool.sock</text>
  <text x="310" y="178" text-anchor="middle" fill="#c33">（问题就出在这一步）</text>
  <!-- step 4: listandwatch -->
  <line x1="120" y1="210" x2="500" y2="210" stroke="#333" marker-end="url(#arr)"/>
  <text x="310" y="203" text-anchor="middle">④ ListAndWatch → 上报设备列表</text>
  <!-- step 5: register returns -->
  <line x1="500" y1="250" x2="120" y2="250" stroke="#333" marker-end="url(#arr)"/>
  <text x="310" y="243" text-anchor="middle">⑤ Register 返回成功</text>
  <!-- step 6: allocate -->
  <line x1="500" y1="300" x2="120" y2="300" stroke="#393" marker-end="url(#arr)"/>
  <text x="310" y="293" text-anchor="middle" fill="#393">⑥ Pod 调度后 → Allocate()</text>
  <line x1="120" y1="330" x2="500" y2="330" stroke="#393" marker-end="url(#arr)"/>
  <text x="310" y="323" text-anchor="middle" fill="#393">返回 envs / devices 注入容器</text>
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#333"/>
    </marker>
  </defs>
</svg>

请记住第 ① 步和第 ③ 步的关系：**插件必须先把自己的 gRPC server 起起来（socket 可被连接），kubelet 才能在注册时成功反向拨号。** 本文的 bug 正是踩在这里。

#### 1.4 一个最小的 Device Plugin 怎么写

下面用一段去掉所有业务细节的 Go 伪代码，展示一个最小可用的 device plugin 骨架（基于 `k8s.io/kubelet/pkg/apis/deviceplugin/v1beta1`）。

**实现四个接口**（这里只展示最关键的 `ListAndWatch` 和 `Allocate`）：

```go
// ListAndWatch：把本节点的设备列表推给 kubelet，并持续保持这个流
func (p *Plugin) ListAndWatch(_ *api.Empty, srv api.DevicePlugin_ListAndWatchServer) error {
    // 首次把全部设备推过去
    srv.Send(&api.ListAndWatchResponse{Devices: p.devices})
    // 之后阻塞住；如果设备健康状态变化，再 Send 一次新的列表
    for range p.health {
        srv.Send(&api.ListAndWatchResponse{Devices: p.devices})
    }
    return nil
}

// Allocate：Pod 真正使用设备时被 kubelet 调用
func (p *Plugin) Allocate(_ context.Context, reqs *api.AllocateRequest) (*api.AllocateResponse, error) {
    var resp api.AllocateResponse
    for _, req := range reqs.ContainerRequests {
        resp.ContainerResponses = append(resp.ContainerResponses, &api.ContainerAllocateResponse{
            // 把分到的设备 ID 以环境变量形式注入容器
            Envs: map[string]string{
                "COOL_VISIBLE_DEVICES": strings.Join(req.DevicesIDs, ","),
            },
            // 真实场景里这里还会有 Devices（挂 /dev/xxx）、Mounts 等
        })
    }
    return &resp, nil
}
```

**启动 gRPC server（Start）与向 kubelet 注册（Register）**：

```go
// Start：清理旧 socket、生成设备、启动 gRPC server 并开始 listen
func (p *Plugin) Start() error {
    os.Remove(p.socketPath)                       // 清理残留 socket
    p.generateDevices()                           // 生成本节点设备列表
    lis, err := net.Listen("unix", p.socketPath)  // 在自己的 socket 上监听
    if err != nil {
        return err
    }
    p.server = grpc.NewServer()
    api.RegisterDevicePluginServer(p.server, p)
    go p.server.Serve(lis)                        // 后台 serve
    return nil
}

// Register：拨号 kubelet.sock，告诉 kubelet "我是谁、我的 socket 在哪"
func (p *Plugin) Register() error {
    conn, err := dial(kubeletSocket, 5*time.Second)
    if err != nil {
        return err
    }
    defer conn.Close()

    client := api.NewRegistrationClient(conn)
    _, err = client.Register(context.Background(), &api.RegisterRequest{
        Version:      api.Version,
        Endpoint:     filepath.Base(p.socketPath), // 只传文件名，kubelet 自己拼目录
        ResourceName: "example.com/cool-device",   // 资源名格式：<vendor>/<resource>
    })
    return err
}
```

最后 `main` 里把它们串起来。**注意下面这段顺序——它就是本文 bug 的核心：**

```go
func main() {
    p := NewPlugin()
    // 看似无害的顺序：先注册，再启动
    if err := p.Register(); err != nil {   // ← 这里会在新版本集群里失败
        log.Fatalf("Device plugin register failed, err: %v", err)
    }
    if err := p.Start(); err != nil {
        log.Fatalf("Device plugin start failed, err: %v", err)
    }
    select {} // block forever
}
```

------

### 2. 升级集群后遇到的奇怪问题

把上面这份代码（先 `Register()` 后 `Start()`）打成镜像，在旧版本集群上跑了很久都没问题。直到把集群升级到新版本，DaemonSet 一启动 Pod 就 CrashLoopBackOff，日志稳定停在这一行：

```
E  Device plugin register failed, err: rpc error: code = Unknown
   desc = failed to dial device plugin: context deadline exceeded
```

这里有几个"反直觉"的点，正是它一开始让人摸不着头脑的原因：

1. **代码和镜像完全没变**，唯一变量是集群版本——所以第一反应根本不会怀疑自己的代码；
2. 错误显示在 `Register()` 这一步，但内容是 `failed to dial device plugin`——注册请求明明是插件**主动**发给 kubelet 的，怎么会"拨号设备插件失败"？谁拨谁？
3. `context deadline exceeded` 是个 10 秒超时，说明 kubelet 在等一个永远等不到的连接。

把第 1 节那张握手图拿出来对照，答案其实已经呼之欲出了。

------

### 3. 基于原理的问题分析

#### 3.1 定位：是谁在拨号

回到握手时序图的第 ③ 步：**kubelet 在处理注册请求时，会反过来去连接插件声明的那个 socket**（为了建立 `ListAndWatch` 流）。

而我们的 `main` 里顺序是「先 `Register()`，后 `Start()`」：

```
Register()  ──→ kubelet 收到注册，立刻去 dial 插件的 cool.sock
                     │
                     ▼
              但此时 Start() 还没执行，cool.sock 根本不存在！
                     │
                     ▼
              kubelet 拨号阻塞，10 秒后超时
                     │
                     ▼
       Register() RPC 收到 kubelet 返回的错误：
       "failed to dial device plugin: context deadline exceeded"
```

也就是说，错误信息里的 "device plugin" 指的是**我们自己的插件**，是 kubelet 在抱怨"我连不上你"。根因是 socket 还没就绪，插件就抢先注册了。

#### 3.2 那为什么旧集群一直没事？

如果顺序本来就是错的，为什么旧版本集群从来不报错？这就要看 kubelet 在不同版本里**处理注册请求的方式**了。

**旧版本（Kubernetes ≤ 1.24）**——异步回拨。kubelet 的注册 handler（`pkg/kubelet/cm/devicemanager/manager.go`）收到 `Register` 后，**立即返回成功**，把"反向拨号连插件"丢进一个 goroutine 里异步做：

```go
// v1.24 manager.go 的 Register handler（简化）
func (m *ManagerImpl) Register(ctx context.Context, r *pluginapi.RegisterRequest) (*pluginapi.Empty, error) {
    // ...一些版本/名称校验...
    go m.addEndpoint(r)          // ← 异步！fire-and-forget
    return &pluginapi.Empty{}, nil  // ← 立刻返回成功
}
```

于是时间线变成：`Register()` 瞬间返回成功 → 插件继续执行 `Start()`、socket 建好 → 稍后那个 goroutine 才去拨号，**这时 socket 已经就绪了**。错误的调用顺序被这个"异步 + 时间差"悄悄兜住了，bug 一直潜伏着没暴露。

**新版本（Kubernetes ≥ 1.25）**——同步回拨。注册逻辑被重构到了新的 `pkg/kubelet/cm/devicemanager/plugin/v1beta1/server.go`，那个 goroutine 没了，改成在 handler 里**同步**连接插件，连不上就直接把错误返回给注册请求：

```go
// v1.25 plugin/v1beta1/server.go 的 Register handler（简化）
func (s *server) Register(ctx context.Context, r *api.RegisterRequest) (*api.Empty, error) {
    // ...校验...
    if err := s.connectClient(r.ResourceName, filepath.Join(s.socketDir, r.Endpoint)); err != nil {
        return &api.Empty{}, err   // ← 同步拨号，失败直接返回 error
    }
    return &api.Empty{}, nil
}
```

`connectClient` 内部是一个带 `grpc.WithBlock()`、10 秒超时的阻塞拨号。插件要是还没 listen，这一拨就必然超时——于是我们看到了 `context deadline exceeded`。

一张表对比两个版本的差异：

| | Kubernetes ≤ 1.24 | Kubernetes ≥ 1.25 |
| --- | --- | --- |
| Register handler 回拨方式 | `go m.addEndpoint(r)` 异步 | `connectClient()` 同步 |
| Register 何时返回 | 立即返回成功 | 拨号成功后才返回 |
| 对"错误顺序"的容忍 | 有时间差兜底，掩盖 bug | 零容忍，注册即失败 |
| 现象 | 一切正常 | `failed to dial: context deadline exceeded` |

#### 3.3 版本、PR 与官方说法

这个行为变化的来龙去脉是有据可查的：

- 引入它的是 PR [kubernetes/kubernetes#109016](https://github.com/kubernetes/kubernetes/pull/109016)——"Refactor all device-plugin logic into separate 'plugin' package under the devicemanager"，于 2022 年 5 月合入，**随 Kubernetes v1.25.0 发布**。有意思的是，这个 PR 的本意只是**重构**（为后续支持多版本插件 API 做准备），async → sync 的语义变化其实是个**非预期的副作用**。
- 副作用是后来才被发现的：有人（KubeVirt 的 device plugin）升级后挂了，于是提了 issue [kubernetes/kubernetes#112395](https://github.com/kubernetes/kubernetes/issues/112395) —— "Change in semantics for the device plugin registration process"。维护者讨论后**决定保留新语义而不是回退**，理由是「先起 server 再注册」本来就是更正确、更符合直觉的顺序，而且这个顺序对新老集群都兼容。
- 官方文档与博客也把它确认为新的要求：[Device Plugins 官方文档](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) 描述了标准的注册流程；[Kubernetes 1.26: Device Manager graduates to GA](https://kubernetes.io/blog/2022/12/19/devicemanager-ga/) 这篇博客在 Device Manager 转正时一并把它作为既定行为记录了下来（注意代码变更实际落在 1.25，1.26 的博客只是追认）。

#### 3.4 修复

知道根因后，修复就是一行顺序调整——**先 `Start()` 把 server 起好，再 `Register()`**：

```diff
 func main() {
     p := NewPlugin()
-    if err := p.Register(); err != nil {
-        log.Fatalf("Device plugin register failed, err: %v", err)
-    }
     if err := p.Start(); err != nil {
         log.Fatalf("Device plugin start failed, err: %v", err)
     }
+    if err := p.Register(); err != nil {
+        log.Fatalf("Device plugin register failed, err: %v", err)
+    }
     select {}
 }
```

这个顺序对新老集群都是安全的：

- 在新集群（≥1.25）上，kubelet 同步回拨时 socket 已经就绪，握手成功；
- 在老集群（≤1.24）上，先起 server 也从来不会有副作用——它本来就该这样。

------

### 4. 总结

这个 bug 本身很小（调换两行代码），但它串起来的几件事值得记一下：

1. **Device plugin 的握手是双向的**。插件主动发起 `Register`，但建立设备上报通道是 kubelet **反向**连接插件的 socket。所以正确顺序永远是：先 `Start()`（让 socket 可被连接），再 `Register()`。把这条记牢，就不会踩这个坑。

2. **不要依赖"未被承诺"的时序行为**。旧版本 kubelet 的"异步注册"从来不是 API 契约的一部分，它只是实现细节。我们的代码顺序本来就是错的，只是被这个实现细节意外兜住了。一旦对方重构，潜伏的 bug 立刻暴露。**依赖外部系统时，要依赖它承诺的契约，而不是它当前的实现时序。**

3. **同步/异步的语义差异，足以把一个潜伏已久的 bug 从"看不见"变成"必现"**。这次的导火索恰恰是一次 async → sync 的改动——异步会用时间差掩盖顺序错误，同步则把它无情地暴露出来。排查这类"代码没动、升级就挂"的问题时，沿着报错链路读对方的源码 + changelog + issue，往往能快速锁定真正的变化点。

排查这类问题最高效的路径，其实就是这篇文章的结构本身：**先彻底理解原理（握手时序），再回到现象（谁在拨谁），最后到对方源码里找差异（async vs sync）。**
