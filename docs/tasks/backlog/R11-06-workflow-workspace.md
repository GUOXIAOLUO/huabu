# CARD R11-06 — Workflow Workspace

- Round: R11
- Priority: P1
- Status: BACKLOG
- Depends on: R11-05

## Goal

Provide visual/editable business workflow workspace.

## Before Owner

legacy workflow import/export UI

## After Owner

Workflow Workspace

## In Scope

- Render steps/transitions/status.
- Edit definition version via explicit save/new version.
- Inspect run state.

## Out of Scope

- Do not expose executor-native graphs as same model.

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

- [ ] Workflow authoring/run inspection works through generic contracts.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-07`

Do not execute the next card in the same Agent run.
