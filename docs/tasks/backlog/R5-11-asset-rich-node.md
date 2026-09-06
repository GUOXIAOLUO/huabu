# CARD R5-11 — Asset Rich Node

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-10

## Goal

Prove Rich Node presentation using a generic existing asset/media record.

## Before Owner

basic media card

## After Owner

Rich Asset presentation

## In Scope

- Implement card/expanded/workspace/inspector behavior using existing asset-compatible data.
- Keep R9 AssetVersion architecture out.
- Test load/reload and legacy payload compatibility.

## Out of Scope

- No Resource Library yet.

## Compatibility / Migration

- Preserve existing behavior and data unless the card explicitly authorizes a migration.

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

- Add/run the smallest behavioral tests that prove this card's goal.
- Run `./scripts/agent-verify.sh`.

## Definition of Done

- [ ] Asset node exercises all four presentation levels without future-system leakage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-12`

Do not execute the next card in the same Agent run.
