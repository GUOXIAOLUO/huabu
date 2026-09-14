# CARD R10-07 — Knowledge Search

- Round: R10
- Priority: P1
- Status: DONE — independent Review PASS; archived 2026-09-14
- Depends on: R10-06

## Goal

Provide scoped search/query for project/package knowledge.

## Before Owner

manual context selection

## After Owner

Knowledge service

## In Scope

- Implement lexical/metadata search first.
- Return provenance and scope.
- Expose API/Resource UI.

## Out of Scope

- Semantic/vector search can be later.

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

- [x] Skills/Agent can retrieve knowledge through one boundary: `KnowledgeEntryService.search` and `/api/v1/knowledge-entries/search`.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `KnowledgeEntryRepository.list` contained inline lexical filtering; no explicit search boundary or Resources knowledge view.

After: `KnowledgeEntryService.search` is the authorized retrieval boundary; SQLite search covers lexical content and metadata, while the API and existing Resources shell expose scoped results with source refs and scope.

Duplicate owner removed: no new repository/service/runtime owner; `list` remains a compatibility delegate to `search`.

## Implementation Evidence

- Focused backend/API tests: `tests/test_knowledge_entry.py` — 3 passed.
- JavaScript syntax and diff checks passed.
- Resource UI reuses `resourceLibraryShell`; no second Canvas runtime or top-level Resources page was added.

## Next Recommended Card

`R10-08`

Do not execute the next card in the same Agent run.
