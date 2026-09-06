# CARD ENG-04 — packages Directory Cleanup

- Round: ENG
- Priority: P1
- Status: BACKLOG
- Depends on: R4-41

## Goal

Reserve packages/ for Workbench packages by moving vendored wheels.

## Before Owner

packages/ used for wheels

## After Owner

vendor/wheels + packages/{common,media,wholehouse}

## In Scope

- Inventory vendored wheels/consumers.
- Move to vendor/wheels.
- Update paths/tests.

## Out of Scope

- Do not break offline install support.

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

- [ ] packages/ semantic namespace is available for PackageRuntime.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-05`

Do not execute the next card in the same Agent run.
