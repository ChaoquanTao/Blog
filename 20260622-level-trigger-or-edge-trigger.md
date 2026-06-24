---
title: "level-trigger OR edge-trigger，谈谈 Kubernetes controller 的开发范式"
date: 2026-06-22
categories: 云原生
tags:
  - Kubernetes
  - Controller
  - Go
---

# level-trigger OR edge-trigger，谈谈 Kubernetes controller 的开发范式

> 很多人是从 `kubebuilder` 的脚手架开始接触 controller 的：`kubebuilder init`、`create api`，一个 `Reconcile` 函数就摆在你面前，照着填就能跑。但填着填着就会冒出一堆问号——为什么 `Reconcile` 不告诉我"发生了什么事件"？为什么要写得幂等？Finalizer 到底在防什么？
>
> 这些问号其实都指向同一个源头。这篇文章不从框架 API 讲起，而是从一个更古老的话题——**电平触发还是边沿触发**——出发。理解了这个选择，controller 的整套范式就不再是一堆需要背诵的"最佳实践"，而是一条必然的推论。
>
> 面向"会 Go、但没写过 controller"的工程师。技术名词保留英文，首次出现做中英对照。

---

## 一、两种触发哲学：edge-triggered 与 level-triggered

"触发"这个词，最早的精确定义来自数字电路。一个寄存器要在什么时候采样输入信号？这里有两种截然不同的设计：

- **边沿触发（edge-triggered）**：在信号**发生跳变的那一瞬间**动作。它关心的是"变化"这个**事件**本身——比如时钟从低电平跳到高电平的那个上升沿。
- **电平触发（level-triggered）**：只要信号**当前处于某个电平**就持续动作。它关心的是"现在是什么状态"，而**不关心它是怎么变成这样的**。

这组概念后来被借用到了各种软件系统里。最为 Linux 工程师熟悉的，就是 `epoll` 的两种模式：`EPOLLET`（edge-triggered）只在"有新数据到达"的那一刻通知你一次，你要是没一次读干净，剩下的数据它不会再提醒；而默认的 level-triggered 模式只要缓冲区里"还有数据没读完"就会一直通知你。

抛开电路和 `epoll`，我们用一个更生活化的比喻把这两种哲学的差别讲透。假设你要看护一个水箱，**不让它溢出**：

- **edge-triggered 的做法**：在警戒线上装一个传感器，水面**越过警戒线的那一瞬间**给你发一个信号。你收到信号，就跑过去放水。
- **level-triggered 的做法**：你不装传感器，而是每隔一段时间走过去**看一眼**——"现在水位是不是高于警戒线了？高了就放水，没高就走人。"

平时这两种做法效果完全一样：水位一高，要么传感器报警、要么你巡检发现，反正水都被放掉了。差别要等到出意外时才显现。

---

## 二、为什么 edge-triggered 这么脆弱

edge-triggered 看起来更"高级"也更省事——不用反复巡检，有事它叫你，没事你睡觉。问题在于，它的正确性建立在一个**极其脆弱的前提**上：

> **每一个事件都必须被可靠地捕捉到，一个都不能漏。**

而在真实世界里，这个前提**永远不成立**。我们看两个一定会发生的现实。

**现实一：信号会丢。** 那个水位传感器，可能在水面越线的瞬间正好接触不良抖了一下，信号没发出去；可能信号发出来了，但你当时正在忙别的没收到；也可能网络丢了这个包。无论哪种，那个"越线事件"就这样**永久地消失了**。从此水位一直高着——但"越线"这个**瞬间**已经过去，再也不会有第二个事件来提醒你。水箱就这么静悄悄地溢了。

**现实二：进程会重启。** 看护者本身也会下线。你要吃饭、睡觉、换班；放到软件里，进程会崩溃、会被滚动升级、会被驱逐重调度。在你离线的这段时间里发生的所有事件，你**全部错过了**。等你回来，世界已经变了样，而你手里没有任何关于"这期间发生过什么"的记录。

对 edge-triggered 来说，这两个现实是**致命的**。它的整个工作模型就是"捕捉事件 → 响应事件"，一旦中间漏掉一环，系统就会**永久地**停留在错误状态——因为没有任何机制会让那个事件"重新发生一次"。

