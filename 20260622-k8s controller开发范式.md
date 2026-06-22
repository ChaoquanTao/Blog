---
title: 从第一性原理推导 k8s controller 开发范式
date: 2026-06-22
categories: 云原生
tags:
  - Kubernetes
  - Controller
  - Go
---

# 从第一性原理推导 k8s controller 开发范式

> 这篇文章不从 API 和框架讲起，而是从一个更根本的问题出发：在一个**会丢事件、会重启**的世界里，怎样才能保证系统最终正确？答案是两条铁律——理解了它们，controller 的整个开发范式就自然浮现了。
> 面向"会 Go、但没写过 controller"的工程师。技术名词保留英文，首次出现中英对照。

---

# 第一部分：Controller 的核心原理

Kubernetes 是一个**声明式（declarative）**系统：用户写下**期望状态（desired state）**——"我要 3 个 nginx 副本"，系统负责让现实趋近它。**Controller** 就是那个负责"让现实趋近期望"的东西——一个不断观察当前状态、和期望比较、采取行动消除差异的**控制循环（control loop）**。Kubernetes 里跑着几十个这样的循环：Deployment controller 让副本数一致，Node controller 让节点状态一致，Job controller 让任务完成数一致……

控制循环本身不难理解。真正难的问题是：在一个**会丢事件、会重启**的世界里，这个循环要怎么设计，才能保证**最终正确**？答案收敛在两条铁律上。

## 一、铁律一：level-triggered 而非 edge-triggered

"触发"有两种哲学，名字借自电子电路：

- **边沿触发（edge-triggered）**：在**状态发生变化的那一瞬间**触发。关注的是"发生了什么事件"——比如"温度从 25 跳到 26 的那一刻"。
- **水平触发（level-triggered）**：只要**当前状态满足某个条件**就触发，**不管它是怎么变成这样的**。关注的是"现在处于什么状态"——比如"现在温度高于 26"。

用**水位**再打个比方。你要控制一个水箱不要溢出：

- **edge-triggered 的做法**：装一个传感器，在"水面上升越过警戒线的那一瞬间"发一个信号给你，你收到信号就去放水。
- **level-triggered 的做法**：你每隔一段时间走过去看一眼，"现在水位高于警戒线了吗？高了就放水"。

用时间线来对比两者在"信号丢失"时的行为差异：

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

平时两者效果一样。但考虑两个**一定会发生**的现实：

**现实一：信号会丢。** 假设 edge-triggered 那个传感器，在水面越线的瞬间正好抖了一下、信号没发出去，或者你当时正好在重启。那个"越线事件"**永远地丢失了**。从此水位一直高着，但因为"越线"这个**瞬间**已经过去了，再也不会有新的事件来提醒你——水箱就这么溢了。

**现实二：进程会重启。** controller 是会崩溃、会被滚动升级、会被驱逐重调度的。一旦它重启，它**错过了重启期间发生的所有事件**。

对 edge-triggered 来说，这两个现实是致命的：它依赖"捕捉到每一个事件"，而事件**天生不可靠**——会丢、会因为宕机而错过。一旦漏掉一个，系统就永久地停留在错误状态，因为没有"重新发生一次"的机制。

对 level-triggered 来说，这两个现实**毫无影响**：

> 它根本不在乎"发生了什么事件"。它每一轮都**重新观察当前的全量状态**，**重新计算现在该做什么**。漏了一万个事件都没关系——只要它再跑一轮，看到"水位还是高的 / 副本还是只有 2 个"，它就会再纠正一次。

所以 Kubernetes controller 必须是 level-triggered 的。这不是一个"最佳实践"，而是**在一个会丢事件、会重启的世界里，唯一能保证最终正确的方案。**

这里有一个常见的误解需要澄清：**"controller 不是用 watch 监听事件的吗？那不就是 edge-triggered？"**

