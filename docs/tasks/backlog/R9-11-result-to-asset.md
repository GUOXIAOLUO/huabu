# CARD R9-11 — Result to Asset

- Round: R9
- Priority: P1
- Status: BACKLOG
- Depends on: R9-10

## Goal

Explicitly save selected run result as an Asset/AssetVersion.

## Before Owner

tray-only result

## After Owner

Asset materialization action

## In Scope

- Create asset identity/version from eligible output.
- Preserve run provenance.
- Return stable ref.

## Out of Scope

- No silent save of all results.

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

- [ ] User-selected result becomes reusable Asset.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R9-12`

Do not execute the next card in the same Agent run.
