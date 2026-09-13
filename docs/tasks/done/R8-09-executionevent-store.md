# CARD R8-09 — ExecutionEvent Store

- Round: R8
- Priority: P0
- Status: ACTIVE — implementation complete; awaiting independent Review
- Depends on: R8-08

## Goal

Store/stream normalized execution events.

## Before Owner

executor-specific logs

## After Owner

ExecutionEvent

## In Scope

- Define event sequence/type/payload/time.
- Persist/stream through service.
- Preserve bounded retention strategy.

## Out of Scope

- Do not make raw provider logs business authority.

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

- [x] Run progress can be reconstructed/observed through normalized events.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: executor-specific event streams had no Workbench-owned durable
normalized event record or restart-safe polling boundary.

After: `ExecutionEventRecord` owns normalized type, monotonic per-run
sequence, run/attempt references, payload, and occurrence time. SQLite
persists and polls events after restart with a bounded per-run retention
window; service/API expose append and after-sequence observation.

Duplicate owner removed: raw provider logs remain executor diagnostics and are
not persisted as business authority; no UI or Legacy monolith owns event state.

## Next Recommended Card

`R8-10`

Do not execute the next card in the same Agent run.
