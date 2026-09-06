# CARD R15-08 — Site Analysis Skill

- Round: R15
- Priority: P1
- Status: BACKLOG
- Depends on: R15-07

## Goal

Analyze site photos/measurements/constraints as a separate reusable Skill.

## Before Owner

manual site review

## After Owner

WholeHouse Site Analysis Skill

## In Scope

- Define site photo Collection and notes inputs.
- Produce SiteAnalysis Artifact.
- Link room/space entities where available.

## Out of Scope

- No hidden computer vision claims beyond model capability.

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

- [ ] Output is structured and traceable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-09`

Do not execute the next card in the same Agent run.
