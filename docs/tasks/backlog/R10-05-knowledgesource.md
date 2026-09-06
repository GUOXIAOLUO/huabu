# CARD R10-05 — KnowledgeSource

- Round: R10
- Priority: P0
- Status: BACKLOG
- Depends on: R10-04

## Goal

Define source records for reusable project/domain knowledge.

## Before Owner

unstructured scattered files/prompts

## After Owner

KnowledgeSource

## In Scope

- Define source type/ref/scope/status/provenance.
- Support asset/document/manual sources.

## Out of Scope

- No vector DB requirement.

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

- [ ] Knowledge source lifecycle is explicit.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R10-06`

Do not execute the next card in the same Agent run.
