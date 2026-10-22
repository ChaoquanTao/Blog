---
title: 什么是 Agent 基础设施：从 Solo.io 的 Agentic AI 产品栈说起
date: 2026-10-20
categories: AI Infra
tags:
  - AI Agent
  - Agent 基础设施
  - MCP
  - A2A
  - kagent
  - agentgateway
  - 云原生
---

# 什么是 Agent 基础设施：从 Solo.io 的 Agentic AI 产品栈说起

> Agent 基础设施是让 AI Agent 从"能跑的 demo"变成"敢放进生产的系统"的那一层底座：它不让 Agent 更聪明，而是让 Agent 可运行、可连接、可控制、可观测、可信任。

## 引言：demo 和生产之间隔着一层看不见的东西

今天做一个 Agent demo 只需要一个下午：一段系统提示词、几个 MCP 工具、一个大模型 API Key。它能查日志、写代码、回答问题，效果往往令人惊艳。

真正卡住团队的是下一步。安全团队会问：它能不能删生产库？财务会问：上个月花了多少 token？业务方会问：昨天那个错误答案是怎么来的？平台团队会问：公司里到底跑着多少个 Agent？

这些问题和模型能力无关，却每一个都能让项目停在试点阶段。安全、可观测性、韧性和治理，才是阻碍 Agent 从试点走向生产的主要障碍。回答这些问题的那一层，就是 Agent 基础设施。

为什么从 Solo.io 说起？这家以服务网格和 API 网关起家的公司，近两年围绕 Agent 陆续开源了 kagent（运行时）、agentgateway（网关）、agentregistry（注册中心）和 agentevals（评估），恰好覆盖了 Agent 基础设施的大部分层次，而且几个项目都已进入 CNCF 或 Linux Foundation 等中立基金会。用它作为参照样本，能把一个抽象的概念落到具体的工程组件上。

本文先讲清楚这个概念，再按层拆解它在工程上长什么样，最后以这套产品栈为例，看看每一层的代表性实现，以及它们如何串成一个 Agent 的完整生命周期。

## 什么是 Agent 基础设施

一句话定义：Agent 基础设施是位于大模型与 Agent 业务逻辑之下、负责运行、连接、授权、治理、观测和评估 Agent 的平台层。

用一个熟悉的类比最容易理解。上线一个 Web 应用，业务代码只是一小部分，你还需要：

- Kubernetes 来运行和扩缩容
- API 网关和服务网格来管理流量
- IAM 和 RBAC 来控制谁能做什么
- 日志、监控、链路追踪来排查问题
- 镜像仓库来管理版本，CI 来保证质量

这一整套被称为云原生基础设施。开发者平时感觉不到它，但没有它，系统就上不了生产。

Agent 基础设施是同样的思路，只是服务对象从"确定性的程序"换成了"会自主决策、会调用工具、行为不确定的 Agent"。模型决定 Agent 的能力上限，基础设施决定企业敢不敢把它用起来。

## 为什么云原生那一套不够用

既然已有成熟的云原生基础设施，为什么还要新的一层？因为 Agent 有五个传统应用没有的特性，每一个都会击穿现有工具的假设。

| Agent 的特性 | 传统基础设施的假设 | 带来的新需求 |
| --- | --- | --- |
| 行为不确定：换模型、改提示词，行为就可能变 | 测试通过即可靠 | 持续评估，而不只是一次性测试 |
| 会主动行动：自己决定调用哪些工具、按什么顺序 | 程序只执行写死的操作 | 细到"哪个 Agent 能调哪个工具"的授权，高风险动作人工审批 |
| 使用新协议：MCP、A2A、LLM API，有状态、长会话、流式 | 一个请求对应一个后端 | 理解 Agent 协议的专用网关 |
| 按 token 计费，且代表某人行动 | 成本按机器算，身份按服务算 | 按团队和用户的计量、预算与身份传递 |
| 数量爆炸：人人都在造 Agent、MCP Server、Skills | 服务目录变化缓慢 | 统一注册中心，防止"影子 AI" |

