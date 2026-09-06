# CARD R17-05 — GuiGui Manual Handoff Validation

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R17-04

## Goal

Measure real manual CAD/file handoff friction with GuiGui.

## Before Owner

assumed handoff contract

## After Owner

observed GuiGui handoff evidence

## In Scope

- Use formal HandoffPackage.
- Record required CAD conventions/files/manual corrections/errors/time.

## Out of Scope

- No direct GuiGui control.

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

- [ ] Observed gaps feed integration decision.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-06`

Do not execute the next card in the same Agent run.
