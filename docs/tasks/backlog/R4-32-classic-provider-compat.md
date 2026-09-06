# CARD R4-32 — Extract Classic Provider Compatibility

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-31

## Goal

Detach retained provider-shaped UI behavior from canvas.js.

## Before Owner

canvas.js

## After Owner

compatibility modules under unified runtime

## In Scope

- Extract presentation/controls.
- Use unified render/interaction boundaries.
- Remove Canvas lifecycle ownership.

## Out of Scope

- No R7 registry.

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

- [ ] Provider compatibility no longer makes canvas.js a product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-33`

Do not execute the next card in the same Agent run.
