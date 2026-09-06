# CARD R8-01 — Executor Contract

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R7-13

## Goal

Define a runtime-neutral executor lifecycle.

## Before Owner

legacy execution paths

## After Owner

Executor interface

## In Scope

- Define prepare/start/stream/cancel/status/cleanup contracts.
- Define typed input/output/event envelopes.
- Specify idempotency/cancellation expectations.

## Out of Scope

- No executor-specific Core branching.

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

- [ ] At least a fake executor passes contract tests.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-02`

Do not execute the next card in the same Agent run.
