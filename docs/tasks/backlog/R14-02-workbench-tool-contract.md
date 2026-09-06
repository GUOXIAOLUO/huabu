# CARD R14-02 — Workbench Tool Contract

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R14-01

## Goal

Define safe application-level tools available to Agent runtimes.

## Before Owner

potential raw repository/DOM access

## After Owner

WorkbenchToolContract

## In Scope

- Define typed tool request/response/error/audit context.
- Require application services.
- Define authorization/confirmation metadata.

## Out of Scope

- No direct DOM/SQLite/raw Canvas tools.

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

- [ ] Fake Agent can call tools without access to forbidden layers.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-03`

Do not execute the next card in the same Agent run.
