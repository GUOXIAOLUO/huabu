# CARD R16-04 — Cabinet Design Knowledge

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-03

## Goal

Add cabinet concept/design-rule knowledge without turning Core into拆单 software.

## Before Owner

manual designer expertise only

## After Owner

WholeHouse cabinet knowledge

## In Scope

- Curate design constraints/ergonomics/construction considerations.
- Expose to Skills/Agent as knowledge.

## Out of Scope

- No CNC/BOM production authority yet.

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

- [ ] Knowledge assists concept/review without production execution.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-05`

Do not execute the next card in the same Agent run.
