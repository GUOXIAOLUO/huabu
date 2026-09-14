# CARD R9-13 — Generic Catalog Domain

- Round: R9
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
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

- [x] Generic catalogs persist and version items.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: no canonical Catalog, CatalogItem or CatalogItemVersion domain or
persistence owner existed; product lists were ad hoc and not versioned.

After: generic `Catalog`, `CatalogItem` and immutable `CatalogItemVersion` are
owned by `workbench/domain/catalog`; `CatalogService` validates item attributes
and `SqliteCatalogRepository` persists catalog/item/version records for both
workspace and project scope.

Duplicate owner removed: none. Existing Collection, Asset and Artifact owners
remain separate; Catalog media references point to those resources without
collapsing their identities.

## Developer Verification

- Added generic attribute schema and typed Asset/Artifact media references.
- Added workspace/project-scoped Catalog persistence with atomic first ItemVersion
  creation and append-only item version ordinals.
- Added canonical Catalog API routes and composition wiring.
- Focused suite: `tests.test_catalog_domain` and
  `tests.test_catalog_persistence_api` plus current-fact checks — **7 tests PASS**.
- Full `./scripts/agent-verify.sh`: **PASS — 1311 tests**, 275 Python AST files,
  152 JavaScript files, 4 architecture guards, and clean `git diff --check`.

## Next Recommended Card

`R9-14`

Do not execute the next card in the same Agent run.
