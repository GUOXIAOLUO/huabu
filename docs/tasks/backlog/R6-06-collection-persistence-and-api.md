# CARD R6-06 — Collection Persistence and API

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-05

## Goal

Persist Collections canonically and expose application/API boundaries.

## Before Owner

in-memory/ad hoc structures

## After Owner

CollectionRepository + service/API

## In Scope

- Add SQLite persistence.
- Add CRUD/query service.
- Add canonical API and tests.

## Out of Scope

- No batch execution yet.

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

- [ ] Collections survive restart and can be referenced by id.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-07`

Do not execute the next card in the same Agent run.
