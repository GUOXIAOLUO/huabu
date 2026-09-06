# CARD R7-09 — Codex Bounded Event Queue

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-08

## Goal

Bound Codex bridge event buffering to avoid unbounded memory growth.

## Before Owner

unbounded asyncio.Queue

## After Owner

bounded/backpressure event queue

## In Scope

- Choose bounded strategy.
- Define overflow/backpressure behavior.
- Add stress test.

## Out of Scope

- Do not drop critical terminal events silently.

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

- [ ] Memory is bounded under event burst.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-10`

Do not execute the next card in the same Agent run.
