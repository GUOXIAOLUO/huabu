# CARD R5-01 — Project Repository

- Round: R5
- Priority: P0
- Status: BACKLOG
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

- [ ] Project reads/writes can be served through the repository.
- [ ] No new normal write path targets data/projects.json.
- [ ] Focused persistence tests pass.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-02`

Do not execute the next card in the same Agent run.
