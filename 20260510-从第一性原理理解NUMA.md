---
title: 从第一性原理理解NUMA
date: 2026-05-10 09:00:00
categories: 操作系统
---

# 从第一性原理理解 NUMA

## 一、一个反直觉的现象

先看一个例子。

我们有一台双路服务器，里面装了两颗 CPU，跑一个内存敏感的服务。同样的硬件、同样的代码、同样的负载，做两件事：

- **不绑核**：让操作系统自由调度
- **绑核**：用 `numactl` 把进程绑到一颗 CPU 上

结果绑核的版本性能高了将近 30%。

奇怪吗？理论上"内存就是内存"，访问哪一块都一样，为什么仅仅是"换了颗 CPU 来跑"，性能就掉这么多？

要回答这个问题，得回到一个更基础的事实：**在多 CPU 的服务器上，"内存"早就不是均匀的了。** 这个事实有个名字，叫 NUMA。

要理解 NUMA，得先从它的前身 UMA 开始。

## 二、UMA：所有 CPU 共享一块内存

**UMA**（Uniform Memory Access，统一内存访问）是 90 年代多 CPU 服务器的标准设计。

它的思路很直觉：一台机器有多颗 CPU，但**共享同一块内存**。任何 CPU 访问任何内存地址，延迟都一样。

```
   CPU0      CPU1      CPU2      CPU3
    │         │         │         │
    └─────────┴────┬────┴─────────┘
                   │
              ┌────▼────┐
              │ 内存总线│
              └────┬────┘
                   │
              ┌────▼────┐
              │   内存  │
              └─────────┘
```

UMA 最大的好处是**对程序员透明**——不管几颗 CPU，写代码时都不用关心"内存在哪里"。在 2 颗、4 颗 CPU 的时候，这种方案跑得很好。

但当 CPU 数量继续上涨，UMA 就开始撞墙了。

## 三、UMA 撞了什么墙？

简单说四件事，每一件都和物理世界过不去。

**第一，总线带宽分不够。** 所有 CPU 共用一条访问内存的总线。总线的带宽是固定的，CPU 越多，每颗能分到的就越少。8 颗 CPU 等于 8 个人挤一条独木桥，再多就直接堵死。

