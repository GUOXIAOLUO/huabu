# CARD R11-14 — Handoff Validation

- Round: R11
- Priority: P0
- Status: BACKLOG
- Depends on: R11-13

## Goal

Run structured completeness/format/version validation before export.

## Before Owner

manual checking

## After Owner

HandoffValidator

## In Scope

- Define generic validation result model.
- Validate required refs/files/checksums/approval state.
- Surface errors/warnings.

## Out of Scope

- No industry rules in Core; package rules plug in later.

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

- [ ] Invalid package cannot be marked ready without explicit policy.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R11-15`

Do not execute the next card in the same Agent run.
