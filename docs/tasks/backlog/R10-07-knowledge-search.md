# CARD R10-07 — Knowledge Search

- Round: R10
- Priority: P1
- Status: BACKLOG
- Depends on: R10-06

## Goal

Provide scoped search/query for project/package knowledge.

## Before Owner

manual context selection

## After Owner

Knowledge service

## In Scope

- Implement lexical/metadata search first.
- Return provenance and scope.
- Expose API/Resource UI.

## Out of Scope

- Semantic/vector search can be later.

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

- [ ] Skills/Agent can retrieve knowledge through one boundary.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-08`

Do not execute the next card in the same Agent run.
