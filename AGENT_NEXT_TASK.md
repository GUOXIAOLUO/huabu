# Agent Next Task

> This file is the single task-selection authority for coding agents.
> It does not replace `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Active Task

- Task ID: `R4-03`
- Round: `R4`
- Priority: `P0`
- Status: `READY`
- Task Card: `docs/tasks/active/R4-03-split-brain-guard.md`

## Completed Tasks

- `R4-02` — `DONE` 2026-09-06T17:37+08:00. Card:
  `docs/tasks/done/R4-02-sqlite-legacy-reconcile.md`. Evidence: read-only
  reconciliation of `data/canvases` (23 files) vs `data/workbench.sqlite3`
  (23 rows, 17 active) — 0 legacy-only, 0 sqlite-only, 23/23 payload
  comparisons matched, 0 unexpected rows, authority `sqlite`, database
  byte-identical (sha256 `3cca0054…`) before/after; regression 297 tests PASS.
  Report: `data/r4-canvas-reconciliation-report.json`.

- `R4-01` — `DONE` 2026-09-06T17:07+08:00. Card archived at
  `docs/tasks/done/R4-01-local-truth.md`. Evidence: verified HEAD
  `f764ce134e9496ba753fcb60943a0bbbbc2c2558` on `main`; baseline 294 tests PASS;
  `./scripts/agent-verify.sh` PASS; recorded in
  `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Required Reads

1. `AGENTS.md`
2. `.agent/AGENT_CONTRACT.md`
3. `docs/status/CURRENT_EXECUTION_STATUS.md`
4. `docs/tasks/active/R4-03-split-brain-guard.md`

Read architecture documents only as required by the card.## Execution Rule

Execute **exactly this one card**.

Do not start the next task.

## Completion Rule

After implementation / verification:

1. update current status evidence;
2. update ownership matrix only if ownership changed;
3. set this card status to `DONE` only when its DoD is actually satisfied;
4. write the recommended next card here, but do **not** execute it;
5. stop.

## Recommended Successor

Expected successor if R4-03 passes:

`R4-04 — Split-Brain Regression` (`docs/tasks/backlog/R4-04-split-brain-regression.md`)

Actual successor must still be checked against the repository's current verified state.