把这种脆弱性翻译到真实的业务代码里，就是这样一类 bug：

```
监听 "Pod 删除" 事件  →  收到后重建一个 Pod
```

这段逻辑在 demo 里跑得很好。但只要你的接收服务重启一次，恰好错过了某个 Pod 的删除事件，这个 Pod 就**永远不会被重建**了。没有报错，没有崩溃，系统只是悄无声息地少了一个副本，直到某天有人发现容量不对。更隐蔽的是它**难以复现**——本地测不出来，因为本地不会恰好在那个时刻重启。

用一张时间线把两者在"信号丢失"时的命运对比一下：

```
时间 ─────────────────────────────────────────────────────────►

水位    ── 正常 ──┐                                      一直高着
                  ├─ 越过警戒线 ─────────────────────────────────
                  │
  edge-triggered:
    传感器发信号 ──✗ 信号丢了！──（之后再也没有新事件）──  ❌ 水箱溢出

  level-triggered:
    [巡检→正常]  [巡检→正常]  [巡检→高了！放水]  [巡检→正常]
                                ✅ 下一轮巡检自动发现并纠正
```

而对 level-triggered 来说，这两个现实**几乎毫无影响**：

> 它根本不在乎"刚才发生了什么事件"。它每一轮都**重新观察当前的全量状态，重新计算现在该做什么**。漏掉一万个事件都没关系——只要它再巡检一轮，看到"水位还是高的"，就会再放一次水。

代价当然是有的：你得**不停地巡检**，哪怕大多数时候啥事没有，这是一种"轮询的代价"。但换来的是一个无比珍贵的性质——**系统能从任意错误状态中自愈**。漏了事件？下一轮纠正。进程重启了？起来重新看一遍全量，该补的补、该删的删。状态读错了？下一轮再读一次就对了。

这就是为什么，**任何一个需要在不可靠环境里保证最终正确的控制系统，最终都会收敛到 level-triggered 上**。这不是品味问题，而是在一个会丢事件、会重启的世界里，唯一能站得住脚的选择。

记住这个结论，我们带着它去看 Kubernetes。

---

## 三、Kubernetes controller：一个把 level-triggered 刻进基因的系统

先说 Kubernetes 是个什么东西。它是一个**声明式（declarative）**系统：用户不写"怎么做"，只写"我要什么"。你提交一段 YAML 说"我要 3 个 nginx 副本"，这叫**期望状态（desired state）**；至于现在有几个、怎么从 1 个变成 3 个、某个节点挂了怎么补——这些都不归你管，系统自己想办法。

那"系统自己想办法"这件事，是谁在做？答案就是 **controller（控制器）**。

> **Controller 就是那个不断观察当前状态、和期望状态比较、采取行动消除差异的循环。** 它有一个更标准的名字：**控制循环（control loop）**。

Kubernetes 里跑着几十个这样的循环，各管一摊：Deployment controller 让副本数与期望一致，Node controller 跟踪节点的健康，Job controller 盯着任务完成数……它们的形状都一样：**观察 → 比较 → 纠偏**，循环往复。

现在请把第一、二节的结论叠加上来：这些控制循环跑在一个**会丢事件、会重启**的分布式环境里。API Server 会重启，controller 自己会被升级重调度，watch 长连接会断开重连。在这样的环境里，要保证"最终正确"，答案我们已经推过了——**它必须是 level-triggered 的**。

所以 Kubernetes controller 的核心范式，一句话就能概括：

> **不要响应事件，而要调谐状态（reconcile）。** 永远拿当前的全量状态去和期望比较，把差异消除掉；不要去关心"刚才发生了哪个事件"。

这一句话听起来简单，但它像一条主梁，把后面所有的工程构件都串了起来。不过在拆解这些构件之前，得先澄清一个常见的误解。

### 一个先澄清的误解：controller 不是用 watch 监听事件吗？

很多人第一反应是：controller 明明靠 watch 监听对象变化来工作，那它不就是 edge-triggered 吗？

