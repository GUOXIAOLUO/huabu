# CARD R17-04 — Kujiale Manual Handoff Validation

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R17-03

## Goal

Measure friction and missing data in real manual file handoff to Kujiale.

## Before Owner

assumed handoff contract

## After Owner

observed Kujiale handoff evidence

## In Scope

- Use formal HandoffPackage.
- Record conversions/missing files/repeated input/errors/time.
- Identify only evidence-backed integration opportunities.

## Out of Scope

- No direct integration implementation in this card.

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

- [ ] Clear integration decision inputs are recorded.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-05`

Do not execute the next card in the same Agent run.
