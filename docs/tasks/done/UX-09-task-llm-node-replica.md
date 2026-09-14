# CARD UX-09 — Task / LLM Node Replica

- Round: UX Video Replica Wave
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: `UX-08`

## Goal

Make TaskRichNode present the video LLM/AI-task interaction while preserving Skill/Model/Execution separation.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize TaskRichNode, SkillSelector, ModelSelector and input preview.
- Compose compact inputs, prompt, skill/model summary and run action using shared NodeShell.
- Support structured/text/list output presentation without creating LLM-specific domain semantics.
- Verify multimodal inputs.


## Out of Scope

- No new LLMNode domain type.
- No provider credentials inside the node.
- No WholeHouse-specific task branching in Core.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/design/video-replica/VIDEO_NODE_SPEC.md`
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

- [x] Task node matches reference hierarchy and remains Definition/Skill driven.
- [x] Skill and model selection still resolve through canonical registries.
- [x] Execution/result behavior remains unchanged.
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

Before: Task nodes entered the existing Canvas through the Classic/Legacy
compatibility adapter. `TaskRichNode` was a generic state skeleton with
optional Skill/Model/input seams, but there was no production compact Task
card composition for the reference hierarchy.

After: `task-card-presentation.js` owns the generic compact Task hierarchy;
`TaskRichNode` owns Task state and delegates updates; `NodeShell` and the
shared `NodeCardHost` remain the single card/runtime composition boundary;
the existing Canvas save scheduler remains the persistence owner. Production
registry inputs are read from the injected shared
`WorkbenchRuntimeRegistries`/`WorkbenchRegistries` bundle or existing aliases;
Canvas does not create a registry.

Duplicate owner removed: no second Canvas runtime, no LLM-specific NodeKind,
and no provider/credential ownership were added. The prior blank Task body is
replaced by the shared presentation mounted after the bounded Legacy adapter;
the Legacy path remains compatibility-only.

Browser/reference evidence: required Task references were read and the local
server was exercised through the real Canvas page. A temporary Task canvas
created through the formal Canvas API displayed the shared NodeShell card with
title/status, Skill summary and toggle, route/model summary, multimodal input
resource chip, Prompt editor, canonical Model route selector, text/list/
structured output modes, and Run action. Prompt editing updated the visible
control and the temporary canvas was then removed through the formal delete
endpoint.

Focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -q
tests.test_ux09_task_llm_node_replica tests.test_task_rich_node
tests.test_model_selector tests.test_execution_input_preview
tests.test_nodeshell_v2 tests.test_presentation_state` — 30 tests passed;
all changed JavaScript files passed `node --check` and `git diff --check`.

Regression: `./scripts/agent-verify.sh` — PASS, 1371 tests, 309 Python AST
files, 157 JavaScript files, 4 architecture guards, and clean
`git diff --check`.

## Next Recommended Card

`UX-10`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-14. The Task presentation remains on the shared Unified Canvas
boundary, Skill/Model selectors consume injected canonical registries, and
NodeShell no longer duplicates selector ownership. Focused and regression
evidence passed without introducing a new runtime, service, API, NodeKind, or
credential path.
