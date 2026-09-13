# CARD R7-09 — Codex Bounded Event Queue

- Round: R7
- Priority: P0
- Status: DONE — independent Review PASS 2026-09-11
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

- [x] Memory is bounded under event burst.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `CodexBridge.events` used an unbounded `asyncio.Queue`, and the stdout
reader awaited every event insertion.

After: `CodexBridge` owns a fixed-capacity queue (`maxsize=256`) and publishes
with non-blocking `put_nowait`; normal overflow is counted, one slot is
reserved for critical events, and critical events only evict ordinary buffered
events. Critical overflow is separately counted rather than silently evicting
another critical event.

Duplicate owner removed: none introduced; queue ownership remains exclusively
inside `workbench/codex/bridge.py`.

Focused evidence: `test_event_storm_is_bounded_and_preserves_critical_event`
publishes 5,000 notifications, verifies the queue never exceeds 256 entries,
verifies the terminal transport event survives overflow, and verifies a fully
critical queue reports critical overflow explicitly. The focused Codex bridge
suite passes (6 tests).

## Next Recommended Card

`R7-10`

Do not execute the next card in the same Agent run.
