# CARD R11-03 — WorkflowStep Contract

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-02

## Goal

Define generic workflow step kinds through actions/definitions.

## Before Owner

ad hoc step behavior

## After Owner

WorkflowStep

## In Scope

- Support invoke Skill/human wait/approval/integration/artifact action abstractions.
- Define inputs/outputs/transitions.

## Out of Scope

- No WholeHouse step kinds in Core.

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

- [ ] Step contract can express generic end-to-end flow.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-04`

Do not execute the next card in the same Agent run.
