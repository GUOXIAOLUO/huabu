# CARD R8-21 — Result to Collection

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-20

## Goal

Allow selected results to be added to a Collection explicitly.

## Before Owner

manual copy/Canvas nodes

## After Owner

explicit collection materialization

## In Scope

- Create references/items from selected outputs.
- Preserve run/result lineage metadata.

## Out of Scope

- No formal Asset/Artifact conversion yet.

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

- [ ] Selected results can populate a Collection without Canvas node creation.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-22`

Do not execute the next card in the same Agent run.
