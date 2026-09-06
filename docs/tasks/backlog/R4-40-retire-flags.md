# CARD R4-40 — Retire R4 Feature Flags

- Round: R4
- Priority: P1
- Status: BACKLOG
- Depends on: R4-39

## Goal

Remove R4 migration flags that no longer represent real runtime choices.

## Before Owner

migration flags

## After Owner

single stable runtime path

## In Scope

- Inventory R4 flags against actual code.
- Delete dead branches and tests that only preserve completed migration paths.
- Keep only flags with explicit post-R4 purpose.

## Out of Scope

- Do not delete unrelated feature configuration.

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

- [ ] No flag can re-enable Classic/Smart product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R4-41`

Do not execute the next card in the same Agent run.
