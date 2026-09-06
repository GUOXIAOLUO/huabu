# CARD R13-06 — Generic Workbench End-to-End Gate

- Round: R13
- Priority: P0
- Status: BACKLOG
- Depends on: R13-05

## Goal

Prove the Workbench is complete and useful with WholeHouse NOT installed.

## Before Owner

component-level platform

## After Owner

generic product proof

## In Scope

- Run Project → Asset → Collection → Task → Skill → Execution → Result → Artifact → Workflow flow.
- Verify Resource Library/Inspector/history/restart.
- Disable/uninstall WholeHouse if present in test environment.

## Out of Scope

- Do not waive failures by enabling WholeHouse.

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

- [ ] Full generic flow passes without WholeHouse.
- [ ] Core contains no WholeHouse imports.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R14-01`

Do not execute the next card in the same Agent run.
