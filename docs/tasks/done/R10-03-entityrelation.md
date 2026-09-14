# CARD R10-03 — EntityRelation

- Round: R10
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: R10-02

## Goal

Represent generic typed relations between entities/resources.

## Before Owner

implicit links

## After Owner

EntityRelation

## In Scope

- Define relation type/from/to/metadata/version behavior.
- Add query service.

## Out of Scope

- Do not replace Canvas Edge; different concern.

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

- [x] Relations are queryable outside Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Business relations had no generic Core record, project-scoped
persistence, or query service; Canvas Edge was the only graph relationship
surface.

After: `EntityRelation` owns immutable project-scoped typed endpoints,
relation type, metadata and revision. `SqliteEntityRelationRepository` is the
canonical persistence/query owner; `EntityRelationService` is the authorized
application boundary and `/api/v1/entity-relations` exposes creation and
filterable queries outside Canvas. Version-pinned endpoints retain the
resource and version identity without changing Canvas Edge semantics.

Duplicate owner removed: none. Canvas Edge remains graph topology; EntityRelation
is a separate business/resource relation and no second Canvas runtime or
WholeHouse-specific relation types were added.

Developer verification: focused Entity domain/version/relation/Current Truth
suite passed (15 tests); `./scripts/agent-verify.sh` passed (1327 tests, 287
Python AST files, 153 JavaScript files, 4 architecture guards, clean
`git diff --check`).

Independent Review: PASS. The active card was reviewed against its DoD,
canonical ownership and architecture constraints before archival.

## Next Recommended Card

`R10-04`

Do not execute the next card in the same Agent run.
