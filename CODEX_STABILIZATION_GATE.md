# CODEX_STABILIZATION_GATE.md

> 目的：给 Codex / Codex Harness 提供一个**可直接执行、但不干扰后续任务卡开发**的前置稳定化文件。
>
> 本文件不是新的产品路线，不替代 `AGENT_NEXT_TASK.md`、`TASK_INDEX.md`、现有 Task Card，也不重新定义 R9。
>
> 它只负责：
>
> 1. 修复当前工作树中已经确认的高优先级稳定性问题；
> 2. 保持现有行为和 public contract；
> 3. 通过 Stability Gate；
> 4. 然后立即把开发控制权交还给现有任务系统。

---

# 1. Authority / 权威顺序

Codex 必须按照下面顺序理解项目事实：

```text
1. 当前本地工作树实际代码
2. AGENTS.md
3. AGENT_NEXT_TASK.md
4. 当前 ACTIVE Task Card
5. TASK_INDEX.md
6. CURRENT_EXECUTION_STATUS.md
7. CURRENT_ARCHITECTURE.md
8. 本文件 CODEX_STABILIZATION_GATE.md
```

本文件的权威范围仅限：

```text
S0 stabilization tasks
```

本文件**无权**：

```text
修改后续任务卡目标
重编号任务
改变后续任务依赖
提前实现未来任务
重新定义产品路线
扩大 R9-03 / R9-04 / R9-05 等 scope
```

如本文件与当前 ACTIVE Task Card 对未来功能描述发生冲突：

```text
当前 ACTIVE Task Card 优先
```

如本文件指出的稳定性 bug 与当前本地代码事实冲突：

```text
当前本地代码优先
```

---

# 2. Non-Interference Rule / 不影响后续开发原则

执行本文件时，必须保证：

```text
只修 bug
不提前开发 feature
只加兼容 seam
不提前建未来 UI
只修当前 contract violation
不重新设计未来 domain
只加必要测试
不重写后续 task cards
```

任何修改如果会改变后续任务卡的业务语义，必须停止并标记：

```text
DEFER_TO_ACTIVE_TASK_CARD
```

不得自行“顺便做完”。

---

# 3. Local Worktree Safety

