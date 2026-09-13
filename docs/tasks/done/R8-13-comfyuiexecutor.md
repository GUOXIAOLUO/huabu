# CARD R8-13 — ComfyUIExecutor

- Round: R8
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-12 (DONE, independent Review PASS)

## Goal

Wrap ComfyUI workflows behind the generic Executor contract.

## Before Owner

ComfyUI-shaped Canvas/execution behavior

## After Owner

ComfyUIExecutor

## In Scope

- Define workflow/profile references.
- Map input roles to workflow inputs.
- Normalize progress/output.

## Out of Scope

- Do not recreate ComfyUI graph in main Canvas.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

## Execution Pattern

```text
characterize
→ focused test
→ establish seam
→ implement/migrate
→ verify
→ remove duplicate ownership
```

## Focused Tests

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [x] Task can execute a ComfyUI-backed Skill without provider-shaped Canvas node dependency.

Proven by `tests/test_comfyui_executor.py`: a generic `ExecutionRun` whose input
projection carries a `prompt` role runs through `ExecutionService` with
`ComfyUIExecutor`, injects the value into the resolved workflow node input,
persists `started → progress → partial_result → completed`, and yields two
normalized image outputs — with no Canvas node, Canvas repository, or
provider-shaped Canvas payload involved. A source-scan test pins that
`workbench/comfyui` imports neither Canvas/legacy modules nor any provider SDK.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: ComfyUI execution only existed as Canvas-shaped behavior. `main.py`
submitted a workflow carried inside a Canvas task payload
(`/api/canvas-comfy-tasks`), tracked status in a Canvas task table, and
interpreted progress/outputs in that Canvas context. No Workbench boundary
owned a ComfyUI run, so a Task could not execute a ComfyUI-backed Skill
without going through provider-shaped Canvas node behavior.

After: `workbench/comfyui/` owns the Workbench side of one ComfyUI run.
`ComfyUIExecutor` resolves an explicit versioned `ComfyUIWorkflowRef`
(`workflow_id@version`; an implicit "latest" is rejected) plus the configured
`ExecutionProfile`, maps Workbench input roles onto ComfyUI node input slots
through the workflow's binding table (unknown roles and missing required roles
are bounded errors), submits one `ComfyUICall` through the injected
`ComfyUITransport` port, and normalizes queued/executing/progress/output
events into typed `ExecutionEvent`/`ExecutionOutput` values, including output
kind and deterministic output names. The workflow graph is copied before input
injection, so the immutable workflow record is never mutated. ComfyUI
transport, backend selection, HTTP/WebSocket details, prompt submission and
output classification belong to the transport adapter, not to this seam.

Duplicate owner removed: none. `main.py`'s legacy `/api/canvas-comfy-tasks`
path and its ComfyUI helpers are intentionally preserved unchanged: this card
does not authorize migrating or deleting existing Canvas behavior, and the new
seam deliberately does not re-implement those helpers (output classification is
declared by the transport), so no duplicate ComfyUI output classifier was
introduced. Canvas node ownership, the ComfyUI graph editor, and asset
materialization remain outside this card.

## Developer Verification

- Focused: `24` tests covering workflow/profile reference resolution,
  rejection of an implicit latest version and of a mismatched workflow version,
  unknown workflow rejection, workflow-graph non-mutation, role mapping
  (including declared `input_roles`), unknown and missing-required-role errors,
  progress normalization, output normalization by kind and deterministic
  naming, completed/failed terminal events, stream-end completion, transport
  failure, timeout, submit failure, repeatable and explicit cancellation,
  cancellation of a waiting stream, unaccepted cancellation,
  prepare/start/handle boundaries, profile authority, workflow credential and
  duplicate-role rejection, the no-Canvas/no-provider-SDK source scan,
  `ExecutorRegistry` resolution of the `comfyui` runtime route without
  substitution, and generic Task execution plus active-handle cancellation
  through `ExecutionService`.
- Full: `./scripts/agent-verify.sh` PASS — `902` tests, `197` Python AST files,
  `135` JavaScript files, `4` architecture guards, and clean diff check.
- Developer Git Review: PASS; the only reviewed changes are the new
  `workbench/comfyui/` package, the new `tests/test_comfyui_executor.py`
  suite, and this card plus the status document update. No existing module was
  modified and no Canvas behavior, executor wiring, or fallback path was added.
- Independent Review: PASS on 2026-09-12. The review re-ran the focused suite
  (24 tests) and the full gate (902 tests, 197 Python AST files, 135 JavaScript
  files, 4 architecture guards, clean diff check), and mutation-tested three
  further guarded behaviours the developer had not covered (required-role
  validation, declared output naming, declined cancellation reporting); each
  mutation was caught and the source file was restored byte-identical. It also
  probed the frozen-value injection path (FrozenDict/tuple inputs inject
  cleanly without mutating the workflow record) and confirmed structurally that
  `workbench/comfyui` imports only stdlib, pydantic and `workbench.domain.*`.
  `main.py`'s legacy ComfyUI path was verified intact, so no unauthorized
  migration and no duplicate ComfyUI output classifier were introduced. R8-13
  is archived in `docs/tasks/done/`; R8-14 is now the sole ACTIVE task and was
  not started.

## Next Recommended Card

`R8-14`

Do not execute the next card in the same Agent run.
