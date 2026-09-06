# CARD R17-06 — Studio KPI Baseline

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R17-05

## Goal

Quantify whether Workbench improves real studio design workflow.

## Before Owner

qualitative impressions

## After Owner

measured KPI baseline

## In Scope

- Measure prep time/data organization/design AI usage/human time/adoption/rework/handoff error rate.
- Compare across validated projects where possible.

## Out of Scope

- No fabricated ROI.

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

- [ ] Metrics and measurement caveats are documented.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-07`

Do not execute the next card in the same Agent run.
