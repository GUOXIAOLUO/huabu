# CARD R4-15 — Selection Ownership Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-14

## Goal

Unify single/multi/box selection and projection.

## Before Owner

duplicated page selection state

## After Owner

InteractionController

## In Scope

- Migrate single selection.
- Migrate multi-select and box selection.
- Remove duplicated page selection source of truth.

## Out of Scope

- No workspace/Inspector work.

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

- [ ] Selection behavior passes on old Classic/Smart records.
- [ ] One selection authority remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-16`

Do not execute the next card in the same Agent run.
