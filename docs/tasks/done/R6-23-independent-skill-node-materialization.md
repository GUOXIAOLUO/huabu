# CARD R6-23 — Independent Skill Node Materialization

- Round: R6
- Priority: P2
- Status: DONE — independent Review PASS (2026-09-11)
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

- [x] Standalone Skill is optional and does not duplicate SkillDefinition.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

Skills were represented only through embedded Task SkillBinding; no optional
standalone Skill node renderer or materialization command existed.

After:

`WorkbenchSkillNodeMaterializer` creates a generic `skill` DefinitionRef
command with the exact SkillBinding embedded in `initial_config`, then
delegates persistence to the injected canonical NodeCreationService/client
callback. `WorkbenchSkillNodeRenderer` renders the existing Skill node's
definition ref, binding, and typed ports through the shared RendererRegistry.

Duplicate owner removed:

No second SkillDefinition, Canvas mutation, persistence, or execution owner was
added. Embedded Task SkillBinding remains the default path; standalone node
materialization is opt-in and its visible ports only reuse canonical node data.

## Next Recommended Card

`R6-24`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_skill_node_materialization.py` coverage passes (3 tests),
including canonical command delegation, optional renderer behavior, binding
preservation, and shared RendererRegistry wiring. `./scripts/agent-verify.sh`
passes with 766 tests, 135 Python AST files, 132 JavaScript files, 4
architecture guards, and clean diff check. Independent Review PASS on
2026-09-11; R6-24 was not started.

## Independent Review

PASS — 2026-09-11. Standalone Skill materialization is optional, delegates
canonical creation, renders the generic Skill definition ref/binding/ports,
and does not duplicate SkillDefinition or runtime ownership.
