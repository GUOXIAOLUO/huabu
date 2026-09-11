# CARD R6-05 — Collection Domain Model

- Round: R6
- Priority: P0
- Status: DONE — independently reviewed PASS
- Depends on: R6-04
- Completed: 2026-09-11

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

- [x] Collection round-trips independently from Canvas Group.

## Completion Evidence (2026-09-11)

- Added the independent Core `workbench.domain.collection` module with
  `Collection`, `CollectionSchema`, `CollectionColumn`, `CollectionItem`, and
  explicit literal/reference cell records.
- Collection validation owns unique column keys, unique item ids/order,
  required columns, known column keys, and cell-type compatibility. Group
  membership fields are rejected by the CollectionItem contract.
- Focused tests: 4 passed. Full `./scripts/agent-verify.sh`: PASS (712 tests,
  112 Python AST files, 121 JavaScript files, 4 architecture guards, clean diff
  check).
- Developer Git Review: PASS. Independent Review: PASS.

## Final Ownership Evidence

Before: group/ad hoc arrays were the only multi-item shape and could be
mistaken for structured resource data.

After: the Core Collection domain owns schema, ordered items, typed reference
cells, literals, default-view metadata, and validation independently from
Canvas Group.

Duplicate owner removed: Collection no longer relies on Canvas Group membership
or node-id arrays for item identity or ordering.

## Next Recommended Card

`R6-06`

Do not execute the next card in the same Agent run.
