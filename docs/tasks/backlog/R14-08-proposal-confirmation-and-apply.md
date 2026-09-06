# CARD R14-08 — Proposal Confirmation and Apply

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-07

## Goal

Apply Agent proposals only through explicit confirmation/application boundary.

## Before Owner

proposal-only

## After Owner

confirmed application service mutation

## In Scope

- Add confirmation UI/action.
- Revalidate revision/authorization.
- Audit apply/reject.

## Out of Scope

- No bypass path for Agent.

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

- [ ] Confirmed valid proposal applies; stale/rejected proposal does not.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-09`

Do not execute the next card in the same Agent run.
