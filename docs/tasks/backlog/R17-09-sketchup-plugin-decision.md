# CARD R17-09 — SketchUp Plugin Decision

- Round: R17
- Priority: P1
- Status: BACKLOG
- Depends on: R17-08

## Goal

Decide whether the backup SketchUp design/breakdown plugin is warranted.

## Before Owner

planned backup idea

## After Owner

evidence-backed go/no-go decision

## In Scope

- Compare current Workbench+handoff limitations.
- Define SU plugin value/scope/integration boundary if needed.
- Record go/no-go/defer decision.

## Out of Scope

- Do not start SU plugin implementation here.

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

- [ ] Decision is based on validated studio needs and keeps SU outside Core.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`POST-R17`

Do not execute the next card in the same Agent run.
