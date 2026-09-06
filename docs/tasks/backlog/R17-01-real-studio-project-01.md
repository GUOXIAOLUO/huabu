# CARD R17-01 — Real Studio Project 01

- Round: R17
- Priority: P0
- Status: BACKLOG
- Depends on: R16-09

## Goal

Validate the complete WholeHouse workflow on one real studio project.

## Before Owner

synthetic/demo validation

## After Owner

real project evidence

## In Scope

- Run intake → analysis → concept → selection → review → frozen → handoff.
- Record failures/manual steps/time/quality.

## Out of Scope

- Do not conceal manual interventions.

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

- [ ] Project completes with auditable outputs and issue log.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-02`

Do not execute the next card in the same Agent run.
