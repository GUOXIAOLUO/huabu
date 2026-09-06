# CARD R10-02 — EntityVersion

- Round: R10
- Priority: P0
- Status: BACKLOG
- Depends on: R10-01

## Goal

Version meaningful entity state changes.

## Before Owner

mutable entity data

## After Owner

EntityVersion

## In Scope

- Define version payload/author/time/lineage.
- Add repository/service/API.

## Out of Scope

- No approval semantics.

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

- [ ] Entity refs can pin versions when required.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-03`

Do not execute the next card in the same Agent run.
