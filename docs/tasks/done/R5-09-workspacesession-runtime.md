# CARD R5-09 — WorkspaceSession Runtime

- Round: R5
- Priority: P1
- Status: DONE
- Previous implementation: COMPLETE — re-executed and repaired 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-08

## Goal

Create a generic lifecycle for immersive node workspaces.

## Before Owner

ad hoc overlays/editors

## After Owner

WorkspaceSession

## In Scope

- Define open/close/context/dirty/save/discard lifecycle.
- Create WorkspaceRegistry contract.
- Integrate with current canvas selection/context.

## Out of Scope

- No CAD/Image specialized workspace in this card.

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

- [x] A generic workspace can open/close safely.
- [x] Dirty-state behavior is tested.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: immersive editing was represented by ad hoc overlay/editor flags and had no generic lifecycle boundary.

After: `WorkbenchWorkspaceSession` owns transient open/close/context/dirty/save/discard lifecycle, while `WorkspaceRegistry` owns generic workspace definition registration and lookup. `WorkbenchCanvasWorkspaceSession` projects the current Canvas node, selection, canvas, and project into that runtime without persisting Canvas records.

Duplicate owner removed: dirty close/save/discard policy is centralized in the session; specialized workspace implementations remain out of scope and Canvas persistence remains owned by existing application services.

Verification: focused WorkspaceSession, Canvas adapter, and registry tests pass
(3 tests); the selection context is copied and frozen at open time, the
adapter is called by the Canvas open action, and dirty close/save/discard
behavior remains covered. `./scripts/agent-verify.sh` passes (691 tests, 104
Python AST files, 121 JavaScript files, 4 architecture guards, clean diff
check). Developer Git Review PASS; independent Review PENDING.

## Next Recommended Card

`R5-10`

Do not execute the next card in the same Agent run.
