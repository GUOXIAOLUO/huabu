# CARD R7-04 — ModelAvailability

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-03

## Goal

Represent a model available through a specific connection/runtime.

## Before Owner

implicit provider+model pair

## After Owner

ModelAvailability

## In Scope

- Define model ref/connection ref/status/limits/runtime route.
- Add availability repository/service.

## Out of Scope

- Codex itself is not a ModelDefinition.

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

- [ ] Same model can have multiple availability routes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-05`

Do not execute the next card in the same Agent run.
