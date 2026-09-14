# CARD UX-07 — Connect-to-Create

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `UX-06`

## Goal

Match the video flow where dragging/clicking from a node connection handle opens a compatibility-filtered picker and creates node + edge atomically.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize existing CreateNodeAndEdge path.
- Create connection intent from source port.
- Filter Node Picker entries using canonical type compatibility.
- Commit node + edge through canonical command/service and preserve undo/save behavior.


## Out of Scope

- No direct frontend graph mutation shortcut.
- No legacy.any-based recommendation logic except compatibility fallback.


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

- [x] Source handle → picker → compatible node → node+edge works as one user flow.
- [x] Undo/redo/save behavior remains valid.
- [x] Incompatible definitions do not appear or cannot be committed.
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

Before: `canvas-app-interaction.js` owned the connection gesture and
`canvas-app-records.js` built a separate hard-coded link menu; the formal
`GraphMutationService` and `NodeCreationService` paths already existed.

After: the shared `WorkbenchNodePicker` owns connection-picker presentation;
`canvas-app-interaction.js` owns intent and typed admission; connected creation
delegates to the existing atomic graph service path.

Duplicate owner removed: the shared picker replaces the hard-coded link menu
when available; the bounded legacy fallback remains for unavailable versioned
creation.

Browser/reference evidence: isolated browser acceptance dragged a Loop output
port to empty space, showed only four compatible entries, selected Prompt, and
verified two nodes plus one persisted connection with HTTP 201 from
`graph/create-node-and-edge`.

Focused tests: `./.venv/bin/python -m unittest -q tests.test_ux07_connect_to_create tests.test_frontend_workbench_modules tests.test_canvas_runtime_state tests.test_canvas_nodes_runtime` — 426 passed.

Regression: `./scripts/agent-verify.sh` — PASS; 1358 Python tests, 307 AST
files, 155 JavaScript files, 4 architecture guards, and `git diff --check`.

## Next Recommended Card

`UX-08`

## Close-out

Independent Review: PASS. Closed after DoD, architecture, ownership, focused
tests, regression and isolated browser acceptance review. Archived on
2026-09-14; UX-08 was activated separately and remains implementation-not-started.

Do not execute the next card in the same Agent run.
