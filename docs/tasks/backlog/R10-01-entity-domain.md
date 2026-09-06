# CARD R10-01 — Entity Domain

- Round: R10
- Priority: P0
- Status: BACKLOG
- Depends on: R9-15

## Goal

Define generic business/entity identity and schema-driven types.

## Before Owner

ad hoc project/business fields

## After Owner

Entity

## In Scope

- Define entity id/type/schema/project/state/metadata.
- Allow package-defined entity definitions later.

## Out of Scope

- No Customer/Room hardcoded Core classes.

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

- [ ] Core supports generic entity definitions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-02`

Do not execute the next card in the same Agent run.
