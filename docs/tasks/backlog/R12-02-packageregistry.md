# CARD R12-02 — PackageRegistry

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-01

## Goal

Discover/load enabled packages through one runtime boundary.

## Before Owner

static imports

## After Owner

PackageRegistry

## In Scope

- Register installed packages.
- Resolve exact versions.
- Expose definitions to registries safely.

## Out of Scope

- No arbitrary package code execution without policy.

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

- [ ] Core can operate with zero optional industry packages.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-03`

Do not execute the next card in the same Agent run.
