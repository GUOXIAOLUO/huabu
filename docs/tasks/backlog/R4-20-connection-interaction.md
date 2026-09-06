# CARD R4-20 — Connection Interaction Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-19

## Goal

Unify port hover, draft edge, validation and drop interaction.

## Before Owner

page-specific connect UI

## After Owner

InteractionController

## In Scope

- Migrate connection gesture lifecycle.
- Keep persistence mutation behind application service.
- Preserve cancel/error states.

## Out of Scope

- Do not encode legacy side effects in Core interaction.

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

- [ ] Connection UI has one owner.
- [ ] Persistence is not directly mutated by UI controller.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-21`

Do not execute the next card in the same Agent run.
