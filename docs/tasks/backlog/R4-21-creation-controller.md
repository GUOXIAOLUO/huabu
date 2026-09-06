# CARD R4-21 — Unified CreationController

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-20

## Goal

Route all normal node creation entry points through one controller and NodeCreationService.

## Before Owner

page-specific creation entry points

## After Owner

CreationController → NodeCreationService

## In Scope

- Inventory context menu/toolbar/file drop/paste/workflow/connected creation.
- Route one by one through CreationController.
- Remove direct raw Canvas creation paths.

## Out of Scope

- Do not expand NodeCreationService into UI/business logic.

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

- [ ] All migrated entry points use same creation boundary.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-22`

Do not execute the next card in the same Agent run.
