# CARD R4-26 — Group Mutation Cutover

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-25

## Goal

Unify group create/add/remove/ungroup mutations.

## Before Owner

page-specific group persistence

## After Owner

Graph/application mutation boundary

## In Scope

- Migrate group mutations.
- Preserve old payload compatibility.
- Verify revision/save/reload.

## Out of Scope

- Do not introduce Collection semantics.

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

- [ ] Group mutation has one authoritative path.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-27`

Do not execute the next card in the same Agent run.
