# CARD R16-02 — WholeHouse Product Knowledge

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-01

## Goal

Add product/application knowledge linked to catalog items.

## Before Owner

catalog attributes only

## After Owner

product knowledge layer

## In Scope

- Attach verified usage/design constraints.
- Link to item/version refs.
- Support search.

## Out of Scope

- No inventory/ordering system.

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

- [ ] Product selection can cite structured knowledge.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-03`

Do not execute the next card in the same Agent run.
