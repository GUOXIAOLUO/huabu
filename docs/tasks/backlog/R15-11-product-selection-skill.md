# CARD R15-11 — Product Selection Skill

- Round: R15
- Priority: P1
- Status: BACKLOG
- Depends on: R15-10

## Goal

Recommend/select product/catalog options for spaces/design decisions.

## Before Owner

manual product selection

## After Owner

WholeHouse Product Selection Skill

## In Scope

- Use product catalog/constraints.
- Produce ProductProposal/selection refs.
- Allow Collection candidates.

## Out of Scope

- No purchasing/ERP integration.

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

- [ ] Selections are version-pinned and reviewable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-12`

Do not execute the next card in the same Agent run.
