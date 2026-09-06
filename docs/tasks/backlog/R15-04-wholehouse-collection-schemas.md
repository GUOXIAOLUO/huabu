# CARD R15-04 — WholeHouse Collection Schemas

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-03

## Goal

Define reusable structured collections for whole-house design work.

## Before Owner

generic collection only

## After Owner

package CollectionSchemas

## In Scope

- Define ProjectReferences/SpaceInputs/MaterialOptions/ProductOptions/RenderCandidates schemas.
- Add role definitions.

## Out of Scope

- No custom collection engine.

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

- [ ] Schemas work in generic Collection Table/Binding Table.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-05`

Do not execute the next card in the same Agent run.
