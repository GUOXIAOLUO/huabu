# CARD R13-04 — Common Compare Skill

- Round: R13
- Priority: P1
- Status: BACKLOG
- Depends on: R13-03

## Goal

Add generic compare Skill over multiple resources/results.

## Before Owner

manual compare only

## After Owner

Common compare Skill

## In Scope

- Define collection/multi-input schema.
- Return structured comparison artifact/result.
- Use Result Compare workspace where appropriate.

## Out of Scope

- No WholeHouse design-review rules.

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

- [ ] Generic compare works across supported resources.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-05`

Do not execute the next card in the same Agent run.
