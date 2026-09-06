# CARD R9-04 — Resource Library Shell

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-03

## Goal

Create unified Resources UI shell without adding top-level navigation.

## Before Owner

scattered asset/prompt/skill UX

## After Owner

Resource Library

## In Scope

- Create category/search/filter layout.
- Integrate Asset/Collection/Prompt/Skill entry points.
- Keep extensible resource registry.

## Out of Scope

- No new top-level nav categories.

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

- [ ] Resources are reachable under one top-level section.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-05`

Do not execute the next card in the same Agent run.
