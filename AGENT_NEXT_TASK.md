# Agent Next Task

> This file is the single task-selection authority for coding agents.
> It does not replace `docs/status/CURRENT_EXECUTION_STATUS.md`.

## Active Task

- Task ID: `R4-13`
- Round: `R4`
- Priority: `P1`
- Status: `READY`
- Task Card: `docs/tasks/backlog/R4-13-provider-compat-renderers.md`

## Completed Tasks

- `R4-12` — `DONE` 2026-09-06T21:28+08:00. Card:
  `docs/tasks/active/R4-12-generic-rendering.md`. Evidence: Classic prompt
  family cut over to registry-owned rendering (`prompt-card` renderer builds
  the card DOM inside NodeShell; page state behind rendererOptions callbacks;
  flags-off fallback preserved); behavioral pipeline + wiring contract tests;
  regression 339 tests PASS.

- `R4-11` — `DONE` 2026-09-06T21:05+08:00. Card:
  `docs/tasks/done/R4-11-media-rendering.md`. Evidence: runtime-owned
  media-state projection (`mediaState` capture on unmount / restore on mount),
  MediaRenderer elements carry the signature URL, page sweeps exclude
  shell-mounted cards; behavioral tests for all three; regression 337 tests
  PASS.

- `R4-10` — `DONE` 2026-09-06T20:25+08:00. Card:
  `docs/tasks/done/R4-10-group-rendering.md`. Evidence:
  `WorkbenchRenderRuntime.mountGroupCard` owns the Group mount contract
  (record assembly, media/legacy decision with `mediaEnabled:false` rollback,
  lifecycle, resolved shell view, empty-state hook); Classic group branch and
  Smart group batch delegate; behavioral + cutover contract tests; regression
  334 tests PASS.

- `R4-09` — `DONE` 2026-09-06T19:33+08:00. Card:
  `docs/tasks/done/R4-09-render-runtime.md`. Evidence:
  `WorkbenchRenderRuntime` owns the mounted-card lifecycle (keyed registry,
  ordered destroy on remount/unmount, batch mounting, canvas-load reset); both
  adapters inject the host mount once and route all five adoption mounts +
  delete flows through it; behavioral + wiring contract tests; regression 332
  tests PASS.

- `R4-08` — `DONE` 2026-09-06T19:20+08:00. Card:
  `docs/tasks/done/R4-08-render-ownership-map.md`. Evidence: rendering
  ownership map in `docs/plans/R4_OWNERSHIP_MATRIX.md` (per-family
  create/update/destroy/listener/media-state owners with file:line evidence,
  six adoption paths, next migration unit = mounted-card lifecycle); anchored
  by a source-contract test; regression 330 tests PASS.

- `R4-07` — `DONE` 2026-09-06T19:00+08:00. Card:
  `docs/tasks/done/R4-07-remote-sync-revision.md`. Evidence: canonical meta
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
4. `docs/tasks/active/R4-11-media-rendering.md`

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

Expected successor if R4-13 passes:

`R4-14 — Interaction Controller` (`docs/tasks/backlog/R4-14-interaction-controller.md`)

Actual successor must still be checked against the repository's current verified state.
