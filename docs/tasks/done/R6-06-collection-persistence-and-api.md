# CARD R6-06 — Collection Persistence and API

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS 2026-09-11
- Depends on: R6-05

## Goal

Persist Collections canonically and expose application/API boundaries.

## Before Owner

in-memory/ad hoc structures

## After Owner

CollectionRepository + service/API

## In Scope

- Add SQLite persistence.
- Add CRUD/query service.
- Add canonical API and tests.

## Out of Scope

- No batch execution yet.

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

- `tests/test_collection_persistence_api.py` — 3 focused tests PASS.
- Full `./scripts/agent-verify.sh` PASS: 715 tests, 116 Python AST files,
  121 JavaScript files, 4 architecture guards, clean diff check.

## Definition of Done

- [x] Collections survive SQLite restart and can be referenced by id through
  the repository and canonical `/api/v1/collections` API.

## Final Ownership Evidence

Before: Collection records had only the R6-05 domain model; no canonical
repository, application service, or versioned transport existed.

After: `SqliteCollectionRepository` owns durable aggregate payloads and
revision CAS; `CollectionService` owns commands/queries; the canonical API
owns transport validation and error mapping. Project membership authorization
and the existing audit outbox are enforced at the repository boundary.

Duplicate owner removed: none identified; no batch execution or legacy
Collection persistence path was added.

## Independent Review

PASS — verified against this card's DoD, repository/service/API ownership,
SQLite restart behavior, project authorization, revision conflict behavior,
canonical API CRUD/query behavior, architecture constraints, and recorded
test results.

## Next Recommended Card

`R6-07`

Do not execute the next card in the same Agent run.
