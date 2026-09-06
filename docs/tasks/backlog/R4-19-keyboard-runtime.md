# CARD R4-19 — Keyboard Runtime Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-18

## Goal

Unify keyboard command handling.

## Before Owner

page-specific keyboard handlers

## After Owner

Unified command/interaction runtime

## In Scope

- Migrate delete/copy/paste/select-all/group shortcuts.
- Preserve undo/redo compatibility as characterized.
- Remove duplicate listeners.

## Out of Scope

- Do not redesign command palette.

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

- [ ] Keyboard behavior passes with one listener/owner path.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-20`

Do not execute the next card in the same Agent run.
