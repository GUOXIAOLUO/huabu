# CARD R6-10 — Quick Collection

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-09

## Goal

Create a Collection quickly from selected resources/nodes.

## Before Owner

manual/ad hoc grouping

## After Owner

Quick Collection action

## In Scope

- Add multi-select action contribution.
- Create collection from eligible references.
- Prompt for title minimally and preserve order.

## Out of Scope

- Do not conflate with Group.

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

- [ ] Selected resources can become a Collection without changing visual Group semantics.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-11`

Do not execute the next card in the same Agent run.
