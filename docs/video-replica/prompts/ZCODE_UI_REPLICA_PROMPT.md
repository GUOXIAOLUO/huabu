# ZCode / GLM — UI Replica Start Prompt

任务：在不改变 Infinite-Canvas / AI Workbench 现有产品目标和架构边界的前提下，实现参考视频中的 Canvas 与节点 UI/交互复刻。

开始任何代码修改前必须读取：

- `AGENTS.md`
- `docs/status/CURRENT_EXECUTION_STATUS.md`
- `CURRENT_ARCHITECTURE.md`
- `TARGET_ARCHITECTURE.md`
- `MIGRATION_PLAN.md`
- `IMPLEMENTATION_PLAN.md`
- 当前 Task Card
- `docs/design/video-replica/README.md`
- `docs/design/video-replica/ARCHITECTURE_GUARDRAILS.md`
- `docs/design/video-replica/VIDEO_CANVAS_REPLICA_SPEC.md`
- `docs/design/video-replica/VIDEO_INTERACTION_SPEC.md`
- `docs/design/video-replica/VIDEO_NODE_SPEC.md`
- `docs/design/video-replica/VIDEO_ACCEPTANCE_CHECKLIST.md`
- 与当前任务对应的 `references/` 关键帧

核心原则：

```text
UI 尽可能 1:1 复刻视频
架构不复制视频未知内部实现
One Unified Canvas
Definition/Skill/Model/ProviderConnection/Executor 分离
WholeHouse 仍是 package
新增能力不扩张 classic-* 长期责任
```

工作方法：

1. 先定位当前实现文件与 tests。
2. 对照 reference 图片列出视觉/交互差异。
3. 优先修改 shared presentation/runtime，不写一次性节点特例。
4. 保持 canonical mutation、revision、authorization、execution 语义。
5. 修改后跑测试，并进行浏览器交互验收。
6. 输出“reference -> implementation -> test”映射表。

如果当前 Round 未授权 UI 大改，不得越权实现，只能留下可执行任务计划或当前 Round 允许的变更。
