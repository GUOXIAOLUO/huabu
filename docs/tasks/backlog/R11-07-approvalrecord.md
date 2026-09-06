# CARD R11-07 — ApprovalRecord

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-06

## Goal

Create explicit human approval records linked to artifact/workflow state.

## Before Owner

implicit/manual confirmation

## After Owner

Approval

## In Scope

- Define request/decision/requester/approver/comment/time/target version.
- Add authorization seam.

## Out of Scope

- Agent/executor cannot self-approve.

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

- [ ] Approval decisions are auditable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-08`

Do not execute the next card in the same Agent run.
