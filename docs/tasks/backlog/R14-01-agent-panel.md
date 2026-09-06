# CARD R14-01 — Agent Panel

- Round: R14
- Priority: P0
- Status: BACKLOG
- Depends on: R13-06

## Goal

Add contextual right-side Agent panel without making Agent a top-level product silo.

## Before Owner

no formal Agent UX

## After Owner

Agent Panel

## In Scope

- Create open/close/context lifecycle.
- Show current project/canvas selection context.
- Keep panel separate from raw Codex UI.

## Out of Scope

- No direct mutation tools yet.

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

- [ ] Panel can converse/observe context without bypassing app boundaries.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-02`

Do not execute the next card in the same Agent run.
