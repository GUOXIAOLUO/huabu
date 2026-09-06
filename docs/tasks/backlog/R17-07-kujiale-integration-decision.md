# CARD R17-07 — Kujiale Integration Decision

- Round: R17
- Priority: P1
- Status: BACKLOG
- Depends on: R17-06

## Goal

Decide file handoff vs API/MCP/Local Bridge for Kujiale from observed evidence.

## Before Owner

preference/speculation

## After Owner

documented architecture decision

## In Scope

- List observed friction.
- Evaluate integration options, maintenance/risk/value.
- Choose defer/file/API/MCP/local bridge with rationale.

## Out of Scope

- Do not implement integration yet unless a new approved round/card is created.

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

- [ ] Decision is evidence-backed and reversible.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R17-08`

Do not execute the next card in the same Agent run.
