# CARD R15-10 — Material Selection Skill

- Round: R15
- Priority: P1
- Status: BACKLOG
- Depends on: R15-09

## Goal

Recommend package catalog material options under explicit constraints.

## Before Owner

manual material selection

## After Owner

WholeHouse Material Selection Skill

## In Scope

- Use WholeHouse catalogs + requirement/space context.
- Produce structured MaterialProposal.
- Expose rationale/constraints.

## Out of Scope

- No unverified price/inventory authority unless supplied.

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

- [ ] Recommendations reference exact catalog item versions.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-11`

Do not execute the next card in the same Agent run.