答案是：watch 事件只是一个**性能优化**——它让 controller 知道"嘿，有东西可能变了，你该去看一眼了"。但 controller 收到事件后**并不直接处理这个事件**，而是拿着对象的标识去**重新读取全量状态、重新 reconcile**。事件丢了也没关系，因为还有**定期的全量重新同步（resync）**兜底。换句话说：

> **事件只用来"提醒该看了"，绝不用来"告诉你发生了什么"。** 决策永远基于"当前完整状态"，而非"这个事件本身"。

记住这一句，你就抓住了 controller 的灵魂。

## 二、铁律二：幂等（idempotency）

level-triggered 还会逼出另一个铁律。

既然 controller 每一轮都重新观察、重新执行，那么**同一个对象的 reconcile 逻辑，会被反复地、不确定次数地执行**：

- 集群里风平浪静，它可能因为定期 resync 每 10 分钟跑一次；
- 状态频繁变化，它可能 1 秒内被触发好几次；
- 它崩溃重启后，会把所有对象重新 reconcile 一遍。

如果你的 reconcile 逻辑写成"每跑一次就创建一个 Pod"，那 100 次 reconcile 就会创建 100 个 Pod——灾难。

所以必然要求：

> **幂等（idempotency）**：同一段 reconcile 逻辑，对同一个状态，**跑 1 次和跑 100 次，结果必须完全一致。**

幂等的写法不是"创建一个 Pod"，而是"**确保（ensure）**存在一个符合期望的 Pod"：

- 不存在 → 创建；
- 已存在但不符合期望 → 更新；
- 已存在且符合期望 → 什么都不做。

注意它和开头所说的控制循环是同一回事：**永远先观察，再决定动作；动作的目标是"消除 diff"，而不是"执行一次操作"。** level-triggered 和 idempotency，本质上是一枚硬币的两面。

## 三、spec 与 status 的分工

最后补上 Kubernetes 对象模型里两个字段的分工，它们正好对应控制循环的两端：

- **`spec`（期望状态）**：由**用户**填写，表达"我想要什么"。这是控制循环的输入。用户只动 spec。
- **`status`（实际状态）**：由 **controller** 填写，表达"现在实际是什么样、我做到哪了"。这是控制循环的输出/反馈。用户只读不写 status。

```
   用户 ──写──► spec   （desired，我想要什么）
                  │
                  ▼
            ┌───────────┐
            │ controller │  观察现实 → 比较 → 纠偏
            └───────────┘
                  │
   用户 ◄─读── status   （actual，现在实际怎么样）
```

一句话记忆：**spec 是用户对 controller 提的需求，status 是 controller 对用户的汇报。** 谁写谁读分得清清楚楚——这也是后面"为什么 spec 和 status 走不同的子资源更新"的根源。

到这里，controller 的三块基石已经就位：level-triggered、幂等、spec/status 分工。第二部分我们把它们"翻译"成实际开发中的构件。

---

# 第二部分：Controller 的开发范式

第一部分推出了两条铁律：level-triggered 和幂等。第二部分讲的是这两条铁律在工程上的具体落地，以及 Kubernetes 和 controller-runtime 为此提供的配套设施。不是每个构件都直接由铁律"逼出来"，有些（如 OwnerReference、Status 子资源）更像是 Kubernetes 为了让你更容易写出符合铁律的代码而提供的便利机制。

为了让后续的代码示例更有体感，我们把抽象的 `Foo` 换成一个稍微具体的场景：**假设你要实现一个 `MyApp` 资源**——用户声明应用名称、副本数和镜像，controller 负责创建对应的 Deployment，并在云厂商那边申请一个负载均衡器把流量导进来。这样你会自然地遇到本文讲的所有机制：Deployment 是集群内子资源（OwnerReference 管级联删除），负载均衡器是集群外资源（Finalizer 管临终清理），status 要告诉用户"LB 的外网 IP 是多少、当前是否就绪"。后续代码里仍然用 `Foo` 命名以保持简洁，但你心里可以把它映射到这个场景。

