# CARD R4-24 — Generic Connect Command

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-23

## Goal

Create an application-level connect mutation boundary.

## Before Owner

page side effects + raw save

## After Owner

GraphMutationService/application command

## In Scope

- Define generic connect command.
- Validate revision/project/canvas.
- Keep UI interaction separate from mutation.

## Out of Scope

- Do not put Classic/Smart side effects into Core graph model.

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

- [ ] Generic connect mutation is atomic and revision-safe.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-25`

Do not execute the next card in the same Agent run.
