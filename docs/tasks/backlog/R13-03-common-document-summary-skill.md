# CARD R13-03 — Common Document Summary Skill

- Round: R13
- Priority: P1
- Status: BACKLOG
- Depends on: R13-02

## Goal

Add executable document-summary Skill as second generic proof.

## Before Owner

no packaged generic summary

## After Owner

Common document-summary Skill

## In Scope

- Define document input/summary output/parameters.
- Use model compatibility resolver.
- Add tests.

## Out of Scope

- No custom document editor required.

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

- [ ] Skill executes through same generic runtime.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-04`

Do not execute the next card in the same Agent run.
