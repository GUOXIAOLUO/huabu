# CARD R15-14 — WholeHouse Human Approval / Frozen Design

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-13

## Goal

Use generic Approval lifecycle to create a frozen design milestone.

## Before Owner

domain-specific informal confirmation

## After Owner

generic Approval + Frozen Artifact

## In Scope

- Define WholeHouse workflow step/rules using generic approval.
- Require authorized human freeze.
- Pin exact artifact/catalog/resource versions.

## Out of Scope

- No WholeHouse private approval subsystem.

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

- [ ] Frozen milestone is immutable/auditable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-15`

Do not execute the next card in the same Agent run.
