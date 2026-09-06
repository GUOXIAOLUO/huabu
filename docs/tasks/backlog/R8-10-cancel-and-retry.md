# CARD R8-10 — Cancel and Retry

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-09

## Goal

Provide application-level cancellation and retry semantics.

## Before Owner

executor-specific controls

## After Owner

ExecutionService cancel/retry

## In Scope

- Implement cancel flow.
- Retry failed attempt/item according to policy.
- Normalize terminal states.

## Out of Scope

- No automatic infinite retry.

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

- [ ] Cancel/retry behave consistently across fake/available executors.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-11`

Do not execute the next card in the same Agent run.