开始任何修改前必须执行：

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
```

规则：

- 本地工作树是唯一开发事实来源。
- 不得用 remote 覆盖本地。
- 不得回滚用户未提交修改。
- 禁止自动：
  - `git reset`
  - `git restore`
  - `git checkout -- <file>`
  - `git clean`
  - `git stash`
  - `git pull`
  - `git rebase`
  - `git merge`
  - `git commit`
  - `git push`
- 若目标文件已有无关本地修改，只改最小 hunk。
- 无法安全隔离时输出：

```text
BLOCKED_BY_LOCAL_CHANGES
```

---

# 4. Scope Freeze

本文件允许修改的范围，仅限与下列稳定性问题直接相关的代码、测试和当前事实文档。

允许：

```text
API availability / gating
privileged capability boundary
workflow path validation
remote URL fetch security
revision/timestamp correctness
upload/resource limits
async blocking I/O
current status documentation consistency
```

禁止借机：

```text
重写 Canvas
迁移前端框架
重新设计 Project schema
重新设计 Execution schema
新建 Artifact 系统
新建 Catalog 系统
实现 Resource Library UI
实现 Asset Inspector
实现 drag-to-canvas feature
实现 Result→Asset / Result→Artifact
大规模拆 main.py
大规模目录重构
```

---

# 5. Compatibility Freeze

除非当前 bug 本身要求，否则本轮不得主动改变：

```text
Canvas URL
Project API payload
Canvas API payload
Node schema
Graph schema
WebSocket message shape
SQLite existing schema
Provider request semantics
existing route names
existing response field names
existing persisted identifiers
existing task numbering
existing task card filenames
```

如修复安全问题必须改变某一 public behavior：

1. 先确认是否存在不破坏 contract 的修复方式；
2. 优先选择兼容修复；
3. 必须增加 regression test；
4. 记录在：

```text
docs/decisions/
```

或项目已有的 decision-log 机制中。

不要把该变化扩展到未来任务。

---

# 6. Future Task Protection

执行 S0 时，禁止修改未来任务卡，除非只是修正：

```text
明显错误的 current-status pointer
```

默认禁止修改：

```text
docs/tasks/backlog/R9-04*
docs/tasks/backlog/R9-05*
docs/tasks/backlog/R9-06*
docs/tasks/backlog/R9-07*
docs/tasks/backlog/R9-08*
...
```

如果发现未来任务可能受到当前修复影响：

不要改它。

只记录：

```text
FUTURE_TASK_NOTE
task:
reason:
contract affected:
recommended follow-up:
```

然后继续当前 stabilization。

---

# 7. Execution Model

每个 S0 任务严格：

```text
inspect
→ reproduce/characterize
→ focused failing test
→ minimal fix
→ focused verify
→ full gate
→ diff review
→ stop
```

每次只执行一个 S0 任务。

完成后停止。

不要自动串行执行下一项。

---

# 8. S0 Task Order

顺序：

```text
S0-01 Canonical API availability in LAN mode
S0-02 Privileged filesystem capability boundary
S0-03 Workflow path traversal
S0-04 Unified SafeRemoteFetch
S0-05 canvas_revision / updated_at correctness
S0-06 Upload/import resource budgets
S0-07 Async route blocking HTTP
S0-08 Current-status documentation sync
```

如果本地代码已经修复：

```text
ALREADY_FIXED_CURRENT_WORKTREE
```

并给出代码 + 测试证据后跳到下一任务。

---

# 9. S0-01 — Canonical API Availability

## Goal

Canonical product API 不应因为 host 为：

```text
0.0.0.0
::
```

而整体不挂载。

检查：

```text
main.py
WORKBENCH_NODE_API_ENABLED
node_api_is_enabled_for_host()
app.include_router(...)
```

确认是否把：

```text
Project
Canvas
Collection
Prompt
Execution
normal Node/Graph application API
```

错误地与：

```text
privileged local-machine capability
```

绑定。

## Required Fix

只做 capability split。

不要重新设计 API。

目标语义：

```text
Canonical product API:
    normal product availability policy

Privileged local-machine API:
    local/authorized capability policy
