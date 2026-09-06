# CARD R5-13 — Artifact Rich Node Skeleton

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-12

## Goal

Create the generic presentation boundary for formal work outputs.

## Before Owner

generic/legacy output cards

## After Owner

Artifact Rich Node skeleton

## In Scope

- Define artifact card/expanded/workspace/inspector presentation.
- Keep formal ArtifactVersion persistence for R9.
- Use compatibility data where needed.

## Out of Scope

- No approval lifecycle yet.

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

- [ ] Artifact presentation is generic and version-ready.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-01`

Do not execute the next card in the same Agent run.
