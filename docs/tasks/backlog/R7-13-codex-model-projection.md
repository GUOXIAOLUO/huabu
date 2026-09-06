# CARD R7-13 — Codex Model Projection

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-12

## Goal

Project Codex-discovered model routes into ModelAvailability.

## Before Owner

Codex-specific model/config listing

## After Owner

ModelAvailability projection

## In Scope

- Read Codex model/config source.
- Map models/connections/runtime route.
- Refresh availability without redefining ModelDefinition incorrectly.

## Out of Scope

- Do not label Codex as a model.

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

- [ ] Codex route appears as availability of a model/runtime connection.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-01`

Do not execute the next card in the same Agent run.
