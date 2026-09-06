# CARD R12-10 — IntegrationCapability

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-09

## Goal

Normalize capabilities/actions offered by connections.

## Before Owner

client-specific methods

## After Owner

IntegrationCapability

## In Scope

- Define capability id/action schemas/connection refs.
- Register/refresh capabilities.

## Out of Scope

- No WholeHouse capability names in Core beyond generic strings.

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

- [ ] Skills can request capabilities without knowing transport.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-11`

Do not execute the next card in the same Agent run.
