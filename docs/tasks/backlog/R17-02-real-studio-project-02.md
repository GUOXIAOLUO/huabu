# CARD R17-02 — Real Studio Project 02

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R17-01

## Goal

Validate different/complex floorplan and data conditions.

## Before Owner

single-project evidence

## After Owner

cross-project robustness evidence

## In Scope

- Choose materially different project.
- Repeat end-to-end flow.
- Compare failure modes and reused knowledge/templates.

## Out of Scope

- No feature expansion without observed need.

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

- [ ] Second project identifies/validates generalization issues.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-03`

Do not execute the next card in the same Agent run.
