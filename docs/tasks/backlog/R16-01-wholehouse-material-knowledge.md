# CARD R16-01 — WholeHouse Material Knowledge

- Round: R16
- Priority: P1
- Status: BACKLOG
- Depends on: R15-15

## Goal

Build package knowledge sources/entries for material rules and design guidance.

## Before Owner

prompt-local knowledge

## After Owner

WholeHouse material knowledge

## In Scope

- Curate verified material knowledge sources.
- Create entries with provenance.
- Expose through ProjectKnowledgeContext.

## Out of Scope

- No unverifiable manufacturer claims as facts.

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

- [ ] Skills retrieve material knowledge through generic Knowledge service.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R16-02`

Do not execute the next card in the same Agent run.
