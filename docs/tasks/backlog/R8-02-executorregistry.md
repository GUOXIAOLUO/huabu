# CARD R8-02 — ExecutorRegistry

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-01

## Goal

Discover executors by capability/runtime route.

## Before Owner

hardcoded execution selection

## After Owner

ExecutorRegistry

## In Scope

- Register executors.
- Resolve by ExecutionProfile/runtime route.
- Return explicit unavailable reasons.

## Out of Scope

- No silent fallback.

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

- [ ] Executor resolution is deterministic.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-03`

Do not execute the next card in the same Agent run.
