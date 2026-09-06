# CARD R4-07 — Remote Sync Uses Revision

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-06

## Goal

Make remote/window synchronization compare canonical revisions instead of timestamps.

## Before Owner

updatedAt comparison

## After Owner

logical revision comparison

## In Scope

- Characterize current remote sync.
- Replace normal timestamp ordering with revision ordering.
- Test stale second-window save and refresh/adopt flow.

## Out of Scope

- No UI redesign.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] Two-window stale conflict is deterministic.
- [ ] Remote apply cannot regress to an older revision.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-08`

Do not execute the next card in the same Agent run.
