# CARD R6-09 — Collection Table Workspace

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-08

## Goal

Implement the multi-dimensional table workspace as a first-class Rich Node workspace.

## Before Owner

no structured table workspace

## After Owner

Collection Table Workspace

## In Scope

- Render rows/columns with typed cells.
- Support text/reference cells, row/column add/edit, ordering, basic sort/filter.
- Respect WorkspaceSession dirty/save lifecycle.

## Out of Scope

- No spreadsheet formula engine.
- No Execution Runtime.

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

- [ ] Table edits persist correctly.
- [ ] Reference cells point to resources rather than copying data.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-10`

Do not execute the next card in the same Agent run.
