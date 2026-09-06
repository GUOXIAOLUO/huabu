# CARD R8-05 — ExecutionInputProjection

- Round: R8
- Priority: P0
- Status: BACKLOG
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

- [ ] Run inputs are reproducible after source resources later change.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-06`

Do not execute the next card in the same Agent run.
