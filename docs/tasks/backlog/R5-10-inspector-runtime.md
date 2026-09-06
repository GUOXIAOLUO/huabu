# CARD R5-10 — Inspector Runtime

- Round: R5
- Priority: P1
- Status: BACKLOG
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

- [ ] One inspector owner remains.
- [ ] Generic nodes can contribute sections.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-11`

Do not execute the next card in the same Agent run.
