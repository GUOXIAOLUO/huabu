# CARD R13-02 — Common Image Analysis Skill

- Round: R13
- Priority: P0
- Status: BACKLOG
- Depends on: R13-01

## Goal

Implement a real executable generic image-analysis Skill.

## Before Owner

R6 proof definition

## After Owner

Common image-analysis Skill

## In Scope

- Define input/output schemas/prompt/capabilities/presentation.
- Bind to available execution route.
- Produce formal/preview result.

## Out of Scope

- No industry assumptions.

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

- [ ] Image asset → Task → Skill → Execution → Result works.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-03`

Do not execute the next card in the same Agent run.
