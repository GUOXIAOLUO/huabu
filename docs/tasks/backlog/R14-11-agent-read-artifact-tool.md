# CARD R14-11 — Agent read_artifact Tool

- Round: R14
- Priority: P1
- Status: BACKLOG
- Depends on: R14-10

## Goal

Expose exact ArtifactVersion content/metadata/lineage to Agent.

## Before Owner

manual artifact inspection

## After Owner

read_artifact tool

## In Scope

- Require exact artifact/version ref where material.
- Return state/lineage/content summary.

## Out of Scope

- No modification through read tool.

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

- [ ] Agent can reason on formal outputs without mutable latest ambiguity.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-12`

Do not execute the next card in the same Agent run.