## 四、Reconcile 函数：为什么只接收 key

在 controller-runtime 框架里，你要写的核心就是一个 `Reconcile` 函数，它的签名长这样：

```go
func (r *MyReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)
```

而 `ctrl.Request` 里**只有一个东西**：对象的 key，也就是 `namespace/name`。

```go
type Request struct {
    types.NamespacedName // 就是 {Namespace, Name}
}
```

请停下来体会这个设计——它**不接收事件类型**。没有"这是一个 Create 事件还是 Update 事件还是 Delete 事件"这种信息。框架只告诉你："`default/my-app` 这个对象你该看一眼了。"

这正是第一节 **level-triggered** 的直接体现：

> 框架不告诉你"发生了什么"，只告诉你"该看谁"。你的工作是拿着这个 key，去**重新读取它当前的完整状态**，然后**重新计算该做什么**。

reconcile 的标准骨架几乎总是这四步，每一步都对应前面的原理：

```
1. 读期望对象          ← 重新观察当前全量状态（level-triggered）
2. 处理删除 / finalizer ← 对象正在被删？先做临终清理
3. 确保子资源存在       ← ensure 而非 create（幂等）
4. 回填 status         ← 向用户汇报实际状态
```

具体代码我们放到第十一节一次性给出。先把支撑它的几个构件讲清楚。

## 五、Informer / Cache：为什么不直接打 API Server

第一节说，controller 每一轮都要"重新观察当前全量状态"。最朴素的实现是：每次 reconcile 都向 API Server 发一个 GET/LIST 请求。

但这样有个致命问题：**API Server 扛不住。** 集群里几十个 controller、成千上万个对象，如果每次 reconcile、每次定期 resync 都去打 API Server，API Server 会被读请求淹没。

解决方案是 **Informer**（其背后是一个本地 **Cache / 缓存**）。它的机制是：

1. **List**：启动时向 API Server 拉一次某类资源的全量列表，灌进本地内存缓存；
2. **Watch**：之后建立一个长连接，API Server 把后续的增量变化（add/update/delete）持续推过来，实时更新本地缓存；
3. **读缓存**：controller 的 reconcile 里读对象时，**读的是本地缓存，根本不碰 API Server。**

这就是经典的 **List + Watch** 模式。它把"成千上万次读 API Server"压缩成了"一次 List + 一条 Watch 长连接"。

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

**代价是什么？** 本地缓存可能**短暂陈旧（stale）**——API Server 上对象已经变了，但 Watch 事件还在路上，你这一瞬间读到的缓存是旧的。

但这正好是 level-triggered + 幂等的用武之地：**读到旧数据没关系。** 因为缓存马上会被更新，更新会再次触发一次 reconcile，下一轮你就读到新数据、重新纠正了。陈旧状态会被**下一次 reconcile 自愈**。如果当初是 edge-triggered，一次读错就可能永久错下去；而 level-triggered 让"短暂读旧"变成了一个无害的、会自动修复的小插曲。

## 六、WorkQueue：把惊群压平

Informer 收到变化后，并不直接调用 `Reconcile`，而是先把对象的 key 塞进一个 **WorkQueue（工作队列）**，由 worker 协程从队列里取 key 来处理。中间隔这么一层队列，是为了三件事：

1. **去重（dedup）。** 同一个对象在短时间内变了 50 次，不会触发 50 次 reconcile。WorkQueue 内部维护了一个 dirty 集合：如果某个 key 正在被 worker 处理，新的事件只会把它**标记为 dirty**；等当前处理完成后，worker 发现它是 dirty 的，会重新入队再跑一轮。如果 key 既没在处理、队列里也已经有了，则不会重复入队。最终效果是：50 次变化可能只触发两三次 reconcile，每次都读当前最新状态——天然把"惊群（thundering herd）"压平了。这一点只有 level-triggered 才敢这么做：反正我不关心那 50 个事件分别是什么，我只关心"当前状态"，合并处理完全没有信息损失。
2. **限速（rate limiting）。** 队列能控制 reconcile 的速率，防止某个抖动的对象把 worker 和 API Server 打爆。
3. **失败重试 + 指数退避（exponential backoff）。** reconcile 返回 error 时，框架会把这个 key **重新入队**，并且退避时间逐次翻倍（比如 1s → 2s → 4s → …）。这样既保证了"出错的对象最终会被重试到成功"，又不会在它持续失败时疯狂打 API Server。

