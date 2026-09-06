# CARD R7-03 — ModelDefinition

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-02

## Goal

Represent model identity/capabilities independently from access route.

## Before Owner

provider-specific model strings

## After Owner

ModelDefinition

## In Scope

- Define model id/provider-family-neutral metadata/capabilities/context/IO metadata.
- Import/project existing model lists.

## Out of Scope

- Do not encode connection credentials.

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

- [ ] ModelDefinition is not an availability instance.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-04`

Do not execute the next card in the same Agent run.
