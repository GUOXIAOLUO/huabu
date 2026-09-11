# CARD R5-12 — Task Rich Node Skeleton

- Round: R5
- Priority: P1
- Status: DONE
- Previous implementation: COMPLETE — re-executed and repaired 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-11

## Goal

Create the generic Task Rich Node shell before Skill/Execution exists.

## Before Owner

no stable generic task UX

## After Owner

Task Rich Node skeleton

## In Scope

- Define generic task presentation fields.
- Add inputs/definition/skill placeholder/status/workspace/inspector slots.
- Persist only generic task metadata available in R5.

## Out of Scope

- No real Skill Registry.
- No real model execution.

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

- [x] Task is a generic NodeKind/presentation, not an industry node.
- [x] Reload preserves Task state.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: no stable generic task UX existed before Skill and execution domains were introduced.

After: `WorkbenchTaskRichNode` provides generic task identity, inputs, definition placeholder, skill placeholder, status, workspace, inspector, and all four presentation levels. NodeShell creates it for compatible task records and shares the single presentation controller.

Duplicate owner removed: the skeleton persists only the declared generic task metadata, reuses NodeShell's presentation owner, and keeps future Skill Registry/model execution ownership out of the task presentation layer.

Verification: focused TaskRichNode and NodeShell tests pass (4 tests), covering
generic fields, reload, shared presentation ownership, and the production
NodeShell seam. `./scripts/agent-verify.sh` passes (694 tests, 104 Python AST
files, 121 JavaScript files, 4 architecture guards, clean diff check).
Developer Git Review PASS; independent Review PENDING.

## Next Recommended Card

`R5-13`

Do not execute the next card in the same Agent run.
