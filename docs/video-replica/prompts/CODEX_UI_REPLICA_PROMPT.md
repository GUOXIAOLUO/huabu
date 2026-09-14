# Codex — UI Replica Start Prompt

你正在 `Infinite-Canvas / AI Workbench` 仓库执行 UI Replica 工作。

## 强制读取顺序

先读取并遵守：

1. `AGENTS.md`
2. `docs/status/CURRENT_EXECUTION_STATUS.md`
3. `CURRENT_ARCHITECTURE.md`
4. `TARGET_ARCHITECTURE.md`
5. `MIGRATION_PLAN.md`
6. `IMPLEMENTATION_PLAN.md`
7. 当前授权 Task Card
8. `docs/design/video-replica/README.md`
9. `docs/design/video-replica/ARCHITECTURE_GUARDRAILS.md`
10. `docs/design/video-replica/VIDEO_CANVAS_REPLICA_SPEC.md`
11. `docs/design/video-replica/VIDEO_INTERACTION_SPEC.md`
12. `docs/design/video-replica/VIDEO_NODE_SPEC.md`
13. `docs/design/video-replica/VIDEO_ACCEPTANCE_CHECKLIST.md`
14. 本任务对应 `references/` 图像

## 目标

深度继承参考视频的 Canvas UI、Node UI 与交互语言，使新增页面/节点看起来像同一个产品自然延伸；但**代码架构重构不等于 UI 重设计**，不得改变现有 AI Workbench / WholeHouse 长期目标。

## 禁止

- 不创建第二套 Canvas Runtime。
- 不做 greenfield rewrite。
- 不把 WholeHouse 业务塞进 Core。
- 不把 Provider/Model/Executor 合并成 Node type。
- 不在 Node 中保存 API Key。
- 不绕过 NodeCreationService / NodeMutationService / GraphMutationService。
- 不继续向 `classic-*` 添加新的长期业务责任。
- 不因 UI 复刻提前直接控制酷家乐/柜柜。
- 不越过当前 Round/Gate。

## 实施要求

1. 先 inventory 当前实现与对应 reference image。
2. 明确哪些能力是 presentation change，哪些需要 generic runtime support。
3. 最大化复用 NodeShell、RendererRegistry、PresentationState、FloatingActionBar、Collection、Result runtime、Execution runtime。
4. Provider-specific UI 优先收敛为 generic Definition/schema presentation，不复制分支。
5. 每次修改后跑受影响 tests + browser acceptance。
6. 最终报告必须列出：修改文件、reference 编号、差异、测试、仍存在的 legacy debt。

如果当前授权 Round 不是 UI Replica Wave，只输出计划/规范或执行该 Round 允许的最小工作，不私自进入未来 Round。