这就是为什么你的 `Reconcile` 只要"返回 error"就行，**剩下的重试、退避、去重，框架全给你兜住了**——你只管把"当前该把状态调谐成什么样"这件事写对、写幂等。

## 七、OwnerReference：级联 GC 与反向触发

一个 controller 通常会为它管理的对象创建**子资源**。比如你写一个 `Foo` controller，它会为每个 `Foo` 创建一个 Deployment。这里有两个需求：

**需求一：删掉 Foo 时，它创建的 Deployment 也要被删掉。** 你不想手动追着删。

**需求二：有人手动删了那个 Deployment，Foo controller 要能感知到并重建。**

这两件事都靠 **OwnerReference（属主引用）** 解决。你在子资源（Deployment）的 metadata 里写一条 OwnerReference，指向它的属主（Foo）：

- **级联垃圾回收（cascading GC）**：Kubernetes 的垃圾回收器看到"属主 Foo 没了"，会自动把所有以它为 owner 的子资源回收掉。你不用写一行删除子资源的代码。
- **反向触发（在 controller-runtime 里叫 `Owns`）**：你声明 `Owns(&appsv1.Deployment{})` 后，框架会 watch 这些 Deployment，一旦某个带着 Foo 这条 OwnerReference 的 Deployment 发生变化（比如被人删了），框架就把**它的属主 Foo 的 key** 塞进 WorkQueue，触发 Foo 的 reconcile。

第二点又一次呼应 level-triggered：子资源被人动了 → 触发属主重新 reconcile → 属主重新观察"我的子资源还在不在、对不对" → 不对就修。你不需要写"监听 Deployment 删除事件然后重建"的逻辑，你只需要在 reconcile 里**幂等地 ensure 子资源存在**，反向触发会负责"什么时候该再 ensure 一次"。

## 八、Finalizer：删除前的临终清理

GC 能帮你回收**集群内**的子资源（靠 OwnerReference）。但如果你的 controller 在**集群外**也分配了东西呢？比如：

- 在云厂商那边申请了一个负载均衡器；
- 在某个外部数据库里建了一条记录；
- 在对象存储里建了一个 bucket。

用户删掉你的对象时，Kubernetes 的 GC 管不到这些外部资源。如果对象"啪"地一下从 etcd 消失了，你**再也没机会**去释放它们了——它们会变成泄漏的孤儿资源。

**Finalizer（终结器）** 就是为此而生：它是删除前的一道"临终清理"钩子。机制是这样的：

1. controller 在对象创建时，往它的 `metadata.finalizers` 列表里加一个自己的标记，比如 `foo.example.com/cleanup`。
2. 用户执行删除时，Kubernetes **不会**立刻把对象删掉。它只是给对象打上一个 `metadata.deletionTimestamp`（删除时间戳），然后**就停在那里**——只要 finalizers 列表还非空，对象就一直存在（处于 "Terminating" 状态）。
3. controller 的 reconcile 看到 `deletionTimestamp != nil`，知道"这是要删了"，于是去执行外部资源的清理。
4. 清理成功后，controller 把自己那个 finalizer 标记从列表里**移除**。
5. 当 finalizers 列表空了，Kubernetes 才真正把对象从 etcd 删掉。

```
   用户 delete ──► deletionTimestamp 被设置（对象进入 Terminating，但不消失）
                          │
                          ▼
              reconcile 检测到 deletionTimestamp != nil
                          │
                  执行外部资源清理（释放 LB / 删记录 / ...）
                          │
                  移除自己的 finalizer
                          │
                          ▼
              finalizers 空了 ──► Kubernetes 真正删除对象
```