答案是：**watch 事件只是一个性能优化，不是决策依据。** 它的作用仅仅是敲一下你的肩膀："嘿，`default/my-app` 这个对象可能变了，你该去看一眼了。" controller 收到这个提醒后，**并不去处理这个事件**，而是拿着对象的名字**重新读取它当前的完整状态，重新调谐一遍**。事件丢了也没关系，因为还有**定期的全量重新同步（resync）**在背后兜底——每隔一段时间，所有对象都会被重新过一遍。

```
   watch 事件   →  只用来"提醒该看了"   →  绝不用来"告诉你发生了什么"
                                          决策永远基于「当前完整状态」
```

把这句话刻在脑子里，你就抓住了 controller 的灵魂：**事件用来触发，状态用来决策。**

## 四、范式落地：七个要点

下面我们把挂在这条主线上的七个要点一个一个拆开看——Reconcile、幂等、Informer/Cache、WorkQueue、OwnerReference、Finalizer、Status/Conditions。你会发现，**每一个要么是这条范式逼出来的硬约束，要么是 Kubernetes 为了让你更容易遵守它而提供的便利**。

### Reconcile：为什么它只接收一个 key

在实际开发中（用 `controller-runtime` 框架），你要写的核心就是一个 `Reconcile` 函数，签名长这样：

```go
func (r *FooReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)
```

最值得玩味的是入参 `ctrl.Request`——它里面**只有一样东西**：对象的 key，也就是 `namespace/name`。

```go
type Request struct {
    types.NamespacedName // 就是 {Namespace, Name}
}
```

请停下来体会这个设计：它**不接收事件类型**。没有"这是 Create 还是 Update 还是 Delete"这种信息，框架只告诉你一句话——"`default/my-app` 这个对象，你该看一眼了。"

这正是 level-triggered 在 API 层面的**直接体现**:

> 框架不告诉你"发生了什么"，只告诉你"该看谁"。你的工作是拿着这个 key,**重新读取它当前的完整状态，重新计算该做什么**。

这也解释了为什么 reconcile 的标准骨架几乎总是这四步——每一步都对应前面的原理：

```
1. 读期望对象           ← 重新观察当前全量状态(level-triggered)
2. 处理删除 / finalizer  ← 对象正在被删?先做临终清理
3. 确保子资源存在        ← ensure 而非 create(幂等)
4. 回填 status          ← 向用户汇报实际状态
```

### 幂等（idempotency）：被 level-triggered 逼出来的第二条铁律

level-triggered 还会顺手逼出另一条铁律。

> **幂等（idempotency）：同一段逻辑，对同一个状态，跑 1 次和跑 100 次，结果必须完全一致。**

既然 controller 每一轮都重新观察、重新执行，那么**同一个对象的 reconcile 逻辑，会被反复地、不确定次数地执行**:

- 集群风平浪静时，它可能因为定期 resync 每 10 分钟跑一次；
- 状态频繁变化时，它可能 1 秒内被触发好几次；
- 它崩溃重启后，会把所有对象从头 reconcile 一遍。

如果你的逻辑写成"每跑一次就创建一个 Pod"，那 100 次 reconcile 就会创建 100 个 Pod——灾难。所以必然要求幂等。

幂等的写法不是"创建一个 Pod"，而是"**确保（ensure）**存在一个符合期望的 Pod":

```
不存在        → 创建
已存在但不对   → 更新
已存在且正确   → 什么都不做
```

注意它和控制循环本来就是一回事：**永远先观察、再决定动作；动作的目标是"消除差异"，而不是"执行一次操作"。** level-triggered 和幂等，本质上是一枚硬币的两面——前者决定了"逻辑会被重复执行"，后者保证了"重复执行不会出乱子"。

### Informer / Cache：每轮都读全量，API Server 受得了吗

在往下讲之前，先花一句话交代 **API Server** 是什么——后面会反复提到它。它是整个集群**唯一的入口**：集群里所有对象（Pod、Deployment、你的 Foo……）都存在一个叫 **etcd** 的数据库里，而**谁都不能直接碰 etcd**，所有的读和写都必须经过 API Server 这道门。你敲的 `kubectl`、每个节点上的 kubelet、还有我们正在讲的 controller，全都是它的客户端。

