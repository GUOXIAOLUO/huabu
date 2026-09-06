# CARD R8-20 — Regenerate and Branch

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-19

## Goal

Create new runs/attempt branches from selected results/inputs.

## Before Owner

manual rerun

## After Owner

Execution branch action

## In Scope

- Define regenerate using same snapshot/policy override.
- Preserve lineage to source run/result.
- Show branch in history.

## Out of Scope

- No destructive overwrite of prior run.

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

- [ ] Every regeneration has lineage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-21`

Do not execute the next card in the same Agent run.
