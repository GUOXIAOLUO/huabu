# CARD R8-05 — ExecutionInputProjection

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-12
- Depends on: R8-04

## Goal

Freeze resolved Task inputs into deterministic run input items.

## Before Owner

live mutable bindings at execution time

## After Owner

ExecutionInputProjection

## In Scope

- Resolve InputBindings/Collection rows.
- Snapshot refs/versions/parameters/prompt/model route.
- Return validation errors before execution.

## Out of Scope

- Do not execute yet.

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

- [x] Run inputs are reproducible after source resources later change.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Execution would read live mutable bindings and resource values at run
time without one deterministic input snapshot.

After: `ExecutionInputProjectionService` resolves typed bindings, expands
Collection rows in stable order, deep-copies source snapshots, and freezes
parameters plus Skill/Prompt/ModelAvailability/ExecutionProfile references
before execution.

Duplicate owner removed: The service only projects and validates; it does not
execute, mutate Canvas/Collection resources, or own Executor/ExecutionPolicy
semantics. Invalid and unresolved inputs return explicit pre-execution errors;
R8-06 was not started.

## Next Recommended Card

`R8-06`

Do not execute the next card in the same Agent run.
