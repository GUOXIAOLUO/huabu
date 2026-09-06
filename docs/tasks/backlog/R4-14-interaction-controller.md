# CARD R4-14 — Establish InteractionController

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-13

## Goal

Create a single interaction owner over the existing pure runtime-state/math kernel.

## Before Owner

Classic/Smart page interaction state

## After Owner

Unified InteractionController

## In Scope

- Define interaction lifecycle and event wiring.
- Use runtime-state as state/math kernel.
- Migrate one bounded interaction responsibility first.

## Out of Scope

- No full rewrite in one patch.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [ ] One complete interaction responsibility has a single unified owner.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-15`

Do not execute the next card in the same Agent run.
