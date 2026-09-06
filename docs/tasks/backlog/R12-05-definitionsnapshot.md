# CARD R12-05 — DefinitionSnapshot

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-04

## Goal

Snapshot package definitions required to preserve old project meaning.

## Before Owner

live package definitions only

## After Owner

DefinitionSnapshot

## In Scope

- Identify definitions that must be pinned/snapshotted.
- Store hash/version/snapshot refs.
- Resolve old projects safely.

## Out of Scope

- Avoid duplicating large resources unnecessarily.

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

- [ ] Project remains interpretable after package update/removal where policy permits.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-06`

Do not execute the next card in the same Agent run.
