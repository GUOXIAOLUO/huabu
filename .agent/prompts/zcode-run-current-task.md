# Run Current Task (ZCode / GLM)

你在这个 Xinhuabu AI Workbench 仓库中执行恰好一张任务卡。本提示自包含,
不依赖聊天记忆。

## 先按顺序读取

1. `AGENTS.md`
2. `.agent/AGENT_CONTRACT.md`
3. `docs/status/CURRENT_EXECUTION_STATUS.md`
4. `AGENT_NEXT_TASK.md`
5. `AGENT_NEXT_TASK.md` 指向的当前任务卡。

## 执行

- 只完成这一张卡,包括它的 In Scope、Execution Pattern、Focused Tests、
  Regression 各节。
- 禁止开始下一张卡或更后的 Round。规划类编辑不授权未来 Round 的实现。
- 禁止 `git reset`/`checkout`/`clean` 未知改动;禁止自动 commit、push、切换
  任务。遵守契约的 local-first 边界。
- 不修改任务卡范围之外的文件。

## 验证

- 运行任务卡要求的 focused tests。
- 运行回归门 `./scripts/agent-verify.sh`;它必须通过,卡片才能标记 `DONE`。
- 所有结果都要分类为既有 vs 新增。

## 记录,然后停止

1. 用验证过的证据更新 `docs/status/CURRENT_EXECUTION_STATUS.md`。
2. 仅当所有权变化时更新 `docs/plans/R4_OWNERSHIP_MATRIX.md`。
3. 仅当 DoD 真正满足时把任务卡状态置为 `DONE`。
4. 把推荐的下一张卡写入 `AGENT_NEXT_TASK.md`,但不执行它。
5. 完成这一张卡后停止。

## 最终报告必须包含

Before Owner、After Owner、删除的旧所有权、修改文件、测试结果、剩余问题、
推荐的下一张卡。
