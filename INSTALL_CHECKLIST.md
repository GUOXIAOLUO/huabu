# Installation Checklist

把本包合并到现有 Xinhuabu 仓库后检查：

- [ ] 根目录已有 `AGENTS.md`
- [ ] 根目录已有或能找到 `docs/status/CURRENT_EXECUTION_STATUS.md`
- [ ] `.agent/AGENT_CONTRACT.md` 已存在
- [ ] `AGENT_NEXT_TASK.md` 已存在
- [ ] `AGENT_NEXT_TASK.md` 指向的 Active Task 与 `docs/tasks/TASK_INDEX.md` 中的 ACTIVE 行一致
- [ ] `scripts/agent-status.sh` 可执行
- [ ] `scripts/agent-verify.sh` 可执行
- [ ] `scripts/agent-run-codex.sh` 可执行

运行：

```bash
./scripts/agent-status.sh
```

然后：

```bash
./scripts/agent-verify.sh
```

注意：如果仓库当前真实进度已经超过本包默认的 R4-01，
不要回退代码。修改 `AGENT_NEXT_TASK.md` 和对应的 backlog 卡片，使其与
`CURRENT_EXECUTION_STATUS.md` 的真实状态一致。
