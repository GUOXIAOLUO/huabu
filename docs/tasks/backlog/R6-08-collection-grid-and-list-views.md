# CARD R6-08 — Collection Grid and List Views

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-07

## Goal

Add generic grid/list presentations for collections.

## Before Owner

gallery-only collection UX

## After Owner

multi-view Collection presentation

## In Scope

- Implement list/grid switch.
- Preserve selection/order.
- Keep view state separate from collection data semantics.

## Out of Scope

- No advanced query builder.

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

- [ ] View switch does not mutate semantic collection content.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-09`

Do not execute the next card in the same Agent run.
