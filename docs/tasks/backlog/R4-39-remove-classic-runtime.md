# CARD R4-39 — Remove Legacy canvas.js Product Runtime

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-38

## Goal

Replace the old Classic monolith with a small neutral bootstrap.

## Before Owner

canvas.js monolith

## After Owner

small canvas-app bootstrap

## In Scope

- Move remaining legitimate bootstrap wiring.
- Delete monolithic business/runtime code.
- Verify legacy records.

## Out of Scope

- No new bootstrap monolith.

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

- [ ] No Classic product runtime remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-40`

Do not execute the next card in the same Agent run.
