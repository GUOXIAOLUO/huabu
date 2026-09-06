# CARD R15-12 — Render Review Skill

- Round: R15
- Priority: P1
- Status: BACKLOG
- Depends on: R15-11

## Goal

Review render candidates against requirement/design intent.

## Before Owner

manual effect image review

## After Owner

WholeHouse Render Review Skill

## In Scope

- Accept RenderCandidates Collection + requirements/design refs.
- Return structured review/score/findings.
- Use compare workspace/result refs.

## Out of Scope

- Review does not equal approval.

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

- [ ] Review lineage points to exact renders.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R15-13`

Do not execute the next card in the same Agent run.
