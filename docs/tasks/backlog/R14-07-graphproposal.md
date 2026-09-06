# CARD R14-07 — GraphProposal

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-06

## Goal

Let Agent propose bounded graph mutations with base_revision.

## Before Owner

no safe graph agent mutation

## After Owner

GraphProposal

## In Scope

- Define create/update/connect/remove proposal operations.
- Require base_revision and reason.
- Validate through application services.

## Out of Scope

- No raw Canvas JSON patch.

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

- [ ] Stale proposal cannot apply silently.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-08`

Do not execute the next card in the same Agent run.
