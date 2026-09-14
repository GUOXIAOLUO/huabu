# Video Canvas Replica Specification

## 1. 设计目标

整体应呈现为：**轻、白、克制、以内容为主体的 AI 无限画布工具**。参考 Figma/Linear 类工具的低噪声工作区，而不是传统“节点编辑器”重框架视觉。

## 2. Canvas Surface

### 默认状态

- 大面积近白背景。
- 背景网格/定位纹理极弱，不能抢内容。
- 常驻 UI 尽量少。
- 顶部保留项目/画布级导航与少量全局操作。
- 缩放、回中、添加等画布级控制集中为小型浮动控制组。

### 禁止

- 强烈渐变背景。
- 大面积玻璃拟态。
- 粗重网格线。
- 节点之间用高饱和色大面积区分 Provider。

## 3. Design Tokens（初始冻结值，实施时允许像素微调）

```text
canvas-bg: #F7F8FA ~ #FAFAFB
surface: #FFFFFF
border: 1px neutral-light
radius-card: 12~16px
shadow: very-low elevation
text-primary: near-black
text-secondary: neutral gray
selection: thin blue outline
edge-default: ~1.25px neutral-light
edge-hover: ~1.5px
edge-selected: ~1.75px blue
primary-action: dark/black
```

> 不要求机械照抄色值；验收按视觉等价：浅、低噪、内容优先。

## 4. Node 尺寸层级

```text
Small Resource: 280~320px
Standard:       320~380px
Task/LLM:       360~440px
Collection:     500~720px
Result:         480~900px
Workspace:      不受 Card 固定宽度约束
```

节点尺寸由 presentation 与内容决定，不再强迫所有节点同宽。

## 5. Node Header

参考视频：Header 只是轻量身份区。

目标：

```text
[icon] 节点名称                         [···]
```

- 不使用厚色块标题栏。
- `Ready/Done` 默认不需要大型 Badge。
- `Running/Error/Waiting` 才提高视觉权重。
- Provider/Model 信息通常放参数摘要或 Footer，不抢标题。

## 6. Node Body

原则：**Card 只留完成主任务所需的最少字段。**

复杂参数分级：

```text
Card summary
 -> Parameter Popover
 -> Inspector / Workspace
```

禁止把所有 width/height/CFG/seed/provider-specific fields 永久堆入 Card。

## 7. Node Footer

执行型节点统一语言：

```text
Model / Route              Cost(optional)
1:1 · 4K · ×3                         Run ↑
```

Footer 可承载：

- 当前 Model
- 关键参数摘要
- Batch count
- Cost estimate
- Run/Generate

不同 Provider 不应拥有完全不同的 Footer 信息架构。

## 8. Edge

- 默认细、浅。
- Bezier/柔和曲线。
- Hover/selected 才明显加深。
- Running 可选轻量流动动画，但避免游戏化高亮。

## 9. Port

默认不应让每个 Node 常驻一圈醒目圆点。

建议：

- Hover/selected 时强化可连接位置。
- 边缘出现 `+` / handle。
- 点击或拖出 -> Node Picker -> 自动 create + connect。

底层仍必须保留 typed port / compatibility。

## 10. Floating Action Bar

Resource Node 尤其是 Image，应“内容就是节点”。

选中后再出现：

```text
编辑 / 裁剪 / 抠图 / 下载 / 分析 / 生成 / 更多
```

Action 应由 ActionRegistry + selection capability 驱动，而不是每个节点手写按钮。

## 11. Parameter Popover

视频参考 `REF-101`：

- 浮层覆盖在节点附近。
- 顶部允许“自动 / 系统参数 / 自定义”类似层级。
- 比例与分辨率分栏选择。
- Card 只显示 `1:1 · 4K` 摘要。

此模式应扩展到 WholeHouse 高级参数，而不是把几十项设计参数直接塞在节点里。

## 12. Presentation Levels

统一使用：

- `card`：高频操作与摘要
- `expanded`：更多内容
- `workspace`：复杂编辑/结果/表格
- `inspector`：高级配置与元数据

Card 不应承载 Workspace 级功能。
