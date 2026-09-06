# CARD R12-07 — Package Settings UI

- Round: R12
- Priority: P1
- Status: BACKLOG
- Depends on: R12-06

## Goal

Manage installed/enabled/project packages under Settings without new top-level nav.

## Before Owner

no package management UX

## After Owner

Package settings

## In Scope

- List packages/versions/status.
- Enable/lock/migrate with warnings.
- Show provided capabilities.

## Out of Scope

- No marketplace required.

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

- [ ] Users can understand which package powers project capabilities.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-08`

Do not execute the next card in the same Agent run.