```

## Required Tests

至少：

```text
127.0.0.1 => canonical Project/Canvas available
localhost => canonical Project/Canvas available
0.0.0.0 => canonical Project/Canvas available
:: => canonical Project/Canvas available
privileged-local APIs are not accidentally opened
```

## Non-Interference

不要：

```text
改变 Project payload
改变 Canvas payload
改 route URL
新增未来 auth architecture
```

本轮只建立最小 boundary seam。

---

# 10. S0-02 — Privileged Filesystem Boundary

检查：

```text
/api/storage-settings
/api/storage-files
/api/storage-files/{kind}/...
/api/storage-files/delete
```

以及类似：

```text
配置 host filesystem root
删除 host files
任意 local path 管理
```

## Goal

LAN / non-loopback 模式下：

```text
normal product API 可用
privileged host filesystem mutation 默认不可用
```

优先最小实现：

```text
loopback/local capability => allow
non-loopback without privileged capability => 403
```

## Important

不要在本任务实现完整未来账户系统。

如果项目已有 auth/capability seam，复用。

否则仅建立最小明确 seam。

---

# 11. S0-03 — Workflow Path Validation

检查：

```text
/api/generate
workflow_json
WORKFLOW_DIR
workflow_path_from_name()
```

如果存在：

```python
os.path.join(WORKFLOW_DIR, req.workflow_json)
```

直接使用用户值：

改为复用项目现有安全 resolver。

## Tests

```text
valid workflow => success
../x.json => reject
absolute path => reject
unexpected separator => reject
invalid extension => reject
```

不要创造第二套 path validator。

---

# 12. S0-04 — SafeRemoteFetch Boundary

## Goal

所有用户/Provider 可控 URL 下载进入一个共享安全 seam。

重点审计：

```text
/api/runninghub/upload-asset
/api/local-assets/import-urls
/api/download-output
/api/canvas-assets/download
fetch_remote_media_bytes()
```

复用已有 SSRF-safe 逻辑。

不要复制多份。

要求：

```text
http/https only
DNS resolution validation
reject loopback
reject private
reject link-local
reject multicast/reserved/unspecified
IPv4 + IPv6
validate every redirect
redirect limit
streamed byte budget
timeout
response close
```

## Non-Interference

不要改变：

```text
正常公网 URL 的成功行为
现有 response shape
provider integration contract
```

---

# 13. S0-05 — Revision / updated_at Correctness

检查：

```text
static/js/workbench/canvas/node-creation-client.js
```

如果存在：

```javascript
settings.canvas.updated_at = revision;
```

而 revision 来自：

```text
canvas_revision
```

则删除这种语义污染。

必须保持：

```text
revision = logical revision / CAS cursor
updated_at = timestamp/display metadata
```

revision 使用现有：

```text
onRevision
adoptCanvasRevision
revision cursor
```

机制。

## Tests

```text
creation result does not mutate updated_at
graph creation does not mutate updated_at
connection result does not mutate updated_at
revision still advances correctly
```

不要改变 Canvas 数据模型。

---

# 14. S0-06 — Upload / Import Resource Budgets

检查所有：

```python
await file.read()
response.content
base64.b64decode(...)
```

尤其：

```text
/api/ai/upload
/api/local-assets/upload
/api/asset-library/workflows/upload
/api/canvas-workflows/import
/api/local-assets/import-urls
```

复用项目已有：

```text
chunked read
SpooledTemporaryFile
per-file limit
aggregate request limit
```

模式。

## Goal

防止：

```text
先整文件进入 RAM
→ 再检查 size
```

## Required budgets

根据现有项目常量复用：

```text
per file
aggregate request
file count
raw zip
zip entry count
single uncompressed
total uncompressed
compression ratio
```

不要因为本任务修改产品允许的正常文件类型。

---

# 15. S0-07 — Blocking HTTP in Async Routes

查找：

```text
async def
```

调用链中直接：

```python
requests.get(...)
requests.post(...)
```

优先改为已有 async HTTP client。

如果没有合适 seam，最小过渡：

```python
await asyncio.to_thread(...)
```

## Non-Interference

保持：

```text
timeout
error mapping
response shape
fan-out behavior
partial failure behavior
```

---

# 16. S0-08 — Current Fact Documentation Sync

只修当前事实冲突。

检查：

```text
AGENT_NEXT_TASK.md
CURRENT_EXECUTION_STATUS.md
CURRENT_ARCHITECTURE.md
TASK_INDEX.md
```

目标：

```text
所有 current pointer 对当前 ACTIVE task 一致
```

## Critical

不要：

```text
改写未来 task card
重定义 R9 任务内容
重新排序 backlog
```

如果文档历史部分描述旧架构：

```text
保留历史
更新 current-state section
```

---

# 17. Stability Gate

全部 S0 完成后执行：

```bash
bash scripts/agent-verify.sh
```

以及项目已有 focused/regression tests。

必须报告：

```text
Python tests
JS syntax/tests
architecture guards
git diff --check
Canvas regression
Project regression
Execution regression
```

未执行不能写 PASS。

环境问题必须单独标：

```text
NOT_RUN_ENVIRONMENT
```

---

# 18. Decision Log Rule

如果 stabilization 中必须引入新的 shared seam，例如：

```text
CanonicalApiPolicy
PrivilegedCapability
SafeRemoteFetch
BoundedUploadReader
```

只记录“为什么这个 seam 存在”。

不要在 decision 中定义未来 R9 feature。

建议记录格式：

```text
Decision
Context
Current Bug
Minimal Boundary
Compatibility Guarantee
Explicit Non-Goals
Future Tasks Unchanged
```

---

# 19. Return-Control Rule / 完成后交还开发控制权

当：

```text
S0-01 ... S0-08
+
Stability Gate PASS
```

完成后：

本文件使命结束。

Codex 必须立即：

```text
1. 重新读取 AGENT_NEXT_TASK.md
2. 重新读取当前 ACTIVE Task Card
3. 重新读取 TASK_INDEX.md 中该任务依赖
4. 以 ACTIVE Task Card 为唯一 feature scope
5. 继续原任务开发
```

禁止继续按照本文件“推测”后续实现。

---

# 20. 对 R9-03 的特殊保护

如果当前 ACTIVE task 是：

```text
R9-03
```

S0 完成后：

```text
继续原始 R9-03 task card
```

本文件不自动扩大 R9-03 scope。

特别是：

```text
AssetVersionRef
Asset Repository
legacy asset migration
authorization
SQLite schema
```

都必须以当前 R9-03 task card + 当前代码为准。

如果 stabilization 发现未来需要决定 reference shape：

只记录：

```text
FUTURE_TASK_NOTE
```

除非当前 R9-03 本身明确要求冻结该 contract，否则不要因为本文件提前改。

---

# 21. 禁止长期影响后续开发的行为

本轮绝对禁止：

```text
修改未来 task card 的 Done 条件
修改 R9-04/R9-05 等业务定义
新增第三套 repository
新增第三套 task runtime
新增第三套 Canvas runtime
新增 legacy-compatible-but-new parallel API
为了修 bug 改大量 schema
为了修安全问题引入完整 auth 产品
为了减少 main.py 行数做无业务意义拆分
```

---

# 22. New Bug Handling

如果执行过程中发现新的 bug：

若属于当前 S0 task 的直接根因：

```text
允许一起最小修复
```

若与当前任务无关：

记录：

```text
DISCOVERED_ISSUE
severity:
file:
trigger:
root_cause:
recommended_task:
```

不要顺手修。

---

# 23. Output Format

每完成一个 S0 task，必须输出：

```text
TASK:
STATUS:

