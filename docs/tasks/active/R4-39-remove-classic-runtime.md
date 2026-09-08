# CARD R4-39 — Remove Legacy canvas.js Product Runtime

- Round: R4
- Priority: P0
- Status: IN_PROGRESS
- Activated: 2026-09-08
- Depends on: R4-38

## Goal

Replace the old Classic monolith with a small neutral bootstrap.

The card begins with a dependency-grounded residual-runtime inventory. Deletion
is not authorized merely because R4-38 moved named bodies into Classic seams:
the seams still require page-owned state and host operations from `canvas.js`.
Each removal wave must first establish a real replacement owner and browser
parity, then delete the corresponding Classic ownership.

## Before Owner

canvas.js monolith

## After Owner

small canvas-app bootstrap

## In Scope

- Move remaining legitimate bootstrap wiring.
- Delete monolithic business/runtime code.
- Verify legacy records.

## Out of Scope

- No new bootstrap monolith.

## Execution Pattern

```text
characterize
→ focused test
→ establish seam
→ implement/migrate
→ verify
→ remove duplicate ownership
```

## Wave plan

- [x] Wave 1 — characterize the residual runtime and add an executable close
  gate. Evidence: `docs/plans/R4_39_CLASSIC_RUNTIME_REMOVAL.md` and
  `tests/test_r4_39_classic_runtime_removal.py`.
- [x] Wave 2 — neutral application bootstrap / record-open orchestration.
  `WorkbenchCanvasAppBootstrap.create(host)` exposes one frozen `start()`
  interface and owns initialization order plus Canvas/list routing; canvas.js
  retains only the host adapter and `window.onload` delegation. Behavioral VM
  coverage and default/all-zero isolated browser acceptance pass; the fixture
  renders four nodes on both paths and the canonical-store copy is unchanged.
- [x] Wave 3 — state, persistence and remote-polling ownership.
  `WorkbenchCanvasSession` now owns record open/save/sync/close, dirty and
  in-flight state, revision adoption, remote polling and update-message
  deferral. The page retains only serialization and render projection adapters.
  Stale 409 responses no longer advance the CAS cursor or auto-retry an
  unchanged payload.
