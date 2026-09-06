# CARD R8-17 — Result Preview

- Round: R8
- Priority: P1
- Status: BACKLOG
- Depends on: R8-16

## Goal

Preview text/image/file results generically.

## Before Owner

raw output/log display

## After Owner

Result preview renderers

## In Scope

- Add preview registry.
- Support common result types.
- Handle unavailable/failed output refs.

## Out of Scope

- No R9 formal Asset/Artifact persistence yet.

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

- [ ] Common outputs are inspectable in tray.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-18`

Do not execute the next card in the same Agent run.
