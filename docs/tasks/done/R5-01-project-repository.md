# CARD R5-01 — Project Repository

- Round: R5
- Priority: P0
- Status: DONE
- Activated: 2026-09-10 (explicit user task-activation request)
- Completed: 2026-09-10
- Independent Review: PASS 2026-09-10
- Depends on: R4-41

## Goal

Establish SQLite-backed ProjectRepository as the canonical persistence boundary.

## Before Owner

data/projects.json + page/route helpers

## After Owner

ProjectRepository backed by SQLite

## In Scope

- Characterize all project reads/writes and membership access.
- Define repository interface around ProjectRecord/ProjectMember.
- Implement SQLite repository using existing canonical schema where possible.
- Add migration-safe read compatibility.

## Out of Scope

- Do not redesign project UI yet.
- Do not implement Package Runtime.

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

- [x] Project reads/writes can be served through `ProjectRepository`; the
      project API uses `SqliteProjectRepository` backed by the canonical
      SQLite schema.
- [x] No normal project write path targets `data/projects.json`; Legacy JSON
      is read-only compatibility input and remains byte-unchanged.
- [x] Focused repository/API persistence tests pass (4 R5-01 tests); full
      `./scripts/agent-verify.sh` passes with 661 tests, 86 Python AST files,
      112 JavaScript files, 4 architecture guards, and clean diff check.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

- `main.py` project helpers read and wrote `data/projects.json` directly.

After:

- `SqliteProjectRepository` owns normal project reads/writes and membership
  access, backed by the existing canonical SQLite `projects` and
  `project_members` tables.

Duplicate owner removed:

- `load_projects`, `save_projects`, and direct project JSON mutation were
  removed from the normal API path. Legacy JSON is only a read-compatible
  migration source.

## Next Recommended Card

`R5-02`

Do not execute the next card in the same Agent run.
