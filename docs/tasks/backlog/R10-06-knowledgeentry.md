# CARD R10-06 — KnowledgeEntry

- Round: R10
- Priority: P0
- Status: BACKLOG
- Depends on: R10-05

## Goal

Create normalized reusable knowledge entries with provenance.

## Before Owner

implicit context

## After Owner

KnowledgeEntry

## In Scope

- Define content/structured payload/source refs/tags/scope.
- Persist/query.

## Out of Scope

- Do not hallucinate entries from unverified sources.

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

- [ ] Every entry points back to source.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-07`

Do not execute the next card in the same Agent run.
