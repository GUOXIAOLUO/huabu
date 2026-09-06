# CARD R6-04 — Edge / InputBinding Separation

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-03

## Goal

Make graph relation and execution data binding explicitly separate concepts.

## Before Owner

edge-implied input assumptions

## After Owner

separate GraphRelation + InputBinding semantics

## In Scope

- Audit places where an Edge is treated as runtime input.
- Route true data binding through InputBinding.
- Keep visual/semantic edges independent.

## Out of Scope

- Do not remove useful graph visualization.

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

- [ ] No normal execution-data path depends solely on an Edge.
- [ ] Tests demonstrate Edge can exist without input binding and vice versa.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-05`

Do not execute the next card in the same Agent run.
