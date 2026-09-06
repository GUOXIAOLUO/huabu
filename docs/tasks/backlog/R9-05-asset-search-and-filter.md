# CARD R9-05 — Asset Search and Filter

- Round: R9
- Priority: P1
- Status: BACKLOG
- Depends on: R9-04

## Goal

Search/filter assets by type/project/source/tags/metadata.

## Before Owner

basic asset browsing

## After Owner

asset query service + UI

## In Scope

- Add indexed/queryable metadata.
- Implement search/filter UI.
- Paginate for large libraries.

## Out of Scope

- No semantic vector search requirement.

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

- [ ] Users can find assets without browsing Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-06`

Do not execute the next card in the same Agent run.
