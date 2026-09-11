# CARD R5-05 — Project List UI Cutover

- Round: R5
- Priority: P0
- Status: DONE
- Completed: 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-04

## Goal

Move project list/create/update UI to the canonical Project API.

## Before Owner

legacy project endpoints

## After Owner

canonical API client

## In Scope

- Characterize current UI calls.
- Introduce project API client.
- Cut project list/create/update to canonical endpoints.
- Remove duplicate page write path.

## Out of Scope

- No major visual redesign.

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

- [x] Project UI no longer depends on JSON-backed routes.
- [x] Create/reload/archive smoke tests pass through the canonical client and API contract tests.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `canvas-list.js` directly owned project HTTP transport through legacy `/api/projects` routes, including POST-based rename.

After: `project-api-client.js` owns `/api/v1/projects` list/create/update/archive transport; `canvas-list.js` owns only project UI state, rendering, and interaction.

Duplicate owner removed: all project CRUD fetch calls were removed from `canvas-list.js`; canonical client errors preserve API status/code/message for UI handling.

Verification: focused UI cutover tests pass (6); `./scripts/agent-verify.sh` passes (672 tests, 94 Python AST files, 113 JavaScript files, 4 architecture guards, clean diff check). Git Review PASS.

## Next Recommended Card

`R5-06`

Do not execute the next card in the same Agent run.
