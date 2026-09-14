# Video Interaction Specification

## 1. 画布基本交互

必须保持：

- pan
- zoom
- selection
- multi-selection
- drag
- resize（适用节点）
- open preview/workspace
- edge create/delete
- keyboard delete/escape 等基础行为

UI 复刻不能破坏已有 canonical revision/mutation 规则。

## 2. Connect-to-Create（关键）

视频中最值得复刻的统一语法：

```text
Node output/edge handle
  -> +
  -> Node Picker
  -> compatible definitions only
  -> choose
  -> create node + create edge atomically/through canonical services
```

目标链：

```text
Connection Intent
 -> CompatibilityResolver / PortTypeRegistry
 -> CreationCatalog
 -> DefinitionResolver
 -> NodePicker
 -> NodeCreationService
 -> GraphMutationService
```

### 验收

- 选择 Image output 时不展示明显不兼容节点。
- 创建成功后自动连接。
- stale revision / authorization / validation 失败必须可观察，不能前端偷偷“补写”。

## 3. Node Picker

结构建议：

```text
搜索节点...

最近使用
常用
AI
工作流
资源
WholeHouse（package 安装后）
```

搜索字段：

- title
- description
- keywords
- category
- capability

Catalog UI 不得靠 `quickAdd('xxx')` 永久扩张。

## 4. Parameter Edit

高频参数直接在 Card。
中频参数 Popover。
低频/高级参数 Inspector。
复杂工作进入 Workspace。

修改必须清楚区分：

- 本地编辑态
- canonical persist
- execution-only override（如果产品允许）

## 5. Run / Generate

点击 Run：

1. 解析 Model/Route/Executor。
2. 创建 ExecutionRun/Attempt。
3. Node 进入 Running presentation。
4. 进度通过正式 execution event 呈现。
5. Result 进入 Result runtime，而不是直接拼 DOM。

## 6. Batch / Collection

用户感知：

```text
Collection rows
 -> one Task/Generate node
 -> N executions/results
```

底层不可在 UI 用无约束 `for(fetch)` 充当正式批量执行。

要求：

- concurrency policy
- retry
- cancel
- partial failure
- rerun selected
- durable result linkage

## 7. Result Flow

生成后：

```text
Result Tray
 -> Preview
 -> Selection/Rating
 -> Compare
 -> Collection
 -> Materialize to Canvas / Resource
```

这些能力视觉上应像一个统一 Result Workspace，而不是散落的独立调试控件。

## 8. Media Editor

流程：

```text
select Asset
 -> Floating Action: Edit
 -> Media Workspace
 -> crop/mask/transform/etc.
 -> save
 -> create new version/result/materialization
 -> return Canvas
```

不要让 Canvas Node Body 内直接承载完整媒体编辑器。

## 9. Comfy Workflow Mapping

流程：

```text
Import/select workflow@version
 -> discover candidate inputs
 -> map semantic roles
 -> choose exposed params
 -> choose outputs
 -> save definition
 -> create simplified Workbench node
```

角色示例：

`image`, `prompt`, `mask`, `reference`, `seed`, `width`, `height`, `strength`, `duration`, `audio`。

Workbench 不展示内部 50~100 个 Comfy 节点，除非用户明确进入 ComfyUI 本体。
