---
name: wechat-formatter
description: 将技术文章排版为微信公众号可直接使用的 HTML。当用户提到"公众号排版"、"微信文章"、"排版成公众号格式"、"生成适合微信的 HTML"、"公众号发布"，或者上传了 Markdown/文本文章并希望发布到微信时，必须使用本 skill。输出为全 inline style 的 HTML 文件，用户在 Chrome 中打开后 Ctrl+A → Ctrl+C → 粘贴进 mp.weixin.qq.com 编辑器即可使用，无需任何第三方工具。
---

# WeChat 公众号排版 Skill

## 核心工作流

```
收到文章
  ↓
① 技术内容 Review（如为技术文章）
  ↓
② 生成微信兼容 HTML
  ↓
③ 输出文件 + 告知粘贴方式
```

**使用方式**：用户用 Chrome 打开生成的 HTML 文件 → Ctrl+A → Ctrl+C → 粘贴进 `mp.weixin.qq.com` 编辑器。浏览器复制的是渲染后的富文本，不是源码，微信编辑器会保留 inline style。

---

## 第一步：技术内容 Review（技术文章必做）

在排版前，先对文章做技术审查，输出一个 Markdown 表格，包含：

| 列 | 内容 |
|----|------|
| 位置 | 章节/段落 |
| 原文表述 | 原句摘要 |
| 问题 | 不准确/缺失/过度简化 |
| 建议修正 | 具体改法 |

常见检查点：
- 数字/公式是否有未说明的假设条件
- 算法名称的功能描述是否准确
- "等价"说法是否过度简化（如 ZeRO-3 ≈ FSDP）
- 性能数字是否有适用范围限制
- 枚举列表是否有遗漏项
- 图表/流程图是否和正文一致

Review 完成后询问用户是否将修正应用到排版中，再进行第二步。

---

## 第二步：生成微信兼容 HTML

### 微信渲染环境的硬约束

**绝对禁止（会失效或被过滤）：**
- `display: flex` / `display: grid`
- CSS 自定义变量 `var(--xxx)`
- `::before` / `::after` 伪元素
- 外链字体（`@font-face`、Google Fonts）
- `<style>` 块 / 外链 CSS
- `position: absolute/fixed`

**必须使用：**
- 所有样式写成 `style=""` 行内属性
- 布局用 `<table>`（多列）或块级 `<div>`（单列）
- 字体用系统字体栈（见下方）
- 所有颜色用 hex 值，不用 `rgba()` 的 CSS 变量形式

### 字体栈

```
正文（宋体）：   font-family:'STSong','SimSun','Noto Serif SC',serif
界面/标签：      font-family:'PingFang SC','Microsoft YaHei',sans-serif
代码/等宽：      font-family:'Courier New',Courier,monospace
```

### 移动端优先原则

微信文章 90% 在手机上阅读，屏幕宽度约 320–430px。

**所有横向布局改为纵向：**

| 横向元素 | 改为 |
|---------|------|
| 多列对比卡片 | 纵向堆叠卡片 |
| 左右优缺点 | 上下两张卡 |
| 横向 Pipeline 步骤 | 纵向步骤 + 箭头，或 `inline-block`（自动换行） |
| 三列特性卡 | 纵向左边框卡片 |
| 多列表格 | 简化为 2 列，或改为卡片列表 |

**字号基准：**
- 正文：`font-size:16px`（移动）/ `17px`（桌面）
- 小标题：`19–20px`
- 标签/辅助文字：`11–13px`
- 行高：`line-height:1.9`

---

## 组件库

### 主题色定义

每篇文章选一套主题色（在文件顶部注释中声明），所有组件使用同一套：

```
深色主题（SLAM 文章示例）：
  navy:       #16213e
  teal:       #0d7377
  teal_light: #e8f5f5
  teal_mid:   #14a085
  accent:     #e85d04

暗紫主题（分布式训练示例）：
  navy:       #0f172a
  indigo:     #6366f1
  indigo_light: #eef2ff
  purple:     #8b5cf6
  rose:       #f43f5e
```

---

### A. Hero 区块

```html
<div style="background:#0f172a;padding:52px 28px 44px;text-align:center;">
  <!-- 标签 -->
  <div style="display:inline-block;font-size:11px;letter-spacing:0.12em;
  color:#818cf8;background:rgba(99,102,241,0.15);
  border:1px solid rgba(99,102,241,0.35);padding:5px 16px;
  border-radius:20px;margin-bottom:22px;">标签文字</div>
  <div style="height:10px;"></div>
  <!-- 标题 -->
  <p style="font-family:'STSong','SimSun',serif;font-size:26px;font-weight:700;
  color:#ffffff;line-height:1.5;margin:0 0 14px;letter-spacing:0.04em;">
    主标题<span style="color:#818cf8;">强调词</span>
  </p>
  <!-- 副标题（移动端换行友好） -->
  <p style="font-size:13px;color:rgba(255,255,255,0.4);
  letter-spacing:0.06em;margin:0;line-height:1.7;">
    副标题第一行<br>副标题第二行
  </p>
  <div style="width:36px;height:2px;background:#6366f1;margin:22px auto 0;"></div>
</div>
```

