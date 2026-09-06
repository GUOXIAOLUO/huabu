# CARD R12-09 — IntegrationConnection

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-08

## Goal

Represent configured external connections and credential refs.

## Before Owner

global endpoint settings

## After Owner

IntegrationConnection

## In Scope

- Define connection/config/credential/status/health metadata.
- Add service/API.

## Out of Scope

- No raw credentials in business records.

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

- [ ] Multiple connections and health status are supported.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-10`

Do not execute the next card in the same Agent run.