```
       kubectl ──┐
                 │
   controller ──┼──►  ┌────────────┐  ──►  ┌────────┐
                 │     │ API Server │       │  etcd  │  ← 真正存数据的地方
      kubelet ──┘     └────────────┘  ◄──  └────────┘
                       (唯一入口/门卫)
        所有读写都得走这道门,etcd 不对外直接开放
```

正因为它是**唯一入口**，所有流量都压在它身上——这就是下面这个问题的由来。

第三节说，controller 每轮都要"重新观察当前全量状态"。最朴素的实现是：每次 reconcile 都向 API Server 发一个 GET/LIST。

但这里有个致命问题：**API Server 扛不住。** 集群里几十个 controller、成千上万个对象，如果每次 reconcile、每次 resync 都去打 API Server，它会被读请求压垮。

解决方案是 **Informer**（背后是一个本地 **Cache / 缓存**）。机制是经典的 **List + Watch**:

1. **List**：启动时向 API Server 拉一次某类资源的全量列表，灌进本地内存缓存；
2. **Watch**：之后建立一条长连接，API Server 把后续的增量变化（add/update/delete）持续推过来，实时更新本地缓存；
3. **读缓存**:reconcile 里读对象时，**读的是本地缓存，根本不碰 API Server**。

这就把"成千上万次读 API Server"压缩成了"一次 List + 一条 Watch 长连接"。整条数据流是这样的：

```
   ┌────────────┐  List+Watch   ┌──────────┐  对象变化    ┌───────────┐
   │ API Server │ ────────────► │ Informer │ ──────────► │ WorkQueue │
   │   (etcd)   │  (长连接推送)  │ + Cache  │  (塞入 key) │ (去重限速) │
   └────────────┘               └────┬─────┘             └─────┬─────┘
         ▲                           │                         │
         │ 写操作(create/update)      │ 读缓存                  │ 取出 key
         │                           │ (不打 API Server)       ▼
         │                           │                  ┌───────────┐
         └───────────────────────────┴─────────────────►│ Reconcile │
                                                        └───────────┘
```

**代价是什么？** 本地缓存可能**短暂陈旧（stale）**——API Server 上对象已经变了，但 Watch 事件还在路上，你这一瞬读到的是旧值。

但这正好是 level-triggered + 幂等大显身手的地方：**读到旧数据无所谓。** 因为缓存马上会被更新，更新又会触发一次 reconcile，下一轮你就读到新值、重新纠正了。陈旧状态会被**下一次 reconcile 自愈**。要是换成 edge-triggered，一次读错就可能永久错下去；而 level-triggered 把"短暂读旧"变成了一个无害的、自动修复的小插曲。

### WorkQueue：把"惊群"压平

先解释下标题里的**惊群（thundering herd）**：它原指"一件事发生时，一大群原本在等待的对象**同时被惊动、一拥而上**"——就像往鸽群里扔一块面包，所有鸽子哗地一下全飞过来抢，场面瞬间失控。放到 controller 这里，典型场景有两类：一是**某一个对象在极短时间内被改了几十次**，每次变化都想触发一次 reconcile；二是 controller **刚启动或刚重连**时，缓存里成千上万个对象"看起来全都变了"，瞬间涌出海量待处理任务。如果来一个就立刻处理一个，worker 和 API Server 会被这股洪峰冲垮。

Informer 收到变化后，并不直接调用 `Reconcile`，而是先把对象的 key 塞进一个 **WorkQueue（工作队列）**，再由 worker 协程从队列里取 key 来处理。中间隔这一层队列，是为了三件事——而这三件事，**只有 level-triggered 才敢这么干**:

1. **去重（dedup）。** 同一个对象短时间内变了 50 次，不会触发 50 次 reconcile。队列内部维护了一个 dirty 集合：某个 key 正在被处理时，新事件只把它**标记为 dirty**，等处理完再重新入队跑一轮。最终 50 次变化可能只合并成两三次 reconcile，每次都读当前最新状态。敢这么合并，正是因为 level-triggered **根本不关心那 50 个事件分别是什么**，只关心当前状态——合并完全没有信息损失。

2. **限速（rate limiting）。** 队列能控制 reconcile 的速率，防止某个频繁抖动的对象把 worker 和 API Server 压垮。

