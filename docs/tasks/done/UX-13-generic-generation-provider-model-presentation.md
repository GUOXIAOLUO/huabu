# CARD UX-13 — Generic Generation + Provider / Model Presentation

- Round: UX Video Replica Wave
- Priority: P0
- Status: ACTIVE — implementation complete; independent Review pending
- Depends on: `UX-12`

## Goal

Replace provider-shaped generation cards with a generic generation presentation driven by model availability/capabilities and execution profile.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize generator/msgen/minimax/runninghub/video provider-specific presentation branches.
- Define generic model/execution footer and parameter summary presentation.
- Keep ProviderConnection/credentials in settings, not node records.
- Migrate only presentation responsibilities proven by characterization.


## Out of Scope

- Do not collapse Model, ProviderConnection and Executor concepts.
- Do not delete Classic seams until each replaced responsibility is accepted.
- No API key in node state.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_NODE_SPEC.md`
- `docs/video-replica/references/generation-node/`
- `docs/video-replica/references/provider-settings/`


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

- [x] At least common generation flows use generic presentation.
- [x] Provider-specific differences are expressed through definitions/capabilities/parameter schema where possible.
- [x] No credentials leak into Canvas persistence.
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
Provider-shaped generator, ModelScope and video bodies owned their visible
provider/model presentation independently; parameter summary existed only on
the API generator body.

After:
`generation-presentation.js` owns the shared model/route/execution/capability
projection and is mounted by the existing compatibility body seams. Existing
parameter presentation remains the parameter-summary owner.

Duplicate owner removed:
No new owner. Provider settings and execution remain in their existing bounded
Classic compatibility seams; the new module has no persistence or execution API.

Browser/reference evidence:
Real local Canvas page opened successfully and existing Unified Canvas task
presentation was verified. No populated generation fixture was available in
the current project list; generation projection and credential exclusion were
verified by focused behavioral tests.

Focused tests:
`./.venv/bin/python -m unittest tests.test_ux13_generation_presentation
tests.test_ux08_parameter_presentation tests.test_ux09_task_llm_node_replica`
— 16 passed. Review repair coverage verifies the injected canonical
ModelAvailability registry is preferred and msgen/video retain shared
parameter-summary wiring.

Regression:
`./scripts/agent-verify.sh` — PASS: 1382 tests, 312 Python AST files, 159
JavaScript files, 4 architecture guards, and `git diff --check`.

## Next Recommended Card

`UX-14`

Do not execute the next card in the same Agent run.
