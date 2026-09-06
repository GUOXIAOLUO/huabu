# CARD R4-29 — Extract Smart Media Tools

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-28

## Goal

Detach retained Smart crop/edit/draw/grid/panorama tools from Smart Canvas runtime.

## Before Owner

smart-canvas.js

## After Owner

compatibility workspace/capability modules

## In Scope

- Extract retained tools.
- Use unified selection/render lifecycle.
- Preserve behavior.

## Out of Scope

- Do not build future Media Package yet.

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

- [ ] Retained tools no longer require Smart product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-30`

Do not execute the next card in the same Agent run.
