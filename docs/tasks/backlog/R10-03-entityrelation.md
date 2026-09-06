# CARD R10-03 — EntityRelation

- Round: R10
- Priority: P0
- Status: BACKLOG
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

- [ ] Relations are queryable outside Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-04`

Do not execute the next card in the same Agent run.
