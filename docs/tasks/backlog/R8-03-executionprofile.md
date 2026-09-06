# CARD R8-03 — ExecutionProfile

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-02

## Goal

Represent reusable execution configuration independently from Skill and Model.

## Before Owner

embedded legacy execution config

## After Owner

ExecutionProfile

## In Scope

- Define executor/runtime/model selection/default params/safety/timeouts refs.
- Persist/version appropriately.

## Out of Scope

- Do not store secrets directly.

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

- [ ] Task can reference a profile without duplicating executor internals.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-04`

Do not execute the next card in the same Agent run.
