# CARD R4-06 — Browser Persistence Uses Logical Revision

- Round: R4
- Priority: P0
- Status: BACKLOG
- Depends on: R4-05

## Goal

Move normal browser save concurrency from updated_at/base_updated_at to logical revision.

## Before Owner

timestamp compatibility cursor

## After Owner

logical Canvas revision

## In Scope

- Update canonical persistence client.
- Adopt server revision after save/load.
- Keep updated_at as display/compat metadata only.
- Update focused tests.

## Out of Scope

- Do not refactor rendering/interaction.

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

- [ ] Normal save sends expected_revision.
- [ ] Client adopts returned revision.
- [ ] No normal CAS depends on timestamp.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-07`

Do not execute the next card in the same Agent run.
