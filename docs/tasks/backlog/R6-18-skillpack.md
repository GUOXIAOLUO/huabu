# CARD R6-18 — SkillPack

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-17

## Goal

Group related Skills into installable/discoverable packs.

## Before Owner

flat skill registry

## After Owner

SkillPack

## In Scope

- Define pack metadata.
- Associate skills by refs.
- Support enabled/disabled state at registry level.

## Out of Scope

- No Package Runtime implementation yet.

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

- [ ] Common/Media/future WholeHouse can be represented without Core branching.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-19`

Do not execute the next card in the same Agent run.
