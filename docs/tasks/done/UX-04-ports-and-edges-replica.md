# CARD UX-04 — Ports and Edges Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: `UX-03`

## Goal

Align connection lines and port visibility with the videos while keeping canonical typed compatibility.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize current port and edge rendering.
- Implement low-emphasis idle edges and stronger hover/selected/running states.
- Hide/de-emphasize ports until hover/selection where compatible with accessibility.
- Route compatibility decisions through canonical typed compatibility; legacy.any remains compatibility-only.


## Out of Scope

- No new graph persistence schema.
- No UI-only compatibility rules that disagree with domain rules.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_INTERACTION_SPEC.md`
- `docs/video-replica/references/node-picker/`


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

- [x] Idle/hover/selected edge states visually match reference intent.
- [x] Invalid connections are rejected by canonical compatibility.
- [x] No duplicated compatibility owner is introduced.
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

Before: Edge presentation was owned by `static/js/workbench/canvas/canvas-app-interaction.js`
with binary `link` / `link-active` classes, while port visibility was owned by
the shared Canvas CSS. Connection validity already flowed through
`WorkbenchCanvasGraphInteraction.edgeIntentFromPortDrop` and
`WorkbenchCanvasPortCompatibility.isCompatible`.

After: `static/js/workbench/canvas/graph-interaction.js` now owns the
business-neutral `edgePresentationClass` projection. The existing page
renderer supplies generic selected/hovered/node-running state, and
`static/css/canvas.css` owns edge and port presentation. Canonical typed
compatibility remains the existing shared compatibility module.

Duplicate owner removed: None introduced; no second Canvas runtime or second
compatibility implementation was added.

Browser/reference evidence: Required interaction guidance was read from
`docs/video-replica/VIDEO_INTERACTION_SPEC.md` and the node-picker reference
pack under `docs/video-replica/references/node-picker/`. Browser acceptance
against an isolated local database verified the real Unified Canvas loaded with
persisted nodes and a connection, with idle/selected edge and port states
visible and no fresh console errors.

Focused tests: `tests.test_ux04_ports_edges_visual` plus the existing Canvas
runtime/compatibility suites; results recorded in the status document.

Regression: `./scripts/agent-verify.sh`; result recorded in the status
document.

## Next Recommended Card

`UX-05`

Do not execute the next card in the same Agent run.
