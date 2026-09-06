# CARD R17-08 — GuiGui Integration Decision

- Round: R17
- Priority: P1
- Status: BACKLOG
- Depends on: R17-07

## Goal

Decide file handoff vs Local Bridge/MCP/API for GuiGui from real workflow evidence.

## Before Owner

preference/speculation

## After Owner

documented architecture decision

## In Scope

- Evaluate observed manual steps and Mac client constraints.
- Assess Local Bridge/MCP feasibility and risk.
- Record decision.

## Out of Scope

- No direct implementation in this card.

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

- [ ] Decision explicitly states trigger for future implementation.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-09`

Do not execute the next card in the same Agent run.
