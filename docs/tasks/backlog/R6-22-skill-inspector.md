# CARD R6-22 — Skill Inspector

- Round: R6
- Priority: P1
- Status: BACKLOG
- Depends on: R6-21

## Goal

Add a reusable inspector for Skill definition/binding details.

## Before Owner

no generic Skill inspector

## After Owner

Skill Inspector

## In Scope

- Show inputs/outputs/parameters/package/version/capabilities/prompt refs.
- Expose safe actions such as change/open resource.

## Out of Scope

- No executor internals by default.

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

- [ ] Inspector is definition-driven.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-23`

Do not execute the next card in the same Agent run.
