# CARD R6-11 — Binding Table

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-10

## Goal

Represent one execution item per row using Collection-backed binding tables.

## Before Owner

many edges/ad hoc arrays

## After Owner

Binding Table projection

## In Scope

- Define row-to-input-role mapping.
- Support multiple typed columns.
- Expose validation for missing required cells.

## Out of Scope

- No actual batch run yet.

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

- [ ] A row deterministically projects to a set of InputBindings.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-12`

Do not execute the next card in the same Agent run.
