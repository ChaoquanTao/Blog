
# NUMA & SKU 配置调优实验记录

  

## 问题描述

先 apply test1 (CPU任务, 90c/300Gi) 再 apply test2 (GPU任务, 200c/1600Gi/8DCU) 时，test2 无法获得均匀的 NUMA 资源分配。

  

## 机器信息

- 节点: 10.1.6.32

- CPU: 384 (2 socket x 96 core x 2 thread)

- Memory: ~2.2TiB

- NUMA0 CPUs: 0-95, 192-287

- NUMA1 CPUs: 96-191, 288-383

- 每个NUMA可分配CPU: 95 (96-1 reserved)

  

## 初始配置 (baseline)

```yaml

cpuManagerPolicy: static

cpuManagerPolicyOptions:

distribute-cpus-across-numa: "true"

reservedSystemCPUs: "0,192,96,288"

memoryManagerPolicy: Static

reservedMemory:

- numaNode: 0

limits:

memory: "26704Mi"

- numaNode: 1

limits:

memory: "26705Mi"

topologyManagerPolicy: restricted

```

**结果**: test2 遇到 UnexpectedAdmissionError，被 restricted topology manager 拒绝。原因：test1(Guaranteed 90c)被static CPU manager分配CPU后，test2(200c)无法满足NUMA拓扑约束。

  

---

  

## 实验记录

  

### 实验1: test1 Burstable + memoryManagerPolicy Static + restricted

**修改**: test1.yaml requests改为 cpu:"1", memory:"1Gi" (Burstable QoS)

**kubelet**: 保持原始配置 (Static memory + restricted topology)

**结果**:

- test2 Running ✅

- NUMA分布: **NUMA0: 1048.2 GiB, NUMA1: 451.8 GiB, Ratio: 0.43** ❌

- 分析：test2成功调度但内存分配严重不均。Linux first-touch策略导致单线程Python进程的内存集中在一个NUMA节点上。

  

---

  

### 实验2: test1 Burstable + memoryManagerPolicy None + best-effort

**修改**:

- test1.yaml: Burstable (同实验1)

- kubelet: `memoryManagerPolicy: None`, `topologyManagerPolicy: best-effort`

**结果**:

- test2 Running ✅

- NUMA分布: **NUMA0: 415.2 GiB, NUMA1: 1084.8 GiB, Ratio: 2.61** ❌

- 分析：去掉memory manager后，内存分配完全由kernel控制，first-touch问题依然存在，只是倾斜方向变了。

  

---

  

### 实验3: test1 Burstable + MPOL_INTERLEAVE syscall in test2 ⭐

**修改**:

- test1.yaml: Burstable (同实验1)

- test2.yaml: command中添加 `set_mempolicy(MPOL_INTERLEAVE)` syscall (syscall 238, mode=3)

- kubelet: `memoryManagerPolicy: None`, `topologyManagerPolicy: best-effort`

**结果**:

- test2 Running ✅

- NUMA分布: **NUMA0: 750.0 GiB, NUMA1: 750.0 GiB, Ratio: 1.0000** ✅✅✅

- 分析：`MPOL_INTERLEAVE` 强制内核交替在两个NUMA节点上分配内存页，完美实现了均匀分配。

  

**关键代码片段**:

```python

import ctypes

libc = ctypes.CDLL("libc.so.6", use_errno=True)

MPOL_INTERLEAVE = 3 # 注意不是5！

nodemask = (ctypes.c_ulong * 1)(0x3) # NUMA nodes 0 and 1

ret = libc.syscall(ctypes.c_long(238), ctypes.c_int(MPOL_INTERLEAVE),

ctypes.cast(nodemask, ctypes.c_void_p),

ctypes.c_ulong(3))

```

  

---

  

### 实验4: test1 Guaranteed + MPOL_INTERLEAVE in test2 + kubelet best-effort ⭐⭐

**修改**:

- test1.yaml: **保持原始 Guaranteed QoS** (requests == limits, 90c/300Gi)

- test2.yaml: command中添加 `set_mempolicy(MPOL_INTERLEAVE)` syscall

- kubelet: `memoryManagerPolicy: None`, `topologyManagerPolicy: best-effort`

  

**注意**: 原始 `restricted` + `Static` kubelet 配置下 test2 仍会 `UnexpectedAdmissionError`，必须改为 `best-effort` + `None`。

  

**结果**:

- test1 Running ✅ (Guaranteed)

- test2 Running ✅

- NUMA分布: **NUMA0: 750.0 GiB, NUMA1: 750.0 GiB, Ratio: 1.0000** ✅✅✅

- 分析：即使test1占用Guaranteed资源，在best-effort topology下不会阻止test2调度。MPOL_INTERLEAVE保证了内存均匀分配。

  

---

  

### 实验5a: 先test2再test1，原始配置 (restricted+Static)，无MPOL

