# CARD R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-37

## Goal

Remove Canvas runtime ownership from the Classic monolith.

## Before Owner

canvas.js

## After Owner

Unified runtimes

## In Scope

- Remove rendering ownership.
- Remove interaction ownership.
- Remove persistence/creation/graph lifecycle ownership.
- Leave only bounded bootstrap/compat temporarily if needed.

## Out of Scope

- Do not let Classic 'win' as final runtime.

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

- [ ] canvas.js no longer owns product runtime responsibilities.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-39`

Do not execute the next card in the same Agent run.
