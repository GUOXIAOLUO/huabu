# CARD R6-09 — Collection Table Workspace

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-11
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

- `tests/test_collection_table_workspace.py` — typed literal/reference edits,
  row/column operations, sort/filter, dirty/save lifecycle, semantic
  immutability, and Rich Node workspace mounting.
- Full `./scripts/agent-verify.sh` PASS: 728 tests, 118 Python AST files,
  125 JavaScript files, 4 architecture guards, clean diff check.

## Definition of Done

- [x] Table edits persist correctly through the injected application save boundary.
- [x] Reference cells retain typed resource references rather than copying data.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

No structured Collection table workspace; Collection presentation was gallery-only.
After:

CollectionTableWorkspace owns the editable table projection, typed cell
validation, row/column operations, sort/filter state, and dirty/save intents.
Collection persistence remains owned by the injected application callback.
Duplicate owner removed:

No raw Canvas/Collection persistence path or second Collection semantic owner was
introduced.
## Next Recommended Card

`R6-10`

Do not execute the next card in the same Agent run.
