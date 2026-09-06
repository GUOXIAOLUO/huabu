# CARD R5-08 — Presentation State Model

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-07

## Goal

Introduce card / expanded / workspace / inspector presentation states.

## Before Owner

ad hoc node expansion/editor states

## After Owner

generic presentation state

## In Scope

- Define presentation state and transitions.
- Persist only what is appropriate.
- Integrate with NodeShell and selection without duplicating Canvas state.

## Out of Scope

- No specialized workspaces yet.

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

- [ ] Node can transition predictably between presentation states.
- [ ] Reload behavior is characterized.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-09`

Do not execute the next card in the same Agent run.
