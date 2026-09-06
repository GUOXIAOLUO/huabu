# CARD R12-08 — IntegrationDefinition

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-07

## Goal

Define external integration types independently from live connections.

## Before Owner

ad hoc external clients

## After Owner

IntegrationDefinition

## In Scope

- Define id/type/capabilities/config schema/transport metadata.
- Support API/MCP/LocalBridge/File/CLI categories.

## Out of Scope

- No vendor-specific Core business logic.

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

- [ ] Definitions register generic capabilities.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-09`

Do not execute the next card in the same Agent run.
