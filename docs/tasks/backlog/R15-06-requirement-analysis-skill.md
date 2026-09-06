# CARD R15-06 — Requirement Analysis Skill

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-05

## Goal

Implement executable wholehouse.requirement-analysis.

## Before Owner

manual requirement interpretation

## After Owner

WholeHouse Requirement Analysis Skill

## In Scope

- Define inputs for customer/requirement docs/images.
- Define structured RequirementReport Artifact output.
- Provide prompt/skill parameters and compatible execution route.

## Out of Scope

- No project-specific hidden assumptions.

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

- [ ] Realistic sample produces traceable RequirementReport.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-07`

Do not execute the next card in the same Agent run.
