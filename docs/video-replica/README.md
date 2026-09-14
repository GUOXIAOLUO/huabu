# Video Canvas Replica Reference Pack

这套参考包用于在 **Codex / ZCode / GLM / 其他 Agent 的全新对话** 中继续执行 Infinite-Canvas / AI Workbench 的 UI 改造，而不依赖原 ChatGPT 对话上下文。

## 使用目标

- 复刻两段参考视频中的 Canvas UI、Node UI、节点创建/连线、参数浮层、批量生成、结果工作区、ComfyUI 参数映射、Provider/Model 设置等交互表现。
- **不改变现有项目开发目标与架构边界。**
- 保留 `Unified Canvas + Workbench Project/Resource Runtime + Codex Harness + multi-model/multi-executor + Integration Runtime + Industry Packages`。
- WholeHouse 仍是 Industry Package；酷家乐/柜柜 V1 仍通过 CAD/文件交接，不因 UI 复刻提前改成直接软件控制。

## Agent 必读顺序

在任何 UI 代码修改前，先读项目自己的权威文件：

1. `AGENTS.md`
2. `docs/status/CURRENT_EXECUTION_STATUS.md`
3. `CURRENT_ARCHITECTURE.md`
4. `TARGET_ARCHITECTURE.md`
5. `MIGRATION_PLAN.md`
6. `IMPLEMENTATION_PLAN.md`
7. 当前授权 Task Card
8. 本目录 `VIDEO_CANVAS_REPLICA_SPEC.md`
9. 本目录 `VIDEO_INTERACTION_SPEC.md`
10. 本目录 `VIDEO_NODE_SPEC.md`
11. 本目录 `VIDEO_ACCEPTANCE_CHECKLIST.md`
12. 当前任务对应 `references/` 图片

> 本参考包是 UI/UX 设计依据，不取代仓库自己的 Round/Gate 授权规则。若当前 Round 不允许大规模 UI 改造，只允许做文档、原型或不改变责任边界的小调整。

## 目录

```text
docs/design/video-replica/
├── README.md
├── SOURCE_VIDEO_MANIFEST.md
├── SOURCE_VIDEO_SHA256.txt
├── VIDEO_CANVAS_REPLICA_SPEC.md
├── VIDEO_INTERACTION_SPEC.md
├── VIDEO_NODE_SPEC.md
├── VIDEO_ACCEPTANCE_CHECKLIST.md
├── ARCHITECTURE_GUARDRAILS.md
├── IMPLEMENTATION_WAVE.md
├── references/
│   ├── canvas-overview/
│   ├── node-picker/
│   ├── task-llm-node/
│   ├── generation-node/
│   ├── collection-table/
│   ├── result-workspace/
│   ├── comfy-mapping/
│   ├── provider-settings/
│   └── media-editor/
└── prompts/
    ├── CODEX_UI_REPLICA_PROMPT.md
    └── ZCODE_UI_REPLICA_PROMPT.md
```

## 日常使用方式

- 普通 UI 任务：读 Spec + 对应类别关键帧，不需要重新播放整段视频。
- 有动画/时序/弹层细节争议时：再回看原始视频对应时间段。
- Agent 自主设计不得覆盖视频中已经明确的视觉与交互模式。
- 如果视频表现与项目硬架构约束冲突：**架构约束优先，UI 视觉/交互等价复刻。**
