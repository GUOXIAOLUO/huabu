# CARD R10-08 — Project Knowledge Context

- Round: R10
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
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

- [x] Context is inspectable and provenance-preserving through `ProjectKnowledgeContext` and `/api/v1/projects/{project_id}/knowledge-context`.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Skill/Agent context was ad hoc; Entity and Knowledge services had no controlled composition boundary or snapshot reference envelope.

After: `ProjectKnowledgeContextService` applies explicit Knowledge/resource scope and limit policies, reads Entity and Knowledge through their canonical services, collects typed resource references through injected readers, and emits immutable snapshot refs with provenance.

Duplicate owner removed: no existing Entity/Knowledge/Asset/Artifact/Catalog owner was replaced; the new service is composition-only and does not persist or mutate domain records.

## Implementation Evidence

- `ProjectKnowledgeContext` is immutable and carries entities, knowledge, typed resource refs, policy, generated time and snapshot refs.
- Default policy is project-only for Knowledge and resources; broader scopes must be explicitly requested.
- API reads require `X-User-ID` and underlying canonical services enforce project/resource authorization.
- No full project file dump, WholeHouse type, second Canvas runtime or package-specific Core branch was added.
- Focused suite: `tests.test_project_knowledge_context`, `tests.test_knowledge_entry`, `tests.test_entity_domain` — 8 passed.
- Full `./scripts/agent-verify.sh` — PASS: 1337 tests, 300 Python AST files, 154 JavaScript files, 4 architecture guards.
- Gate repair: formal `KnowledgeSnapshot` is captured by `ExecutionRunService.create` when the canonical context service is wired, and persists with `ExecutionRun`.
- Updated focused ExecutionRun/context suite: 7 passed; full gate: 1338 tests, 300 Python AST files, 154 JavaScript files, 4 architecture guards.

## Next Recommended Card

`R11-01`

Do not execute the next card in the same Agent run.
