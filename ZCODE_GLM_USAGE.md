# ZCode / GLM Usage

ZCode 使用同一套仓库任务 Authority，不需要建立第二套任务系统。

## 第一次

1. 用 ZCode 打开 `xinhuabu` 项目目录。
2. 新建 ZCode Agent 任务。
3. 让 Agent 读取：
   - `AGENTS.md`
   - `.agent/AGENT_CONTRACT.md`
   - `docs/status/CURRENT_EXECUTION_STATUS.md`
   - `AGENT_NEXT_TASK.md`
4. 发送：

```text
读取 .agent/prompts/zcode-run-current-task.md 并执行。
只完成 AGENT_NEXT_TASK.md 当前一张任务卡。
完成验证和 Review 后停止。
```

## 后续任务

每完成一张卡并经过 Review 后，再人工激活下一卡。

不要依赖 ZCode 对上一个聊天的记忆来确定下一任务。
任务 Authority 永远是仓库文件。

## ZCode Review

建议任务完成后在 Review 面板检查：

- 有没有越界修改
- 有没有新增未来 Round 代码
- 有没有只是增加 helper 而未减少旧 ownership
- 是否出现无关格式化/清理
- 是否保留兼容路径
- 测试是否真实覆盖行为

## 和 Codex 配合

推荐：

```text
ZCode implementation
→ Codex review

or

Codex implementation
→ ZCode review
```

两个 Agent 不应同时写同一个 worktree。