**第二，缓存一致性流量爆炸。** 每颗 CPU 都有自己的高速缓存，缓存里的数据要和其他 CPU 保持一致——"我改了这个变量、你那份要作废"。CPU 越多，这种通知就越多，而且呈平方级增长。再加上总线本来就紧张，一致性流量很快把可用带宽吃光。

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:640px;display:block;margin:1.5em auto;font-family:sans-serif">
  <defs>
    <marker id="arrowB" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
      <polygon points="0,0 7,3.5 0,7" fill="#c0392b"/>
    </marker>
  </defs>
  <!-- 背景 -->
  <rect width="640" height="300" fill="#fdfefe" rx="10" stroke="#e0e0e0" stroke-width="1"/>
  <!-- 标题 -->
  <text x="320" y="24" text-anchor="middle" font-size="13" fill="#555">一致性通知数量 = N×(N-1)/2，随 CPU 数量平方级增长</text>
  <!-- ===== 左面板：4颗CPU ===== -->
  <text x="150" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a252f">4 颗 CPU</text>
  <!-- 6条一致性链路（虚线） -->
  <line x1="90" y1="110" x2="210" y2="110" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <line x1="90" y1="110" x2="90" y2="210" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <line x1="90" y1="110" x2="210" y2="210" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <line x1="210" y1="110" x2="90" y2="210" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <line x1="210" y1="110" x2="210" y2="210" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <line x1="90" y1="210" x2="210" y2="210" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="5,3"/>
  <!-- 4颗CPU方块 -->
  <rect x="60" y="88" width="60" height="44" rx="6" fill="#2980b9"/>
  <text x="90" y="115" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU 0</text>
  <rect x="180" y="88" width="60" height="44" rx="6" fill="#2980b9"/>
  <text x="210" y="115" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU 1</text>
  <rect x="60" y="188" width="60" height="44" rx="6" fill="#2980b9"/>
  <text x="90" y="215" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU 2</text>
  <rect x="180" y="188" width="60" height="44" rx="6" fill="#2980b9"/>
  <text x="210" y="215" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU 3</text>
  <text x="150" y="260" text-anchor="middle" font-size="15" fill="#c0392b" font-weight="bold">6 条一致性链路</text>
  <text x="150" y="280" text-anchor="middle" font-size="11" fill="#888">总线压力：尚可接受</text>
  <!-- 分隔线 + 箭头 -->
  <line x1="318" y1="30" x2="318" y2="290" stroke="#ddd" stroke-width="1.5"/>
  <text x="318" y="162" text-anchor="middle" font-size="28" fill="#bbb" font-weight="bold">→</text>
  <!-- ===== 右面板：8颗CPU（圆形排列） ===== -->
  <text x="480" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a252f">8 颗 CPU</text>
  <!-- 8颗CPU圆形排布，圆心(480,160)，半径78 -->
  <!-- 位置：
    CPU0: (558,160)  CPU1: (535,105)  CPU2: (480,82)   CPU3: (425,105)
    CPU4: (402,160)  CPU5: (425,215)  CPU6: (480,238)  CPU7: (535,215) -->
  <!-- 28条一致性链路（细线，半透明） -->
  <g stroke="#e74c3c" stroke-width="1" opacity="0.45" stroke-dasharray="4,2">
    <line x1="558" y1="160" x2="535" y2="105"/><line x1="558" y1="160" x2="480" y2="82"/>
    <line x1="558" y1="160" x2="425" y2="105"/><line x1="558" y1="160" x2="402" y2="160"/>
    <line x1="558" y1="160" x2="425" y2="215"/><line x1="558" y1="160" x2="480" y2="238"/>
    <line x1="558" y1="160" x2="535" y2="215"/>
    <line x1="535" y1="105" x2="480" y2="82"/><line x1="535" y1="105" x2="425" y2="105"/>
    <line x1="535" y1="105" x2="402" y2="160"/><line x1="535" y1="105" x2="425" y2="215"/>
    <line x1="535" y1="105" x2="480" y2="238"/><line x1="535" y1="105" x2="535" y2="215"/>
    <line x1="480" y1="82"  x2="425" y2="105"/><line x1="480" y1="82"  x2="402" y2="160"/>
    <line x1="480" y1="82"  x2="425" y2="215"/><line x1="480" y1="82"  x2="480" y2="238"/>
    <line x1="480" y1="82"  x2="535" y2="215"/>
    <line x1="425" y1="105" x2="402" y2="160"/><line x1="425" y1="105" x2="425" y2="215"/>
    <line x1="425" y1="105" x2="480" y2="238"/><line x1="425" y1="105" x2="535" y2="215"/>
    <line x1="402" y1="160" x2="425" y2="215"/><line x1="402" y1="160" x2="480" y2="238"/>
    <line x1="402" y1="160" x2="535" y2="215"/>
    <line x1="425" y1="215" x2="480" y2="238"/><line x1="425" y1="215" x2="535" y2="215"/>
    <line x1="480" y1="238" x2="535" y2="215"/>
  </g>
  <!-- 8颗CPU圆形节点 -->
  <circle cx="558" cy="160" r="20" fill="#2980b9"/><text x="558" y="165" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU0</text>
  <circle cx="535" cy="105" r="20" fill="#2980b9"/><text x="535" y="110" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU1</text>
  <circle cx="480" cy="82"  r="20" fill="#2980b9"/><text x="480" y="87"  text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU2</text>
  <circle cx="425" cy="105" r="20" fill="#2980b9"/><text x="425" y="110" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU3</text>
  <circle cx="402" cy="160" r="20" fill="#2980b9"/><text x="402" y="165" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU4</text>
  <circle cx="425" cy="215" r="20" fill="#2980b9"/><text x="425" y="220" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU5</text>
  <circle cx="480" cy="238" r="20" fill="#2980b9"/><text x="480" y="243" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU6</text>
  <circle cx="535" cy="215" r="20" fill="#2980b9"/><text x="535" y="220" text-anchor="middle" font-size="10" fill="white" font-weight="bold">CPU7</text>
  <text x="480" y="270" text-anchor="middle" font-size="15" fill="#c0392b" font-weight="bold">28 条一致性链路</text>
  <text x="480" y="288" text-anchor="middle" font-size="11" fill="#888">总线被打满，CPU 在排队</text>
</svg>

