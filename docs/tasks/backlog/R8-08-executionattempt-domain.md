# CARD R8-08 — ExecutionAttempt Domain

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-07

## Goal

Track per-item attempts/retries/output refs.

## Before Owner

coarse run state

## After Owner

ExecutionAttempt

## In Scope

- Define item index/status/retry/error/output/timing.
- Associate attempts with run.
- Persist deterministically.

## Out of Scope

- No UI polish.

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

- [ ] Batch items have independent attempt histories.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-09`

Do not execute the next card in the same Agent run.