**顺序**: test2 → test1（反向apply）

**修改**: 无（原始配置）

**结果**:

- test2 Running ✅

- test1 **TopologyAffinityError** ❌

- 分析：restricted topology 下 test2 (200c) 先锁定大部分NUMA资源，test1 (90c) 无法满足拓扑约束。

  

---

  

### 实验5b: 先test2再test1，Guaranteed + MPOL_INTERLEAVE + best-effort ⭐⭐

**顺序**: test2 → test1（反向apply）

**修改**:

- test2.yaml: 添加 `set_mempolicy(MPOL_INTERLEAVE)` syscall，保持 Guaranteed

- test1.yaml: 保持原始 Guaranteed

- kubelet: `memoryManagerPolicy: None`, `topologyManagerPolicy: best-effort`

**结果**:

- test2 Running ✅

- test1 Running ✅

- NUMA分布: **NUMA0: 750.0 GiB, NUMA1: 750.0 GiB, Ratio: 1.0000** ✅✅✅

- 分析：无论 apply 顺序如何（先test1再test2 或 先test2再test1），best-effort + MPOL_INTERLEAVE 方案都能保证 test2 内存均匀分配。

  

---

  

### 实验6a: t2→t1, test1增大到600Gi, 无MPOL

**顺序**: test2 → test1

**修改**: test1 内存增大到 600Gi (Guaranteed), test2 使用 MPOL_INTERLEAVE

**kubelet**: best-effort + None

  

**第1次结果**:

- test2 Running ✅

- test1 **OutOfmemory** ❌

- 分析：test2 MPOL_INTERLEAVE每NUMA占800GiB，单NUMA剩余~333GiB，test1 first-touch 600GiB集中一个NUMA导致OOM。

  

**第2次结果 (复现验证)**:

- test2 Running ✅

- test1 Running ✅ (未OOM)

- NUMA分布: **NUMA0: 549.8 GiB, NUMA1: 950.2 GiB, Ratio: 1.73** ❌

- 分析：OOM为**偶现**，取决于test1 first-touch时pages落在哪个NUMA。如果大量落在已被test2占满的NUMA则OOM，否则能运行但NUMA严重倾斜。

  

---

  

### 实验6b: t1→t2, test1增大到600Gi, 无MPOL

**顺序**: test1 → test2

**修改**: test1 内存增大到 600Gi (Guaranteed, 无MPOL), test2 使用 MPOL_INTERLEAVE

**kubelet**: best-effort + None

**结果**:

- test1 Running ✅

- test2 Running ✅

- NUMA分布: **NUMA0: 549.1 GiB, NUMA1: 951.0 GiB, Ratio: 1.73** ❌

- 分析：test1 first-touch倾斜占用一个NUMA，导致test2的interleave在该NUMA上分配不到足够页面。

  

---

  

### 实验6c: t2→t1, test1增大到600Gi, 两者都MPOL ⭐⭐⭐

**顺序**: test2 → test1

**修改**: test1 600Gi + MPOL_INTERLEAVE, test2 MPOL_INTERLEAVE

**kubelet**: best-effort + None

**结果**:

- test2 Running ✅

- test1 Running ✅

- NUMA分布: **NUMA0: 750.0 GiB, NUMA1: 750.0 GiB, Ratio: 1.0000** ✅✅✅

- 分析：两者都用MPOL_INTERLEAVE时，内存均匀分配到两个NUMA，不会出现单NUMA OOM。

  

---

  

### 实验6d: t1→t2, test1增大到600Gi, 两者都MPOL ⭐⭐⭐

**顺序**: test1 → test2

**修改**: test1 600Gi + MPOL_INTERLEAVE, test2 MPOL_INTERLEAVE

**kubelet**: best-effort + None

**结果**:

- test1 Running ✅

- test2 Running ✅

- NUMA分布: **NUMA0: 750.0 GiB, NUMA1: 750.0 GiB, Ratio: 1.0000** ✅✅✅

- 分析：与6c一致，apply顺序不影响结果。

  

---

  

### 实验7a: t2→t1, test1=300Gi, 两者都无MPOL, best-effort+None

**顺序**: test2 → test1

**修改**: 无MPOL，原始yaml

**kubelet**: best-effort + None

**结果**:

- test2 Running ✅

- test1 Running ✅

- NUMA分布: **NUMA0: 706.2 GiB, NUMA1: 793.8 GiB, Ratio: 1.12** ❌

- 分析：无MPOL时first-touch导致轻微NUMA倾斜，但300Gi的test1影响较小。

  

---

  

### 实验7b: t2→t1, test1=600Gi, 两者都无MPOL, best-effort+None

**顺序**: test2 → test1

**修改**: test1增大到600Gi，无MPOL

**kubelet**: best-effort + None

**结果**:

- test2 Running ✅

- test1 Running ✅

