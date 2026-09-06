# CARD R16-08 — WholeHouse Standard Workflow

- Round: R16
- Priority: P0
- Status: BACKLOG
- Depends on: R16-07

## Goal

Compose the main design workflow from generic Workflow/Skill/Approval/Handoff primitives.

## Before Owner

manual sequence

## After Owner

WholeHouse workflow template

## In Scope

- Create Requirement → Floorplan/Site → Space Concept → Material/Product → Render/Review → Approval/Frozen → Handoff workflow.
- Use exact Skill refs/versions.

## Out of Scope

- No production/install/after-sales steps.

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

- [ ] Workflow runs/restarts/audits end to end.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-09`

Do not execute the next card in the same Agent run.
