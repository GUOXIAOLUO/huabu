# CARD R17-03 — Real Studio Project 03 Batch/Collection Validation

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R17-02

## Goal

Stress Collection/Binding/Batch Execution on a real multi-space project.

## Before Owner

limited batch proof

## After Owner

real batch workflow evidence

## In Scope

- Use SpaceInputs/Binding Table across multiple spaces.
- Run preview/batch policies/result tray.
- Record errors/retries/adoption.

## Out of Scope

- No automatic approval of batch results.

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

- [ ] Batch workflow is controllable and recoverable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-04`

Do not execute the next card in the same Agent run.
