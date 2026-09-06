# CARD R5-04 — Project JSON Migration and Cutover

- Round: R5
- Priority: P0
- Status: BACKLOG
- Depends on: R5-03

## Goal

Migrate project runtime authority from data/projects.json to SQLite.

## Before Owner

JSON project authority

## After Owner

SQLite ProjectRecord authority

## In Scope

- Build/verify migration from JSON.
- Compare project/member counts and payloads.
- Switch normal writes to SQLite.
- Keep explicit import/recovery compatibility only.

## Out of Scope

- Do not silently discard unknown project fields.

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

- [ ] Normal project runtime uses SQLite.
- [ ] JSON remains compatibility/recovery only.
- [ ] Migration comparison passes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-05`

Do not execute the next card in the same Agent run.
