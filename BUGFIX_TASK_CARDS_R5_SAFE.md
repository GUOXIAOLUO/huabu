# HUABU Bugfix Task Cards — R5 Safe Edition

> 直接交给 Codex / Codex Harness 执行。
>
> **核心约束**
> - 真正项目仓库在本地电脑，本地工作区是唯一事实源。
> - GitHub `GUOXIAOLUO/huabu` 仅用于备份、审计参考和历史对照。
> - 不允许为了匹配 GitHub 备份而回退、覆盖或重建本地项目。
> - 目标：修复已确认 Bug，同时不打断现有任务卡开发，并确保修复后可继续进入 R5。

## A. Codex 强制执行规则

### A1. 开始前只确认本地状态

```bash
pwd
git rev-parse --show-toplevel
git status --short
git branch --show-current
git rev-parse HEAD
```

只记录，不改变工作区。

### A2. 禁止操作

除非用户单独明确授权，禁止：

```text
git pull
git reset
git reset --hard
git checkout .
git restore .
git clean
git stash
git rebase
git merge
git commit
git push
git force-push
自动切换分支
自动删除未跟踪文件
```

GitHub 备份不是开发基线，不得用 GitHub HEAD 覆盖本地代码。

### A3. 保护本地持续开发

若目标文件已有未提交修改：

1. 先读取本地当前实际代码。
2. 判断该 Bug 在本地最新版是否仍存在。
3. 只改 Bug 所需最小 hunk。
4. 保留所有与本卡无关修改。
5. 禁止整文件替换，除非该文件本身就是本卡新建测试文件。
6. 完成后执行：

```bash
git diff -- <本卡涉及文件>
```

如果无法安全区分“正在开发的修改”和“Bug 修复修改”：

```text
STATUS = BLOCKED_BY_LOCAL_CHANGES
```

停止该卡，不回滚、不覆盖。

### A4. 本地已修复

如果审计时存在，但本地后续开发已经修复：

```text
STATUS = ALREADY_FIXED
```

必须用回归测试证明，然后跳到下一卡，不重复改写。

### A5. 一次只执行一张卡

```text
确认 Bug
→ 写/补回归测试
→ 证明旧行为错误
→ 最小修复
→ 定向测试
→ 相关模块测试
→ 全量 Gate
→ git diff 检查
→ 输出报告
→ 下一卡
```

### A6. 禁止顺手重构

Bugfix 阶段禁止：

- UI 重设计
- 目录重构
- 全局格式化
- 大规模 rename
- API 重构
- payload schema 重构
- DB schema migration
- 依赖大版本升级
- 无关性能优化
- 无关架构调整

## B. 每张卡统一结果格式

```text
TASK:
STATUS: FIXED / ALREADY_FIXED / BLOCKED_BY_LOCAL_CHANGES / BLOCKED / FAILED

LOCAL_REPO:
LOCAL_BRANCH:
STARTING_HEAD:

PREEXISTING_LOCAL_CHANGES:
CHANGED_FILES:

ROOT_CAUSE:
FIX:
REGRESSION_TESTS:

TARGETED_TEST_RESULT:
RELATED_TEST_RESULT:
FULL_GATE_RESULT:

COMPATIBILITY:
- API contract:
- payload schema:
- DB schema:
- existing local changes preserved:
- unrelated feature behavior preserved:

REMAINING_RISK:
NEXT_TASK:
```

# C. R4.5 Stability Gate / R5 前置 Bugfix

## B1-01 — SQLite Compatibility CAS 并发丢更新

**Priority:** P1
**Category:** Data Loss

参考文件：

```text
workbench/repositories/sqlite_canvas_compatibility_repository.py
workbench/repositories/sqlite_project_canvas_repository.py
tests/test_sqlite_canvas_compatibility_repository.py
```

问题模式：

```text
读取旧 payload
→ 另一 writer 写入新 revision
→ 当前 writer 再读取新 revision
→ 用旧 payload + 新 revision 做 CAS
→ 另一 writer 数据被静默覆盖
```

目标：

- payload 与 revision 必须来自同一个数据库 snapshot。
- 后续 replace 必须使用该 snapshot 的 revision。
- 若并发写发生，必须产生 stale。
- 不修改 API response schema。
- 不修改 Canvas payload schema。
- 不做 DB migration。

推荐边界：

```python
snapshot = repository.load_canvas_snapshot(canvas_id)
# snapshot.payload
# snapshot.revision
```

若 `expected_updated_at` 明确提供：

```text
expected != current
→ stale
```

但保留本地现有 `None/0` 的兼容语义。

必须测试：

```text
test_compat_save_if_current_rejects_interleaved_write
test_compat_mutate_if_current_rejects_interleaved_write
test_future_expected_updated_at_is_rejected
```

真实模拟：

```text
A snapshot revision=N
B 写入 N+1
A 基于旧 snapshot 写入
→ A stale
→ B 数据仍存在
```

## B1-02 — Remote update 不得清空本地 dirty

**Priority:** P1
**Category:** Data Loss

参考：