**第三，频繁的缓存失效。** 一致性通知发出去之后，接收方本地缓存里那份数据就被标记为"无效"。下次这颗 CPU 再读同一个变量，缓存里找不到（cache miss），只能重新去主内存取——这来回一趟叫做"缓存行乒乓"。乒乓每发生一次，就是一次额外的内存访问延迟；如果多颗 CPU 交替写同一块数据，乒乓会持续不断，缓存形同虚设。

<svg viewBox="0 0 660 390" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:660px;display:block;margin:1.5em auto;font-family:sans-serif">
  <defs>
    <marker id="arrR" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><polygon points="0,0 7,3.5 0,7" fill="#2980b9"/></marker>
    <marker id="arrL" markerWidth="7" markerHeight="7" refX="1" refY="3.5" orient="auto"><polygon points="7,0 0,3.5 7,7" fill="#2980b9"/></marker>
    <marker id="arrD" markerWidth="7" markerHeight="7" refX="3.5" refY="6" orient="auto"><polygon points="0,0 7,0 3.5,7" fill="#888"/></marker>
    <marker id="arrDr" markerWidth="7" markerHeight="7" refX="3.5" refY="6" orient="auto"><polygon points="0,0 7,0 3.5,7" fill="#c0392b"/></marker>
  </defs>
  <!-- 背景 -->
  <rect width="660" height="390" fill="#fdfefe" rx="10" stroke="#e0e0e0" stroke-width="1"/>
  <text x="330" y="24" text-anchor="middle" font-size="13" fill="#555">同一缓存行在两颗 CPU 之间反复失效与重载（"缓存行乒乓"）</text>
  <!-- ===== 时刻 1：双方都有有效缓存行 ===== -->
  <text x="20" y="58" font-size="11" fill="#888">时刻①</text>
  <!-- CPU A -->
  <rect x="40" y="65" width="110" height="44" rx="6" fill="#2980b9"/>
  <text x="95" y="84" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU A</text>
  <text x="95" y="100" text-anchor="middle" font-size="10" fill="#aed6f1">缓存：✓ 有效</text>
  <!-- CPU B -->
  <rect x="510" y="65" width="110" height="44" rx="6" fill="#2980b9"/>
  <text x="565" y="84" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU B</text>
  <text x="565" y="100" text-anchor="middle" font-size="10" fill="#aed6f1">缓存：✓ 有效</text>
  <!-- ===== 时刻 2：CPU A 写入，发出失效通知 ===== -->
  <text x="20" y="148" font-size="11" fill="#888">时刻②</text>
  <!-- CPU A 写入 -->
  <rect x="40" y="155" width="110" height="44" rx="6" fill="#1a5276"/>
  <text x="95" y="174" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU A 写入</text>
  <text x="95" y="190" text-anchor="middle" font-size="10" fill="#aed6f1">缓存：已修改</text>
  <!-- 失效通知箭头 -->
  <line x1="155" y1="177" x2="505" y2="177" stroke="#c0392b" stroke-width="1.8" stroke-dasharray="6,3" marker-end="url(#arrR)"/>
  <text x="330" y="170" text-anchor="middle" font-size="11" fill="#c0392b" font-weight="bold">发出失效通知（Invalidate）</text>
  <!-- CPU B 失效 -->
  <rect x="510" y="155" width="110" height="44" rx="6" fill="#922b21"/>
  <text x="565" y="174" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU B</text>
  <text x="565" y="190" text-anchor="middle" font-size="10" fill="#f1948a">缓存：✗ 已失效</text>
  <!-- ===== 时刻 3：CPU B 读取，发生 cache miss ===== -->
  <text x="20" y="238" font-size="11" fill="#888">时刻③</text>
  <!-- CPU A 不变 -->
  <rect x="40" y="245" width="110" height="44" rx="6" fill="#1a5276"/>
  <text x="95" y="264" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU A</text>
  <text x="95" y="280" text-anchor="middle" font-size="10" fill="#aed6f1">缓存：有效</text>
  <!-- CPU B 读取 miss -->
  <rect x="510" y="245" width="110" height="44" rx="6" fill="#784212"/>
  <text x="565" y="264" text-anchor="middle" font-size="12" fill="white" font-weight="bold">CPU B 读取</text>
  <text x="565" y="280" text-anchor="middle" font-size="10" fill="#f0b27a">Cache Miss！</text>
  <!-- 向下取内存的箭头（CPU B → 内存） -->
  <line x1="565" y1="289" x2="565" y2="318" stroke="#c0392b" stroke-width="1.8" marker-end="url(#arrDr)"/>
  <!-- 内存 -->
  <rect x="440" y="318" width="230" height="40" rx="6" fill="#1e8449"/>
  <text x="555" y="340" text-anchor="middle" font-size="12" fill="white" font-weight="bold">主内存（~100 ns 往返）</text>
  <!-- 慢！标注 -->
  <text x="595" y="308" font-size="12" fill="#c0392b" font-weight="bold">慢！</text>
  <!-- ===== 循环箭头（右边绕回顶部） ===== -->
  <path d="M 625 340 Q 648 340 648 200 Q 648 65 620 87" fill="none" stroke="#bbb" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arrL)"/>
  <text x="651" y="205" font-size="10" fill="#aaa" transform="rotate(90,651,205)">反复乒乓…</text>
  <!-- 左侧说明 -->
  <line x1="95" y1="109" x2="95" y2="152" stroke="#555" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arrD)"/>
  <line x1="565" y1="109" x2="565" y2="152" stroke="#555" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arrD)"/>
  <line x1="95" y1="199" x2="95" y2="242" stroke="#555" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arrD)"/>
  <line x1="565" y1="199" x2="565" y2="242" stroke="#555" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arrD)"/>
  <text x="330" y="376" text-anchor="middle" font-size="11" fill="#888">每次乒乓 = 一次 cache miss + 一次内存往返，性能瞬间跌入"慢路径"</text>
