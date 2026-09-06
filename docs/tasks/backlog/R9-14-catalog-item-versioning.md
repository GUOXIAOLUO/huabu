# CARD R9-14 — Catalog Item Versioning

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-13

## Goal

Make catalog item changes versioned/referencable.

## Before Owner

mutable item fields

## After Owner

CatalogItemVersion

## In Scope

- Implement immutable versions/current pointer.
- Preserve references from Tasks/Collections.

## Out of Scope

- No domain pricing engine.

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

- [ ] Old project refs can pin old catalog versions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-15`

Do not execute the next card in the same Agent run.
