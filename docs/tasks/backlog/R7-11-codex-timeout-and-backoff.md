# CARD R7-11 — Codex Timeout and Backoff

- Round: R7
- Priority: P1
- Status: BACKLOG
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

- [ ] Failures are bounded and observable.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-12`

Do not execute the next card in the same Agent run.
