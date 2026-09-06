# CARD R16-09 — WholeHouse Project Knowledge Memory

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-08

## Goal

Accumulate approved decisions, constraints and rejected options as project-scoped knowledge.

## Before Owner

conversation/manual memory

## After Owner

project knowledge entries

## In Scope

- Create entries from approved/frozen design decisions by explicit workflow/action.
- Preserve provenance/state.
- Retrieve in later Skills.

## Out of Scope

- Do not silently treat every AI suggestion as memory/fact.

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

- [ ] Only governed/explicitly accepted information becomes durable project knowledge.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-01`

Do not execute the next card in the same Agent run.
