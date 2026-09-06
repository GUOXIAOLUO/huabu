# CARD R4-23 — Clipboard Unified Creation

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-22

## Goal

Unify copy/paste/duplicate and external paste creation paths.

## Before Owner

page-specific clipboard mutation

## After Owner

CreationController / command runtime

## In Scope

- Migrate node copy/paste.
- Migrate multi-copy.
- Characterize external image/text paste.
- Remove raw create/save duplication.

## Out of Scope

- No new clipboard product scope.

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

- [ ] Clipboard regression passes across legacy record types.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-24`

Do not execute the next card in the same Agent run.
