# CARD R6-17 — SkillRegistry

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-16

## Goal

Provide one registry for discovering installed Skills.

## Before Owner

scattered feature capability lookup

## After Owner

SkillRegistry

## In Scope

- Register/unregister/list/search skills.
- Support package/source/version metadata.
- Resolve exact version.

## Out of Scope

- No online marketplace required.

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

- [x] Task/Agent future callers can discover Skills through one service.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

`workbench.application.SkillRegistry` now owns registration, unregistration,
listing, search, source/package metadata filtering, and exact version
resolution for installed `SkillDefinition` records.

Duplicate owner removed:

No second discovery path, online marketplace, executor, or execution fallback
was added; future Task/Agent callers use the one explicit registry boundary.

## Next Recommended Card

`R6-18`

Do not execute the next card in the same Agent run.
