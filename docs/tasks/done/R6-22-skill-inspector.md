# CARD R6-22 — Skill Inspector

- Round: R6
- Priority: P1
- Status: DONE — independent Review PASS (2026-09-11)
- Depends on: R6-21

## Goal

Add a reusable inspector for Skill definition/binding details.

## Before Owner

no generic Skill inspector

## After Owner

Skill Inspector

## In Scope

- Show inputs/outputs/parameters/package/version/capabilities/prompt refs.
- Expose safe actions such as change/open resource.

## Out of Scope

- No executor internals by default.

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

- [x] Inspector is definition-driven.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before:

There was no reusable Skill definition/binding inspector; Task Rich Node had
selector and presentation seams but no definition detail projection.

After:

`WorkbenchSkillInspector` projects versioned Skill identity, package/version,
inputs, outputs, parameters, capabilities, and Prompt references from injected
definition/binding data. It exposes only injected `change` and `open_resource`
callbacks and mounts through a separate Task Rich Node host.

Duplicate owner removed:

No executor/provider/runtime owner was added. Executor internals are not part
of the inspector view model, and action execution remains with host callbacks.

## Next Recommended Card

`R6-23`

Do not execute the next card in the same Agent run.

## Implementation Evidence

Focused `tests/test_task_rich_node.py` coverage passes (9 tests), including
definition/binding projection, safe actions, executor-field exclusion, and
separate NodeShell host wiring. `./scripts/agent-verify.sh` passes with 763
tests, 134 Python AST files, 130 JavaScript files, 4 architecture guards, and
clean diff check. Independent Review initially found a schema projection gap;
the repair now maps canonical `package.package_id`,
`capability_requirements`, and singular `prompt`, with a red regression test
followed by green focused and full verification. Independent Review PASS on
2026-09-11; R6-23 was not started.

## Independent Review

PASS — 2026-09-11. The Inspector is definition-driven against the canonical
SkillDefinition shape, exposes the required details and injected safe actions,
omits executor internals by default, and preserves the ownership boundaries.
