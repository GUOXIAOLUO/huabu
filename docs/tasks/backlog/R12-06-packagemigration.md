# CARD R12-06 — PackageMigration

- Round: R12
- Priority: P0
- Status: BACKLOG
- Depends on: R12-05

## Goal

Provide explicit, reviewable migration between package versions.

## Before Owner

implicit schema drift

## After Owner

PackageMigration

## In Scope

- Define migration plan/result/backup/validation.
- Require explicit project migration.
- Test rollback boundary.

## Out of Scope

- No automatic hidden migrations.

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

- [ ] Package upgrade produces auditable migration evidence.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R12-07`

Do not execute the next card in the same Agent run.
