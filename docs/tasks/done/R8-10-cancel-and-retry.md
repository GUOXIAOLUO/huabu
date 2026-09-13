# CARD R8-10 — Cancel and Retry

- Round: R8
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-12)
- Depends on: R8-09

## Goal

Provide application-level cancellation and retry semantics.

## Before Owner

executor-specific controls

## After Owner

ExecutionService cancel/retry

## In Scope

- Implement cancel flow.
- Retry failed attempt/item according to policy.
- Normalize terminal states.

## Out of Scope

- No automatic infinite retry.

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

- [x] Cancel/retry behave consistently across fake/available executors.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: cancellation and retry behavior was left to executor-specific controls;
there was no application owner for terminal normalization or retry limits.

After: `ExecutionService` owns explicit cancel orchestration through the
provider-neutral `Executor.cancel` contract, terminal-state normalization, and
bounded failed-attempt retry using `ExecutionPolicy.retry`.

Duplicate owner removed: no executor selection or replacement was added;
unsupported cancellation remains explicit, and no automatic infinite retry or
R8-11 executor implementation was introduced.

Retry creation is serialized inside the SQLite repository with run/attempt
revision checks, latest-item validation, canonical prepared-attempt validation,
and the existing `audit_outbox`; cancellation/status mutations use the same
atomic audit boundary. Direct attempt cancellation and prepared/queued runs
also pass through one terminal-state normalization helper, which evaluates the
latest attempt per item so an earlier failed retry does not poison a later
successful result. The application boundary is exposed through run/attempt
cancel and retry controls and is wired from `main.py`; an explicit retry may
requeue a failed run within the immutable retry policy.

Independent Review: PASS (Standards and Spec axes, 2026-09-12). Full
verification passed with 843 tests.

## Next Recommended Card

`R8-11`

Do not execute the next card in the same Agent run.
