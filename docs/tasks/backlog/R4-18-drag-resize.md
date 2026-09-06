# CARD R4-18 — Drag / Resize Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-17

## Goal

Unify node drag and resize behavior.

## Before Owner

duplicated page interaction

## After Owner

InteractionController

## In Scope

- Migrate single drag/resize.
- Preserve multi-selection/group behavior where characterized.
- Persist/reload correctly.

## Out of Scope

- No new snapping product feature.

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

- [ ] Drag/resize/save/reload pass.
- [ ] No duplicate product owner.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-19`

Do not execute the next card in the same Agent run.
