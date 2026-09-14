# CARD R10-02 — EntityVersion

- Round: R10
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: R10-01

## Goal

Version meaningful entity state changes.

## Before Owner

mutable entity data

## After Owner

EntityVersion

## In Scope

- Define version payload/author/time/lineage.
- Add repository/service/API.

## Out of Scope

- No approval semantics.

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

- [x] Entity refs can pin versions when required.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: EntityRecord carried mutable project state without a canonical version
record, repository, service, or API; typed collection references had no
EntityVersion address object.

After: `EntityVersion` owns immutable state snapshots with author, timestamp,
ordinal and explicit lineage. `SqliteEntityRepository` persists append-only
versions and advances the EntityRecord current-version projection; the
authorized `EntityService` and `/api/v1/entities` API expose creation,
append, list and pinned-version reads. `EntityVersionRef` carries both entity
and version identity for pinned references.

Duplicate owner removed: none introduced. EntityRecord remains the stable
identity/current projection, EntityVersion owns historical state, and no
approval semantics, WholeHouse type, Canvas runtime, or second persistence
owner was added.

Developer verification: focused Entity domain/version/Current Truth suite
passed (10 tests); `./scripts/agent-verify.sh` passed (1322 tests, 283 Python
AST files, 153 JavaScript files, 4 architecture guards, clean
`git diff --check`).

Independent Review: PASS. The active card was reviewed against its DoD,
canonical ownership and architecture constraints before archival.

## Next Recommended Card

`R10-03`

Do not execute the next card in the same Agent run.
