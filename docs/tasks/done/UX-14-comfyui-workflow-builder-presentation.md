# CARD UX-14 — ComfyUI Workflow Builder + Presentation

- Round: UX Video Replica Wave
- Priority: P0
- Status: ACTIVE — implementation complete; independent Review pending
- Depends on: `UX-13`

## Goal

Expose version-pinned ComfyUI workflows as simplified Workbench definitions with mapped user-facing inputs/outputs, matching the reference videos.

## Why Now

This card belongs to the UI Replica Wave that is allowed only after `R10-08` and the R10 gate are complete. It converts the frozen video-reference material into the existing one-card-at-a-time development process without creating a parallel planning system.

## Before Owner

Characterize the actual current owner(s) before editing. Record exact modules/services in Final Ownership Evidence.

## After Owner

The existing canonical Workbench owner(s), refined so the new presentation/interaction is owned by shared Workbench modules rather than a duplicate Canvas runtime.

## In Scope

- Characterize current ComfyUIExecutor and classic-comfy-controls behavior.
- Implement/import workflow definition builder around workflow_id@version.
- Discover/map exposed roles to node_id + input_name and select outputs.
- Render simplified Workbench node using generic shell/parameter patterns.


## Out of Scope

- Do not recreate the full ComfyUI graph editor inside Canvas.
- Do not use implicit latest workflow versions.
- Do not bypass ComfyUIExecutor.


## Characterization

Before editing:

1. Read `AGENTS.md`, `.agent/AGENT_CONTRACT.md`, `docs/status/CURRENT_EXECUTION_STATUS.md`, `AGENT_NEXT_TASK.md`, and this card.
2. Inspect the current implementation and identify the real owner(s); do not assume the reference pack describes current code.
3. Capture/record the current browser state relevant to this card.
4. Read the required video references below.
5. Add the smallest characterization test/evidence needed before migrating responsibility.

## Required Video / Design References

- `docs/video-replica/VIDEO_INTERACTION_SPEC.md`
- `docs/video-replica/references/comfy-mapping/`


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

- [x] A stored workflow version can produce a simplified mapped Workbench definition.
- [x] Input mappings are explicit and version-pinned.
- [x] Local/remote connection semantics remain executor/integration concerns.
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
`workbench/comfyui/executor.py` owned exact-version workflow resolution, input
injection and runtime transport behind `ComfyUIExecutor`; the page-side
`classic-comfy-controls.js` owned legacy workflow selection and field DOM.

After:
`ComfyUIWorkflowDefinitionBuilder` owns version-pinned mapping/discovery and
`comfy-workflow-presentation.js` owns only the generic mapped projection.
`ComfyUIExecutor` remains the runtime owner and the classic module remains a
bounded compatibility adapter.

Duplicate owner removed:
None. No second Canvas/runtime/repository/service was added; legacy controls
remain for unversioned saved records.

Browser/reference evidence:
Read the Comfy mapping interaction spec, node spec, architecture guardrails and
REF-501 through REF-504. The real Canvas entry remains the single runtime;
versioned mapped workflow presentation is covered by focused DOM contract tests.

Focused tests:
`./.venv/bin/python -m unittest tests.test_comfyui_workflow_definition_builder
tests.test_ux14_comfy_workflow_presentation tests.test_comfyui_executor
tests.test_frontend_workbench_modules` — 199 passed, including the independent
Review repair regression and the end-to-end VM projection assertion.

Regression:
`./scripts/agent-verify.sh` — **PASS: 1391 tests**, 315 Python AST files,
160 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`UX-15`

Do not execute the next card in the same Agent run.
