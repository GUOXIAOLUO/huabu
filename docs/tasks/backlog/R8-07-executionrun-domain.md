# CARD R8-07 — ExecutionRun Domain

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-06

## Goal

Persist top-level execution runs and immutable run snapshots.

## Before Owner

legacy transient job state

## After Owner

ExecutionRun

## In Scope

- Define run id/task/profile/policy/input snapshot/status/timestamps/summary.
- Add repository/service/API.

## Out of Scope

- No result materialization yet.

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

- [ ] Run survives restart with status/history.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-08`

Do not execute the next card in the same Agent run.
