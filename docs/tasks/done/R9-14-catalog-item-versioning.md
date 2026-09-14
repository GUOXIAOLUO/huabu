# CARD R9-14 — Catalog Item Versioning

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
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

- [x] Old project refs can pin old catalog versions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: CatalogItem versions existed but the item had no explicit current
version pointer, and Collection references had no Catalog Item Version type.

After: CatalogItem keeps stable identity plus immutable version IDs and a
validated `current_version_id`; appending a version advances only that pointer
while preserving all older version records. Collection references can pin a
specific `catalog_item_version`.

Duplicate owner removed: none. CatalogItemVersion remains owned by the Catalog
domain/repository; Task and Collection references point to version IDs without
owning or rewriting Catalog versions.

## Developer Verification

- Added current-version pointer validation, creation/append advancement, and
  compatibility inference for legacy items with existing version IDs.
- Added explicit `catalog_item_version` Collection reference support.
- Focused Catalog/Collection/Current Truth suite: **15 tests PASS**.
- Full `./scripts/agent-verify.sh`: **PASS — 1312 tests**, 275 Python AST files,
  152 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`R9-15`

Do not execute the next card in the same Agent run.
