# CARD R6-05 — Collection Domain Model

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-04

## Goal

Create Collection, CollectionSchema and CollectionItem as generic structured multi-item data.

## Before Owner

group/ad hoc arrays

## After Owner

Collection domain

## In Scope

- Define schema/columns/items/order/default_view metadata.
- Allow typed reference cells and literals.
- Keep Group semantics separate.

## Out of Scope

- No WholeHouse schemas in Core.

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

- [ ] Collection round-trips independently from Canvas Group.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-06`

Do not execute the next card in the same Agent run.
