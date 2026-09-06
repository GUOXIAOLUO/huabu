# CARD R14-06 — TaskProposal

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-05

## Goal

Let Agent propose creation/configuration of a Task without directly mutating Canvas.

## Before Owner

manual Task creation only

## After Owner

TaskProposal

## In Scope

- Define proposal payload/reason/base revision/required inputs/skill binding.
- Render proposal for confirmation.

## Out of Scope

- No automatic apply by default.

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

- [ ] Proposal is inspectable and revision-aware.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-07`

Do not execute the next card in the same Agent run.
