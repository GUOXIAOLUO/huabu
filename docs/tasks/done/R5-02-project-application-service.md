# CARD R5-02 — Project Application Service

- Round: R5
- Priority: P0
- Status: DONE
- Activated: 2026-09-10 (explicit user task-activation request after R5-01 review)
- Completed: 2026-09-10
- Independent Review: PASS 2026-09-10
- Depends on: R5-01

## Goal

Move project create/read/update/archive behavior behind an application service.

## Before Owner

routes/helpers

## After Owner

ProjectService

## In Scope

- Define create/get/list/update/archive operations.
- Enforce basic validation and repository use.
- Keep authorization semantics compatible with current runtime.

## Out of Scope

- No project package locking yet.
- No global auth redesign.

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

- [x] `ProjectService` is the normal application boundary for project
      create/list/update/archive operations, including default-project
      creation and basic validation.
- [x] Project routes delegate to the service; archive Canvas reassignment is
      injected as an explicit port and is not duplicated in the route.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

- Project lifecycle validation, default-project creation, ordering and
  archive/reassignment orchestration lived in `main.py` route helpers.

After:

- `ProjectService` owns lifecycle commands and delegates persistence to
  `ProjectRepository`; Canvas reassignment is an injected compatibility port.

Duplicate owner removed:

- Project routes no longer contain project lifecycle mutation logic; they only
  map service results/errors to HTTP responses.

## Next Recommended Card

`R5-03`

Do not execute the next card in the same Agent run.
