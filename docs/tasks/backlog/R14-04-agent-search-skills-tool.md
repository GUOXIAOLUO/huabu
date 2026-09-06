# CARD R14-04 — Agent search_skills Tool

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-03

## Goal

Expose Skill discovery through safe Agent tool.

## Before Owner

no agent skill discovery

## After Owner

search_skills

## In Scope

- Wrap SkillRegistry.
- Return compatibility/capability metadata.
- Respect installed packages.

## Out of Scope

- No direct registry mutation.

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

- [ ] Agent can discover WholeHouse later without hardcoded knowledge.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-05`

Do not execute the next card in the same Agent run.
