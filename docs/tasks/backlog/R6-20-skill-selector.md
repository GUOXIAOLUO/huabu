# CARD R6-20 — Skill Selector

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-19

## Goal

Let users choose Skills inside a generic Task Rich Node.

## Before Owner

manual/legacy task capability selection

## After Owner

Skill selector UI

## In Scope

- Support search/recent/recommended/installed packs.
- Bind selected skill through SkillBinding.
- Keep Task NodeKind unchanged.

## Out of Scope

- No industry-specific Task node types.

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

- [ ] Changing Skill changes binding, not NodeKind.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-21`

Do not execute the next card in the same Agent run.
