# CARD R15-07 — Floorplan Analysis Skill

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-06

## Goal

Implement wholehouse.floorplan-analysis over CAD/floorplan/site references.

## Before Owner

manual floorplan review

## After Owner

WholeHouse Floorplan Analysis Skill

## In Scope

- Accept CAD/image/requirements/site photo Collection.
- Produce FloorplanAnalysis Artifact.
- Expose warnings/uncertainty rather than fabricated dimensions.

## Out of Scope

- No direct CAD editing.
- No production拆单.

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

- [ ] Analysis preserves input version refs and structured findings.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-08`

Do not execute the next card in the same Agent run.
