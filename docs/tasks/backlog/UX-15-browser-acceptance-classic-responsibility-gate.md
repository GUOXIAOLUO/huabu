# CARD UX-15 — Browser Acceptance + Classic Responsibility Gate

- Round: UX Video Replica Wave
- Priority: P0
- Status: BACKLOG
- Depends on: `UX-14`

## Goal

Close the UI Replica Wave only after end-to-end browser acceptance and bounded retirement of replaced Classic presentation responsibilities.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Run full visual/interaction acceptance against reference checklist.
- Exercise default/hover/selected/editing/running/success/error/workspace states.
- Inventory Classic presentation responsibilities replaced by UX-01..14.
- Remove only duplicate ownership proven safe; leave unresolved compat seams explicitly documented.
- Run focused, regression and browser acceptance gates.


## Out of Scope

- No blanket deletion of classic-* files.
- No R11 implementation.
- No architecture scope expansion to WholeHouse.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_ACCEPTANCE_CHECKLIST.md`
- `docs/design/video-replica/ARCHITECTURE_GUARDRAILS.md`
- `docs/design/video-replica/REFERENCE_INDEX.md`


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

- [ ] Reference checklist has evidence for all required flows.
- [ ] Canonical architecture guards pass.
- [ ] Any removed Classic responsibility has named before/after ownership evidence.
- [ ] Full regression gate passes.
- [ ] Independent Review can evaluate a bounded UX wave closure.
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

Before:

After:

Duplicate owner removed:

Browser/reference evidence:

Focused tests:

Regression:

## Next Recommended Card

`R11-01`

Do not execute the next card in the same Agent run.
