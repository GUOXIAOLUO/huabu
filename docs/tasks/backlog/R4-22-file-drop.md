# CARD R4-22 — File Drop Unified Creation

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-21

## Goal

Route image/video/pdf/file drop through unified creation.

## Before Owner

page-specific file drop

## After Owner

CreationController

## In Scope

- Characterize file drop types.
- Create via NodeCreationService/compat adapter.
- Preserve old records and upload behavior.

## Out of Scope

- Do not build AssetVersion runtime.

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

- [ ] File drop creates through unified boundary and reloads correctly.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-23`

Do not execute the next card in the same Agent run.
