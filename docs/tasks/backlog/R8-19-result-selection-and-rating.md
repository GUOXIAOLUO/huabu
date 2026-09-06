# CARD R8-19 — Result Selection and Rating

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-18

## Goal

Track user selection/rating metadata on run results.

## Before Owner

no formal candidate choice

## After Owner

result selection metadata

## In Scope

- Add select/favorite/rating/comment where generic.
- Persist with run/result metadata.

## Out of Scope

- No Approval/Frozen semantics.

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

- [ ] Candidate preference survives reload.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-20`

Do not execute the next card in the same Agent run.
