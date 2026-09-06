# CARD R15-03 — WholeHouse Entity Definitions

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-02

## Goal

Define WholeHouse business facts as package Entity definitions.

## Before Owner

no formal vertical entities

## After Owner

package-defined entities

## In Scope

- Define Customer/Requirement/Room/Space/DesignDecision/MaterialSelection/ProductSelection schemas.
- Register through generic Entity system.

## Out of Scope

- Do not hardcode entity classes into Core.

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

- [ ] Entities render through generic entity mechanisms.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-04`

Do not execute the next card in the same Agent run.
