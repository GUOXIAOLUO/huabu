# CARD R6-16 — SkillDefinition

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-15

## Goal

Define Skill as a generic versioned capability contract.

## Before Owner

legacy feature-specific actions

## After Owner

SkillDefinition

## In Scope

- Define id/version/package/title/description/input/output/parameter schemas/capability requirements/prompt/presentation/workspace/execution route metadata.
- Keep execution routes declarative.

## Out of Scope

- No executor implementation.
- No WholeHouse skill definitions yet.

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

- [ ] SkillDefinition contains no provider SDK or industry assumptions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-17`

Do not execute the next card in the same Agent run.
