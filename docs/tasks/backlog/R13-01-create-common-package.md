# CARD R13-01 — Create Common Package

- Round: R13
- Priority: P0
- Status: BACKLOG
- Depends on: R12-12

## Goal

Move generic reusable skills/definitions into packages/common.

## Before Owner

Core/generic scattered features

## After Owner

Common Package

## In Scope

- Create manifest/structure.
- Register through PackageRuntime.
- Move only truly generic definitions.

## Out of Scope

- No WholeHouse dependencies.

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

- [ ] Workbench boots and package loads through generic package path.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-02`

Do not execute the next card in the same Agent run.