---

### B. 章节标题

```html
<table width="100%" cellpadding="0" cellspacing="0" style="margin:36px 0 18px;">
  <tr>
    <td width="46" valign="top" style="padding-top:2px;">
      <span style="display:inline-block;font-size:11px;font-weight:500;
      color:#6366f1;background:#eef2ff;
      border:1px solid rgba(99,102,241,0.25);padding:4px 9px;
      border-radius:4px;letter-spacing:0.06em;white-space:nowrap;">01</span>
    </td>
    <td valign="top">
      <p style="font-family:'STSong','SimSun',serif;font-size:19px;
      font-weight:700;color:#0f172a;line-height:1.45;margin:0;
      padding-bottom:8px;border-bottom:2px solid #6366f1;">章节标题</p>
    </td>
  </tr>
</table>
```

---

### C. 正文段落

```html
<!-- 普通段落 -->
<p style="font-family:'STSong','SimSun',serif;font-size:16px;color:#334155;
line-height:1.9;margin:0 0 14px;text-align:justify;">正文内容</p>

<!-- 引言段落（左侧竖线） -->
<p style="font-family:'STSong','SimSun',serif;font-size:16px;color:#1a1a2e;
border-left:3px solid #6366f1;padding-left:16px;margin:0 0 18px;line-height:1.9;">
引言内容
</p>
```

---

### D. Pull Quote（深色引用块）

```html
<div style="background:#0f172a;border-radius:8px;padding:26px 22px;margin:28px 0;">
  <p style="font-family:'STSong','SimSun',serif;font-size:32px;
  color:#6366f1;line-height:1;margin:0 0 6px;opacity:0.7;">"</p>
  <p style="font-family:'STSong','SimSun',serif;font-size:16px;
  color:#ffffff;line-height:1.9;margin:0;text-align:justify;">引用文字</p>
</div>
```

---

### E. Callout 标注框

```html
<!-- 蓝/绿色：核心判断、重要结论 -->
<div style="background:#eef2ff;border-left:4px solid #6366f1;
padding:16px 18px;margin:22px 0;border-radius:0 6px 6px 0;">
  <p style="font-size:11px;font-weight:bold;letter-spacing:0.1em;
  color:#6366f1;margin:0 0 8px;text-transform:uppercase;">核心判断</p>
  <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:14px;line-height:1.8;margin:0;color:#334155;text-align:justify;">
  正文内容
  </p>
</div>

<!-- 橙色：工程细节、注意事项 -->
<div style="background:#fff3ed;border-left:4px solid #e85d04;
padding:16px 18px;margin:22px 0;border-radius:0 6px 6px 0;">
  <p style="font-size:11px;font-weight:bold;letter-spacing:0.1em;
  color:#e85d04;margin:0 0 8px;text-transform:uppercase;">工程细节</p>
  <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:14px;line-height:1.8;margin:0;color:#334155;text-align:justify;">
  正文内容
  </p>
</div>
```

---

### F. Key Statement（高亮结论）

```html
<div style="background:#eef2ff;border:1px solid rgba(99,102,241,0.2);
border-radius:8px;padding:18px 22px;margin:24px 0;">
  <p style="font-family:'STSong','SimSun',serif;font-size:16px;
  font-weight:700;color:#4338ca;line-height:1.85;margin:0;text-align:justify;">
  一句话核心结论
  </p>
</div>
```

---

### G. Pipeline 流程条（移动端自动换行）

使用 `inline-block`，在窄屏上自动换行：

```html
<div style="background:#ffffff;border:1px solid #e2e8f0;
border-radius:8px;padding:16px 18px;margin:18px 0;">
  <p style="font-size:11px;color:#94a3b8;letter-spacing:0.1em;margin:0 0 10px;">
  // 流程标题</p>
  <p style="margin:0;line-height:2.4;">
    <span style="display:inline-block;padding:6px 12px;border-radius:5px;
    font-size:12px;font-weight:bold;background:#eef2ff;color:#6366f1;
    border:1px solid rgba(99,102,241,0.25);">步骤一</span>
    <span style="color:#94a3b8;font-size:14px;padding:0 4px;">→</span>
    <span style="display:inline-block;padding:6px 12px;border-radius:5px;
    font-size:12px;font-weight:bold;background:#fff7ed;color:#ea580c;
    border:1px solid rgba(249,115,22,0.25);">步骤二</span>
    <span style="color:#94a3b8;font-size:14px;padding:0 4px;">→</span>
    <span style="display:inline-block;padding:6px 12px;border-radius:5px;
    font-size:12px;font-weight:bold;background:#0f172a;color:#ffffff;">步骤三</span>
  </p>
</div>
```