3. **失败重试 + 指数退避（exponential backoff）。** reconcile 返回 error 时，框架把这个 key **重新入队**，且退避时间逐次翻倍（1s → 2s → 4s → …）。既保证"出错的对象最终会被重试到成功"，又不会在它持续失败时把 API Server 拖垮。

这就是为什么你的 `Reconcile` **只要"返回 error"就行**——剩下的重试、退避、去重，框架全替你兜住了。你只管把"当前该把状态调谐成什么样"这件事写对、写幂等。

### OwnerReference：级联删除与反向触发

controller 通常会为它管理的对象创建**子资源**。比如一个 `Foo` controller，会为每个 `Foo` 创建一个 Deployment。这里有两个需求：

- **需求一：删掉 Foo 时，它创建的 Deployment 也要被删掉**——你不想手动追着删。
- **需求二：有人手动删了那个 Deployment,Foo controller 要能感知并重建**。

两件事都靠 **OwnerReference（属主引用）** 解决。你在子资源（Deployment）的 metadata 里写一条 OwnerReference，指向它的属主（Foo）:

- **级联垃圾回收（cascading GC）**:Kubernetes 的垃圾回收器看到"属主 Foo 没了"，会自动回收所有以它为 owner 的子资源。你不用写一行删除代码。
- **反向触发（`controller-runtime` 里叫 `Owns`)**：你声明 `Owns(&appsv1.Deployment{})` 后，框架会 watch 这些 Deployment，一旦某个带着 Foo 这条 OwnerReference 的 Deployment 变了（比如被人删了），框架就把**它属主 Foo 的 key** 塞进 WorkQueue，触发 Foo 的 reconcile。

第二点又一次呼应 level-triggered：子资源被人动了 → 触发属主重新 reconcile → 属主重新观察"我的子资源还在不在、对不对" → 不对就修。你**不需要**写"监听 Deployment 删除事件然后重建"这种脆弱的 edge-triggered 逻辑——你只需在 reconcile 里**幂等地 ensure 子资源存在**，而"什么时候该再 ensure 一次"由反向触发负责。

### Finalizer：删除前的临终清理

OwnerReference 的级联 GC 能帮你回收**集群内**的子资源。但如果你的 controller 在**集群外**也分配了东西呢？比如：

- 在云厂商那边申请了一个负载均衡器（LB）;
- 在某个外部数据库里建了一条记录；
- 在对象存储里建了一个 bucket。

用户删掉你的对象时，Kubernetes 的 GC 管不到这些外部资源。如果对象一下子从 etcd 消失，你就**再也没机会**去释放它们了——它们会变成泄漏的孤儿。

**Finalizer（终结器）** 就是为此而生的一道"临终清理"钩子：

```
   用户 delete ──► deletionTimestamp 被设置(对象进入 Terminating,但不消失)
                          │
                          ▼
              reconcile 检测到 deletionTimestamp != nil
                          │
                  执行外部资源清理(释放 LB / 删记录 / ...)
                          │
                  移除自己的 finalizer
                          │
                          ▼
              finalizers 空了 ──► Kubernetes 真正删除对象
```

具体来说：controller 在对象创建时往 `metadata.finalizers` 里加一个自己的标记；用户删除时，Kubernetes **不会**立刻删对象，只是打上一个 `deletionTimestamp` 然后停在那里（状态变成 `Terminating`);reconcile 看到 `deletionTimestamp != nil` 就去清理外部资源，清理成功后把自己的 finalizer 标记移除；等列表空了，Kubernetes 才真正删除对象。

**这是 controller 里最容易出 bug 的地方，** 而原因还是那两条铁律：

- **清理必须幂等。** reconcile 可能在"清理外部资源"和"移除 finalizer"之间崩溃重启，重启后又会重进清理逻辑。所以"释放外部资源"必须能安全地跑第二次。
- **对 NotFound 宽容。** 如果要删的外部资源"本来就不存在了"（上次可能已经删过），不能当成错误。否则 reconcile 永远返回 error、finalizer 永远移不掉，对象**永远卡在 Terminating**，让用户非常头疼。正确写法是："删，如果返回 NotFound，当作成功。"

