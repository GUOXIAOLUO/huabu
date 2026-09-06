# CARD R8-12 — DirectModelExecutor

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-11

## Goal

Add a generic direct model/API execution route if supported by current product needs.

## Before Owner

provider-specific direct calls

## After Owner

DirectModelExecutor

## In Scope

- Adapt generic executor contract.
- Use ProviderConnection/ModelAvailability.
- Normalize outputs/events.

## Out of Scope

- Skip implementation if no valid direct route exists; document decision instead.

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

- [ ] No direct provider SDK leaks into domain.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-13`

Do not execute the next card in the same Agent run.
