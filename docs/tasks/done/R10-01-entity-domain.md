# CARD R10-01 — Entity Domain

- Round: R10
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-14)
- Depends on: R9-15

## Goal

Define generic business/entity identity and schema-driven types.

## Before Owner

ad hoc project/business fields

## After Owner

Entity

## In Scope

- Define entity id/type/schema/project/state/metadata.
- Allow package-defined entity definitions later.

## Out of Scope

- No Customer/Room hardcoded Core classes.

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

- [x] Core supports generic entity definitions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Core had no canonical EntityDefinition, EntitySchema, or EntityRecord
domain owner; entity-shaped values only appeared as unowned compatibility data.

After: `workbench/domain/entity` owns generic EntityDefinition, EntitySchema,
EntityPropertyDefinition and project-owned EntityRecord contracts. Entity
definitions carry a generic entity type and schema; records carry project
identity, definition reference, properties, state and metadata.

Duplicate owner removed: none introduced. EntityVersion, Relation,
repository/service/API and package-specific entity classes remain out of scope
for this card.

Developer verification: focused Entity domain and Current Truth tests passed
(5 tests); `./scripts/agent-verify.sh` passed (1317 tests, 279 Python AST
files, 153 JavaScript files, 4 architecture guards, clean `git diff --check`).

Independent Review: PASS. The active card was reviewed against its DoD,
canonical ownership and architecture constraints before archival.

## Next Recommended Card

`R10-02`

Do not execute the next card in the same Agent run.
