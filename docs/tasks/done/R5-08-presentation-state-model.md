# CARD R5-08 — Presentation State Model

- Round: R5
- Priority: P1
- Status: DONE
- Completed: 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-07

## Goal

Introduce card / expanded / workspace / inspector presentation states.

## Before Owner

ad hoc node expansion/editor states

## After Owner

generic presentation state

## In Scope

- Define presentation state and transitions.
- Persist only what is appropriate.
- Integrate with NodeShell and selection without duplicating Canvas state.

## Out of Scope

- No specialized workspaces yet.

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

- [x] Node can transition predictably between presentation states.
- [x] Reload behavior is characterized.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: NodeShell had only ad hoc selected/card rendering state; presentation was not represented as a generic state model.

After: `WorkbenchPresentationState` owns the generic card/expanded/workspace/inspector states, valid transitions, snapshots, and optional adapter-backed persistence. NodeShell projects the state through `data-presentation-state` and state classes and exposes `transitionPresentation()` while selection remains external.

Duplicate owner removed: presentation transition and reload semantics are centralized in the state model; NodeShell does not persist or own Canvas selection/business data.

Verification: re-executed focused presentation-state, NodeShell, render-host, and Canvas runtime tests pass (400 tests); `./scripts/agent-verify.sh` passes (690 tests, 104 Python AST files, 120 JavaScript files, 4 architecture guards, clean diff check). Developer Git Review PASS; independent Review PENDING.

## Next Recommended Card

`R5-09`

Do not execute the next card in the same Agent run.
