# CARD R6-08 — Collection Grid and List Views

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS
- Depends on: R6-07

## Goal

Add generic grid/list presentations for collections.

## Before Owner

gallery-only collection UX

## After Owner

multi-view Collection presentation

## In Scope

- Implement list/grid switch.
- Preserve selection/order.
- Keep view state separate from collection data semantics.

## Out of Scope

- No advanced query builder.

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

- `tests/test_collection_rich_node.py` — R6-08 grid/list persistence,
  semantic immutability, real Registry → NodeShell → Gallery remount recovery,
  and selection/order preservation across both layouts.
- Full `./scripts/agent-verify.sh` PASS: 723 tests, 117 Python AST files,
  123 JavaScript files, 4 architecture guards, clean diff check.

## Definition of Done

- [x] View switch does not mutate semantic collection content.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.

## Final Ownership Evidence

Before:

Gallery-only Collection presentation with no independent view-mode state.

After:

Collection Rich Node owns presentation-only grid/list state and controls while
Collection data retains ownership of items, order, and references.

Duplicate owner removed:

No duplicate view-state or Collection semantic-data owner introduced.

## Next Recommended Card

`R6-09`

Do not execute the next card in the same Agent run.
