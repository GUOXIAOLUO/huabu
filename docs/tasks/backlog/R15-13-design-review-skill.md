# CARD R15-13 — Design Review Skill

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-12

## Goal

Perform structured design review before formal human approval.

## Before Owner

manual design checking

## After Owner

WholeHouse Design Review Skill

## In Scope

- Consume selected artifacts/entities/catalog refs.
- Produce DesignReview Artifact with blockers/warnings.
- Support workflow integration.

## Out of Scope

- Cannot approve/freeze.

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

- [ ] Human can act on exact review artifact.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-14`

Do not execute the next card in the same Agent run.
