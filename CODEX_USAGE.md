# Codex Usage

当前包使用 Codex 的非交互执行模式：

```bash
codex exec PROMPT
```

并通过 stdin 提供 `.agent/prompts/run-current-task.md`。

直接运行：

```bash
./scripts/agent-run-codex.sh
```

如果你希望交互式操作，也可以：

```bash
codex
```

然后输入：

```text
Read AGENTS.md, .agent/AGENT_CONTRACT.md and AGENT_NEXT_TASK.md.
Execute exactly the active task card, run verification, update required status documents, and stop.
```

## Review 模式

可开另一个 Codex session，让它读取：

`.agent/prompts/review-current-task.md`

用于独立审查前一个 Agent 的修改。

## 安全

脚本不会：

- 自动 git reset
- 自动 commit
- 自动 push
- 自动切换下一任务

这些动作故意留给人工 Review 后决定。
