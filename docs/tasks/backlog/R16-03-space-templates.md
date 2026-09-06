# CARD R16-03 — Space Templates

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-02

## Goal

Provide package templates for common space input/decision structures.

## Before Owner

manual repeated setup

## After Owner

WholeHouse space templates

## In Scope

- Define reusable collection/task/workflow templates.
- Instantiate through generic package/template mechanisms.

## Out of Scope

- No hardcoded Canvas page.

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

- [ ] Template creates generic nodes/resources only.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-04`

Do not execute the next card in the same Agent run.
