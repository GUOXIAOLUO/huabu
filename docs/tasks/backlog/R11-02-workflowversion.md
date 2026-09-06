# CARD R11-02 — WorkflowVersion

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-01

## Goal

Make workflow definitions immutable/versioned.

## Before Owner

mutable workflow config

## After Owner

WorkflowVersion

## In Scope

- Implement versioning/current pointer.
- Preserve old runs pinned to exact version.

## Out of Scope

- No destructive rewrite of historical workflows.

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

- [ ] Runs resolve exact workflow version.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-03`

Do not execute the next card in the same Agent run.
