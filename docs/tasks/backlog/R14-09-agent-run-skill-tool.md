# CARD R14-09 — Agent run_skill Tool

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-08

## Goal

Allow Agent to request generic Skill execution through ExecutionService.

## Before Owner

human-only execution

## After Owner

run_skill tool

## In Scope

- Resolve Task/Skill/inputs/profile.
- Respect confirmation policy.
- Return run ref and normalized status.

## Out of Scope

- Agent cannot choose unavailable hidden fallback.

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

- [ ] Tool uses same execution path as human UI.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-10`

Do not execute the next card in the same Agent run.