一句话：**finalizer 的清理逻辑，要写得像 reconcile 主干一样——假设自己会被重复调用，假设资源可能已经不在了。**

### Status 与 Conditions：对外的单一事实源

最后是对象模型里 `spec` 和 `status` 的分工，它们正好对应控制循环的两端：

- **`spec`（期望状态）**：由**用户**写，表达"我想要什么"，是控制循环的输入。用户只动 spec。
- **`status`（实际状态）**：由 **controller** 写，表达"现在实际怎么样、做到哪了"，是控制循环的输出。用户只读不写 status。

```
   用户 ──写──► spec   (desired,我想要什么)
                  │
                  ▼
            ┌───────────┐
            │ controller │  观察现实 → 比较 → 纠偏
            └───────────┘
                  │
   用户 ◄─读── status   (actual,现在实际怎么样)
```

光说有点抽象，看一个真实对象长什么样（`kubectl get foo my-app -o yaml` 的节选）：

```yaml
apiVersion: example.com/v1
kind: Foo
metadata:
  name: my-app
  generation: 2            # 用户每改一次 spec,这个数 +1(这里改过 2 次)
spec:                      # ── 用户写的"我想要什么" ──
  replicas: 3
  image: nginx:1.27
status:                    # ── controller 写的"现在实际怎么样" ──
  observedGeneration: 2    # controller 已处理到 generation=2,说明 status 是最新的
  conditions:
  - type: Ready            # 这个 Condition 表达"整体是否就绪"
    status: "True"         #   True / False / Unknown
    reason: AllReplicasReady
    message: "3/3 replicas are available"
    lastTransitionTime: "2026-06-22T03:14:00Z"
  - type: Progressing
    status: "False"
    reason: ReconcileComplete
    message: "Deployment has settled, no rollout in progress"
    lastTransitionTime: "2026-06-22T03:14:00Z"
```

对着这个例子看下面三个要点，会清楚很多：

**其一，status 是对外的单一事实源（single source of truth）。** 别人（用户、其他系统、`kubectl get`）想知道"这对象现在怎么样了"，只看 status。常用 **Conditions（条件）** 这种结构化方式表达——每个 Condition 有 `type`（如 `Ready`)、`status`(`True`/`False`/`Unknown`)、`reason`、`message`，组合起来表达健康状况和进度。

**其二，`observedGeneration` 用来判断 status 是否跟上了最新的 spec。** 用户每改一次 spec,Kubernetes 会自动递增 `metadata.generation`。controller 每轮结束时把当前 `generation` 抄进 `status.observedGeneration`。外部只要比较两个值就知道：`observedGeneration < generation` 说明 controller 还没处理你最新的改动。

**其三，spec 和 status 走不同的子资源（subresource）更新。** Kubernetes 把 status 做成了独立子资源 `/status`:

> **更新 spec 用 `Update`，更新 status 用 `Status().Update()`，两者互不影响。**

为什么要分开？因为 spec 由用户写、status 由 controller 写。如果混在一起更新，controller 回填 status 时可能不小心覆盖掉用户刚改的 spec，反之亦然。分成两个子资源，从机制上保证了"用户的意图"和"controller 的汇报"井水不犯河水。

---

## 五、三条纪律：开始写代码前先在脑子里装一句话

到这里七个要点都讲完了。但在敲第一行代码前，我推荐你先把一个**思维模型**装进脑子，因为它能帮你绕开新手 90% 的坑。这个模型只有一句话：

> **不要问"发生了什么，我该做什么反应"；要问"现在是什么样，期望是什么样，我怎么把前者变成后者"。**

这句话听起来像废话，但它会实实在在地改变你写每一行代码的方式。每当你想写下 `if 收到删除事件 { ... }` 这样的逻辑时，停下来——这是 edge-triggered 思维在作祟。正确的姿势永远是：**读全量、算差异、消差异**。把这套思维展开，就是三条具体的纪律：

1. **决策只依赖"当前读到的状态"，绝不依赖"我是被什么触发的"。** 你的 `Reconcile` 从头到尾都不应该关心自己为什么被调用。
2. **每个写操作都是"ensure"，不是"do once"。** 创建、更新、删除，都要能安全地重复执行——因为它**一定会**被重复执行。
3. **把每一种中途崩溃都想一遍。** "如果我在这一行之后、下一行之前挂掉，重启后重新进 reconcile，会出乱子吗？" 如果会，说明这段还不够幂等。