- [ ] Wave 4 — interaction, render and graph/group lifecycle ownership.
  Slice 1 (2026-09-08) done: the residual page-owned window mouse-slot
  assignments (LLM pane resize, box selection, selection-link drag, knife
  drag) now begin through the InteractionController session lifecycle and the
  cleanup sites (finishSelection, endDrag, blur guard) unwire through
  `controller.end()`; no direct `window.onmousemove`/`window.onmouseup`
  assignment remains in `canvas.js`. Slice 2 (2026-09-08) done: the move-driven
  group-membership transition (containment detection, membership add/remove,
  generator-edge handoff) moved into the shared
  `WorkbenchCanvasGroupMembership.resolveMembershipTransition`; the page keeps
  type pairs, geometry, eligibility/connect policy and side effects only.
  Slice 3 (2026-09-08) done: `WorkbenchCanvasRenderSweep` delegates
  mounted-card reconciliation to `WorkbenchRenderRuntime`, which owns
  teardown-before-build, remote-node removal, failed-build cleanup and clear.
  Classic graph-connect admission and its generator/media-output
  classifications now live in `WorkbenchLegacyGraphCompatibility`; the page
  retains only the adapter call. Focused behavior covers partial refresh versus
  full-sweep fallback, all-node lifecycle cleanup, and historical connection
  admission. Default and all-zero browser acceptance rendered the 15-node
  fixture and verified repeated full/partial LTX editor rebuilds without
  console errors. Slice 4 (2026-09-08) done: selected image/prompt grouping
  now delegates child-to-generator edge handoff to
  `WorkbenchCanvasGroupMembership.handoffChildEdgesToGroup`, reusing the same
  transition owner as move-driven membership. The page retains group creation,
  selection and save/render effects only. Focused behavior covers idempotent
  edge removal/re-parenting and page delegation. Remaining graph/group
  mutation clusters remain. Slice 5 (2026-09-08) done: versioned ordinary
  connection commits now project the returned edge, undo snapshot and canvas
  revision through `WorkbenchNodeClient.applyConnectionResult`; the page keeps
  compatibility side effects, save and render only. Rollback mode remains the
  explicit raw legacy adapter. Slice 6 (2026-09-08) done: single-node
  deletion projections now use the shared
  `WorkbenchCanvasGraphFragment.removeGraphRecords` path across raw and
  versioned adapters; the page retains undo, selection, render and save
  effects. Slice 7 (2026-09-08) done: link deletion now uses the same shared
  graph-fragment owner for connection projection.
  Slice 8 (2026-09-08) done: output-to-input-group replacement and grouped
  upload replacement now reuse the same node/incident-edge projection owner.
  Slice 9 (2026-09-08) done: Alt-drag duplication now delegates subgraph
  cloning and optional incoming-edge projection to the shared graph-fragment
  owner; the page retains only insertion and compatibility admission effects.
  Slice 10 (2026-09-08) done: workflow-transfer modal lifecycle and selection
  metadata now live in `WorkbenchCanvasWorkflowTransferUi`; the page retains
  payload construction, import/export actions and Canvas state callbacks.
  Slice 11 (2026-09-08) done: Classic crop/grid/resize math now delegates to
  `WorkbenchCanvasMediaTools`; the page retains DOM state and media mutation.
  Slice 12 (2026-09-08) done: prompt-template naming, text composition,
  search filtering and default-name derivation now use the neutral
  `WorkbenchCanvasPromptTemplateData` module.
  Slice 13 (2026-09-08) done: prompt-template category-label resolution now
  uses the same neutral data owner for system and remote libraries.
  Slice 14 (2026-09-08) done: image-editor Grid layout metadata now delegates
  to `WorkbenchCanvasMediaTools`.
  Slice 15 (2026-09-08) done: workflow export filename sanitization and
  timestamp formatting now use `WorkbenchCanvasWorkflowTransfer`.
  Slice 16 (2026-09-08) done: image-editor mode normalization and presentation
  mapping now use `WorkbenchCanvasMediaEditorState`.
- [ ] Wave 5 — prompt/workflow/media-editing compatibility UI ownership.
- [ ] Wave 6 — replace the wide Classic seam host, delete `canvas.js`, and run
  default plus rollback browser acceptance.

## Focused Tests

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Wave 2 verification (2026-09-08): PASS — 367 Python tests, 77 Python AST
files, 85 JavaScript files, 4 architecture guards, and clean diff check.

Wave 3 verification (2026-09-08): PASS — focused session/CAS behavior, default
and all-zero browser reads across remote-poll intervals, 368 Python tests, 77
Python AST files, 86 JavaScript files, 4 architecture guards, and clean diff
check. The isolated SQLite copy remained byte-identical.

Wave 4 slice 1 verification (2026-09-08): PASS — residual pointer-session
cutover pinned by source contract plus controller behavior test; full
`./scripts/agent-verify.sh`: PASS (369 tests; Python AST 77 files; JavaScript
syntax 86 files; architecture guards 4; diff check clean).

Wave 4 slice 2 verification (2026-09-08): PASS — membership-transition
behavior test over the real shared module plus delegation wiring contract;
focused frontend suite PASS (122 tests); full `./scripts/agent-verify.sh`:
PASS (371 tests; Python AST 77 files; JavaScript syntax 86 files;
architecture guards 4; diff check clean).

Wave 4 slice 3 verification (2026-09-08): PASS — 131 focused frontend and
R4-39 lifecycle tests; default/all-zero isolated browser acceptance over the
15-node Classic fixture; full `./scripts/agent-verify.sh`: PASS (376 tests,
78 Python AST files, 87 JavaScript files, 4 architecture guards, clean diff
check).