LOCAL BASELINE:
branch:
head:
dirty files preserved:

BUG CONFIRMED:
yes/no

ROOT CAUSE:

FILES CHANGED:

MINIMAL FIX:

PUBLIC CONTRACT CHANGED:
yes/no

FUTURE TASKS MODIFIED:
no

TESTS ADDED:

FOCUSED TEST RESULT:

FULL GATE RESULT:

DISCOVERED_ISSUES:

FUTURE_TASK_NOTES:

NEXT ACTION:
stop
```

默认 `NEXT ACTION` 必须是：

```text
stop
```

等待下一条用户/Codex 指令。

---

# 24. First Execution Instruction

第一次使用本文件时，Codex 执行：

```text
1. Read AGENTS.md
2. Read AGENT_NEXT_TASK.md
3. Read current ACTIVE task card
4. Record current branch / HEAD / git status
5. Do not edit future task cards
6. Validate whether S0-01 still exists
7. If already fixed:
      prove with code/tests
      mark ALREADY_FIXED_CURRENT_WORKTREE
      stop
8. If present:
      add focused regression test
      make minimal fix
      run focused tests
      run scripts/agent-verify.sh
      inspect git diff
      output required report
      stop
```

不要自动执行 S0-02。

---

# 25. Completion Contract

本文件的成功终态不是“开发更多功能”。

而是：

```text
Current product behavior remains compatible
Confirmed stabilization bugs are removed
Security boundaries are clearer
Regression tests exist
Current docs are coherent
Future task cards are untouched
Development returns to AGENT_NEXT_TASK.md
```

---

# 26. One-Sentence Rule

> 本文件只清理后续开发道路，不重新规划后续道路。
