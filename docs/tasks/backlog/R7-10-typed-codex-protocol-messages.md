# CARD R7-10 — Typed Codex Protocol Messages

- Round: R7
- Priority: P1
- Status: BACKLOG
- Depends on: R7-09

## Goal

Move raw JSON handling behind typed compatibility/message models.

## Before Owner

raw dict dispatch

## After Owner

typed protocol boundary

## In Scope

- Define request/response/event models for used protocol subset.
- Validate incoming/outgoing envelopes.
- Keep protocol-version compatibility isolated.

## Out of Scope

- No Workbench business types inside raw protocol layer.

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

- [ ] Bridge callers no longer depend on arbitrary raw dict shapes.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R7-11`

Do not execute the next card in the same Agent run.
