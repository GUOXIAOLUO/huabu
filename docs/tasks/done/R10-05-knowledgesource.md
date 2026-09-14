# CARD R10-05 — KnowledgeSource

- Round: R10
- Priority: P0
- Status: DONE — independent Review PASS; archived 2026-09-14
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

- [x] Knowledge source lifecycle is explicit.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: no canonical KnowledgeSource record or lifecycle contract.

After: `KnowledgeSource` defines typed source type/ref, scope, status and
provenance with explicit lifecycle transitions.

Duplicate owner removed: none; no legacy KnowledgeSource owner existed and no
repository/API/vector-store owner was introduced.

## Implementation Evidence

- Added `workbench.domain.knowledge.KnowledgeSource` and
  `KnowledgeSourceProvenance` with asset/document/manual source types, system /
  common / industry / company / workspace / project / user scopes, and
  draft → active → archived lifecycle behavior.
- Scope and reference requirements are validated explicitly; records and
  provenance metadata are frozen and credential-safe.
- Focused suite: `.venv/bin/python -m unittest tests.test_knowledge_source_domain
  -v` — 3 tests passed.
- Full gate: `./scripts/agent-verify.sh` — PASS, 1332 tests, 291 Python AST
  files, 154 JavaScript files, 4 architecture guards, and clean diff check.

## Next Recommended Card

`R10-06`

Do not execute the next card in the same Agent run.
