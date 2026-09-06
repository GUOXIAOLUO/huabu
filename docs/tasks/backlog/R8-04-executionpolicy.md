# CARD R8-04 — ExecutionPolicy

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-03

## Goal

Represent single/batch/map execution policy explicitly.

## Before Owner

ad hoc concurrency/start row settings

## After Owner

ExecutionPolicy

## In Scope

- Support mode/concurrency/start_index/limit/retry/timeout/order/continue_on_error.
- Validate ranges and defaults.

## Out of Scope

- Do not put policy into Collection semantics.

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

- [ ] Policy round-trips and validation tests pass.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-05`

Do not execute the next card in the same Agent run.
