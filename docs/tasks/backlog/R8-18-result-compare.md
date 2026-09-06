# CARD R8-18 — Result Compare

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-17

## Goal

Compare multiple candidate outputs without materializing them.

## Before Owner

manual Canvas comparison

## After Owner

Result compare workspace

## In Scope

- Support multi-select compare.
- Provide side-by-side metadata/preview.
- Preserve selection.

## Out of Scope

- No domain-specific scoring.

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

- [ ] Users can compare candidates while they remain run results.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-19`

Do not execute the next card in the same Agent run.
