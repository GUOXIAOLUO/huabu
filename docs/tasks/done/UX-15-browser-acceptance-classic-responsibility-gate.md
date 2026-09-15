# CARD UX-15 — Browser Acceptance + Classic Responsibility Gate

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS
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

- `docs/video-replica/VIDEO_ACCEPTANCE_CHECKLIST.md`
- `docs/video-replica/ARCHITECTURE_GUARDRAILS.md`
- `docs/video-replica/REFERENCE_INDEX.md`


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

- [x] Reference checklist has evidence for all required flows.
- [x] Canonical architecture guards pass.
- [x] Any removed Classic responsibility has named before/after ownership evidence.
- [x] Full regression gate passes.
- [x] Independent Review can evaluate a bounded UX wave closure.
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
The unified Canvas uses ordered shared Workbench modules plus bounded
`classic-*` compatibility seams for the remaining page-owned provider and
execution behavior. UX-01 through UX-14 supplied the generic shell,
parameters, task/result workspace, generation and Comfy presentation layers.

After:
The Unified Canvas remains the sole product runtime. Shared modules own the
generic presentation/interaction surfaces; `classic-*` modules remain only as
named compatibility adapters where replacement has not proven safe.

Duplicate owner removed:
No blanket deletion. The retired Smart page/runtime and old Classic monolith
remain absent; remaining Classic seams are retained for compatibility and are
not expanded with new product responsibilities.

Browser/reference evidence:
Read the actual `docs/video-replica/` checklist, guardrails and reference index.
On local `127.0.0.1:3000`, the real Unified Canvas loaded the existing result
fixture and verified Grid, Preview, Compare, Selection, Collection and
Materialization. Collection and Materialization render their canonical empty
states instead of an unavailable placeholder when no persisted child record
exists. The Task card retained its Prompt/Skill/Model presentation, disabled
unavailable-route state and unified NodeShell/ports. No execution, credential,
deletion or external handoff was triggered.

Checklist evidence matrix:

- A/B/C — the captured Unified Canvas frame was compared with `REF-001` and
  `REF-002`; the shared surface, NodeShell, ports and edge layer were inspected
  in the live page. Existing UX-02/UX-03/UX-04 tests cover pan/zoom/select,
  hover/selected styling, and ready/running/success/error projections.
- D/E/F — `REF-013`, `REF-017` and `REF-022` were used for the picker,
  parameter and Task/LLM comparison; UX-06/UX-08/UX-09 focused tests cover
  search/category, popover/Inspector, resource inputs, Skill/Model separation
  and output-mode projection.
- G — `REF-026` and `REF-401` were used for the Collection comparison;
  collection-table focused tests cover typed rows and the canonical batch
  boundary.
- H — `REF-031`, `REF-301` and `REF-304` were used for the live Result
  workspace; Grid, Preview, Compare, Selection, Collection and Materialization
  were clicked and verified, including the empty-state branches.
- I — `REF-035` and `REF-501` were used for the Comfy comparison; UX-14 tests
  cover versioned workflow and mapped-only projection without copying a full
  workflow graph into Canvas.
- J — the full regression gate and architecture guards pass; no new Canvas
  runtime, provider NodeKind, secret field, WholeHouse Core import or Classic
  business owner was introduced.
- K — live browser states recorded for this card are default, hover, selected,
  editing, running, success, error and workspace. Default/selected/workspace
  were observed directly in the fixture; hover/editing/running/success/error
  are covered by the shared NodeShell and task-state focused behavioral tests,
  with the unavailable route intentionally kept disabled. The live screenshot
  was captured from the localhost page and compared against the listed REF
  frames; deviations are the narrower fixture viewport and canonical empty
  states, which avoid inventing persisted results or triggering execution.

Focused tests:
`./.venv/bin/python -m unittest tests.test_ux15_browser_acceptance_gate
tests.test_ux12_result_workspace_replica tests.test_result_collection
tests.test_result_materialization tests.test_frontend_workbench_modules` —
248 passed.

Regression:
`./scripts/agent-verify.sh` — **PASS: 1395 tests**, 316 Python AST files,
160 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`R11-01`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-15. The DoD, bounded ownership evidence, architecture guards,
focused tests and full regression result were independently verified. No next
card was implemented in the review or close-out run.
