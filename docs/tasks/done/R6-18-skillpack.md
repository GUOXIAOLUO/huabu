# CARD R6-18 — SkillPack

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS (2026-09-11)
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

- [x] Common/Media/future WholeHouse can be represented without Core branching.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

`SkillPack` now owns generic pack metadata and exact `SkillRef` associations;
`SkillRegistry` owns Pack registration, exact Pack-version resolution, and
registry-level enable/disable state while filtering disabled Pack members from
normal Skill discovery.

Duplicate owner removed:

No Package Runtime, provider/industry branch, online marketplace, or alternate
Skill discovery owner was added.

## Next Recommended Card

`R6-19`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-11. The generic SkillPack metadata, exact SkillRef
associations, and registry-level enable/disable behavior satisfy the card DoD.
No Package Runtime, provider-specific, or industry-specific ownership was
introduced.
