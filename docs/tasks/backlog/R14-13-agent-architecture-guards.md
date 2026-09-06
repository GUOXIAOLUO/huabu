# CARD R14-13 — Agent Architecture Guards

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-12

## Goal

Make forbidden Agent access mechanically testable.

## Before Owner

policy/documentation only

## After Owner

architecture guard tests

## In Scope

- Guard against direct DOM mutation modules.
- Guard direct SQLite/repository imports from Agent layer.
- Guard raw Canvas persistence mutation and approval bypass.

## Out of Scope

- No weakening guards for convenience.

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

- [ ] Forbidden dependency tests fail on intentional violations and pass current code.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-01`

Do not execute the next card in the same Agent run.
