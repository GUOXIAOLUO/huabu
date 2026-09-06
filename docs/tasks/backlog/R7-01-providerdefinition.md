# CARD R7-01 — ProviderDefinition

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R6-24

## Goal

Define provider metadata independently from credentials and models.

## Before Owner

provider-shaped settings/code

## After Owner

ProviderDefinition

## In Scope

- Define generic provider id/title/capabilities/config schema metadata.
- Migrate/read existing provider definitions through adapters.

## Out of Scope

- No credentials stored in definition.

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

- [ ] Provider definition can exist without a connection.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-02`

Do not execute the next card in the same Agent run.
