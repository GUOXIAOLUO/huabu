# CARD UX-05 — Floating Action Toolbar

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: `UX-04`

## Goal

Make selected-resource/node actions appear in a contextual floating toolbar instead of bloating node bodies.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Inventory existing FloatingActionBar actions and node-local buttons.
- Define action visibility by selection/capability rather than provider-specific branches.
- Move eligible common actions to the floating toolbar.
- Keep destructive/advanced actions explicit and accessible.


## Out of Scope

- Do not migrate Media Editor internals.
- Do not remove node-local controls that are still required for behavior until replacement is proven.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_INTERACTION_SPEC.md`
- `docs/video-replica/VIDEO_CANVAS_REPLICA_SPEC.md`
- `docs/video-replica/ARCHITECTURE_GUARDRAILS.md`
- `docs/video-replica/references/media-editor/`
- `docs/video-replica/references/canvas-overview/`


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

- [x] Selected image/resource shows contextual toolbar matching reference hierarchy.
- [x] Actions remain capability-driven and keyboard/mouse usable.
- [x] Duplicate eligible controls are removed only after acceptance.
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
`static/js/workbench/canvas/canvas-app-interaction.js` owned selection-hub wiring and
selection-count predicates; `static/js/workbench/canvas/floating-action-bar.js`
rendered text-labelled buttons; node-local image menus remained in
`canvas-app-records.js`/media-editor code.

After:
Shared `WorkbenchFloatingActionBar` owns contextual button projection and intent
emission. Canvas interaction owns capability derivation from the selected node
records and dispatches the existing preview/edit/open/copy/group/collection/delete
commands. No domain, persistence, or runtime ownership moved.

Duplicate owner removed:
No node-local control was removed: the card's out-of-scope Media Editor internals
and required node menus remain as compatibility behavior. The duplicate visual
toolbar label rendering was replaced by icon-plus-accessible-label projection in
the shared floating-action-bar module.

Browser/reference evidence:
Isolated SQLite copy served at `127.0.0.1:3012`; selecting a real image node
displayed a dark compact toolbar with five icon buttons. AX exposed 打开/预览/编辑/
复制/删除. Keyboard Enter on 编辑 opened the existing 裁剪图片 editor, and the
toolbar matched the hierarchy in `docs/video-replica/references/media-editor/`.

Focused tests:
`./.venv/bin/python -m unittest -q tests.test_ux05_floating_action_toolbar
tests.test_floating_action_bar tests.test_ux03_nodeshell_visual
tests.test_canvas_runtime_state tests.test_canvas_render_lifecycle
tests.test_frontend_workbench_modules` — 407 passed.

Regression:
`./scripts/agent-verify.sh` — PASS; 1352 tests, 305 Python AST files, 154
JavaScript files, 4 architecture guards, and `git diff --check` passed.

## Next Recommended Card

`UX-06`

Do not execute the next card in the same Agent run.
