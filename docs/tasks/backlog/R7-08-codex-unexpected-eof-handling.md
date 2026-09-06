# CARD R7-08 — Codex Unexpected EOF Handling

- Round: R7
- Priority: P0
- Status: BACKLOG
- Depends on: R7-07

## Goal

Fail all pending requests predictably when App Server exits unexpectedly.

## Before Owner

incomplete EOF behavior

## After Owner

explicit transport failure lifecycle

## In Scope

- Detect EOF.
- Fail pending futures.
- Normalize terminal error.
- Test recovery/restart path.

## Out of Scope

- No silent auto-substitution.

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

- [ ] No pending request hangs after EOF.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-09`

Do not execute the next card in the same Agent run.
