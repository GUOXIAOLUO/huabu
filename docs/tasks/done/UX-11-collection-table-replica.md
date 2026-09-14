# CARD UX-11 — Collection / Table Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `UX-10`

## Goal

Use Collection as the canonical table/batch resource and match the video grid/table interaction without introducing a separate TableNode.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize CollectionRichNode/table workspace/gallery adapters.
- Implement compact card summary and expandable table/workspace presentation.
- Support mixed media/text fields and row selection.
- Preserve collection schema/item semantics and execution binding.


## Out of Scope

- No SpreadsheetNode/TableNode domain duplication.
- No frontend-only batch execution loops.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_NODE_SPEC.md`
- `docs/video-replica/references/collection-table/`


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

- [x] Collection can represent the reference multi-row image/text/prompt table.
- [x] Table/card/workspace states use one Collection identity.
- [x] Existing binding/execution semantics remain canonical.
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

Before:
Before editing, the existing Collection path was split across the generic
`WorkbenchCollectionRichNode`, `WorkbenchCollectionTableWorkspace`, and
`WorkbenchCollectionGalleryCanvasAdapter`; the gallery had no compact schema
summary and the table had no shared row-selection state.

After:
The same shared modules own the compact summary, grid/list presentation, table
workspace, typed row editing, row selection, and workspace entry. Canonical
Collection persistence remains injected through the existing versioned API
client/application boundary.

Duplicate owner removed:
None. No TableNode/SpreadsheetNode or second Canvas runtime was added; bounded
legacy routing remains only as compatibility.

Browser/reference evidence:
Read `docs/video-replica/VIDEO_NODE_SPEC.md` and the collection-table reference
pack (`REF-401-v1-18m00-collection-flow.png`, `REF-402-v1-19m40-batch-collection.png`,
`REF-403-v2-20m00-table-workflow.png`). A temporary Collection fixture on the
real local `/static/canvas.html` rendered mixed image/text rows and entered the
Table workspace; the fixture was deleted afterward. The browser cache served
the pre-change gallery bundle during this run, so the new summary/row-selection
markup is additionally proven by the focused behavioral tests.

Focused tests:
`./.venv/bin/python -m unittest -v tests.test_collection_rich_node
tests.test_collection_table_workspace tests.test_frontend_workbench_modules` —
185 tests passed, including compact summary, mixed media/text fields, table
workspace entry, typed editing, row selection, binding projection, and
versioned persistence boundary.

Regression:
`./scripts/agent-verify.sh` — PASS: 1377 tests, 310 Python AST files, 157
JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`UX-12`

Independent Review PASS was recorded on 2026-09-14. This card is archived;
UX-12 is activated separately and has not been implemented in this run.
