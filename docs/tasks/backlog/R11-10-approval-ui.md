# CARD R11-10 — Approval UI

- Round: R11
- Priority: P1
- Status: BACKLOG
- Depends on: R11-09

## Goal

Add request/review/decision UI in Inspector/Workflow.

## Before Owner

no governed approval UX

## After Owner

Approval UI

## In Scope

- Show target version and changes.
- Capture decision/comment.
- Expose frozen status clearly.

## Out of Scope

- No domain-specific approval screens.

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

- [ ] Human can review exact version before approving/freezing.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-11`

Do not execute the next card in the same Agent run.
