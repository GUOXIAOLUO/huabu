# CARD UX-02 — Canvas Surface Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `UX-01`

## Goal

Make the Canvas surface, navigation chrome, zoom/pan controls, and empty-space presentation match the reference videos while preserving the existing runtime.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize current surface layout and controls.
- Apply video-derived spacing, background, chrome hierarchy, and control density.
- Preserve pan/zoom/selection/semantic-zoom behavior.
- Verify common desktop viewport states.


## Out of Scope

- No NodeShell redesign yet.
- No new graph model or Canvas implementation.
- No provider-specific UI changes.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_CANVAS_REPLICA_SPEC.md`
- `docs/design/video-replica/references/canvas-overview/`


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

- [x] Canvas surface visually matches reference baseline at accepted desktop viewport.
- [x] Pan, zoom, selection and semantic zoom remain functional.
- [x] No duplicate surface runtime/owner is added.
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

Before: `static/css/canvas.css` owned the persistent Canvas surface presentation
rules (`.board`, `.topbar`, `.toolbar`, `.minimap`) while
`canvas-app-interaction.js` and `interaction-controller.js` owned pan, zoom,
selection and minimap interaction.

After: the existing CSS owner consumes shared UX-01 presentation tokens for
Canvas surface spacing, background grid, chrome density, control sizing and
minimap placement. The existing interaction owners remain unchanged.

Duplicate owner removed: none; no second Canvas surface or runtime was added.

Browser/reference evidence: against `REF-001` and `REF-002`, the local desktop
browser viewport shows a near-white low-noise dotted surface, compact top-left
navigation, compact top-right action chrome, restrained minimap and selected
node action hub, plus the bottom-center zoom/fit control group. Browser
interaction verification completed on the existing two-node Canvas: selection
rendered the action hub; wheel zoom changed the indicator from 69% to 75%; the
surface `放大` control changed the label from 69% to 79%; `适配全部节点`
changed it to 36%; board drag translated the world and minimap viewport; fresh
Console errors were absent. Before/after screenshots were captured in the
browser session.

Focused tests: `tests.test_ux02_canvas_surface` — 2 passed;
`tests.test_ux01_design_tokens` plus current-fact pointer tests — 6 passed;
semantic zoom and Canvas runtime tests — 240 passed.

Regression: `./scripts/agent-verify.sh` — PASS, 1344 tests, 302 Python AST
files, 154 JavaScript files, 4 architecture guards, clean `git diff --check`.

## 下一推荐任务

`UX-03`

Do not execute the next card in the same Agent run.
