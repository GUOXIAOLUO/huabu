# CARD R6-19 — SkillBinding

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-18

## Goal

Bind a Skill version and parameters to a generic Task Rich Node.

## Before Owner

Task skill placeholder

## After Owner

typed SkillBinding

## In Scope

- Define skill id/version/enabled/parameters/prompt override/execution profile ref.
- Persist on Task.
- Validate against SkillDefinition schema.

## Out of Scope

- No execution.

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

- [ ] Task reload restores exact Skill version and parameters.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-20`

Do not execute the next card in the same Agent run.
