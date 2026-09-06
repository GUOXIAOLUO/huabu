# CARD R9-13 — Generic Catalog Domain

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-12

## Goal

Define generic structured catalog resources without WholeHouse semantics.

## Before Owner

future/adhoc product lists

## After Owner

Catalog

## In Scope

- Define Catalog/CatalogItem/CatalogItemVersion.
- Support schema/attributes/media refs.

## Out of Scope

- No Board/Hardware types in Core.

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

- [ ] Generic catalogs persist and version items.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-14`

Do not execute the next card in the same Agent run.
