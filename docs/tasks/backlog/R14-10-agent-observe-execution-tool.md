# CARD R14-10 — Agent observe_execution Tool

- Round: R14
- Priority: P1
- Status: BACKLOG
- Depends on: R14-09

## Goal

Let Agent observe ExecutionRun/events/results safely.

## Before Owner

manual run monitoring

## After Owner

observe_execution tool

## In Scope

- Read run status/events/result refs.
- Support wait/poll/stream at safe abstraction.
- Bound output volume.

## Out of Scope

- No raw executor transport events required.

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

- [ ] Agent can reason about completed/failed runs through normalized model.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-11`

Do not execute the next card in the same Agent run.
