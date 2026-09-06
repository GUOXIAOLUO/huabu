# CARD R9-01 — Asset Domain

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R8-22

## Goal

Define Asset as external/input resource identity.

## Before Owner

file + JSON metadata

## After Owner

Asset

## In Scope

- Define asset identity/project/source/type/status/metadata.
- Separate identity from versions.

## Out of Scope

- No WholeHouse asset subclasses in Core.

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

- [ ] Asset can reference multiple immutable versions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-02`

Do not execute the next card in the same Agent run.
