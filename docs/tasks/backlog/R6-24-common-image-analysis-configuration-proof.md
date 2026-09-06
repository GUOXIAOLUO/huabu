# CARD R6-24 — Common Image Analysis Configuration Proof

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-23

## Goal

Prove Asset → Task + common.image-analysis SkillBinding → save/restart without actual execution.

## Before Owner

individual components

## After Owner

cross-system persisted configuration proof

## In Scope

- Register a minimal generic common.image-analysis definition.
- Create Task binding to an image input and prompt.
- Save/restart/reload and verify exact refs/versions.

## Out of Scope

- No real AI/model execution.

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

- [ ] End-to-end configuration survives restart with no WholeHouse dependency.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-01`

Do not execute the next card in the same Agent run.