**这是 controller 里最容易出 bug 的地方，** 原因还是那两条铁律：

- **清理必须幂等。** reconcile 可能在"清理外部资源"和"移除 finalizer"之间崩溃重启，重启后又会重新进入清理逻辑。所以"释放外部资源"必须能安全地跑第二次。
- **对 NotFound 宽容。** 如果你要删的外部资源"本来就不存在了"（可能上次已经删过了），不能把这当成错误。否则 reconcile 永远返回 error、finalizer 永远移不掉，对象**永远卡在 Terminating**，用户会很抓狂。正确的写法是："删，如果返回 NotFound，当作成功。"

一句话：**finalizer 的清理逻辑，要写得像 reconcile 主干一样——假设自己会被重复调用，假设资源可能已经不在了。**

## 九、Status 与 Conditions：对外的单一事实源

第三节讲了 spec/status 的分工。落到开发上有三个要点：

**第一，status 是对外的单一事实源（single source of truth）。** 别人（用户、其他系统、`kubectl get`）想知道"这个对象现在到底怎么样了"，只看 status。controller 在每轮 reconcile 的最后，都应该把观察到的实际情况**回填**到 status 里。常见的是用 **Conditions（条件）** 这种结构化的方式表达——每个 Condition 有一个 `type`（如 `Ready`）、`status`（`True`/`False`/`Unknown`）、`reason` 和 `message`，组合起来就能表达对象的健康状况和进度。具体的结构体定义见第十一节 11.0 的 `FooStatus`。

**第二，ObservedGeneration：判断 status 是否跟上了最新的 spec。** Kubernetes 每次用户修改 spec 时会自动递增对象的 `metadata.generation`。controller 在每轮 reconcile 结束时，把当前的 `generation` 抄进 `status.observedGeneration`。这样外部系统（或用户）只要比较这两个值就能判断："controller 是否已经处理了我最新的改动？"如果 `observedGeneration < generation`，说明 controller 还没来得及 reconcile 最新的 spec。

**第三，spec 和 status 走不同的子资源更新（subresource）。** Kubernetes 把 status 做成了对象的一个独立子资源 `/status`。这带来一个重要后果：

> **更新 spec 用 `Update`，更新 status 用 `Status().Update()`，两者互不影响。**

为什么要分开？因为 spec 由用户写、status 由 controller 写（第三节）。如果它们混在一起更新，controller 回填 status 时可能不小心覆盖掉用户刚改的 spec，反之亦然。分成两个子资源，从机制上保证了"用户的意图"和"controller 的汇报"井水不犯河水。

## 十、框架栈：client-go → controller-runtime → kubebuilder

前面讲的 Informer、WorkQueue、reconcile 这些东西，分别由三层工具提供。搞清楚这三层的关系，你就不会在一堆库里迷路：

| 层 | 是什么 | 提供什么 | 类比 |
| --- | --- | --- | --- |
| **client-go** | 最底层的官方 Go 客户端 | Informer、WorkQueue、Clientset、Lister——一堆**原始积木** | 钢筋、水泥、砖 |
| **controller-runtime** | 在 client-go 之上的封装 | Manager、Reconciler 接口、Builder（`For`/`Owns`/`Complete`）、Client（带缓存的读 + 写）——把积木**拼成了控制循环的脚手架** | 预制墙板、楼梯模块 |
| **kubebuilder** | 代码生成脚手架工具 | 命令行生成项目骨架、CRD 定义、Reconcile 模板、RBAC、Makefile——帮你**把房子的框架先搭起来** | 建筑总包，按图纸把毛坯起好 |

它们是**逐层封装**的关系，而不是三选一：

