# CARD R4-16 — Viewport / Pan / Zoom Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-15

## Goal

Unify viewport state and pan/zoom behavior.

## Before Owner

page runtime viewport wiring

## After Owner

InteractionController + runtime-state

## In Scope

- Migrate pan.
- Migrate zoom/fit/center.
- Preserve viewport persistence/restore.

## Out of Scope

- No semantic zoom redesign.

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

- [ ] Pan/zoom/restore pass.
- [ ] No duplicate viewport owner.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-17`

Do not execute the next card in the same Agent run.
