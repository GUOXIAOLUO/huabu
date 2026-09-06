# CARD R15-01 — Create WholeHouse Package

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R14-13

## Goal

Create packages/wholehouse as a PackageRuntime-loaded industry extension.

## Before Owner

no formal industry package

## After Owner

WholeHouse Package

## In Scope

- Create manifest/directory structure.
- Register through PackageRegistry.
- Declare package metadata/version.

## Out of Scope

- No Core imports from WholeHouse.
- No second Canvas.

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

- [ ] Workbench works with package enabled/disabled.
- [ ] Core remains generic.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-02`

Do not execute the next card in the same Agent run.