```text
static/js/workbench/canvas/canvas-session.js
static/js/workbench/canvas/canvas-remote-sync.js
static/js/workbench/canvas/canvas-update-message.js
```

任务要求：

- remote notification 不得清空 `dirty`
- 不得取消本地 scheduled save
- in-flight save 时只允许延迟 remote sync
- 真正 CAS conflict 走现有 conflict path
- 不自动用远端 payload 覆盖本地未保存图

测试：

```text
test_remote_update_does_not_clear_dirty_state
test_remote_update_does_not_cancel_scheduled_save
test_remote_update_during_inflight_save_is_deferred
test_remote_update_applies_after_local_state_is_safe
```

## B1-03 — 实现真正 Save Drain

**Priority:** P1
**Category:** Data Loss

参考：

```text
static/js/workbench/canvas/canvas-save-scheduler.js
static/js/workbench/canvas/canvas-session.js
```

目标语义：

```text
schedule() = debounce
flush()    = 立即推进一次保存
drain()    = 等 scheduler 完全静止
cancel()   = 取消尚未执行的可取消 timer
```

`drain()` 返回前必须：

```text
no debounce timer
no retry timer
no in-flight save
no pending again
```

关闭：

```text
停止 remote apply
→ drain 当前 Canvas
→ 再清 session
```

切换 A → B：

```text
drain A
→ A 安全落盘
→ 再 load B
```

测试：

```text
test_close_waits_for_inflight_save
test_close_waits_for_pending_retry
test_open_new_canvas_drains_previous_canvas
test_scheduler_drain_waits_until_quiescent
test_scheduler_cancel_does_not_leave_untracked_retry
```

## B2-01 — revision / updated_at 完全分离

**Priority:** P2
**Category:** Data Consistency

参考：

```text
static/js/workbench/canvas/canvas-persistence-client.js
static/js/workbench/canvas/canvas-session.js
static/js/workbench/canvas/canvas-app-state.js
```

要求：

- revision 只进入 `revisionCursors`
- 不得因为 adopt revision 修改 `canvas.updated_at`
- 不得因为 adopt revision 修改 `session.updatedAt`
- 只有服务器返回真实 timestamp 才更新 timestamp

测试：

```text
test_adopt_revision_does_not_change_updated_at
test_revision_cursor_advances_independently
test_server_updated_at_remains_timestamp
test_versioned_write_does_not_corrupt_display_time
```

## B3-01 — API/.env 停止 Git 跟踪但保留本地文件

**Priority:** P1/P2
**Category:** Secret Safety

**禁止删除本地真实 `API/.env`。**

检查：

```bash
git ls-files -- API/.env
git check-ignore -v API/.env || true
```

若仍 tracked：

```bash
git rm --cached -- API/.env
```

只移除 index，不删除物理文件。

禁止：

- 打印 secret
- 输出 secret 内容
- 上传 secret
- 把真实值写入 `.env.example`

验收：

```bash
test -f API/.env
git ls-files -- API/.env
git check-ignore -v API/.env
```

要求：

```text
本地文件存在
git ls-files 无输出
ignore rule 生效
```

## B4-01 — RunningHub upload-asset SSRF + 下载上限

**Priority:** P1/P2
**Category:** Security

目标：

- 仅 http/https
- 校验 hostname
- DNS resolve 后拒绝 loopback/private/link-local/multicast/unspecified/reserved
- IPv4/IPv6 都检查
- redirect 每跳重新验证
- redirect 次数限制
- streaming download
- 最大下载 bytes
- 超限中止
- 不整响应一次性进入 RAM

测试：

```text
reject localhost
reject 127.0.0.1
reject ::1
reject RFC1918
reject link-local
reject redirect_to_private_address
reject oversized_response
accept_normal_public_asset
```

网络测试使用 mock。

## B5-01 — SQLite foreign_keys=ON

每个 SQLite connection：

```sql
PRAGMA foreign_keys = ON;
```

测试：

```text
test_sqlite_connections_enable_foreign_keys
test_invalid_foreign_key_write_is_rejected
```

若发现已有 FK-invalid 历史数据，不自动删除，标记 BLOCKED 并报告。

## B5-02 — malformed 时间字段不得变 500

非法用户输入时间字段应转换成正常 4xx validation error，不得吞掉真实数据库异常。

测试：

```text
malformed_deleted_at_returns_4xx
valid_time_still_works
```

## B6-01 — Legacy JSON 原子写

目标：

```text
same-dir temp
→ write
→ flush
→ fsync
→ os.replace
```

测试：

```text
successful_atomic_replace
failed_write_preserves_previous_file
temp_cleanup
```

## B6-02 — Legacy Canvas ID 碰撞

若 filename 通过删除非法字符生成，`a/b` 与 `ab` 可能碰撞。

新请求应拒绝非法 ID，不要直接更换所有旧 filename mapping。

若发现历史非法 ID：

```text
STATUS = BLOCKED
```

先报告，不自动迁移。

## B7-01 — WebSocket multi-socket / ghost connection

建议数据结构：

