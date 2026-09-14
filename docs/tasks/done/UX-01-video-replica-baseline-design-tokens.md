# CARD UX-01 — Video Replica Baseline + Design Tokens

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: `R10-08`

## Goal

Freeze the video-derived visual baseline and introduce shared design tokens without changing Canvas behavior.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize current Canvas screenshots at default/selected states.
- Map video references to concrete tokens: canvas background, border, radius, shadow, typography, selection, edge, primary/secondary actions.
- Introduce shared token definitions used by future UX cards.
- Do not restyle all node families yet.


## Out of Scope

- No Node/Graph/Execution/Provider semantics change.
- No Classic capability migration in this card.
- No WholeHouse-specific styling.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_CANVAS_REPLICA_SPEC.md`
- `docs/design/video-replica/ARCHITECTURE_GUARDRAILS.md`
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

- [ ] Token layer exists and is consumed by at least the Canvas/root shell seam.
- [ ] Before/after screenshots are captured for comparison.
- [ ] No behavior regression and no second Canvas runtime introduced.
- [ ] `AGENT_NEXT_TASK.md` still authorizes only this card during implementation.
- [ ] No next card or later Round was implemented in the same Agent run.
- [ ] Focused tests and regression gate results are recorded with evidence.

## Rollback

Revert only this card's bounded presentation/interaction change or re-enable the prior bounded compatibility seam. Do not roll back unrelated completed Round work or reset unknown local changes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md` with verified evidence required by the current task lifecycle.
- Update this card's status/evidence according to the repository's current task lifecycle.
- Update `AGENT_NEXT_TASK.md` only as permitted by the repository's independent Review/activation procedure.
- Do not rewrite architecture documents merely to describe visual changes unless ownership actually changed.

## Final Ownership Evidence

Before: `static/css/canvas.css` owned the Canvas visual variables and component
rules in one local `:root`/`.theme-dark` block; the Canvas root shell consumed
those aliases directly.

After: `static/css/workbench-canvas-tokens.css` is the shared presentation
token owner. `canvas.html` loads it before `canvas.css`; the Canvas `body` and
`.panel` root-shell seam consume semantic `--wb-*` tokens while compatibility
aliases keep existing component rules stable.

Duplicate owner removed: the duplicate Canvas `:root` and `.theme-dark`
variable definitions were removed from `canvas.css`. No Canvas runtime,
domain, node, graph or execution owner was added.

Browser/reference evidence: baseline and post-change screenshots were captured
from the local Workbench browser session, including the single Canvas editor
in default and selected-node states. The late-loaded media-editor handlers now
bind lazily and the inspector guard distinguishes the browser's element global;
cache-busted script URLs ensure the repaired sources are exercised. The editor
loaded with two nodes and no fresh console errors, and selection actions were
visible in the accessibility tree. Visual target references: `REF-001` and
`REF-002`; token values follow the light, low-noise surface, border, radius,
selection and edge guidance in `VIDEO_CANVAS_REPLICA_SPEC.md`.

Focused tests: `tests.test_ux01_design_tokens` — 4 passed; current-fact
pointer tests — 2 passed.

Regression: `./scripts/agent-verify.sh` — PASS, 1342 tests, 301 Python AST
files, 154 JavaScript files, 4 architecture guards, clean `git diff --check`.

## Next Recommended Card

`UX-02`

Do not execute the next card in the same Agent run.
