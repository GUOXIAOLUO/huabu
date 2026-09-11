# CARD R5-04 — Project JSON Migration and Cutover

- Round: R5
- Priority: P0
- Status: DONE
- Completed: 2026-09-10
- Independent Review: PASS — 2026-09-10
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

- [x] Normal project runtime uses SQLite.
- [x] JSON remains compatibility/recovery only.
- [x] Migration comparison passes: 1 project, 1 member, zero differences; authority switched to SQLite.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `data/projects.json` was the compatibility source and the repository could lazily import it while authority was `legacy_json`.

After: `project_authority_state` records `sqlite`; normal reads/writes use SQLite and legacy JSON is not consulted after cutover.

Duplicate owner removed: automatic Legacy JSON project import is gated off after the explicit SQLite authority switch; unknown source fields are retained under `metadata.legacy.source`.

Verification: focused project migration tests pass (4); `./scripts/agent-verify.sh` passes (670 tests, 93 Python AST files, 112 JavaScript files, 4 architecture guards, clean diff check). Migration report records project/member counts 1=1 and zero differences.

## Next Recommended Card

`R5-05`

Do not execute the next card in the same Agent run.