带着这三条纪律，我们来看代码。

---

## 六、骨架代码：把七个要点串起来

下面这份骨架把前面的要点全部串在一起（用 `controller-runtime`，重在理解，不保证可直接编译）。

### 类型定义：声明 spec 与 status

先用 Go 结构体定义资源（`kubebuilder` 会据此自动生成 CRD 的 YAML):

```go
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status    // 启用 /status 子资源(见 Status/Conditions 一节)
type Foo struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`

    Spec   FooSpec   `json:"spec,omitempty"`   // 用户写:期望状态
    Status FooStatus `json:"status,omitempty"` // controller 写:实际状态
}

type FooSpec struct {
    Replicas *int32 `json:"replicas"`
    Image    string `json:"image"`
}

type FooStatus struct {
    ObservedGeneration int64              `json:"observedGeneration,omitempty"`
    Conditions         []metav1.Condition `json:"conditions,omitempty"`
}
```

### main：用 Builder 声明式地搭出控制循环

```go
func main() {
    // Manager 持有共享的 Cache(前文 Informer/缓存)、
    // Client(带缓存的读 + 直写 API Server 的写)、WorkQueue 等基础设施。
    mgr, _ := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
        // 生产必开 LeaderElection:多副本部署时只有 leader 跑 reconcile,
        // 否则多副本会并发 reconcile 同一对象,产生冲突和重复操作。
        LeaderElection:   true,
        LeaderElectionID: "foo-controller.example.com",
    })

    // 这几行就是范式的核心:声明"看谁",而不是"处理什么事件"。
    _ = ctrl.NewControllerManagedBy(mgr).
        For(&v1.Foo{}).             // 主资源:Foo 变了 → Foo 的 key 入队(level-triggered 的"提醒")
        Owns(&appsv1.Deployment{}). // 子资源:带 Foo 这条 OwnerReference 的 Deployment 变了
                                    //        → 反向触发属主 Foo 重新 reconcile(见 OwnerReference 一节)
        Complete(&FooReconciler{Client: mgr.GetClient()})

    _ = mgr.Start(ctrl.SetupSignalHandler())
}
```

### Reconcile 主干：四步骨架

```go
func (r *FooReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // ❶ 读期望对象。拿着 key 重新读"当前全量状态",而不是处理某个事件。
    //    这就是 level-triggered:决策只基于当下状态。
    var foo v1.Foo
    if err := r.Get(ctx, req.NamespacedName, &foo); err != nil {
        // 对象已不在(可能已被删除)。对 NotFound 宽容:当作正常,无需重试。
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // ❷ 处理删除 / finalizer(见 Finalizer 一节)。
    const finalizer = "foo.example.com/cleanup"
    if !foo.DeletionTimestamp.IsZero() {
        // 对象正在被删除。
        if controllerutil.ContainsFinalizer(&foo, finalizer) {
            // 外部资源临终清理。必须幂等、对 NotFound 宽容(崩溃重启会重进这里)。
            if err := r.cleanupExternalResources(ctx, &foo); err != nil {
                return ctrl.Result{}, err // 失败 → 入队重试(指数退避,见 WorkQueue 一节)
            }
            controllerutil.RemoveFinalizer(&foo, finalizer)
            if err := r.Update(ctx, &foo); err != nil {
                return ctrl.Result{}, err
            }
        }
        return ctrl.Result{}, nil
    }
    // 对象存活:确保 finalizer 已挂上,否则将来没机会做外部清理。
    // 加 finalizer 会改变 resourceVersion,所以加完就 return,让下一轮拿最新对象继续。
    if !controllerutil.ContainsFinalizer(&foo, finalizer) {
        controllerutil.AddFinalizer(&foo, finalizer)
        return ctrl.Result{}, r.Update(ctx, &foo)
    }

    // ❸ 确保子资源存在(呼应幂等一节:ensure 而非 create,整段必须幂等)。
    if err := r.ensureDeployment(ctx, &foo); err != nil {
        return ctrl.Result{}, err
    }

    // ❹ 回填 status(见 Status/Conditions 一节)。走 /status 子资源,与用户写的 spec 互不覆盖。
    foo.Status.ObservedGeneration = foo.Generation
    meta.SetStatusCondition(&foo.Status.Conditions, metav1.Condition{
        Type:               "Ready",
        Status:             metav1.ConditionTrue,
        Reason:             "Reconciled",
        LastTransitionTime: metav1.Now(),
    })
    if err := r.Status().Update(ctx, &foo); err != nil {
        return ctrl.Result{}, err
    }

    // 返回 nil:本轮收敛完成。若返回 error,框架按指数退避把 key 重新入队(见 WorkQueue 一节)。
    return ctrl.Result{}, nil
}
```

### ensureDeployment：幂等收敛的核心动作

```go
func (r *FooReconciler) ensureDeployment(ctx context.Context, foo *v1.Foo) error {
    dep := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{Name: foo.Name, Namespace: foo.Namespace},
    }

    // CreateOrUpdate 是幂等的关键工具(呼应幂等一节):
    //   不存在     → 按 mutate 填充后创建
    //   已存在     → 读出来、跑 mutate、有 diff 才更新
    //   已存在无 diff → 什么都不做
    // 跑 1 次和跑 100 次结果一致,这正是 level-triggered 世界的生存法则。
    _, err := controllerutil.CreateOrUpdate(ctx, r.Client, dep, func() error {
        labels := map[string]string{"app": foo.Name}
        dep.Spec.Selector = &metav1.LabelSelector{MatchLabels: labels}
        dep.Spec.Replicas = foo.Spec.Replicas
        dep.Spec.Template = buildPodTemplate(foo)
        dep.Spec.Template.Labels = labels

        // 设置 OwnerReference(见 OwnerReference 一节):级联 GC + 反向触发,二合一。
        return controllerutil.SetControllerReference(foo, dep, r.Scheme)
    })
    return err
}
```

把这几段连起来读，你会发现整份代码里**找不到一处"监听某事件 → 做某动作"的影子**。所有逻辑都是"**读当前状态 → ensure 成期望的样子**"。这就是范式本身。

---

## 收尾

回到开篇的那个二选一：**level-trigger OR edge-trigger?**

对 Kubernetes controller 来说，这根本不是一道选择题。在一个**会丢事件、会重启**的世界里，edge-triggered 那种"捕捉事件 → 响应事件"的模型天生脆弱——漏一个事件，系统就可能永久停在错误状态。而 level-triggered "每轮重读全量、重算差异"的模型，能从任意错误中自愈。这是唯一站得住脚的选择。

而本文后半篇讲的所有东西——Reconcile 只收 key、幂等、Informer/Cache、WorkQueue、OwnerReference、Finalizer、Status/Conditions——没有一个是孤立的"知识点"。它们要么是 level-triggered 逼出来的**硬约束**（只收 key、幂等、finalizer 的重入安全），要么是 Kubernetes 为了让你更容易遵守它而铺的**便利设施**(Informer 让"读全量"变便宜，WorkQueue 让"重复触发"变无害，OwnerReference 让"反向触发"开箱即用）。

所以真正要记住的，其实只有一句话：**不要响应事件，要调谐状态。** 把它装进脑子，你再看任何 controller 源码，都能立刻问出那个对的问题——**它在把什么 actual 调谐到什么 desired？它的幂等是怎么保证的？**


### 推荐学习路径

1. **跟一遍 The Kubebuilder Book 的 CronJob 教程。** 官方最经典的上手教程，带你用 `kubebuilder` 从零生成一个真实 controller，把本文每个概念落到可运行的代码上。
2. **用 `envtest` 写单元测试。** `controller-runtime` 自带的 `envtest` 能起一个真实的 API Server + etcd（不需完整集群），是验证"幂等""finalizer 正确性"的最好方式。
3. **读一个工业级 controller 源码。** 比如 cert-manager 或 kubeflow training-operator——看本文所有范式在真实项目里如何组织与取舍：多 reconcile 协作、复杂 status、各种边界处理。
