# CARD R4-37 — Delete smart-canvas.js Product Runtime

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-36

## Goal

Remove Smart monolith as a product runtime.

## Before Owner

smart-canvas.js

## After Owner

Unified runtime + small compatibility modules

## In Scope

- Verify no retained capability depends on Smart monolith.
- Delete runtime.
- Update imports/tests.

## Out of Scope

- Do not replace it with another monolith.

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

- [ ] smart-canvas.js no longer exists as product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-38`

Do not execute the next card in the same Agent run.
