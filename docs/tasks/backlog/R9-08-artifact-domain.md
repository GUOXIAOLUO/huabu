# CARD R9-08 — Artifact Domain

- Round: R9
- Priority: P0
- Status: BACKLOG
- Depends on: R9-07

## Goal

Define Artifact as identity for Workbench-produced formal outputs.

## Before Owner

legacy output/result records

## After Owner

Artifact

## In Scope

- Define identity/type/project/title/state/metadata.
- Separate versions.

## Out of Scope

- No approval/frozen lifecycle yet beyond placeholder state.

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

- [ ] Artifact exists independently from Canvas node.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-09`

Do not execute the next card in the same Agent run.
