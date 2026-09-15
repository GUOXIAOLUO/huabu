# CARD UX-12 — Result Workspace Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-15
- Depends on: `UX-11`

## Goal

Unify ResultTray/Preview/Compare/Selection/Collection/Materialization into the video-style result experience.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Inventory existing result runtimes and ownership seams.
- Create a coherent compact card + expanded/workspace result presentation.
- Expose preview, compare, select/rate, collect and materialize actions without duplicating result state.
- Verify multiple result types.


## Out of Scope

- No new result data model.
- Do not move approval/frozen lifecycle earlier than R11.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_NODE_SPEC.md`
- `docs/video-replica/references/result-workspace/`


`ARCHITECTURE_GUARDRAILS.md` applies to every UX card even when not repeated above.

## Implementation Steps

1. Characterize current behavior and ownership.
2. Add or update focused tests before/with the change.
3. Establish or reuse the canonical shared seam.
4. Implement only this card's visual/interaction responsibility.
5. Verify browser behavior against the cited references.
6. Remove duplicate ownership only when replacement is proven.
7. Update evidence/status, then stop. Do not execute the next card in the same Agent run.

## Compatibility / Migration

- Preserve existing saved projects, node records, execution semantics, resource identity and provider credentials.
- Prefer presentation-layer changes over domain/schema changes unless this card explicitly requires otherwise.
- Classic/legacy code may remain as a bounded compatibility seam until its replacement is proven by focused + browser acceptance tests.
- Never introduce a second Canvas runtime or a UI-only source of truth.

## Focused Tests

- Add/run the smallest behavioral tests proving this card's goal and ownership boundary.
- Add source-contract tests only where they protect a real architecture boundary; do not substitute string tests for behavior.
- Run browser acceptance for the states named in this card.

## Regression

Run the repository regression gate required by the active repository contract (currently `./scripts/agent-verify.sh`). If the repository contract changes by the time this card activates, follow the then-current active contract.

## Definition of Done

- [x] Result features appear as one coherent experience.
- [x] Existing Result runtime remains source of truth.
- [x] Compare/select/materialize flows pass focused and browser acceptance tests.
- [x] `AGENT_NEXT_TASK.md` still authorizes only this card during implementation.
- [x] No next card or later Round was implemented in the same Agent run.
- [x] Focused tests and regression gate results are recorded with evidence.

## Rollback

Revert only this card's bounded presentation/interaction change or re-enable the prior bounded compatibility seam. Do not roll back unrelated completed Round work or reset unknown local changes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md` with verified evidence required by the current task lifecycle.
- Update this card's status/evidence according to the repository's current task lifecycle.
- Update `AGENT_NEXT_TASK.md` only as permitted by the repository's independent Review/activation procedure.
- Do not rewrite architecture documents merely to describe visual changes unless ownership actually changed.

## Final Ownership Evidence

Before: `result-tray-runtime.js`, `result-preview-runtime.js`, `result-compare-runtime.js`, `result-selection-runtime.js`, `result-collection-runtime.js` and `result-materialization-runtime.js` each owned separate presentation hosts. `NodeShell` only composed them independently, and the Canvas task adapter exposed selection separately.

After: `result-workspace-runtime.js` is the shared Workbench presentation owner for navigation and composition. It delegates result state and actions to the existing six runtimes; `NodeShell`/`NodeCardHost` mount it as the task-card workspace.

Duplicate owner removed: no result domain/repository/service/runtime was added. The standalone selection host is suppressed when the unified workspace is present; legacy individual options remain available for callers without the workspace.

Browser/reference evidence: required result-workspace references `REF-301` through `REF-304` were read. A temporary local Canvas fixture rendered the unified workspace with two results; Preview showed `Preview A`, Compare opened, and Select / rate showed the persisted preference row and Save as asset. The fixture was deleted afterward and no user project was mutated.

Focused tests: `./.venv/bin/python -m unittest -v tests.test_ux12_result_workspace_replica tests.test_result_tray_runtime tests.test_result_preview tests.test_result_compare tests.test_result_selection tests.test_result_collection tests.test_result_materialization tests.test_frontend_workbench_modules` — 313 tests passed. The repair additionally pins that persisted result items initialize the existing Tray state, so Grid does not report zero staged results for a populated workspace.

Regression: `./scripts/agent-verify.sh` — PASS: 1379 tests, 311 Python AST files, 158 JavaScript files, 4 architecture guards, clean `git diff --check`.

## Next Recommended Card

`UX-13`

Do not execute the next card in the same Agent run.