---

### H. 纵向步骤流程（移动端推荐）

```html
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;">
  <div style="background:#eef2ff;border:1px solid rgba(99,102,241,0.25);
  border-radius:6px;padding:10px 14px;margin-bottom:6px;">
    <p style="font-size:13px;font-weight:700;color:#6366f1;margin:0 0 2px;">① 步骤一标题</p>
    <p style="font-size:12px;color:#64748b;margin:0;">步骤说明</p>
  </div>
  <p style="text-align:center;color:#94a3b8;font-size:14px;margin:3px 0;">↓</p>
  <div style="background:#f0fdf4;border:1px solid rgba(34,197,94,0.3);
  border-radius:6px;padding:10px 14px;margin-bottom:6px;">
    <p style="font-size:13px;font-weight:700;color:#16a34a;margin:0 0 2px;">② 步骤二标题</p>
    <p style="font-size:12px;color:#64748b;margin:0;">步骤说明</p>
  </div>
  <p style="text-align:center;color:#94a3b8;font-size:14px;margin:3px 0;">↓</p>
  <div style="background:#0f172a;border-radius:6px;padding:10px 14px;text-align:center;">
    <p style="font-size:13px;font-weight:700;color:#ffffff;margin:0;">最终结果</p>
  </div>
</div>
```

---

### I. 纵向卡片列表（替代多列对比）

```html
<!-- 替代左右两列、三列横排 -->
<div style="background:#ffffff;border:1px solid #e2e8f0;
border-left:4px solid #6366f1;border-radius:0 6px 6px 0;
padding:14px 16px;margin-bottom:8px;">
  <p style="font-size:14px;font-weight:700;color:#0f172a;margin:0 0 4px;">卡片标题</p>
  <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:13px;color:#64748b;margin:0;line-height:1.6;">卡片内容</p>
</div>
```

---

### J. 优缺点（纵向，移动端友好）

```html
<!-- 优点 -->
<div style="background:#f0fdf4;border:1px solid rgba(34,197,94,0.2);
border-radius:6px;padding:12px 16px;margin-bottom:8px;">
  <p style="font-size:12px;font-weight:700;color:#16a34a;margin:0 0 6px;">✓ 优点</p>
  <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:13px;color:#334155;margin:0;line-height:1.7;">内容</p>
</div>
<!-- 缺点 -->
<div style="background:#fff1f2;border:1px solid rgba(244,63,94,0.2);
border-radius:6px;padding:12px 16px;margin-bottom:20px;">
  <p style="font-size:12px;font-weight:700;color:#be123c;margin:0 0 6px;">✗ 代价</p>
  <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:13px;color:#334155;margin:0;line-height:1.7;">内容</p>
</div>
```

---

### K. 代码/算法名标签（行内）

```html
<span style="font-family:'Courier New',Courier,monospace;font-size:13px;
background:#f0f0f8;color:#0d7377;padding:2px 6px;border-radius:4px;
border:1px solid rgba(13,115,119,0.15);">FAST-LIO2</span>
```

---

### L. 数据表格（宽屏友好）

```html
<table width="100%" cellpadding="0" cellspacing="0"
style="margin:16px 0;border-collapse:collapse;
font-family:'PingFang SC','Microsoft YaHei',sans-serif;font-size:14px;">
  <tr>
    <td style="padding:10px 13px;background:#0f172a;
    color:rgba(255,255,255,0.8);font-weight:500;font-size:13px;">列1</td>
    <td style="padding:10px 13px;background:#0f172a;
    color:rgba(255,255,255,0.8);font-weight:500;font-size:13px;">列2</td>
  </tr>
  <tr>
    <td style="padding:10px 13px;border-bottom:1px solid #e2e8f0;
    background:#ffffff;color:#334155;">内容</td>
    <td style="padding:10px 13px;border-bottom:1px solid #e2e8f0;
    background:#ffffff;color:#64748b;">内容</td>
  </tr>
  <tr>
    <td style="padding:10px 13px;border-bottom:1px solid #e2e8f0;
    background:#f8f8fc;color:#334155;">内容</td>
    <td style="padding:10px 13px;border-bottom:1px solid #e2e8f0;
    background:#f8f8fc;color:#64748b;">内容</td>
  </tr>
</table>
```

> ⚠️ 表格列数建议不超过 3 列；列多时改用纵向卡片列表。

