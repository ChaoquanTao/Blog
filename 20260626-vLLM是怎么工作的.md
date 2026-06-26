---
title: vLLM 是怎么工作的？
date: 2026-06-26
categories: AI Infra
tags:
  - vLLM
  - LLM
  - 推理优化
  - PagedAttention
---

# vLLM 是怎么工作的？

> 本文翻译并整理自 Amit Shekhar 的 [How does vLLM work?](https://outcomeschool.com/blog/how-does-vllm-work)。

## 目录

- 什么是"服务一个 LLM"
- Prefill、Decode 与 KV cache 快速回顾
- 问题：KV cache 吞噬 GPU 显存
- 为什么朴素的服务方式会浪费内存
- vLLM 是什么
- PagedAttention：核心思想
- PagedAttention 如何共享内存
- 连续批处理（Continuous Batching）
- OpenAI 兼容的 API 服务器
- vLLM 的收益
- 与 SGLang、TensorRT-LLM 的横向对比
- vLLM 在真实世界中的应用

---

## 什么是"服务一个 LLM"

在谈 vLLM 之前，先要明白"服务（serving）一个 LLM"到底意味着什么。

大语言模型（LLM）是 ChatGPT、Claude 这类产品背后的核心技术。我们给它一段文本，它就返回另一段文本。**所谓服务一个 LLM，就是把模型部署在机器上，让大量用户能够同时向它提问、并拿到回答。** 而负责把请求收进来、调度模型运行、再把回复发回去的那段软件，就叫**服务引擎（serving engine）**。

```
用户 1 ──问题──▶  ┌───────────────┐    ┌────────────────┐
用户 2 ──问题──▶  │   服务引擎    │───▶│  GPU 上的模型  │
用户 3 ──问题──▶  │ （接请求、发  │    │ （干重活、生成 │
   ...           │   回复）      │◀───│   回复）       │
用户 N ──问题──▶  └───────────────┘    └────────────────┘
                       │
                       └──回复──▶ 回到每个用户
```

LLM 跑在 **GPU** 上。GPU 算力强劲，但显存既有限又昂贵。**显存每浪费一分，能服务的用户就少一分，成本也就随之高一分。**

所以，服务 LLM 的本质目标可以归结为一句话：**在一张 GPU 上，尽可能多、也尽可能快地服务用户。** 记住这个目标——vLLM 正是为了赢下这场博弈而生的。

## Prefill、Decode 与 KV cache 

先从最基础的讲起。LLM 收到一段文字后，并不是按"一个完整单词"来读，而是先把它切成更小的片段——叫做 **token（词元）**。token 可以是一个词、半个词，或一个标点；为了好理解，下面我们就近似地把一个 token 当成一个词。

关键要先建立一个直觉：**模型每"跑"一次，只能往外吐出 1 个新 token。** 想写出一整句话，就得让模型反复跑很多次，一次接一次地把词续上去。整个过程分成两个阶段。

### 第一阶段：Prefill（把 prompt 读进去）

假设用户的 prompt 是 `Tell me a joke`，切成 4 个 token。模型会把这 4 个 token **一次性、同时**喂进去处理一遍，然后吐出回复的第 1 个 token。这一步只做一次：

```
        输入（prompt 的全部 4 个 token，一起喂进去）
        ┌──────┬──────┬──────┬──────┐
        │ Tell │  me  │  a   │ joke │
        └──────┴──────┴──────┴──────┘
                      │
                      ▼  模型跑一次
                  ┌───────┐
        输出 ───▶ │  Why  │   ← 只产出 1 个新 token
                  └───────┘

此时完整序列： Tell me a joke │ Why
```

### 第二阶段：Decode（一个词一个词地往下写）

接下来进入循环。**每一步，模型都把"到目前为止的全部 token"重新看一遍，然后再吐出 1 个新 token，接到末尾。** 然后拿这个更长的序列再跑下一步，如此往复：

```
DECODE 第 1 步
  看： Tell me a joke Why            → 吐出： did
  现在： Tell me a joke Why did

DECODE 第 2 步
  看： Tell me a joke Why did        → 吐出： the
  现在： Tell me a joke Why did the

DECODE 第 3 步
  看： Tell me a joke Why did the    → 吐出： chicken
  现在： Tell me a joke Why did the chicken

  ……每一步都比上一步长 1 个 token，
     直到模型吐出"结束符"或到达长度上限，才停下。
```

注意到关键的一点了吗：decode 的**每一步，都要回头参考前面所有的 token**。这正是为什么 prefill 计算密集（一口气算完一长串），而 decode 是逐 token 慢慢挤出来的。

### 为什么需要 KV cache

现在问题来了：decode 每一步都要"重新看一遍前面所有 token"。如果每次都把前面那些**老 token** 的内部计算从头再算一遍，会非常浪费——而且越往后序列越长，越算越慢。

于是有了一个关键优化：模型把每个 token 算过一次的中间结果（每一层、每个注意力头上的 **Key / Value 张量**）**缓存起来**，这份缓存就叫 **KV cache**。有了它，decode 每一步只需要**真正计算那 1 个新 token**，前面所有老 token 直接从缓存里读，不再重算。

> **先搞懂 Key / Value 和"注意力头"**（已经熟悉 Transformer 的读者可以跳过）
>
> 模型处理一个 token 时，要判断前面哪些 token 跟它有关。这个过程很像一次"软查询"：每个 token 都会产出三个向量——**Query（我在找什么）**、**Key（我是关于什么的，相当于索引）**、**Value（我实际携带的信息）**。当前 token 用自己的 Query 去比对前面所有 token 的 Key，算出"该关注谁、关注多少"，再按这个权重把对应的 Value 汇总起来，就得到了它从上下文里"读到"的东西。
>
> 而模型不会只做一次这种查询，而是并行做很多份，每一份就叫一个**注意力头（attention head）**：不同的头各盯一种关系——有的管语法搭配，有的负责弄清代词指代谁……每个头都有自己独立的一套 Q/K/V。模型有很多层，每层又有很多个头，所以"每一层、每个注意力头上"才都有一份 K/V。
>
> **举个例子**，看这句话：`The cat sat on the mat because it was tired.`（猫坐在垫子上，因为它累了）。当模型处理到 `it` 时：
> - `it` 发出 Query，含义大致是"我是个代词，正在找我指代的那个名词"；
> - 前面每个 token 亮出自己的 Key：`cat` 的 Key ≈"我是个动物、能当主语"，`mat` 的 Key ≈"我是个物体"；
> - `it` 的 Query 和 `cat` 的 Key 最匹配，于是注意力权重集中到 `cat` 上，主要汲取 `cat` 的 Value（它携带的语义）——模型就此"读懂"了 `it` 指的是猫，而不是垫子。
>
> 而这件事是多个头**同时**在做、各管一摊：可能 1 号头负责把 `it` 连到 `cat`（指代消解），2 号头负责把 `sat` 连到主语 `cat` 和地点 `mat`（语法结构），3 号头负责把 `tired` 和 `because` 关联起来（因果）。把所有头、所有层的结果叠加，模型才真正"理解"了整句话。
>
> 至于**为什么缓存的是 K 和 V、不是 Q**：生成新 token 时，是拿**新 token 的 Query** 去对照**前面所有老 token 的 Key/Value**。老 token 的 K/V 算过一次就不再改变，存下来即可；新 token 只需现算自己的 Q，再把自己的 K/V 追加进缓存。

```
带 KV cache 的视角：每生成 1 个 token，缓存就多 1 份，永不重算旧的

PREFILL：一次性为 prompt 的 4 个 token 各存 1 份
  KV cache:  [Tell][me][a][joke]                     共 4 份

DECODE 第 1 步：只算新 token "Why"，存进缓存
  KV cache:  [Tell][me][a][joke][Why]                共 5 份
DECODE 第 2 步：只算新 token "did"
  KV cache:  [Tell][me][a][joke][Why][did]           共 6 份
DECODE 第 3 步：只算新 token "the"
  KV cache:  [Tell][me][a][joke][Why][did][the]      共 7 份
  ……                                                 （每步 +1 份）
```

**关键点：KV cache 会随着回答变长而不断增长，而且全部驻留在 GPU 显存里。** 以一个 7B 模型在 fp16 下为例，单个 token 的 KV cache 大约几十 KB；上千 token 的长对话就要占掉几十到上百 MB——而一张卡的显存总共也就 24/40/80 GB。正因如此，**这份会不断膨胀的缓存，后面会成为整个系统的瓶颈**——这也是 vLLM 要解决的核心问题。

## 问题：KV cache 吞噬 GPU 显存

模型本身就占掉一大块显存，剩下的空间才用来放所有正在服务的请求的 KV cache。

**所以，决定"一次能并发服务多少用户"的往往不是算力，而是留给 KV cache 的那点显存。** 服务 LLM 的真正瓶颈，从来不是算得快不快，而是**显存管理**。

## 为什么朴素的服务方式会浪费内存

朴素的服务引擎会做一件"看似稳妥、实则很浪费"的事：

**请求一进来，引擎并不知道回答最终会有多长，于是干脆按最坏情况——比如 2000 个 token——预留一整块连续显存。**

可绝大多数回答其实只有几十到一两百个 token，剩下 1900 多个 token 的空间就被白白锁住，谁也用不上。

这种浪费在 PagedAttention 论文里有更精确的术语：

- **内部碎片（internal fragmentation）**：单个请求预留了 2000，实际只用了 50，剩下的 1950 都浪费在了这个请求自己的内存块内部。
- **外部碎片（external fragmentation）**：多个请求各占一块，块与块之间散落着零碎的小空隙，单看任何一处都塞不下一个新请求。

```
朴素服务：每个请求一块大连续内存

请求 A: [#### 用 50 ........... 为 2000 预留但浪费 .............]
请求 B: [###### 用 120 ......... 为 2000 预留但浪费 .............]
请求 C: [## 用 20 ............. 为 2000 预留但浪费 .............]

剩余空闲：零碎小块 → 装不下任何新请求
```

于是出现了一个尴尬的局面：显卡账面上明明还剩不少显存，实际却只能服务寥寥几个用户。这正是 vLLM 要解决的问题。

## vLLM 是什么

**vLLM 是一个面向 LLM 推理的高吞吐服务引擎**，它的核心，就是把 KV cache 的显存管理做到极致。

所谓**吞吐量（throughput）**，指的是单位时间内能完成多少工作——具体到这里，就是每秒能处理多少 token、服务多少请求。

vLLM 主要靠两件事来解决问题：

- **PagedAttention**：把 KV cache 拆成固定大小的小块，用多少分多少，而不是一上来就预留一大片。
- **连续批处理（Continuous Batching）**：在每一个 decode 步上让请求动态进出，尽量不让 GPU 闲着。

## PagedAttention：核心思想

PagedAttention 借鉴的是操作系统的**分页**机制。

操作系统不会一次性把进程申请的内存连续分配出去，而是切成固定大小的 **page（页）**，按需分配、不要求物理上相邻，再用**页表**记录每一页落在哪里。

vLLM 对 KV cache 做了同样的事：

- 把 KV cache 切成固定大小的 **block（块）**（默认每块 16 个 token，可配置）
- 给每个请求维护一张 **block table（块表）**，记录"这个请求逻辑上的第 0、1、2…… 块 KV cache，分别落在物理上的哪一块"
- 请求需要更多 token 时，就从空闲池里取一块给它，**不要求物理上相邻**
- 请求一旦结束，它占用的所有块立刻归还空闲池

```
PagedAttention：KV cache 切成等大小的小块

GPU 物理块池: [B1][B2][B3][B4][B5][B6][B7][B8][B9] ...

请求 A 的 block table → B1, B4, B7   （按需拿了 3 块）
请求 B 的 block table → B2, B3       （按需拿了 2 块）
请求 C 的 block table → B5           （刚开始，1 块）

空闲块: B6, B8, B9
```

这里要分清两个概念：

- **逻辑块（logical block）**：从请求自己的视角看，就是"我的第 0、1、2 块"，编号是连续的。
- **物理块（physical block）**：显存里实际占用的那一块，物理位置上可以散落在任何地方。

**这套机制是有代价的**：注意力计算所需的 K/V 张量在显存里不再连续，普通的 attention CUDA kernel 没法直接用——vLLM 必须配套一个能在**非连续内存**上做注意力计算的自定义 kernel。这也是为什么 PagedAttention 在实现层面远不止"加一个内存分配器"这么简单。

>这句话稍微展开一下。所谓 **kernel**，就是真正跑在 GPU 上、执行某一段具体计算（这里指注意力计算）的程序。GPU 之所以快，靠的是成千上万个线程一起读显存、一起算；而要榨干带宽，这些线程通常**默认数据是一整块连续排布的**——挨着读、按规整的步长读，效率才最高。现成的高性能注意力 kernel（如 FlashAttention）正是建立在"一个序列的 K/V 在显存里连成一片"这个前提上写的。
>
  可 PagedAttention 偏偏把 K/V 打散成了一块块、物理上四处散落的 block。对原来的 kernel 来说，这等于把它赖以提速的前提抽走了：它不知道下一个 token 的 K/V 跳到哪去了，自然没法直接用。于是 vLLM 只能**重写一个 kernel**：让它先查 block table，弄清每个逻辑位置对应的物理块到底在哪，再去那些零散的地址上把 K/V 取出来做注意力——既要兼容"分页"的内存布局，又得尽量不丢掉 GPU 的并行效率。
>
>所以 PagedAttention 真正的工作量，一半在"分页式的显存管理"，另一半在"为这种布局专门定制的 GPU kernel"。只看前者会觉得它不过是给 KV cache 加了个内存分配器，但正是后者——那个能在非连续内存上高效跑注意力的 kernel——才是它落地的难点所在。

## PagedAttention 如何共享内存

一旦 KV cache 按块来组织，**内存共享**几乎是顺手就能拿到的红利。

**两个不同的请求，只要把各自 block table 里的某一项指向同一个物理块，就实现了内存共享。**

典型的两种共享场景：

**相同前缀**。很多用户的请求都以同一段长长的 system prompt 开头，比如"你是某汽车经销商的客服助手，请保持礼貌……"。这种情况下，vLLM 把这段开头的 KV cache 只算一次、只存一份，所有请求的 block table 都指向同样那几块。

**Beam search（束搜索）**。模型同时探索多条候选回答（beam），它们共享同一个开头，只在后面才分叉。于是开头的块可以共享，分叉之后的部分再各自分配。

```
共享

共享开头:  [B1][B2]   ← 物理上只有一份
              │
       ┌──────┼──────┐
       │      │      │
   请求 A  请求 B  Beam C
   加 [B5]  加 [B6]  加 [B7]
```

## 连续批处理（Continuous Batching）

GPU 一次同时跑多个请求时效率最高，所以要做**批处理（batching）**。但最朴素的做法——**静态批处理（static batching）**——是凑齐一批请求一起跑，**必须等整批里最慢的那个结束，才能开始下一批**。

问题在于，不同请求的回答长度差别巨大：一个用户 20 个 token 就答完了，另一个却要 800 个。在静态批里，那个 20 token 的请求早早跑完，可它占的 slot 还得一直空等着，直到 800 token 的那个也结束。这段空等的时间纯属浪费。

**连续批处理**换了个思路：**在每一个 decode 步**都重新决定这一批里到底跑哪些请求——某个请求一结束，就立刻从等待队列里拉一个新请求补进它的位置，让 GPU 一刻都不空转。

```
静态批处理（朴素）：整批等最慢的

step:   1    2    3    4    5    6    7    8
请求 A:  X    X    X   完成 -    -    -    -    ← slot 空转
请求 B:  X    X    X    X    X    X    X   完成

连续批处理（vLLM）：finished 立即被填掉

step:   1    2    3    4    5    6    7    8
slot1:  A    A    A    C    C    C    D    D   ← A 结束 C 进来，C 结束 D 进来
slot2:  B    B    B    B    B    B    B   完成
```

连续批处理和 PagedAttention 可以说是**天作之合**：前者一空出 slot，后者就立刻把对应的 block 回收进空闲池，新请求随即拿到显存和算力，无缝接上。


## OpenAI 兼容的 API 服务器

vLLM 不只是一个推理库，它对外暴露的是一个 **OpenAI 兼容的 HTTP 服务器**——`/v1/chat/completions`、`/v1/completions`、`/v1/embeddings` 一应俱全，并支持流式输出、function calling 等特性。

这一点的意义在于：你用 OpenAI SDK 写好的现有代码，只要把 `base_url` 指向自己的 vLLM 地址，就能无缝切换到自家 GPU 上的开源模型，**业务代码一行都不用动**。这正是 vLLM 在工程圈传播得如此之快的重要原因之一。

## vLLM 的收益

- **更高的吞吐量**：PagedAttention 省显存，连续批处理省算力，二者叠加，在很多场景下相比朴素引擎能拿到 **2–4 倍**、甚至更高的吞吐提升（数字来自 SOSP '23 原始论文，实际幅度取决于工作负载）。
- **更高的 GPU 利用率**：显存和算力都能接近打满。
- **更低的单请求成本**：一张卡能服务更多用户，分摊到每个请求上的硬件成本随之下降。
- **极低的接入成本**：一套 OpenAI 兼容 API，现有代码几乎拿来即用。

**不过有一个 trade-off：连续批处理叠加大 batch，通常意味着**单个请求的延迟（尤其是 TTFT 和 TBT）会上升**——因为你的请求得和其他人的请求一起排队调度。所以生产部署时，需要在吞吐（throughput）和延迟（latency）之间权衡取舍，天下没有免费的午餐。

## 与 SGLang、TensorRT-LLM 的横向对比

vLLM 并不是唯一的选择。截至 2026 年，生产环境里常见的同类方案还有以下几个：

### TensorRT-LLM（NVIDIA）

- **优势**：NVIDIA 官方出品，kernel 优化一路做到了 PTX/SASS 层级，**在 H100/H200/B200 上的裸吞吐往往是同类里的天花板**。in-flight batching（相当于连续批处理）、paged KV cache、speculative decoding，以及 FP8、INT4 AWQ、INT8 SmoothQuant 等各种量化它都支持。
- **劣势**：需要 **AOT 编译**（把模型先转成 TensorRT engine），编译耗时长，对新模型的适配也偏慢；调试和扩展门槛较高；而且只支持 NVIDIA 硬件。
- **适用**：模型稳定、不常更换，硬件已锁定 NVIDIA，且对延迟极其敏感的场景。

### SGLang（Berkeley 等）

- **优势**：核心创新是 **RadixAttention**——用基数树（radix tree）来做 KV cache 的前缀共享，**比 vLLM 的 prefix caching 更激进**。在 agent、多轮对话、RAG 这类"前缀大量重复"的场景下，命中率和性能都明显优于 vLLM。它还内置了一套面向 LLM 程序的 DSL，做结构化生成和约束解码很方便。
- **劣势**：社区比 vLLM 小，硬件后端覆盖窄一些，对很多冷门模型的适配速度比 vLLM 慢。
- **适用**：以 agent / RAG / 多轮对话为主、前缀复用率高的工作流。

### LMDeploy（上海 AI Lab）

- **优势**：TurboMind 后端在某些中文场景和特定硬件（含国产卡）上很有竞争力，量化支持完善。
- **适用**：国内部署、需要考虑国产硬件，或者重度依赖 InternLM 等模型的场景。

### vLLM

- **优势**：**社区最活跃、文档最全、模型覆盖最广**，对 NVIDIA、AMD、Intel Gaudi、Google TPU、AWS Neuron 等硬件都有支持；扩展性也好，接入新模型、新量化、新 attention 后端都很容易。
- **劣势**：单论 NVIDIA 上的极限吞吐，通常略逊于 TensorRT-LLM；单论前缀共享，又略逊于 SGLang。
- **适用**：默认首选。除非你有非常明确、足以压倒一切的特定需求，否则从 vLLM 起步几乎不会出错。

一句话概括：**TRT-LLM 拼极限、SGLang 拼前缀、vLLM 拼通用**。

## vLLM 在真实世界中的应用

vLLM 是当下最流行的开源 LLM 服务引擎之一，对于任何想在自家 GPU 上跑开源模型的团队来说，它几乎都是默认选项。其中有两类场景尤其受益：

- **高流量聊天应用**：连续批处理把每个 GPU slot 都填满，PagedAttention 则把所有用户的 KV cache 紧凑地塞进显存，两头都不浪费。
- **Agent 系统**：agent 每一步都要带上同一段长指令（system prompt + 工具说明 + 历史对话），前缀共享（prefix sharing）的省显存效果在这种场景下格外突出；与此同时，agent 往往步骤多、单步回答短，连续批处理能把 GPU 的空闲时间压到极低。

## 一句话总结

说到底，vLLM 的高吞吐建立在两块基石上。一是 **PagedAttention**：把操作系统的分页思想搬到了 KV cache 上，用固定大小的小块按需分配显存，既消灭了"预留一大片却用不满"的碎片浪费，又让相同前缀能以近乎免费的代价共享。二是**连续批处理（continuous batching）**：在每一个 decode 步动态地放入新请求、放走已完成的请求，让 GPU 永不空转。两者一个省显存、一个省算力，正好互补；最后再裹上一层 OpenAI 兼容 API，让现有代码几乎零成本接入。三者合到一起，同一张 GPU 就能服务远多于朴素方案的用户。

它当然不是这条赛道上的唯一选手——单论 NVIDIA 上的极限吞吐有 TensorRT-LLM，单论前缀复用有 SGLang。但凭着最活跃的社区、最广的模型与硬件支持，vLLM 依然是绝大多数团队最稳妥的默认起点。

---

**参考链接**

- vLLM 原始论文（SOSP '23）：_Efficient Memory Management for Large Language Model Serving with PagedAttention_
- vLLM 官方文档：[https://docs.vllm.ai](https://docs.vllm.ai/)
- SGLang：[https://github.com/sgl-project/sglang](https://github.com/sgl-project/sglang)
- TensorRT-LLM：[https://github.com/NVIDIA/TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)