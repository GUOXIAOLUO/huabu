# CARD R6-11 — Binding Table

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-11
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

- [x] A row deterministically projects to a set of InputBindings.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Collection rows had typed cells but no row-to-input projection or required-cell validation.

After:

`WorkbenchBindingTable` maps each ordered row and typed column to deterministic
`InputBinding` payloads, applies column input-role/target metadata, and reports
missing required or mismatched cells. CollectionTableWorkspace exposes row and
collection projections without owning execution.

Duplicate owner removed:

No edge or batch-execution owner was introduced; existing Collection persistence
and Canvas graph ownership remain unchanged.

## Independent Review

PASS — the current Active Task review verified the DoD, typed row projection,
required-cell and reference-type validation, architecture constraints, and
Collection/Graph ownership separation. Focused and full verification passed.

## Next Recommended Card

`R6-12`

Do not execute the next card in the same Agent run.
