# CARD R6-07 — Collection Gallery View

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-06

## Goal

Add gallery presentation for visual collections.

## Before Owner

no collection UX

## After Owner

Collection Rich Node gallery view

## In Scope

- Render referenced media/items efficiently.
- Support selection/open item.
- Integrate with Rich Node card/expanded/workspace.

## Out of Scope

- No image editing.

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

- [ ] Gallery works for mixed valid visual references and reloads.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-08`

Do not execute the next card in the same Agent run.
