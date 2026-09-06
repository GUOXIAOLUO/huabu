# CARD R15-15 — First CAD/File Handoff

- Round: R15
- Priority: P0
- Status: BACKLOG
- Depends on: R15-14

## Goal

Create first real WholeHouse HandoffPackage for manual Kujiale/GuiGui transfer.

## Before Owner

manual loose files

## After Owner

formal validated handoff

## In Scope

- Prepare CAD/PDF/images/material/design docs as refs.
- Generate manifest/checksums.
- Run wholehouse.handoff-check/package validation.
- Export for human handoff.

## Out of Scope

- No direct Agent control of Kujiale/GuiGui.
- No production/installation/after-sales.

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

- [ ] Package can be independently verified and manually consumed downstream.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-01`

Do not execute the next card in the same Agent run.
