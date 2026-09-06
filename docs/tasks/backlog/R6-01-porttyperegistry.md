# CARD R6-01 — PortTypeRegistry

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R5-13

## Goal

Establish an extensible registry for typed ports without industry-specific permanent Core types.

## Before Owner

stringly-typed/ad hoc port artifact types

## After Owner

PortTypeRegistry

## In Scope

- Characterize existing port strings.
- Define generic core types and extension mechanism.
- Include generic CAD-compatible type such as asset.cad without WholeHouse semantics.

## Out of Scope

- No executor-specific port logic.

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

- [ ] Ports resolve through one registry.
- [ ] Package extension does not require new Core NodeKind.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-02`

Do not execute the next card in the same Agent run.
