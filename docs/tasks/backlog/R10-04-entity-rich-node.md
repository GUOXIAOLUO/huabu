# CARD R10-04 — Entity Rich Node

- Round: R10
- Priority: P1
- Status: BACKLOG
- Depends on: R10-03

## Goal

Render/edit generic entity data through Rich Node/Inspector.

## Before Owner

no entity UX

## After Owner

Entity Rich Node

## In Scope

- Definition-driven fields.
- Version-aware edit flow.
- Show relations.

## Out of Scope

- No industry-specific fields in Core.

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

- [ ] Package entity definitions can drive UI later.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-05`

Do not execute the next card in the same Agent run.
