# CARD R8-14 — RunningHubExecutor

- Round: R8
- Priority: P2
- Status: BACKLOG
- Depends on: R8-13

## Goal

Wrap retained RunningHub execution behind the generic Executor contract.

## Before Owner

legacy RunningHub card/runtime

## After Owner

RunningHubExecutor

## In Scope

- Migrate retained route.
- Normalize events/results.
- Remove legacy execution ownership where possible.

## Out of Scope

- No provider-specific Core NodeKind.

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

- [ ] RunningHub works as executor route, not Canvas runtime owner.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R8-15`

Do not execute the next card in the same Agent run.