---

### M. 分割线

```html
<div style="text-align:center;margin:32px 0;">
  <span style="display:inline-block;width:28%;height:1px;
  background:#e2e8f0;vertical-align:middle;"></span>
  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#6366f1;vertical-align:middle;margin:0 10px;"></span>
  <span style="display:inline-block;width:28%;height:1px;
  background:#e2e8f0;vertical-align:middle;"></span>
</div>
```

---

### N. 编号原则卡片

```html
<div style="background:#ffffff;border:1px solid #e2e8f0;
border-radius:6px;padding:14px 16px;margin-bottom:8px;">
  <table cellpadding="0" cellspacing="0"><tr valign="top">
    <td width="32" style="padding-top:1px;">
      <div style="width:24px;height:24px;background:#6366f1;border-radius:50%;
      text-align:center;line-height:24px;">
        <span style="font-size:12px;font-weight:700;color:#ffffff;">1</span>
      </div>
    </td>
    <td style="padding-left:10px;">
      <p style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;
      font-size:14px;color:#334155;line-height:1.7;margin:0;">
      <strong>原则标题</strong>：详细说明。
      </p>
    </td>
  </tr></table>
</div>
```

---

### O. 结尾 Closing 块

```html
<div style="background:#0f172a;border-radius:8px;padding:26px 22px;
margin:28px 0 0;text-align:center;">
  <p style="font-family:'STSong','SimSun',serif;font-size:16px;
  color:rgba(255,255,255,0.75);line-height:2;margin:0;">
  结尾段落文字，可以用 <br> 换行。<br><br>
  <strong style="color:#818cf8;">强调句子。</strong>
  </p>
</div>
```

---

### P. Footer

```html
<div style="margin-top:44px;padding-top:18px;border-top:1px solid #e2e8f0;">
  <p style="font-size:11px;color:#94a3b8;letter-spacing:0.05em;margin:0;line-height:1.8;">
  标签1 · 标签2 · 标签3
  </p>
</div>
```

---

## 文章结构模板

```
Hero（标题 + 副标题 + 标签）
  ↓
导语 Callout（文章目的/读者收益）
  ↓
[章节标题 01]
  正文段落
  组件（Pull Quote / Callout / Pipeline / 表格）
  分割线
  ↓
[章节标题 02]
  ...
  ↓
[写在最后]
  编号原则卡片
  Closing 深色块
  Footer
```

---

## 标题优化指南

面向**工程师 + 产品经理**混合读者时：

- **工程师信号词**：架构、pipeline、约束、原理、实现、调优
- **产品经理信号词**：数据闭环、基础设施、决策路径、分工逻辑

好标题同时包含两类信号，例：
> `智驾数据闭环的地基：SLAM 的工程本质与架构逻辑`
> `从第一性原理理解分布式训练`

避免：纯学术名词堆砌、过长（>20 字）、无动词。

---

## 文章内容的不可渲染元素处理

| 原格式 | 处理方式 |
|--------|---------|
| LaTeX 公式 `$$...$$` | 改写为文字描述，保留核心含义 |
| Mermaid 流程图 | 用纵向步骤组件（H）或决策树重建 |
| 外链图片 | 说明"微信会屏蔽外链"，用 HTML 组件等价替代 |
| `<code>` 代码块 | 用 Callout 框 + 等宽字体呈现关键行 |
| 表格超过 3 列 | 拆分为卡片列表（I）或多个 2 列表格 |

---

## 输出规范

1. 生成完整 HTML 文件，保存到当前工作区目录（或用户指定路径，若源文章在某目录则优先保存在同目录下），命名格式为 `文章名_wechat.html`
2. 在回复中给出该文件的可点击链接（`file://` 路径），方便用户直接打开
3. 同时输出以下提示：

```
使用方法：
① Chrome 打开此文件
② Cmd+A / Ctrl+A 全选 → Cmd+C / Ctrl+C 复制
③ 打开 mp.weixin.qq.com → 新建图文 → Cmd+V / Ctrl+V 粘贴
④ 点击右上角「手机预览」确认效果后发布
```

---

## 常见错误检查清单

生成 HTML 前自检：

- [ ] 没有任何 `display:flex` 或 `display:grid`
- [ ] 没有 `var(--xxx)` CSS 变量
- [ ] 没有 `::before` / `::after` 伪元素
- [ ] 没有 `<style>` 标签块
- [ ] 没有 Google Fonts 或其他外链字体
- [ ] 多列布局全部用 `<table>` 实现
- [ ] 所有颜色为 hex 值
- [ ] 正文字号 ≥ 16px
- [ ] 段落行高 ≥ 1.9
- [ ] 移动端无需横向滚动（无固定宽度超过 90%）
