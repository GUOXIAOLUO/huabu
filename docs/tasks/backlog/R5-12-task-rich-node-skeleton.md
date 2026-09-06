# CARD R5-12 — Task Rich Node Skeleton

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-11

## Goal

Create the generic Task Rich Node shell before Skill/Execution exists.

## Before Owner

no stable generic task UX

## After Owner

Task Rich Node skeleton

## In Scope

- Define generic task presentation fields.
- Add inputs/definition/skill placeholder/status/workspace/inspector slots.
- Persist only generic task metadata available in R5.

## Out of Scope

- No real Skill Registry.
- No real model execution.

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

- [ ] Task is a generic NodeKind/presentation, not an industry node.
- [ ] Reload preserves Task state.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-13`

Do not execute the next card in the same Agent run.
