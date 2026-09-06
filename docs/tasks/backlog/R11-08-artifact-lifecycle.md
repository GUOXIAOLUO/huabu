# CARD R11-08 — Artifact Lifecycle

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-07

## Goal

Formalize Draft → Formal → Approved → Frozen lifecycle.

## Before Owner

informal output status

## After Owner

governed Artifact state machine

## In Scope

- Define allowed transitions.
- Link approvals.
- Prevent mutation of Frozen versions.

## Out of Scope

- AI completed is not Approved.

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

- [ ] Invalid transitions are rejected.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-09`

Do not execute the next card in the same Agent run.
