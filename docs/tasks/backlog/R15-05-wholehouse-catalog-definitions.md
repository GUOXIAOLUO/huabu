# CARD R15-05 — WholeHouse Catalog Definitions

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-04

## Goal

Define materials/products using generic Catalog extension.

## Before Owner

generic catalog only

## After Owner

WholeHouse catalog definitions

## In Scope

- Define Board/Finish/Hardware/Handle/Lighting/Countertop/Accessory/Product schemas.
- Register package catalogs.

## Out of Scope

- No factory/MES/inventory system.

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

- [ ] Catalog items can be selected/bound through generic system.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-06`

Do not execute the next card in the same Agent run.