</svg>

**第四，物理距离限制速度。** 电信号在主板上一个时钟周期只能跑几厘米。CPU 离内存越远，信号往返一次的时间越长。如果想让所有 CPU 访问任意内存都"一样快"，就只能按"最远那段距离"来设计——这是劣化，不是优化。

四件事叠起来的结果：8 颗 CPU 之后，UMA 加得越多，性能反而越差。多加的 CPU 都在排队，不是在干活。需要一种新方案。

## 四、NUMA：每颗 CPU 配一块自己的内存

**NUMA**（Non-Uniform Memory Access，非统一内存访问）的思路同样朴素：

> 既然让所有 CPU 都"等距离"访问所有内存做不到，那就**让每颗 CPU 专门负责一块离它最近的内存**。

具体做法是把"一颗 CPU + 一块内存"打包成一个单元，叫 **NUMA Node**。每颗 CPU 优先访问自己那块"本地内存"；要访问别人的内存，走一条专用的高速通道（Intel 叫 UPI，AMD 叫 Infinity Fabric）。

<svg viewBox="0 0 780 430" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:780px;display:block;margin:1.5em auto;font-family:sans-serif">
  <defs>
    <marker id="dn" markerWidth="7" markerHeight="7" refX="3.5" refY="6" orient="auto"><polygon points="0,0 7,0 3.5,7" fill="#555"/></marker>
    <marker id="cr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><polygon points="0,0 7,3.5 0,7" fill="#c0392b"/></marker>
    <marker id="cl" markerWidth="7" markerHeight="7" refX="1" refY="3.5" orient="auto"><polygon points="7,0 0,3.5 7,7" fill="#c0392b"/></marker>
  </defs>
  <!-- ===== NUMA Node 0 ===== -->
  <rect x="5" y="20" width="345" height="380" rx="10" fill="#eaf4fb" stroke="#2980b9" stroke-width="2"/>
  <text x="177" y="46" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a5276">NUMA Node 0</text>
  <!-- 4 CPU Cores -->
  <rect x="18"  y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="53"  y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 0</text>
  <text x="53"  y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="53"  y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="100" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="135" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 1</text>
  <text x="135" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="135" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="182" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="217" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 2</text>
  <text x="217" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="217" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="264" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="299" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 3</text>
  <text x="299" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="299" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <line x1="53"  y1="120" x2="53"  y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="135" y1="120" x2="135" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="217" y1="120" x2="217" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="299" y1="120" x2="299" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <!-- L3 Cache -->
  <rect x="18" y="143" width="316" height="40" rx="6" fill="#1a5276"/>
  <text x="176" y="168" text-anchor="middle" font-size="12" fill="white" font-weight="bold">L3 Cache（Node 内共享）</text>
  <line x1="176" y1="183" x2="176" y2="205" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <!-- IMC -->
  <rect x="18" y="205" width="316" height="40" rx="6" fill="#117a65"/>
  <text x="176" y="230" text-anchor="middle" font-size="12" fill="white" font-weight="bold">内存控制器（IMC）</text>
  <line x1="176" y1="245" x2="176" y2="267" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <!-- DDR -->
  <rect x="18" y="267" width="316" height="60" rx="6" fill="#1e8449"/>
  <text x="176" y="292" text-anchor="middle" font-size="12" fill="white" font-weight="bold">本地内存（DDR）</text>
  <text x="176" y="313" text-anchor="middle" font-size="10" fill="#a9dfbf">延迟 ~80 ns　｜　带宽 100%</text>
  <text x="176" y="355" text-anchor="middle" font-size="12" fill="#1e8449" font-weight="bold">✓ 本地访问（快）</text>
  <text x="176" y="374" text-anchor="middle" font-size="10" fill="#555">进程绑定在同一 Node 内时走此路径</text>
  <!-- ===== NUMA Node 1 ===== -->
  <rect x="430" y="20" width="345" height="380" rx="10" fill="#eaf4fb" stroke="#2980b9" stroke-width="2"/>
  <text x="602" y="46" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a5276">NUMA Node 1</text>
  <rect x="443" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="478" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 0</text>
  <text x="478" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="478" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="525" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="560" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 1</text>
  <text x="560" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="560" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="607" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="642" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 2</text>
  <text x="642" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="642" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <rect x="689" y="58" width="70" height="62" rx="6" fill="#2980b9"/>
  <text x="724" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Core 3</text>
  <text x="724" y="96" text-anchor="middle" font-size="9"  fill="#aed6f1">L1 Cache</text>
  <text x="724" y="110" text-anchor="middle" font-size="9" fill="#aed6f1">L2 Cache</text>
  <line x1="478" y1="120" x2="478" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="560" y1="120" x2="560" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="642" y1="120" x2="642" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <line x1="724" y1="120" x2="724" y2="143" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <rect x="443" y="143" width="316" height="40" rx="6" fill="#1a5276"/>
  <text x="601" y="168" text-anchor="middle" font-size="12" fill="white" font-weight="bold">L3 Cache（Node 内共享）</text>
  <line x1="601" y1="183" x2="601" y2="205" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <rect x="443" y="205" width="316" height="40" rx="6" fill="#117a65"/>
  <text x="601" y="230" text-anchor="middle" font-size="12" fill="white" font-weight="bold">内存控制器（IMC）</text>
  <line x1="601" y1="245" x2="601" y2="267" stroke="#555" stroke-width="1.5" marker-end="url(#dn)"/>
  <rect x="443" y="267" width="316" height="60" rx="6" fill="#1e8449"/>
  <text x="601" y="292" text-anchor="middle" font-size="12" fill="white" font-weight="bold">本地内存（DDR）</text>
  <text x="601" y="313" text-anchor="middle" font-size="10" fill="#a9dfbf">延迟 ~80 ns　｜　带宽 100%</text>
  <text x="601" y="355" text-anchor="middle" font-size="12" fill="#1e8449" font-weight="bold">✓ 本地访问（快）</text>
  <text x="601" y="374" text-anchor="middle" font-size="10" fill="#555">进程绑定在同一 Node 内时走此路径</text>
  <!-- ===== 跨节点互联 ===== -->
  <line x1="334" y1="225" x2="430" y2="225" stroke="#c0392b" stroke-width="3" marker-end="url(#cr)" marker-start="url(#cl)"/>
  <rect x="334" y="245" width="96" height="68" rx="6" fill="#fadbd8" stroke="#e74c3c" stroke-width="1"/>
  <text x="382" y="264" text-anchor="middle" font-size="11" fill="#922b21" font-weight="bold">UPI /</text>
  <text x="382" y="279" text-anchor="middle" font-size="11" fill="#922b21" font-weight="bold">Infinity Fabric</text>
  <text x="382" y="297" text-anchor="middle" font-size="10" fill="#c0392b">延迟 ~140 ns</text>
  <text x="382" y="311" text-anchor="middle" font-size="10" fill="#c0392b">带宽 ~50%</text>
  <text x="382" y="335" text-anchor="middle" font-size="11" fill="#c0392b" font-weight="bold">✗ 跨节点访问（慢）</text>
