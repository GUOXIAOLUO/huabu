# Agent Next Task

> This file is the single task-selection authority for coding agents.
> It does not replace `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Active Task

- Task ID: `R4-08`
- Round: `R4`
- Priority: `P0`
- Status: `READY`
- Task Card: `docs/tasks/backlog/R4-08-render-ownership-map.md`

## Completed Tasks

- `R4-07` — `DONE` 2026-09-06T19:00+08:00. Card:
  `docs/tasks/active/R4-07-remote-sync-revision.md`. Evidence: canonical meta
  probe + revision-bearing canvas_updated broadcast; remote-sync coordinator
  and update-message filter order by revision (timestamp fallback); adapters
  feed revisionOf() baselines; regression 329 tests PASS. Ownership matrix
  remote/version-polling row updated.

- `R4-06` — `DONE` 2026-09-06T18:40+08:00. Card:
  `docs/tasks/done/R4-06-browser-logical-revision.md`. Evidence: shared
  persistence client owns the logical-revision cursor and sends canonical CAS
  saves (`expected_revision`); sandbox tests prove load→save→conflict→recovery
  cursor chain and 503/legacy fallbacks; HTTP round-trip test proves CAS
  recovery; regression 323 tests PASS. Ownership matrix revision/CAS row
  updated.

- `R4-05` — `DONE` 2026-09-06T18:22+08:00. Card:
  `docs/tasks/done/R4-05-canonical-canvas-api.md`. Evidence: canonical
  transport `/api/v1/canvases/{canvas_id}` GET (revision/updated_at) + PUT
  (expected_revision CAS, explicit 409 conflict info, 503 without SQLite
  authority) in `workbench/api/canvases.py`; legacy transport shape pinned;
  regression 319 tests PASS. Ownership matrix revision/CAS row updated.

- `R4-04` — `DONE` 2026-09-06T18:10+08:00. Card:
  `docs/tasks/done/R4-04-split-brain-regression.md`. Evidence:
  `tests/test_split_brain_regression.py` — 5 incident-scenario tests (normal
  SQLite routing, refused disabled flag, legacy migration/read/write while
  inactive, restart-durable authority, one-store write isolation); regression
  313 tests PASS.

- `R4-03` — `DONE` 2026-09-06T17:59+08:00. Card:
  `docs/tasks/done/R4-03-split-brain-guard.md`. Evidence: explicit authority
  policy seam (`canvas_authority_policy.py`) + three-layer startup guard; live
  refusal of `WORKBENCH_CANONICAL_CANVAS_ROUTING_ENABLED=false` under
  `authority_state=sqlite` with exit 1 and byte-identical database
  (sha256 `3cca0054…`); recovery paths verified available; regression 308
  tests PASS. Ownership matrix Canvas-persistence row updated.

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
4. `docs/tasks/active/R4-07-remote-sync-revision.md`

Read architecture documents only as required by the card.

## Execution Rule

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

Expected successor if R4-08 passes:

`R4-09 — Render Runtime` (`docs/tasks/backlog/R4-09-render-runtime.md`)

Actual successor must still be checked against the repository's current verified state.
