# CARD R9-15 — Catalog Library UI

- Round: R9
- Priority: P1
- Status: BACKLOG
- Depends on: R9-14

## Goal

Browse/search/inspect generic catalogs under Resources.

## Before Owner

no generic catalog UX

## After Owner

Catalog resource UI

## In Scope

- Add catalog/item browser.
- Search/filter basic attributes.
- Drag/reference items into Collection/Task where compatible.

## Out of Scope

- No WholeHouse-specific faceting.

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

- [ ] Generic catalog works before WholeHouse installation.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-01`

Do not execute the next card in the same Agent run.
