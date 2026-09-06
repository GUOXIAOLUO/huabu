# Xinhuabu — Codex + ZCode/GLM Agent Development Kit

这是一套“仓库自驱动”的 Agent 开发约定，用于让 **OpenAI Codex** 与 **ZCode Agent / GLM** 在同一个 Xinhuabu 仓库中按照同一套架构规则、当前状态与任务卡连续开发。

## 设计目标

Agent 不依赖聊天历史，不需要每次重新粘贴完整架构方案。

仓库内的职责分层：

```text
AGENTS.md
= 仓库长期硬规则（已有文件，继续作为最高规则）

TARGET_ARCHITECTURE.md
= 最终目标

IMPLEMENTATION_PLAN.md
= R0-R17 路线

docs/status/CURRENT_EXECUTION_STATUS.md
= 当前状态唯一 Authority

AGENT_NEXT_TASK.md
= 当前只允许执行哪一张任务卡

docs/tasks/
= 可执行任务卡

.agent/
= Agent 共用 Prompt / Contract

scripts/
= 状态、验证、Codex runner
```

## 安装

把本开发包内容复制/解压到 `xinhuabu` 仓库根目录。

不会要求覆盖现有：

- `AGENTS.md`
- `TARGET_ARCHITECTURE.md`
- `MIGRATION_PLAN.md`
- `IMPLEMENTATION_PLAN.md`
- `docs/status/CURRENT_EXECUTION_STATUS.md`

请保留仓库已有版本。

首次使用前：

```bash
chmod +x scripts/agent-*.sh
./scripts/agent-status.sh
```

## Codex 直接执行

在仓库根目录：

```bash
./scripts/agent-run-codex.sh
```

脚本会把 `.agent/prompts/run-current-task.md` 交给 `codex exec`。

你也可以交互式启动 Codex，然后输入：

```text
Read AGENTS.md, .agent/AGENT_CONTRACT.md and AGENT_NEXT_TASK.md.
Execute exactly the active task card.
Run the required verification and stop after this card.
```

## ZCode / GLM 直接执行

用 ZCode 打开 `xinhuabu` 项目工作区，新建一个 ZCode Agent 任务。

第一次建议把以下文件加入上下文或让 Agent 主动读取：

- `AGENTS.md`
- `.agent/AGENT_CONTRACT.md`
- `AGENT_NEXT_TASK.md`
- `docs/status/CURRENT_EXECUTION_STATUS.md`

然后发送：

```text
读取 .agent/prompts/zcode-run-current-task.md，
严格执行 AGENT_NEXT_TASK.md 指向的当前任务卡。
只完成一张卡，验证、更新状态并 Review 后停止。
```

ZCode 是桌面 ADE，不需要假设存在与 Codex 相同的 CLI。

## 一次只执行一张任务卡

不要让 Agent 自动从 R4-01 连续跑到 R4-20。

正确循环：

```text
当前任务卡
→ Agent 实现
→ focused tests
→ agent-verify
→ git diff review
→ 更新 status
→ 停止
→ 人工/另一个 Agent Review
→ 再激活下一卡
```

## 推荐的双 Agent 模式

```text
ZCode 实现
→ Codex Review

下一卡：

Codex 实现
→ ZCode Review
```

不要让两个 Agent 同时修改同一个 worktree。

如需要并行，使用不同 Git worktree / branch。

## 当前开发阶段

本包默认把 `R4-01 — Re-establish Local Truth` 设为 active。

如果仓库当前实际进度已经超过 R4-01，请先以：

`docs/status/CURRENT_EXECUTION_STATUS.md`

为准，然后修改 `AGENT_NEXT_TASK.md` 指向真实下一卡。

不要为了匹配本包而回退仓库状态。

## 关键原则

R4 的进度不是“新增了多少 helper”，而是：

```text
Classic Runtime Ownership ↓
Smart Runtime Ownership ↓
Unified Runtime Ownership ↑
```

任务完成必须能回答：

- Before Owner
- After Owner
- 删除了哪个旧 ownership
- 建立了哪个新 ownership
- 测试证明了什么


## V2 完整任务卡覆盖

本包现在包含：

- R4-01 ～ R4-41：Unified Canvas Cutover
- R5-01 ～ R5-13：Project Authority + Rich Node
- R6-01 ～ R6-24：Binding / Collection / Prompt / Skill
- R7-01 ～ R7-13：Provider / Model / Codex
- R8-01 ～ R8-22：Execution + Result Tray
- R9-01 ～ R9-15：Asset / Artifact / Catalog
- R10-01 ～ R10-08：Entity / Knowledge
- R11-01 ～ R11-15：Workflow / Approval / Handoff
- R12-01 ～ R12-12：Package / Integration
- R13-01 ～ R13-06：Common Package / Generic Gate
- R14-01 ～ R14-13：Agent
- R15-01 ～ R15-15：WholeHouse Vertical Slice
- R16-01 ～ R16-09：WholeHouse Expansion
- R17-01 ～ R17-09：真实工作室验证与集成决策
- ENG-01 ～ ENG-06：工程治理

所有未来卡默认处于 `backlog/`。
只有 `AGENT_NEXT_TASK.md` 指向并移入 `active/` 的卡才允许执行。
