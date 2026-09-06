# CARD R11-15 — File Handoff Export

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-14

## Goal

Export validated handoff package to filesystem/archive while preserving manifest.

## Before Owner

ad hoc file downloads

## After Owner

formal FileHandoff exporter

## In Scope

- Materialize export directory/archive.
- Include manifest/checksums.
- Record export event/path.

## Out of Scope

- No MCP/API external delivery required.

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

- [ ] Export can be independently verified against manifest.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-01`

Do not execute the next card in the same Agent run.
