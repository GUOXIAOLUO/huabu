# CARD R15-09 — Space Concept Skill

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-08

## Goal

Generate/reason about space concept options using approved inputs.

## Before Owner

manual concept generation

## After Owner

WholeHouse Space Concept Skill

## In Scope

- Consume Requirement/Floorplan/Site/Space refs.
- Produce SpaceConcept candidates/results.
- Use Result Tray for alternatives.

## Out of Scope

- No automatic final approval.
- No new node type.

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

- [ ] Multiple candidates remain results until explicit Artifact promotion.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-10`

Do not execute the next card in the same Agent run.
