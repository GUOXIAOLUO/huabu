# CARD UX-06 — Node Picker

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `UX-05`

## Goal

Introduce the searchable creation picker used by empty-space and connection-driven node creation.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize current quick-add/hard-coded creation menus.
- Project CreationCatalog/Definition metadata into a searchable picker.
- Support category, title, keywords, description, package and compatibility metadata.
- Keep creation routed through canonical NodeCreationService.


## Out of Scope

- Do not hardcode WholeHouse nodes into Canvas source.
- Do not bypass Definition/Creation services.
- Do not activate connect-to-create yet beyond picker seam.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_INTERACTION_SPEC.md`
- `docs/design/video-replica/references/node-picker/`


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

- [x] Picker opens, searches, filters and creates existing definitions through canonical service.
- [x] No new quickAdd/provider-specific menu ownership is introduced.
- [x] Creation metadata can be extended without editing Canvas core UI.
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

Before: `canvas-app-records.js` owned a fixed `#createMenu` projection and
`menuAdd()` selected hard-coded entries; `command-registry.js` already owned
the compatibility creation catalog and `NodeCreationService` remained the
formal creation boundary.

After: `node-picker.js` owns picker presentation/filtering; the shared
`nodePickerCatalogFor()` projection supplies metadata; selection reuses
`menuAdd()` and the existing `WorkbenchInteractionController` creation path.

Duplicate owner removed: no new creation owner; the old menu remains only as
the bounded fallback when the picker seam is unavailable.

Browser/reference evidence: isolated local server acceptance verified the
picker, keyword filtering (`语言` → `LLM 节点`) and selecting `提示词` creating a
second prompt node in Unified Canvas; the node request returned HTTP 201 from
`/api/v1/canvases/{id}/nodes`.

Focused tests: `./.venv/bin/python -m unittest -q tests.test_ux06_node_picker tests.test_frontend_workbench_modules` — 171 passed.

Regression: `./scripts/agent-verify.sh` — PASS; 1355 Python tests, 306 AST
files, 155 JavaScript files, 4 architecture guards, and `git diff --check`.

Independent-review repair: the node adapter's `updated_at` cursor is now held
in the page-level `canvasNodeRevision`; `adoptCanvasRevision()` no longer
advances the logical full-record CAS cursor. Focused UX-06, frontend module,
and Canvas runtime tests — 402 passed; the full regression gate remains PASS.

## Next Recommended Card

`UX-07`

Do not execute the next card in the same Agent run.

## Close-out

Independent Review: PASS. Closed after DoD, architecture, ownership, focused
test, regression and browser evidence review. Archived on 2026-09-14; UX-07
was activated separately and remains implementation-not-started.
