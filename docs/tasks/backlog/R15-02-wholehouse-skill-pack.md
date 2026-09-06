# CARD R15-02 — WholeHouse Skill Pack

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-01

## Goal

Register the initial WholeHouse work capabilities as Skills.

## Before Owner

planned skill list

## After Owner

WholeHouse SkillPack

## In Scope

- Define requirement-analysis/floorplan-analysis/site-analysis/space-concept/material-selection/product-selection/render-review/design-review/cad-review/handoff-check definitions.
- Use generic Task Rich Node presentation.

## Out of Scope

- Do not create permanent WholeHouse NodeKinds.

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

- [ ] WholeHouse capabilities appear in generic Skill selector.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-03`

Do not execute the next card in the same Agent run.
