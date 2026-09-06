# CARD R11-12 — HandoffPackage

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-11

## Goal

Create formal handoff package identity/status around manifest and files.

## Before Owner

ZIP/export action

## After Owner

HandoffPackage

## In Scope

- Define package lifecycle.
- Link artifacts/assets/manifest.
- Persist status/history.

## Out of Scope

- No direct external control yet.

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

- [ ] Handoff is a business object, not just a download.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-13`

Do not execute the next card in the same Agent run.
