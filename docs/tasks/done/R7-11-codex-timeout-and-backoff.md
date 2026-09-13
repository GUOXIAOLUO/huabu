# CARD R7-11 — Codex Timeout and Backoff

- Round: R7
- Priority: P1
- Status: DONE — independent Review PASS 2026-09-11
- Depends on: R7-10

## Goal

Add predictable timeout/retry/backoff policies for transport operations.

## Before Owner

ad hoc waits

## After Owner

transport timeout/backoff policy

## In Scope

- Add request timeouts.
- Define restart/recovery boundaries.
- Test timeout and cancellation.

## Out of Scope

- No infinite retries.

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

- [x] Failures are bounded and observable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `CodexBridge` applied a single ad hoc timeout and had no retry safety
classification, backoff policy, or timeout event.

After: `HarnessLaunchPolicy` owns bounded attempts and capped exponential
backoff. Only initialize/resume/discovery reads retry; side-effecting thread
creation and turns remain single-attempt. Final timeout emits a normalized
transport event and raises `CodexBridgeError`; cancellation and pending cleanup
remain explicit.

Duplicate owner removed: timeout/retry decisions are centralized in the Codex
bridge policy/request boundary; no retry loop was added to callers or business
services.

Focused evidence: tests cover successful retry after timeout, bounded
non-retryable timeout with observable event, cancellation without retry or
pending leakage, and existing recovery behavior. Focused tests pass (9); full
verification passes with 792 tests, 154 Python AST files, 134 JavaScript files,
4 architecture guards, and clean diff check.

## Next Recommended Card

`R7-12`

Do not execute the next card in the same Agent run.
