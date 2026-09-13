# CARD R8-07 — ExecutionRun Domain

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-12
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

- [x] Run survives restart with status/history.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: legacy transient job state was not represented by a durable,
project-authorized Workbench run record.

After: `ExecutionRun` owns the durable run identity, task/profile references,
immutable `ExecutionPolicy` and `ExecutionInputProjection` snapshots, status,
timestamps, summary, and revision. SQLite repository, application service, and
versioned API provide restart-readable status/history.

Duplicate owner removed: none; result materialization and event storage remain
deferred to later R8 cards.

Independent-review repair: nested JSON values in the projection and summary
are recursively frozen while remaining JSON-serializable; invalid status
transitions are rejected and exposed as a client error by the API.

## Next Recommended Card

`R8-08`

Do not execute the next card in the same Agent run.
