# CARD UX-03 — NodeShell Visual Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: `UX-02`

## Goal

Restyle the shared NodeShell presentation so common nodes inherit the video node hierarchy without changing node semantics.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize NodeShell header/content/footer/resize states.
- Implement compact header, subtle border/shadow, selected/running/error visual states.
- Define small/standard/task/collection/result presentation sizing rules.
- Keep advanced content outside default card when possible.


## Out of Scope

- Do not create per-provider NodeShell forks.
- Do not add new Core NodeKinds for WholeHouse.
- Do not move execution logic into renderer code.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_NODE_SPEC.md`
- `docs/design/video-replica/references/canvas-overview/`
- `docs/design/video-replica/references/task-llm-node/`


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

- [x] Shared NodeShell owns the new visual shell.
- [x] Default/hover/selected/running/error states are evidenced.
- [x] At least existing Asset/Task/Collection/Result shells remain behaviorally compatible.
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

Before: `static/js/workbench/canvas/node-shell.js` owned the shared NodeShell
DOM structure and state/selection projection; `static/css/canvas.css` owned
the mounted shell's common geometry and chrome styling. Renderer modules kept
their content and provider compatibility controls.

After: the same NodeShell and CSS owners now provide compact shared chrome,
presentation-size variables, and default/hover/selected/running/done/error
state styling. Renderer content and execution remain outside the shell.

Duplicate owner removed: none; no second shell, renderer registry, or Canvas
runtime was added.

Browser/reference evidence: an isolated copy of the canonical SQLite database
was used so no user data changed. The real Canvas page rendered a shared
NodeShell instance with no fresh Console errors; screenshots verified default,
selected, running, and failed states, including the selected action hub and
state-colored shell border. The NodeShell instance-level state projection
additionally exercises the error transition in
`tests.test_ux03_nodeshell_visual`. Interaction compatibility remains covered
by `tests.test_nodeshell_v2`, `tests.test_presentation_state`, and the frontend
workbench regression suite.
Reference: `REF-204` and the NodeShell rules in `VIDEO_NODE_SPEC.md`.

Focused tests: `tests.test_ux03_nodeshell_visual` (4),
`tests.test_nodeshell_v2` (1), `tests.test_presentation_state` (3), and
`tests.test_frontend_workbench_modules` (174) passed.

Regression: `./scripts/agent-verify.sh` — PASS, 1348 tests, 303 Python AST
files, 154 JavaScript files, 4 architecture guards, clean `git diff --check`.

## Next Recommended Card

`UX-04`

Do not execute the next card in the same Agent run.
