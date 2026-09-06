# CARD R7-06 — Model Selector UI

- Round: R7
- Priority: P1
- Status: BACKLOG
- Depends on: R7-05

## Goal

Expose Auto/compatible model selection in Task without provider plumbing overload.

## Before Owner

provider-shaped selectors

## After Owner

ModelAvailability selector

## In Scope

- Show compatible entries.
- Support Auto while preserving resolved route visibility.
- Show unavailable reason when relevant.

## Out of Scope

- Do not expose credentials in node UI.

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

- [ ] Task binds availability/selection separately from Skill.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-07`

Do not execute the next card in the same Agent run.
