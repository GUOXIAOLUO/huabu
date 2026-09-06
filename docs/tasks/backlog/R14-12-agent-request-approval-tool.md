# CARD R14-12 — Agent request_approval Tool

- Round: R14
- Priority: P1
- Status: BACKLOG
- Depends on: R14-11

## Goal

Allow Agent to request, but never grant, human approval.

## Before Owner

manual approval request only

## After Owner

request_approval tool

## In Scope

- Create Approval request through service.
- Show exact target version/reason.
- Notify/route to human UI.

## Out of Scope

- Agent cannot approve or freeze.

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

- [ ] Tests prove request-only boundary.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-13`

Do not execute the next card in the same Agent run.
