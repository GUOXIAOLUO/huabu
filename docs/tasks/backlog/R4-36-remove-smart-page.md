# CARD R4-36 — Delete smart-canvas.html

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-35

## Goal

Remove duplicate Smart product page after all retained behaviors are hosted elsewhere.

## Before Owner

smart-canvas.html

## After Owner

canvas.html only

## In Scope

- Verify no valid entry references Smart page.
- Delete page.
- Update tests/docs/routes.

## Out of Scope

- Do not hide broken routes with silent redirects unless explicitly intended.

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

- [ ] One visible Canvas page remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-37`

Do not execute the next card in the same Agent run.
