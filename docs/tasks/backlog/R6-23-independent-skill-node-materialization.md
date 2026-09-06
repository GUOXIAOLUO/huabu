# CARD R6-23 — Independent Skill Node Materialization

- Round: R6
- Priority: P2
- Status: BACKLOG
- Depends on: R6-22

## Goal

Allow advanced users to materialize a Skill as a visible workflow/debug node.

## Before Owner

Skill only embedded in Task

## After Owner

optional Skill node presentation

## In Scope

- Create generic skill-node renderer/definition ref.
- Support connecting/binding for workflow visualization.
- Keep embedded SkillBinding as default path.

## Out of Scope

- Do not make every Skill call create a node.

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

- [ ] Standalone Skill is optional and does not duplicate SkillDefinition.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

After:

Duplicate owner removed:

## Next Recommended Card

`R6-24`

Do not execute the next card in the same Agent run.