```text
client_id -> Set[WebSocket]
socket -> client_id
```

正常断开和发送失败统一 cleanup。

测试：

```text
same_client_two_sockets
disconnect_one_keeps_other
last_disconnect_removes_client
send_failure_cleans_reverse_maps
no_ghost_presence
```

禁止改变 WebSocket message schema。

## B8-01 — /api/upload 内存上限

要求：

```text
chunked read
per-file limit
request total limit
413 on limit
temp cleanup
```

测试：

```text
normal_upload
single_file_over_limit
multi_file_total_over_limit
cleanup_after_failure
```

## B8-02 — Workflow ZIP Bomb 防护

限制：

```text
raw zip size
entry count
single entry uncompressed bytes
total uncompressed bytes
compression ratio
```

在真正解包前检查 metadata。

测试：

```text
too_many_entries
oversized_single_entry
oversized_total
extreme_compression_ratio
normal_workflow_zip
```

# D. 修复顺序

```text
B1-01
B1-02
B1-03
B2-01
B3-01
B4-01
B5-01
B5-02
B6-01
B6-02
B7-01
B8-01
B8-02
```

B1 全部 PASS 后再进入 B2。

# E. Compatibility Gate

每个 Batch 完成后验证：

```text
Canvas open
Canvas edit
Canvas save
rapid edit
rapid canvas switch
reload
```

不得意外改变：

```text
API URL
request fields
response fields
Canvas payload schema
Node payload schema
WebSocket message schema
DB schema
```

不得：

```text
删除 Canvas
重建 SQLite
清空 JSON fallback
覆盖 .env
自动迁移未知 legacy data
覆盖用户未提交代码
```

# F. 全量验证 Gate

优先：

```bash
bash scripts/agent-verify.sh
```

若本地已调整，以本地当前验证入口为准。

最低：

```bash
python -m compileall .
python -m pytest
```

并执行仓库现有 Node / JS runtime checks。

# G. R5 Readiness Gate

完成必要 Bugfix 后：

```text
R5_READINESS = PASS / FAIL
```

只有全部满足才 PASS：

```text
P1 数据丢失 Bug = 0
B1-01 PASS
B1-02 PASS
B1-03 PASS
B2-01 PASS
关键安全问题已处理或明确隔离
全量 Gate PASS
Canvas open/edit/save PASS
Canvas switch PASS
API contract 未破坏
payload schema 未破坏
DB schema 未意外改变
本地已有开发内容完整保留
没有自动 commit/push
没有使用 GitHub 备份覆盖本地项目
```

低风险 P2 如暂时无法安全修，可登记 `REMAINING_RISK`；但 P1 Data Loss 未清零：

```text
R5_READINESS = FAIL
```

# H. R5 Readiness 最终报告模板

```markdown
# R5 Readiness Report

## Local project
- path:
- branch:
- starting HEAD:
- ending HEAD:
- pre-existing working tree changes preserved:

## Bugfix status
| Task | Status | Files | Tests |
|---|---|---|---|

## Regression gate
- compile:
- pytest:
- node/js:
- agent-verify:

## Compatibility
- Canvas open:
- Canvas edit:
- Canvas save:
- Canvas switch:
- API contract:
- WebSocket contract:
- payload schema:
- DB schema:
- Legacy fallback:

## Git safety
- no pull/reset/checkout overwrite:
- no stash:
- no auto commit:
- no auto push:
- GitHub used only as reference:

## Remaining risks
- ...

## Final
R5_READINESS = PASS / FAIL

## Next action
If PASS:
Continue existing R5 task cards from the local project's current state.
Do not reset or rebase to the GitHub backup baseline.
```

# I. 直接给 Codex 的启动指令

```text
请严格按照 BUGFIX_TASK_CARDS_R5_SAFE.md 执行。

这是正在持续开发的本地真实项目。
GitHub GUOXIAOLUO/huabu 仅是备份和审计参考，不是真实开发基线。

强制要求：
1. 本地当前工作区是唯一事实源。
2. 不 pull、不 reset、不 checkout/restore 覆盖、不 clean、不 stash。
3. 不自动 commit、不自动 push、不自动切分支。
4. 保留当前所有与任务无关的未提交开发修改。
5. 一次只执行一张 Bug 卡。
6. 每张卡先确认 Bug 在本地仍存在，再补回归测试，再做最小修复。
7. 如果本地已经修复，验证后标记 ALREADY_FIXED，不重复改。
8. 如果无法安全避开正在开发的本地修改，标记 BLOCKED_BY_LOCAL_CHANGES，不强行修改。
9. 每张卡都必须跑定向测试、相关测试和完整 Gate。
10. 修复 Bug 不得顺手重构、不改无关 UI、不改变 API/payload/DB schema，除非卡片明确要求。
11. 从 B1-01 开始，B1 全部通过后再进入 B2。
12. 完成必要修复后执行 R5 Readiness Gate。
13. 只有 R5_READINESS = PASS 后，才继续现有 R5 任务卡开发。
14. R5 必须从本地当前状态继续，绝不能回退到 GitHub 备份版本。
```
