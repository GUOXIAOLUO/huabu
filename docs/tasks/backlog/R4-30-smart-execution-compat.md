# CARD R4-30 — Extract Smart Execution Compatibility

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-29

## Goal

Keep required pre-R8 Smart execution behavior without letting it own Canvas.

## Before Owner

smart-canvas.js

## After Owner

bounded execution compatibility module

## In Scope

- Identify only required R4 compatibility.
- Detach Canvas lifecycle/state ownership.
- Keep future R8 design out.

## Out of Scope

- No ExecutionRuntime implementation.

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

- [ ] Compatibility works through unified Canvas ownership.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-31`

Do not execute the next card in the same Agent run.
