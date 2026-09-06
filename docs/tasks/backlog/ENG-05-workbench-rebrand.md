# CARD ENG-05 — Workbench Rebrand

- Round: ENG
- Priority: P2
- Status: BACKLOG
- Depends on: R4-41

## Goal

Align visible repository/product naming with Xinhuabu Workbench.

## Before Owner

Infinite Canvas legacy naming

## After Owner

Xinhuabu Workbench naming

## In Scope

- Update README/product strings/environment name where safe.
- Keep compatibility identifiers only where technically required.

## Out of Scope

- No behavior rewrite.

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

- [ ] Docs/UI no longer present project primarily as Infinite Canvas.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`ENG-06`

Do not execute the next card in the same Agent run.
