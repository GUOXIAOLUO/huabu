# CARD R10-08 — Project Knowledge Context

- Round: R10
- Priority: P0
- Status: BACKLOG
- Depends on: R10-07

## Goal

Assemble controlled project knowledge context for Skill/Agent use.

## Before Owner

ad hoc context injection

## After Owner

ProjectKnowledgeContext service

## In Scope

- Resolve project-scoped entities/knowledge/resources by policy.
- Snapshot refs used in future execution context.
- Respect package scope.

## Out of Scope

- Do not silently include entire project files.

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

- [ ] Context is inspectable and provenance-preserving.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-01`

Do not execute the next card in the same Agent run.
