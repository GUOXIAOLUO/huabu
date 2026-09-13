# CARD R6-21 — Skill-Driven Presentation

- Round: R6
- Priority: P0
- Status: DONE — independent Review PASS (2026-09-11)
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

- [x] Two different skills produce different Task UI from the same generic node.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Task Rich Node presentation was a static skeleton and did not project Skill
parameter, port, workspace, or action metadata.

After:

`WorkbenchSkillDrivenPresentation` renders parameter controls from the
declarative schema, input roles and output summaries from the definition, and
declared workspace/actions only through injected registries. It mounts through
the shared Task Rich Node and preserves the generic `task` NodeKind; Selector
and presentation use separate content hosts.

Duplicate owner removed:

No arbitrary code from Skill metadata is executed, and no second execution,
Provider, or industry-specific presentation owner was added.

## Next Recommended Card

`R6-22`

Do not execute the next card in the same Agent run.

## Independent Review

PASS — 2026-09-11. Definition-driven controls, input/output projections, and
registry-backed contributions satisfy the DoD without arbitrary Skill code or
new execution/Provider/industry ownership.
