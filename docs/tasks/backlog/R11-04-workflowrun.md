# CARD R11-04 — WorkflowRun

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-03

## Goal

Persist business workflow runs.

## Before Owner

transient workflow state

## After Owner

WorkflowRun

## In Scope

- Define run/version/status/context/timestamps.
- Add service/API.

## Out of Scope

- No hidden executor state as authority.

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

- [ ] Workflow run survives restart.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-05`

Do not execute the next card in the same Agent run.
