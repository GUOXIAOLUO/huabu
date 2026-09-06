# CARD R5-03 — Canonical Project API

- Round: R5
- Priority: P0
- Status: BACKLOG
- Depends on: R5-02

## Goal

Introduce canonical Project API endpoints outside the main.py monolith.

## Before Owner

main.py project routes

## After Owner

workbench/api/projects.py

## In Scope

- Add list/get/create/update/archive endpoints.
- Use ProjectService.
- Add response/request models and focused API tests.

## Out of Scope

- Do not remove old routes until callers are cut over.

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

- [ ] Canonical API is usable and tested.
- [ ] main.py is not gaining new project business logic.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-04`

Do not execute the next card in the same Agent run.
