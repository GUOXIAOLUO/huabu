# CARD R9-15 — Catalog Library UI

- Round: R9
- Priority: P1
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: R9-14

## Goal

Browse/search/inspect generic catalogs under Resources.

## Before Owner

no generic catalog UX

## After Owner

Catalog resource UI

## In Scope

- Add catalog/item browser.
- Search/filter basic attributes.
- Drag/reference items into Collection/Task where compatible.

## Out of Scope

- No WholeHouse-specific faceting.

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

- [x] Generic catalog works before WholeHouse installation.

## Final Ownership Evidence

Before: Resources had no generic Catalog category, item list, attribute filter,
or version inspector; Catalog data could only be reached through backend API
commands.

After: `CatalogService` and `SqliteCatalogRepository` remain the canonical
Catalog owners; `asset-manager.html` exposes the generic Catalog category and
`catalog-library.js` owns presentation/filter/reference-payload behavior.

Duplicate owner removed: none introduced; the page does not persist or mutate
Catalog records directly and no Canvas runtime was added.

Developer verification: focused Catalog persistence/UI/resource-shell tests
passed (11 tests); `./scripts/agent-verify.sh` passed (1314 tests, 276 Python
AST files, 153 JavaScript files, 4 architecture guards, clean `git diff --check`).
Browser acceptance opened the Resources → 目录 surface before WholeHouse
installation and verified the generic empty state and catalog-specific controls.

Independent Review: PASS. The active card was reviewed against its DoD,
canonical ownership and architecture constraints before archival.

## Next Recommended Card

`R10-01`

Do not execute the next card in the same Agent run.