</svg>

Node 内部：CPU 访问自己的内存很快，跟 UMA 时代一样。
Node 之间：也能互相访问内存，但要走互联通道，**会慢一些**——这就是名字里"Non-Uniform"的来源。

---

> **一个容易被忽视的顺序：NUMA 首先是一场硬件层面的重构。**
>
> 把内存控制器从主板芯片组搬进 CPU 内部、用高速点对点互联（UPI / HyperTransport / Infinity Fabric）替换共享总线——这些都是芯片设计和主板工程上的实质性改变，发生在 2003–2008 年间。硬件结构一旦确定，"内存不再均匀"就成了一个客观事实，无论软件层面承不承认。
>
> 操作系统和软件的适配是第二步，是对这个硬件事实的响应：内核需要感知 Node 拓扑、把进程和内存分配在同一个 Node 内（NUMA-aware 调度）；数据库、运行时、中间件需要主动做内存亲和性管理。这些都是在既定硬件约束下"尽量减少跨节点访问"的策略，而不是改变硬件本身。
>
> 理解这个顺序很重要：软件调优（`numactl`、`mbind`、NUMA-aware 分配器）能把跨节点访问的代价降到最低，但永远无法消除——因为那 ~60 ns 的额外延迟刻在了物理距离和信号传播速度里。

