# CARD R14-03 — Agent search_resources Tool

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-02

## Goal

Expose Resource search through safe Agent tool.

## Before Owner

no agent resource tool

## After Owner

search_resources

## In Scope

- Wrap Resource service/query.
- Return refs/provenance/summary.
- Respect project scope.

## Out of Scope

- No arbitrary filesystem search.

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

- [ ] Agent receives resource refs, not secret/raw persistence access.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-04`

Do not execute the next card in the same Agent run.
