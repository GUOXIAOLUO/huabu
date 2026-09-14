# Video Node Specification

## A. Asset / Image Node

参考：`references/canvas-overview/`、`references/media-editor/`

### Card

- 图像本体占主要视觉面积。
- 尽量不显示 path/url/metadata 等技术字段。
- Hover/selected 出现必要控件。

### Actions

- Preview
- Edit
- Crop/Mask（能力存在时）
- Analyze
- Generate from / Use as reference
- Download/Export

### Domain Mapping

`Asset / AssetVersion` + `AssetRichNode`，不要新增永久 Image Domain。

---

## B. Task / LLM Node

参考 `REF-201~205`。

视频本质不是 Chat Bubble，而是通用 Task Processor。

### Card 信息结构

```text
Title / Skill
Platform or route summary   Model
Input resources
Prompt
Skill toggle / Skill selection
Output mode: text / list / structured
Run
```

### Domain Mapping

`TaskRichNode + SkillDefinition + ModelBinding + ExecutionProfile`。

WholeHouse 的需求分析/户型分析/设计评审等优先通过 Skill/Definition 区分，而不是新增大量 Core NodeKind。

---

## C. Generation Node

参考 `REF-101~103`。

### Card

- reference inputs
- prompt
- model/route
- summary `1:1 · 4K · ×N`
- cost estimate（可用时）
- Run

### Parameter Popover

- ratio
- resolution
- count
- model-specific advanced section

Provider 特殊参数通过 schema/field renderer 或 Inspector，避免永久 Provider 专用 Canvas 分支。

---

## D. Collection / Table Node

参考 `REF-401~403`。

### Presentation

同一 `Collection` 可有：

- table
- grid
- gallery
- list
- workspace

### 典型字段

- image/resource
- name
- prompt
- tag/status
- arbitrary typed columns

### WholeHouse 示例

```text
空间 | 柜体 | 材质 | 风格 | Prompt | 状态
```

不要建立独立 Core Spreadsheet/Batch domain。

---

## E. Result Node / Workspace

参考 `REF-301~304`。

### Card/Expanded

- result count
- thumbnail grid
- selection state

### Workspace

- preview
- next/prev
- multi-select
- compare
- rating/selection
- collect
- materialize
- rerun

WholeHouse 将来可直接用来做方案 A/B/C 评审与 Approved/Frozen 前置选择。

---

## F. Comfy Workflow Node

参考 `REF-501~504`。

### Workbench Node 只显示

- mapped inputs
- exposed parameters
- workflow name/version
- output summary
- Run

### 不显示

- 全部内部 KSampler/Loader/latent graph（除非进入 ComfyUI）。

### Domain Mapping

`WorkflowRef@version + ComfyUIInputBinding + ComfyUIExecutor`。

---

## G. Provider/Model Settings

参考 `references/provider-settings/`。

设置页负责：

- provider definition/type
- endpoint/base url
- credential reference
- models
- connection test/status

Canvas Node 负责：

- 用户可理解的 Model/route selection
- capability-compatible options

API Key 不进入 Canvas Node persistence。
