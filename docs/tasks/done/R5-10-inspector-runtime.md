# CARD R5-10 — Inspector Runtime

- Round: R5
- Priority: P1
- Status: DONE
- Previous implementation: COMPLETE — re-executed 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-09

## Goal

Create one right-side Inspector owner instead of renderer-specific side panels.

## Before Owner

renderer/page-specific inspectors

## After Owner

InspectorRegistry + InspectorPanel

## In Scope

- Define inspector contribution contract.
- Support metadata/history/version/execution placeholder sections.
- Bind to current selection.

## Out of Scope

- Do not implement future domain data that does not exist yet.

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

- [x] One inspector owner remains.
- [x] Generic nodes can contribute sections.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: NodeInspector exposed renderer-neutral view models, but there was no single panel owner bound to Canvas selection.

After: `InspectorPanel` owns the right-side inspector DOM, selection visibility, generic metadata/history/version/execution sections, and renderer-contributed sections through `NodeInspector`.

Duplicate owner removed: Canvas render flow now binds the current selection to one InspectorPanel; renderer/page code contributes view-model sections only and does not create competing inspector panels.

Verification: focused InspectorPanel tests pass (3 tests), including single /
multi-selection rendering, Canvas binding, and generic renderer-contributed
sections. `./scripts/agent-verify.sh` passes (692 tests, 104 Python AST files,
121 JavaScript files, 4 architecture guards, clean diff check). Developer Git
Review PASS; independent Review PENDING.

## Next Recommended Card

`R5-11`

Do not execute the next card in the same Agent run.
