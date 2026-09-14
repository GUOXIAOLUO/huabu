# CARD UX-08 — Parameter Summary / Popover / Inspector

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
- Depends on: `UX-07`

## Goal

Replace oversized node parameter bodies with the video hierarchy: compact summary, common-parameter popover, advanced Inspector.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Inventory parameters currently rendered directly in common cards.
- Define field/parameter presentation metadata without provider-specific card forks.
- Implement compact summaries such as ratio/resolution/count/model.
- Place common edits in popover and advanced configuration in Inspector/workspace.


## Out of Scope

- Do not change provider secrets/connection ownership.
- Do not store API keys in nodes.
- Do not migrate every legacy provider control in one step unless covered by acceptance.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_NODE_SPEC.md`
- `docs/design/video-replica/references/generation-node/`


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

- [x] Generation/task cards are materially smaller at default state.
- [x] Parameter edits persist through existing canonical record/update paths.
- [x] Advanced fields remain accessible without node-body sprawl.
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

Before: Classic generator provider-card body rendered provider/model, ratio,
resolution, quality, quantity and custom fields directly in the default card
body; `WorkbenchNodeInspector` was read-only and generic.

After: Shared `parameter-presentation.js` owns the compact summary and common
parameter Popover; the existing generator body remains the advanced field
surface and the existing page save scheduler persists edits.

Duplicate owner removed: no new Canvas/runtime owner; default direct parameter
presentation is removed from the visible generator body while the bounded
Classic body remains available behind the advanced toggle.

Browser/reference evidence: isolated local SQLite browser acceptance created a
generator node, showed `参数 1:1 · 4K · ×1`, edited it to `16:9 · 2K · ×3`,
reloaded successfully, and expanded the advanced controls. This matches the
generation-node summary/Popover hierarchy in `VIDEO_NODE_SPEC.md` and REF-101.

Focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -q
tests.test_ux08_parameter_presentation tests.test_frontend_workbench_modules
tests.test_node_inspector tests.test_inspector_panel` — **182 tests passed**.

Regression: `./scripts/agent-verify.sh` — **PASS**, 1361 tests, 308 Python AST
files, 156 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`UX-09`

Do not execute the next card in the same Agent run.
