# CARD R4-34 — Run Historical Smart Canvas Natively in canvas.html

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-33

## Goal

Open historical Smart canvases directly in the unified page/runtime.

## Before Owner

Smart page/handoff

## After Owner

canvas.html + Unified Runtime

## In Scope

- Characterize old Smart entry routing.
- Load Smart records in canvas.html.
- Verify retained capabilities and persistence.

## Out of Scope

- Do not delete Smart files until verified.

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

- [ ] Historical Smart opens without smart-canvas page switch.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-35`

Do not execute the next card in the same Agent run.
