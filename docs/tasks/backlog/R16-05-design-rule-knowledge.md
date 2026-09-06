# CARD R16-05 — Design Rule Knowledge

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R16-04

## Goal

Encode reusable design review rules with provenance and package scope.

## Before Owner

prompt-only review rules

## After Owner

structured design-rule knowledge

## In Scope

- Define rule metadata/severity/applicability/source.
- Use in review Skills.
- Keep rule result distinct from human approval.

## Out of Scope

- No claims of code compliance without authoritative source.

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

- [ ] Review can identify which rules triggered.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-06`

Do not execute the next card in the same Agent run.
