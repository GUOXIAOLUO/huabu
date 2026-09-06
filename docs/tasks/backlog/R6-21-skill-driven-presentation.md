# CARD R6-21 — Skill-Driven Presentation

- Round: R6
- Priority: P0
- Status: BACKLOG
- Depends on: R6-20

## Goal

Allow Skill metadata/schema to adapt the Task Rich Node UI safely.

## Before Owner

static task skeleton

## After Owner

definition-driven Task presentation

## In Scope

- Render parameter controls from schema.
- Render input roles/output summary from definition.
- Allow declared workspace/action contributions through registries.

## Out of Scope

- No arbitrary code execution from Skill definitions.

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

- [ ] Two different skills produce different Task UI from the same generic node.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-22`

Do not execute the next card in the same Agent run.
