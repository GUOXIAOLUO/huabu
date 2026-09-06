# CARD R6-15 — Prompt Resource UI

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-14

## Goal

Add Prompt management inside Resource Library structure.

## Before Owner

legacy prompt preset UI

## After Owner

generic Prompt resource UI

## In Scope

- List/search/view prompt versions.
- Create/update by new version.
- Expose package/source metadata.

## Out of Scope

- No top-level Prompt navigation.

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

- [ ] Prompt lives under Resources and does not create a new top-level category.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-16`

Do not execute the next card in the same Agent run.