商用 x86 服务器从 2003 年开始走上 NUMA 这条路。AMD 在 Opteron 上把内存控制器搬进 CPU、用 HyperTransport 连接多颗 CPU；Intel 在 2008 年的 Nehalem 上跟进。从那之后，**所有多路 x86 服务器默认都是 NUMA**。这不是某个厂商的设计偏好，而是物理约束推出来的必然方向。

## 五、NUMA 解决了什么，又带来了什么？

**解决了：扩展性。** 多个内存控制器并行工作，每颗 CPU 独享自己的内存带宽，整机的总带宽随 CPU 数量线性增长。CPU 之间也不再共用一条总线，仲裁开销和一致性广播都被局限在每个 Node 内部。今天动辄一百多核的服务器，靠的就是 NUMA。

**带来的代价：访问"自己的"内存快，访问"别人的"内存慢。** 用一台典型双路服务器的数字感受一下：

| 访问类型 | 延迟 | 带宽 |
| --- | --- | --- |
| 本地内存 | ~80 ns | 100% |
| 跨节点内存 | ~140 ns（慢 70%–80%） | ~50% |

差不多多一半的延迟，少一半的带宽。在一个内存敏感的服务里，这点差距会被放大成肉眼可见的性能问题。

## 六、回到开头那个 30%

现在可以回答开头那个问题了。

不绑核的时候，操作系统会出于负载均衡的考虑，把进程在不同 CPU 之间挪来挪去。挪到另一颗 CPU 上之后，原来在 Node 0 分配的内存就成了"远端"，每次访问都要走互联通道，延迟变长、带宽变小。再加上多线程之间跨 Node 的缓存同步开销——所谓"内存不是均匀的"代价，全部体现在那 30% 里。

绑核以后，进程稳稳地待在一个 Node 内：内存在本地、缓存是热的、线程之间的通信也不跨 Node。性能自然就回来了。

所以 NUMA 时代写代码、调服务的核心原则其实就一句话：

> **让数据和处理数据的 CPU，待在同一个 Node 里。**

如果想在自己的机器上看一眼 NUMA 长什么样，下面两条命令就够：

```bash
# 看机器有几个 NUMA Node、每个 Node 多少 CPU 和内存
numactl --hardware

# 把进程的 CPU 和内存都绑到 Node 0
numactl --cpunodebind=0 --membind=0 ./your-app
```

## 七、一句话总结

UMA 是"所有 CPU 共享一块内存"的早期方案，简单但扛不住 CPU 核数膨胀；NUMA 是"每颗 CPU 配一块自己的内存"的现代方案，解决了 UMA 的扩展性问题，代价是访问"别人的"内存会慢一些。

理解了这一点，再去看 `numactl`、看服务器性能调优，就不再神秘了——大部分技巧都只是在帮你做同一件事：**让数据和 CPU 在同一个 Node 里。**