以协议为例。[agentgateway 的文档](https://agentgateway.dev/docs/local/main) 指出，传统 API 网关是一个请求打到一个后端，而 MCP 需要把一个会话分发到多个 MCP Server，并且要应对协议规范不断演进带来的升级与回退。这不是给老网关加个插件就能解决的。

再以可靠性为例。不少团队用 Agent 排查 Kubernetes 部署和网络配置问题后发现：同一个 Agent 在不同模型、不同提示词下，可靠性差别很大。没有持续评估，就无法放心地迭代。

## 分层模型：Agent 基础设施的六层

把上面的需求归类，Agent 基础设施可以拆成六层。它们位于业务 Agent 之下、模型与云原生底座之上，每一层回答一个上线前必须回答的问题。

| 层 | 回答的问题 | 典型开源项目 |
| --- | --- | --- |
| ⑥ 评估 | 它靠不靠谱？改动之后变好了还是变坏了？ | agentevals |
| ⑤ 可观测 | 它刚才做了什么、花了多少、哪一步出错？ | OpenTelemetry |
| ④ 注册与治理 | 公司里有哪些 Agent 和工具？哪些被批准使用？ | agentregistry |
| ③ 身份与策略（横跨运行时与网关） | 谁能调用什么？Agent 代表谁在行动？ | 由运行时与网关共同实现 |
| ② 连接与网关 | Agent 怎么安全地连到模型、工具和其他 Agent？ | agentgateway |
| ① 运行时 | Agent 在哪里跑、怎么部署和扩缩容？ | kagent |

表格自上而下对应从业务 Agent 到底座的顺序：最上面是业务 Agent，最下面是大模型与 Kubernetes 等云原生底座。运行时和网关是地基，身份策略横跨两者；注册、可观测、评估则决定 Agent 能否被规模化地管理和信任。表中项目只是各层的典型示例，可替换为任意同类方案。

## 开源生态中的代表性实现

近两年，云原生社区已经为每一层长出了专门的开源项目，不少已进入中立基金会。下面以 Solo.io 发起的这组项目为主线按层举例：重点是每一层要解决什么，项目只是参照。

### 运行时：把 Agent 当作一等资源

以 Solo.io 开源的 [kagent](https://github.com/kagent-dev/kagent) 为例，它把 Agent、模型配置、MCP 工具都定义成 Kubernetes 自定义资源，用 YAML 声明、用 kubectl 管理。它由控制器、UI、执行引擎和 CLI 组成，内置 Kubernetes、Istio、Helm、Argo、Prometheus 等工具，是 [CNCF sandbox 项目](https://kagent.dev/docs/kagent/introduction/what-is-kagent)。云厂商的托管 Agent 平台是另一条路线：免运维，但与特定云绑定。

典型场景是值班排障。告警触发后，工程师在 Slack 里让 Agent 查看 Pod 事件、日志和内存曲线，Agent 建议调大 memory limit；由于修改 Deployment 是写操作，执行前需要人工批准。

这一层的边界还在扩展：除了程序化和声明式 Agent，常驻型个人助手也开始被纳入统一受治理的运行时。

### 连接与网关：理解 Agent 协议的数据面

以 [agentgateway](https://agentgateway.dev/) 为例，它用 Rust 编写，一个数据面同时处理 HTTP/gRPC 服务流量、LLM 调用、MCP 和 A2A，最初由 Solo.io 开源，现为 Linux Foundation 旗下 [Agentic AI Foundation（AAIF）的托管项目](https://agentgateway.dev/docs/standalone/main/documentation/about/introduction/)。这一层通常解决三类问题：

- MCP 治理：把多个 MCP Server 聚合到一个入口，按身份限定每个调用方能用哪些工具，对工具调用做审计和注入防护；还能把现有 REST API 通过 OpenAPI 直接暴露成 MCP 工具。
- LLM 出口治理：统一接入多家模型，提供虚拟 Key、按团队的 token 预算和花费上限、故障切换。
- A2A 路由：在不同框架的 Agent 之间转发调用，每一跳都带身份和追踪。

一个典型做法：把公司全部 LLM 流量经过网关，只允许经企业身份验证的员工访问模型，并按部门、按模型统计 token 用量。这些全部通过配置完成，后端 MCP Server 无需改动。

### 注册与治理：企业内部的"Agent 应用商店"

以 [agentregistry](https://github.com/agentregistry-dev) 为例，它由 Solo.io 开源、已贡献给 CNCF，集中编目、发现和治理三类制品：Agent、MCP 工具和 Agent Skills，设计上参考了官方 MCP registry 的思路。

平台团队把审核过的故障排查 Agent、慢查询分析 Skill、内部 CMDB 的 MCP Server 发布上去；业务团队搜索、组合、一键部署，而不是去 GitHub 上随手找来路不明的 MCP Server。平台团队也因此能看清公司里跑着哪些 Agent、用了哪些工具。

### 评估：把"靠不靠谱"变成可度量的指标

这一层的代表包括 Solo.io 于 2026 年 3 月开源的 [agentevals](https://solo.io/press-releases/introducing-new-agentic-open-source-project-agentevals)，以及 LangSmith、Langfuse 等评估与可观测平台。共同的思路是：基于追踪数据采集 Agent 的每一次调用，对照团队定义的黄金评估集打分，常用轨迹匹配和 LLM-as-judge 两类评估器，并在换模型、加工具或改提示词时告警。

典型场景是换模型。团队想把运维 Agent 换成更便宜的模型，跑一遍黄金集后发现：多数用例表现一致，但网络策略类问题经常跳过关键排查步骤。于是只在简单问题上用便宜模型，复杂问题仍路由给强模型，而这个路由本身又可以交给网关层来做。

### 可观测性：复用而非重建

OpenTelemetry 已经成为这一层的事实标准。好的 Agent 基础设施组件都会直接输出追踪数据，接入团队现有的 Prometheus、Grafana、Jaeger 体系，而不是再造一套监控。

## 串起来：一个 Agent 的生命周期

把六层放在一起看，Agent 的生命周期和传统软件的"编码、测试、推仓库、部署、网关治理、监控"几乎一一对应。以"平台团队为全公司提供一个集群诊断 Agent"为例：

1. 构建：平台工程师在运行时中用声明式配置定义 Agent，绑定 Kubernetes 和 Prometheus 的 MCP 工具，以及几个排障 Skills。
2. 评估：上线前跑黄金评估集，确认常见故障场景下的推理路径正确。
3. 发布：评估通过后发布到注册中心，标记为已批准，其他团队可以搜索和复用。
4. 运行：业务团队从注册中心拉取，部署到自己的集群，只授予只读 RBAC 权限。
5. 治理：Agent 调用模型、工具和其他 Agent 的流量全部经过网关，统一认证、限流、计费和审计。
6. 持续改进：在线评估生产流量，质量下滑时告警，团队回到第 1 步迭代。

这个闭环里，没有任何一步依赖模型"更聪明"，全部是工程问题。这正是 Agent 基础设施的价值所在。

## 结语

十年前，容器让应用变得容易打包，但真正让企业放心上云的，是围绕容器长出来的 Kubernetes、服务网格、可观测性那一整套基础设施。今天的 Agent 正处在相似的位置：能力已经足够，缺的是让它在生产中可控、可审计、可信任的底座。

业界正在形成的共识是：当 Agent 从实验走向规模化，瓶颈会从"能力"转移到"治理"。无论最终选择哪种方案，理解运行时、连接、身份策略、注册治理、可观测、评估这六层，都是设计企业 Agent 平台的起点。

## 参考资料

- [kagent GitHub 仓库](https://github.com/kagent-dev/kagent)
- [kagent 文档：What is kagent](https://kagent.dev/docs/kagent/introduction/what-is-kagent)
- [agentgateway 官网](https://agentgateway.dev/)
- [agentgateway 文档：Introduction](https://agentgateway.dev/docs/standalone/main/documentation/about/introduction/)
- [agentgateway 文档：本地部署概览](https://agentgateway.dev/docs/local/main)
- [agentregistry GitHub](https://github.com/agentregistry-dev)
- [Solo.io：Introducing agentevals](https://solo.io/press-releases/introducing-new-agentic-open-source-project-agentevals)
- [Cloud Native Now：Solo.io Launches agentevals, Contributes agentregistry to CNCF](https://cloudnativenow.com/uncategorized/solo-io-launches-agentevals-open-source-project-contributes-agentregistry-to-cncf/)
- [IT Brief：Agentic AI Foundation adds agentgateway as hosted project](https://itbrief.co.uk/story/agentic-ai-foundation-adds-agentgateway-as-hosted-project)