- **client-go** 你几乎不会直接拿来手写 controller（太底层，要自己拼 Informer + WorkQueue + 事件分发），但理解它能让你明白上层在做什么；
- **controller-runtime** 是你**实际写代码时面对的 API**——你实现 `Reconcile`、用 Builder 声明 `For`/`Owns`；
- **kubebuilder** 是**项目初始化阶段**用的工具——`kubebuilder init`、`kubebuilder create api` 帮你把目录结构、CRD、controller 骨架、部署清单一次性生成出来，生成的代码底层正是 controller-runtime。

一句话：**用 kubebuilder 搭架子，用 controller-runtime 写逻辑，必要时下沉到 client-go 看原理。**

## 十一、把概念拼起来：一份骨架代码

下面用 controller-runtime 把前面所有概念串成一份**示意代码**（重在理解，不保证可编译）。注释里标注了每一步对应第一部分的哪个原理。

### 11.0 起点：CRD 与类型定义

在写 controller 之前，你需要先告诉 Kubernetes"我要一个新的资源类型"。这就是 **CRD（Custom Resource Definition，自定义资源定义）**——它是一段 YAML，声明了资源的组名、版本、字段结构等。有了 CRD，用户才能 `kubectl apply` 你的自定义资源，API Server 才知道怎么存储和校验它。

在 Go 代码侧，你用结构体定义这个资源的 spec 和 status。kubebuilder 会根据这些结构体**自动生成 CRD 的 YAML**，你不需要手写。下面是 `Foo` 的类型定义（对应前面 MyApp 场景）：

```go
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status    ← 启用 /status 子资源（第九节）
type Foo struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`

    Spec   FooSpec   `json:"spec,omitempty"`
    Status FooStatus `json:"status,omitempty"`
}

type FooSpec struct {
    // 用户声明的期望状态（第三节的 spec）
    Replicas *int32 `json:"replicas"`
    Image    string `json:"image"`
}

