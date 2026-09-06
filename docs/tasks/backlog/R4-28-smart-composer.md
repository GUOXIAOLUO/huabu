# CARD R4-28 — Extract Smart Composer

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-27

## Goal

Detach Smart Composer from smart-canvas product runtime.

## Before Owner

smart-canvas.js

## After Owner

mountable compatibility capability

## In Scope

- Extract lifecycle/dependencies.
- Connect through unified creation/render boundaries.
- Remove Smart runtime ownership.

## Out of Scope

- Do not redesign Composer.

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

- [ ] Composer works without Smart product runtime ownership.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-29`

Do not execute the next card in the same Agent run.
