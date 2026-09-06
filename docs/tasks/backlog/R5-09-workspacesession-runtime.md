# CARD R5-09 — WorkspaceSession Runtime

- Round: R5
- Priority: P1
- Status: BACKLOG
- Depends on: R5-08

## Goal

Create a generic lifecycle for immersive node workspaces.

## Before Owner

ad hoc overlays/editors

## After Owner

WorkspaceSession

## In Scope

- Define open/close/context/dirty/save/discard lifecycle.
- Create WorkspaceRegistry contract.
- Integrate with current canvas selection/context.

## Out of Scope

- No CAD/Image specialized workspace in this card.

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

- [ ] A generic workspace can open/close safely.
- [ ] Dirty-state behavior is tested.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-10`

Do not execute the next card in the same Agent run.
