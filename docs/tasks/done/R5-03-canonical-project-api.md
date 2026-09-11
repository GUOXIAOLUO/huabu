# CARD R5-03 — Canonical Project API

- Round: R5
- Priority: P0
- Status: DONE
- Activated: 2026-09-10 (explicit user task-activation request after R5-02 review)
- Completed: 2026-09-10
- Independent Review: PASS 2026-09-10
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

- [x] Canonical `/api/v1/projects` list/get/create/update/archive endpoints
      are usable and covered by focused API tests (3 R5-03 tests).
- [x] `main.py` only wires the transport router; project API business logic
      remains in `ProjectService`.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

- Project transport endpoints and HTTP error mapping were defined in
  `main.py` alongside the legacy routes.

After:

- `workbench/api/projects.py` owns the canonical versioned Project transport
  contract and delegates all lifecycle behavior to `ProjectService`.

Duplicate owner removed:

- Canonical API route handlers no longer add project lifecycle logic to
  `main.py`; legacy `/api/projects` routes remain only for compatibility as
  authorized by this card.

## Next Recommended Card

`R5-04`

Do not execute the next card in the same Agent run.