- NUMA分布: **NUMA0: 598.2 GiB, NUMA1: 901.8 GiB, Ratio: 1.51** ❌

- 分析：test1 600Gi first-touch更多占用一个NUMA，test2也first-touch，导致NUMA倾斜加剧。

  

---

  

## 实验汇总

  

| 实验 | 顺序 | test1 内存 | test1 MPOL | kubelet topology | kubelet memory | test2 MPOL | 两者调度 | NUMA Ratio | 结果 |

|------|------|-----------|------------|-----------------|---------------|------------|----------|------------|------|

| baseline | t1→t2 | 300Gi | 无 | restricted | Static | 无 | ❌ | - | ❌ |

| 1 | t1→t2 | 300Gi | 无 | restricted | Static | 无 | ✅ | 0.43 | ❌ |

| 2 | t1→t2 | 300Gi | 无 | best-effort | None | 无 | ✅ | 2.61 | ❌ |

| 3 | t1→t2 | 300Gi | 无 | best-effort | None | INTERLEAVE | ✅ | 1.00 | ✅ |

| 4 | t1→t2 | 300Gi | 无 | best-effort | None | INTERLEAVE | ✅ | 1.00 | ✅ |

| 5a | t2→t1 | 300Gi | 无 | restricted | Static | 无 | ❌(t1) | - | ❌ |

| 5b | t2→t1 | 300Gi | 无 | best-effort | None | INTERLEAVE | ✅ | 1.00 | ✅ |

| 6a | t2→t1 | 600Gi | 无 | best-effort | None | INTERLEAVE | ❌或✅(偶现OOM) | 1.73 | ❌ |

| 6b | t1→t2 | 600Gi | 无 | best-effort | None | INTERLEAVE | ✅ | 1.73 | ❌ |

| **6c** | **t2→t1** | **600Gi** | **INTERLEAVE** | **best-effort** | **None** | **INTERLEAVE** | **✅** | **1.00** | **✅** |

| **6d** | **t1→t2** | **600Gi** | **INTERLEAVE** | **best-effort** | **None** | **INTERLEAVE** | **✅** | **1.00** | **✅** |

| 7a | t2→t1 | 300Gi | 无 | best-effort | None | 无 | ✅ | 1.12 | ❌ |

| 7b | t2→t1 | 600Gi | 无 | best-effort | None | 无 | ✅ | 1.51 | ❌ |

  

---

  

## 最终方案

  

### 方案概要

1. **所有任务**: 在启动命令中调用 `set_mempolicy(MPOL_INTERLEAVE)` 或使用 `numactl --interleave=all`，强制内存均匀分配（GPU任务和CPU任务都需要）

2. **kubelet配置**: 改为 `memoryManagerPolicy: None` + `topologyManagerPolicy: best-effort`

3. **test1 (CPU任务)**: 可增大到 600Gi，但**必须**也使用 MPOL_INTERLEAVE（否则 OOM 或 test2 NUMA 倾斜）

  

### 配置文件

  

#### kubelet-config.yaml

```yaml

apiVersion: kubelet.config.k8s.io/v1beta1

kind: KubeletConfiguration

cpuManagerPolicy: static

cpuManagerPolicyOptions:

distribute-cpus-across-numa: "true"

reservedSystemCPUs: "0,192,96,288"

memoryManagerPolicy: None

topologyManagerPolicy: best-effort

```

  

#### test1.yaml (CPU任务模板)

- `resources`: cpu: "90", memory: "600Gi" (Guaranteed)

- 启动命令添加 `set_mempolicy(MPOL_INTERLEAVE)` 或 `numactl --interleave=all`

  

#### test2.yaml (GPU任务模板)

- `resources`: cpu: "200", memory: "1600Gi" (Guaranteed)

- 启动命令添加 `set_mempolicy(MPOL_INTERLEAVE)` 或 `numactl --interleave=all`

  

### 关键代码片段

```python

import ctypes

libc = ctypes.CDLL("libc.so.6", use_errno=True)

MPOL_INTERLEAVE = 3

nodemask = (ctypes.c_ulong * 1)(0x3) # NUMA nodes 0 and 1

ret = libc.syscall(ctypes.c_long(238), ctypes.c_int(MPOL_INTERLEAVE),

ctypes.cast(nodemask, ctypes.c_void_p),

ctypes.c_ulong(3))

```

  

### 核心原理

1. CPU均匀分配由 `distribute-cpus-across-numa: "true"` 保证

2. 内存均匀分配由 `MPOL_INTERLEAVE` 内存策略保证（kernel级别，强制交替分配到两个NUMA）

3. `best-effort` topology避免了Guaranteed pods间的NUMA资源冲突导致AdmissionError

4. **重要发现**: 当test1内存增大到600Gi时，test1也必须使用MPOL_INTERLEAVE，否则first-touch倾斜会导致test2 NUMA不均（6b）或test1 OOM（6a）