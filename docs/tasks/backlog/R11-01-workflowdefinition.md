# CARD R11-01 — WorkflowDefinition

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R10-08

## Goal

Define business workflow independently from executor-native graphs.

## Before Owner

legacy workflow configs/archives

## After Owner

WorkflowDefinition

## In Scope

- Define workflow id/versioned structure/steps/transitions/input-output contracts.
- Keep executor workflow refs external.

## Out of Scope

- Do not model ComfyUI graph as business workflow.

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

- [ ] Business workflow schema is executor-neutral.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-02`

Do not execute the next card in the same Agent run.
