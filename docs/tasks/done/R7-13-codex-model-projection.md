# CARD R7-13 — Codex Model Projection

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS 2026-09-11
- Depends on: R7-12

## Goal

Project Codex-discovered model routes into ModelAvailability.

## Before Owner

Codex-specific model/config listing

## After Owner

ModelAvailability projection

## In Scope

- Read Codex model/config source.
- Map models/connections/runtime route.
- Refresh availability without redefining ModelDefinition incorrectly.

## Out of Scope

- Do not label Codex as a model.

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

- [x] Codex route appears as availability of a model/runtime connection.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: Codex model/config discovery existed only as a Codex-specific listing;
no route availability projection existed.

After: `workbench/codex/model_projection.py` reads typed Codex model/config
sources and projects only known `ModelDefinition` identities into stable
`runtime` / `codex_harness` `ModelAvailability` routes through an abstract
availability sink, carrying the existing definition capabilities for route
matching. Duplicate/unknown discoveries are ignored; Codex is not created as a
model and no credentials/config payload is persisted.

Duplicate owner removed: no ModelDefinition or ModelAvailability ownership was
duplicated; Codex remains an adapter and the existing availability service
remains the write owner.

Focused evidence: tests cover known-model projection and capability carryover,
unknown/duplicate filtering, runtime route identity, typed model/config refresh,
and rejection of untyped config. Focused tests pass (14 across the Codex
bridge/protocol/projection suites); full verification passes with 797 tests,
158 Python AST files, 134 JavaScript files, 4 architecture guards, and clean
diff check.

## Next Recommended Card

`R8-01`

Do not execute the next card in the same Agent run.
