# CARD R7-05 — Capability Matching

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-04

## Goal

Match Skill capability requirements to available model routes.

## Before Owner

manual model selection

## After Owner

ModelCompatibilityResolver

## In Scope

- Normalize capability requirements.
- Filter/score valid ModelAvailability entries.
- Return explicit incompatibility reasons.

## Out of Scope

- No silent fallback.

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

- [ ] Skill requirements resolve deterministically or fail explicitly.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-06`

Do not execute the next card in the same Agent run.
