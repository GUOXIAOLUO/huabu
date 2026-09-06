# CARD R9-10 — Artifact Inspector and History

- Round: R9
- Priority: P1
- Status: BACKLOG
- Depends on: R9-09

## Goal

Expose artifact versions, provenance and comparison in Inspector/Workspace.

## Before Owner

generic artifact skeleton

## After Owner

versioned Artifact UX

## In Scope

- Show version list/current status/lineage.
- Allow compare/open/materialize actions.

## Out of Scope

- No Approval UI yet.

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

- [ ] Version history is inspectable and prior versions remain immutable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-11`

Do not execute the next card in the same Agent run.
