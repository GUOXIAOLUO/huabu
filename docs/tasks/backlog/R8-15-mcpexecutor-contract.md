# CARD R8-15 — MCPExecutor Contract

- Round: R8
- Priority: P2
- Status: BACKLOG
- Depends on: R8-14

## Goal

Define a generic MCP execution adapter boundary without WholeHouse coupling.

## Before Owner

future/adhoc MCP calls

## After Owner

MCPExecutor adapter contract

## In Scope

- Define connection/capability/action invocation mapping.
- Normalize tool result/events/errors.
- Use Integration references where available later.

## Out of Scope

- No specific Kujiale/GuiGui MCP integration.

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

- [ ] Generic contract is testable with a fake MCP server/client.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-16`

Do not execute the next card in the same Agent run.
