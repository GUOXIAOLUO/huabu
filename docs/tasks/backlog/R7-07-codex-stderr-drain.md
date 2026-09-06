# CARD R7-07 — Codex stderr Drain

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-06

## Goal

Prevent Codex App Server stderr pipe buildup and preserve diagnostics.

## Before Owner

undrained stderr task

## After Owner

managed stderr drain

## In Scope

- Add lifecycle-managed drain.
- Bound/log diagnostics safely.
- Test shutdown.

## Out of Scope

- No Agent tools yet.

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

- [ ] Long-running bridge cannot deadlock on stderr pipe.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-08`

Do not execute the next card in the same Agent run.
