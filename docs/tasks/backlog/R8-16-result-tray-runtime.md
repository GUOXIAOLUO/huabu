# CARD R8-16 — Result Tray Runtime

- Round: R8
- Priority: P0
- Status: BACKLOG
- Depends on: R8-15

## Goal

Make execution outputs land in a non-Canvas result staging area by default.

## Before Owner

outputs auto/legacy materialization

## After Owner

Result Tray

## In Scope

- Define tray session/items linked to run/attempt outputs.
- Render generic result cards.
- Keep outputs non-materialized by default.

## Out of Scope

- No automatic Node creation.

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

- [ ] Run outputs appear in tray without polluting Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-17`

Do not execute the next card in the same Agent run.