type FooStatus struct {
    // controller 回填的实际状态（第三节的 status）
    ObservedGeneration int64              `json:"observedGeneration,omitempty"`
    Conditions         []metav1.Condition `json:"conditions,omitempty"`
}
```

`kubebuilder create api` 会帮你生成这个文件的骨架（在 `api/v1/foo_types.go`），你只需要往 Spec 和 Status 里加字段。

### 11.1 最小的 main：组装 Manager 并注册 Reconciler

```go
func main() {
    // Manager 持有共享的 Cache（第五节的 Informer/缓存）、
    // Client（带缓存的读 + 直写 API Server 的写）、WorkQueue 等基础设施。
    // 所有 controller 共享这一套，避免每个 controller 各开一套 List+Watch。
    mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
        // 生产环境必开 LeaderElection：多副本部署时，只有 leader 跑 reconcile，
        // 其余副本待命。leader 挂了，另一个副本自动接管。
        // 不开的话多副本会并发 reconcile 同一个对象，产生冲突和重复操作。
        LeaderElection:   true,
        LeaderElectionID: "foo-controller.example.com",
    })
    if err != nil {
        os.Exit(1)
    }

    // 用 Builder 声明式地搭出控制循环，这几行是范式的核心：
    err = ctrl.NewControllerManagedBy(mgr).
        For(&v1.Foo{}).              // 主资源：Foo 变了 → 把 Foo 的 key 入队（level-triggered 的“提醒”）
        Owns(&appsv1.Deployment{}).  // 子资源：带 Foo 这条 OwnerReference 的 Deployment 变了
                                     //        → 反向触发它的属主 Foo 重新 reconcile（第七节）
        Complete(&FooReconciler{Client: mgr.GetClient()})
    if err != nil {
        os.Exit(1)
    }

    // 启动：跑起所有 Informer、WorkQueue 和 worker 协程
    _ = mgr.Start(ctrl.SetupSignalHandler())
}
```

### 11.2 Reconcile 主干：四步骨架

kubebuilder 生成的 Reconciler 上方会有 **RBAC（Role-Based Access Control，基于角色的访问控制）** 标记注释。Kubernetes 里每个 Pod（包括 controller）都以一个 ServiceAccount 身份运行，默认什么权限都没有。RBAC 就是 Kubernetes 的权限系统——你必须显式声明"我需要读写哪些资源"，集群才会放行。kubebuilder 通过下面这些注释自动生成对应的 RBAC 清单：

```go
// +kubebuilder:rbac:groups=mygroup.example.com,resources=foos,verbs=get;list;watch;create;update;patch
// +kubebuilder:rbac:groups=mygroup.example.com,resources=foos/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch
```

忘写 RBAC 是新手最常踩的坑——controller 启动后一切正常，reconcile 里却 403 Forbidden。

```go
func (r *FooReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // ❶ 读期望对象。
    //    注意：我们拿着 key 重新读“当前全量状态”，而不是处理某个事件。
    //    这正是 level-triggered（第一节）——决策只基于当下状态。
    var foo v1.Foo
    if err := r.Get(ctx, req.NamespacedName, &foo); err != nil {
        // 对象已经不在了（可能已被删除）。对 NotFound 宽容：当作正常，无需重试。
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // ❷ 处理删除 / finalizer（第八节）。
    const finalizer = "foo.example.com/cleanup"
    if !foo.DeletionTimestamp.IsZero() {
        // 对象正在被删除（deletionTimestamp 已被设置）。
        if controllerutil.ContainsFinalizer(&foo, finalizer) {
            // 执行外部资源的临终清理。这段逻辑必须幂等、对 NotFound 宽容，
            // 因为它可能被重复调用（崩溃重启会重进这里）。
            if err := r.cleanupExternalResources(ctx, &foo); err != nil {
                return ctrl.Result{}, err // 失败 → 入队重试（指数退避，第六节）
            }
            // 清理成功，移除 finalizer，Kubernetes 随后才会真正删除对象。
            controllerutil.RemoveFinalizer(&foo, finalizer)
            if err := r.Update(ctx, &foo); err != nil {
                return ctrl.Result{}, err
            }
        }
        return ctrl.Result{}, nil
    }
    // 对象存活：确保我们的 finalizer 已挂上，否则将来没机会做外部清理。
    // 注意：添加 finalizer 会改变对象的 resourceVersion，
    // 如果继续用旧对象做后续操作会 conflict，所以加完就 return，
    // 让下一轮 reconcile 拿到最新对象继续。
    if !controllerutil.ContainsFinalizer(&foo, finalizer) {
        controllerutil.AddFinalizer(&foo, finalizer)
        return ctrl.Result{}, r.Update(ctx, &foo)
    }

    // ❸ 确保子资源存在（第二节：ensure 而非 create，整段必须幂等）。
    if err := r.ensureDeployment(ctx, &foo); err != nil {
        return ctrl.Result{}, err
    }

    // ❹ 回填 status（第三、九节）。status 由 controller 写，走 /status 子资源，
    //    与用户写的 spec 互不覆盖。
    foo.Status.ObservedGeneration = foo.Generation
    meta.SetStatusCondition(&foo.Status.Conditions, metav1.Condition{
        Type:               "Ready",
        Status:             metav1.ConditionTrue,
        Reason:             "Reconciled",
        LastTransitionTime: metav1.Now(), // 必填字段，缺了会校验报错
    })
    if err := r.Status().Update(ctx, &foo); err != nil {
        return ctrl.Result{}, err
    }

    // 返回 nil：本轮收敛完成。若返回 error 或 Result{Requeue:true}，
    // 框架会按指数退避把这个 key 重新入队（第六节）。
    return ctrl.Result{}, nil
}
```

### 11.3 幂等的 ensureDeployment：reconcile 收敛的核心动作

```go
func (r *FooReconciler) ensureDeployment(ctx context.Context, foo *v1.Foo) error {
    // 先构造出”期望的”子资源对象（只填 name/namespace，其余在 mutate 里填）。
    dep := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{Name: foo.Name, Namespace: foo.Namespace},
    }

    // CreateOrUpdate 是幂等的关键工具（呼应第二节）：
    //   - 子资源不存在 → 按 mutate 填充后创建；
    //   - 已存在       → 读出来、跑 mutate、若有 diff 则更新；
    //   - 已存在且无 diff → 什么都不做。
    // 跑 1 次和跑 100 次结果一致，这正是 level-triggered 世界的生存法则。
    _, err := controllerutil.CreateOrUpdate(ctx, r.Client, dep, func() error {
        // labels 和 selector 是 Deployment 的必填字段，缺了创建会直接失败。
        labels := map[string]string{“app”: foo.Name}
        dep.Spec.Selector = &metav1.LabelSelector{MatchLabels: labels}

        // 把”期望状态”写进 dep（副本数、Pod 模板等）。
        dep.Spec.Replicas = foo.Spec.Replicas
        dep.Spec.Template = buildPodTemplate(foo)
        dep.Spec.Template.Labels = labels // Pod 模板的 labels 必须匹配 selector

        // 关键：设置 OwnerReference（第七节）。
        //   - 删除 Foo 时级联 GC 掉这个 Deployment；
        //   - 这个 Deployment 变化时，反向触发 Foo 的 reconcile（配合 main 里的 Owns）。
        return controllerutil.SetControllerReference(foo, dep, r.Scheme)
    })
    return err
}
```

把这三段连起来读，你会发现整份代码里**找不到一处"监听某事件 → 做某动作"的影子**。所有逻辑都是"**读当前状态 → ensure 成期望的样子**"。这就是范式本身。

---

# 收尾

一句话概括全文：**level-triggered + 幂等**不是技巧，而是在一个会丢事件、会重启的世界里，唯一能保证最终正确的根基。第二部分的每一个构件都只是它们在工程上的具体落地。

## 核心概念速查清单

| 概念 | 一句话本质 |
| --- | --- |
| **CRD** | 告诉 Kubernetes"我有一个新资源类型"；Go 结构体定义 spec/status，kubebuilder 自动生成 YAML |
| **Reconcile** | 拿着对象 key，把当前状态调谐到期望状态的函数；只收 key、不收事件 |
| **Level-triggered** | 只看"当前状态"、不看"发生了什么事件"；漏事件无害，下轮自愈 |
| **Idempotency（幂等）** | 同一逻辑跑 1 次和 100 次结果一致；写"ensure"而非"create" |
| **Informer & Cache** | List+Watch 同步到本地缓存，读缓存不打 API Server；代价是可能短暂陈旧 |
| **WorkQueue** | 去重、限速、失败重试 + 指数退避；天然把惊群压平 |
| **OwnerReference** | 级联 GC + 子资源变化反向触发属主 reconcile（`Owns`） |
| **Finalizer** | 删除前的临终清理外部资源；清理必须幂等、对 NotFound 宽容 |
| **Status & Conditions** | controller 对外的单一事实源；与 spec 走不同子资源更新 |

## 推荐学习路径

1. **跟一遍 The Kubebuilder Book 的 CronJob 教程**。这是官方最经典的上手教程，会带你用 kubebuilder 从零生成一个真实 controller，把本文的每个概念都落到可运行的代码上。
2. **用 envtest 写单元测试**。controller-runtime 自带的 `envtest` 能起一个真实的 API Server + etcd（不需要完整集群），让你对着真 API 测 reconcile 逻辑。这是验证"幂等""finalizer 正确性"的最好方式。
3. **读 kubeflow training-operator 作为工业级参考**。它是一个成熟、复杂、生产级的 controller，能看到本文所有范式在真实项目里是怎么组织和取舍的——多 reconcile 协作、复杂 status、各种边界处理。

理解了第一性原理，再看任何 controller 源码，你都能立刻问出那个对的问题：**它在把什么 actual 调谐到什么 desired？它的幂等是怎么保证的？**
