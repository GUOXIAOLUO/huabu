# Architecture Guardrails — UI Replica Must Not Break These

## 1. 不做 Greenfield Rewrite

UI 改造是在现有 Workbench 上进行 Presentation 重构，不重新造第二套 Canvas。

## 2. One Unified Canvas

禁止：

- 为 WholeHouse 新建行业专属 Canvas Runtime。
- 为“视频复刻版”保留另一套 product runtime。
- 通过页面看起来统一但底层仍是两套运行时来冒充统一画布。

## 3. Canonical Concepts 必须分离

```text
Node
!= Prompt
!= Workbench Skill
!= Model
!= ProviderDefinition
!= ProviderConnection
!= ModelAvailability
!= ExecutionRoute
!= ExecutionProfile
!= Executor
!= Asset
!= Artifact
!= Entity
```

禁止为了视频中某个外观直接新增永久 Provider 型 NodeKind。

## 4. Definition 驱动

长期目标：

```text
DefinitionRef
  -> DefinitionResolver
  -> CreationCatalog projection
  -> NodePicker
  -> NodeCreationService
```

Canvas Core 不应对 WholeHouse Skill ID、Provider ID、Comfy workflow ID 进行永久硬编码分支。

## 5. 创建/变更必须走 Application Service

节点与边：

- `NodeCreationService`
- `NodeMutationService`
- `GraphMutationService`

禁止通过 DOM、raw canvas JSON、raw SQLite 或 Provider callback 绕过正式写入边界。

## 6. Compatibility 一套规则

Human UI / Workflow / Agent 必须最终使用同一个 CompatibilityResolver / PortType contract。`legacy.any` 只能作为迁移兼容，不作为新 UI 设计基础。

## 7. Provider/Model/Executor 不写进视觉 Node Type

视频中 API Generate 的视觉可以复刻，但底层应映射：

```text
Definition + ModelBinding + ModelAvailability + ExecutionProfile + Executor
```

Node 内不得保存 API Key。

## 8. Collection ≠ Group ≠ Batch Policy

- Group：画布视觉组织
- Collection：typed multi-item data
- ExecutionPolicy：并行、重试、批量执行语义

视频表格 UI 应落到 Collection presentation，不新增永久 Spreadsheet Core Domain。

## 9. ComfyUI 是 Workflow Executor/Integration

Workbench 不复制 ComfyUI 全图；只暴露被映射的输入/输出参数。

```text
WorkflowRef@version
+ InputRoleMapping
+ OutputMapping
+ ComfyUIExecutor
```

## 10. WholeHouse 不进入 Core

WholeHouse 能力放 `packages/wholehouse/`，复用通用 Asset/Task/Collection/Result/Workflow UI。

## 11. V1 酷家乐/柜柜边界不变

UI 改造不授权提前实现：

- Agent 直接控制酷家乐
- Agent 直接控制柜柜

先保持 CAD/文件/HandoffPackage 交接。

## 12. Legacy/Classic 只迁移，不扩张

在兼容 Gate 未通过前不能盲删，但新增 UI 能力不得继续堆到 `classic-*` 中。迁移步骤应为：characterize -> generic replacement -> delegate -> browser acceptance -> remove。
