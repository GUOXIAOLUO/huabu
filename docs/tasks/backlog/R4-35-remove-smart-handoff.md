# CARD R4-35 — Remove Smart Handoff

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-34

## Goal

Delete page-switch/handoff behavior now that Smart records run natively.

## Before Owner

Smart handoff compatibility

## After Owner

Unified entry

## In Scope

- Remove handoff routing.
- Add regression for historical Smart entry.

## Out of Scope

- Do not delete required compatibility modules.

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

- [ ] No Smart product page routing remains.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-36`

Do not execute the next card in the same Agent run.
