# CARD R11-05 — WorkflowStepRun

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-04

## Goal

Track each workflow step execution/human wait outcome.

## Before Owner

coarse workflow state

## After Owner

WorkflowStepRun

## In Scope

- Persist step status/inputs/outputs/linked executions/approvals.
- Support resume after restart.

## Out of Scope

- No Agent auto-approval.

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

- [ ] Workflow can pause/resume deterministically.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-06`

Do not execute the next card in the same Agent run.
