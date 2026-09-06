# CARD R5-05 — Project List UI Cutover

- Round: R5
- Priority: P0
- Status: BACKLOG
- Depends on: R5-04

## Goal

Move project list/create/update UI to the canonical Project API.

## Before Owner

legacy project endpoints

## After Owner

canonical API client

## In Scope

- Characterize current UI calls.
- Introduce project API client.
- Cut project list/create/update to canonical endpoints.
- Remove duplicate page write path.

## Out of Scope

- No major visual redesign.

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

- [ ] Project UI no longer depends on JSON-backed routes.
- [ ] Create/reload/archive smoke tests pass.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R5-06`

Do not execute the next card in the same Agent run.
