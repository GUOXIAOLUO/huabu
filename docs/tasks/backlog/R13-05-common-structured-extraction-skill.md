# CARD R13-05 — Common Structured Extraction Skill

- Round: R13
- Priority: P1
- Status: BACKLOG
- Depends on: R13-04

## Goal

Add generic structured extraction Skill.

## Before Owner

ad hoc extraction prompts

## After Owner

Common structured-extraction Skill

## In Scope

- Accept document/text/image inputs as capabilities permit.
- Allow schema parameter.
- Return structured output.

## Out of Scope

- No domain schema hardcoding.

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

- [ ] Output validates requested schema and lineage.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R13-06`

Do not execute the next card in the same Agent run.