Wave 4 slice 4 verification (2026-09-08): PASS — shared group-input handoff
behavior and delegation coverage; full `./scripts/agent-verify.sh`: PASS (377
tests, 78 Python AST files, 87 JavaScript files, 4 architecture guards, clean
diff check).

Wave 4 slice 6 verification (2026-09-08): PASS — shared graph-record removal
behavior and page coverage across all single-node deletion paths; full
`./scripts/agent-verify.sh`: PASS (379 tests, 78 Python AST files, 87
JavaScript files, 4 architecture guards, clean diff check).

Wave 5 slice 2 verification (2026-09-08): PASS — crop ratio, crop fitting,
grid splitting, resize clamping and circled-label behavior through the shared
media-tools module; full `./scripts/agent-verify.sh`: PASS (380 tests, 78
Python AST files, 88 JavaScript files, 4 architecture guards, clean diff
check).

Wave 5 slice 3 verification (2026-09-08): PASS — prompt-template projection
and filtering behavior through the neutral data module; full
`./scripts/agent-verify.sh`: PASS (381 tests, 78 Python AST files, 89
JavaScript files, 4 architecture guards, clean diff check).

Wave 5 slice 4 verification (2026-09-08): PASS — image-resize dimensions now
delegate to the shared media-tools math owner; full `./scripts/agent-verify.sh`:
PASS (381 tests, 78 Python AST files, 89 JavaScript files, 4 architecture
guards, clean diff check).

Wave 5 slice 5 verification (2026-09-08): PASS — prompt-template category
label behavior through the neutral data module; full `./scripts/agent-verify.sh`:
PASS (381 tests, 78 Python AST files, 89 JavaScript files, 4 architecture
guards, clean diff check).

Wave 5 slice 6 verification (2026-09-08): PASS — Grid layout metadata
projection through the shared media-tools module; full
`./scripts/agent-verify.sh`: PASS (381 tests, 78 Python AST files, 89
JavaScript files, 4 architecture guards, clean diff check).

Wave 5 slice 7 verification (2026-09-08): PASS — workflow export filename
projection behavior through the shared transfer client; full
`./scripts/agent-verify.sh`: PASS (382 tests, 78 Python AST files, 89
JavaScript files, 4 architecture guards, clean diff check).

Wave 4 slice 5 verification (2026-09-08): PASS — shared connection-result
projection behavior covers endpoint validation, undo retention, revision
adoption and commit callback; full `./scripts/agent-verify.sh`: PASS (378
tests, 78 Python AST files, 87 JavaScript files, 4 architecture guards, clean
diff check).

Wave 4 slice 7 verification (2026-09-08): PASS — shared connection-removal
projection and page wiring; full `./scripts/agent-verify.sh`: PASS (379 tests,
78 Python AST files, 87 JavaScript files, 4 architecture guards, clean diff
check).

Wave 4 slice 8 verification (2026-09-08): PASS — graph-fragment projection
coverage for output conversion and grouped upload replacement; full
`./scripts/agent-verify.sh`: PASS (379 tests, 78 Python AST files, 87
JavaScript files, 4 architecture guards, clean diff check).

Wave 4 slice 9 verification (2026-09-08): PASS — shared Alt-drag subgraph
duplication behavior and page wiring; full `./scripts/agent-verify.sh`: PASS
(379 tests, 78 Python AST files, 87 JavaScript files, 4 architecture guards,
clean diff check).

Wave 5 slice 8 verification (2026-09-08): PASS — media-editor mode
normalization/presentation behavior through the neutral state module; full
`./scripts/agent-verify.sh`: PASS (383 tests, 78 Python AST files, 90
JavaScript files, 4 architecture guards, clean diff check).

Wave 5 slice 1 verification (2026-09-08): PASS — workflow-transfer modal
open/close and metadata behavior through the neutral UI module; full
`./scripts/agent-verify.sh`: PASS (380 tests, 78 Python AST files, 88
JavaScript files, 4 architecture guards, clean diff check).

## Definition of Done

- [ ] No Classic product runtime remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-40`

Do not execute the next card in the same Agent run.
