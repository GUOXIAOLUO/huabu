# CARD R5-07 — Floating Action Bar

- Round: R5
- Priority: P1
- Status: DONE
- Completed: 2026-09-10
- Independent Review: PASS — 2026-09-10
- Depends on: R5-06

## Goal

Add contextual single/multi-selection actions without permanently bloating node cards.

## Before Owner

embedded/permanent node controls

## After Owner

generic FloatingActionBar

## In Scope

- Define action contribution contract.
- Support single- and multi-selection context.
- Wire generic open/copy/delete/group/create-collection placeholders where available.

## Out of Scope

- Do not implement Collection semantics before R6.
- Do not hardcode WholeHouse actions.

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

- [x] Toolbar appears only contextually.
- [x] Actions are registry/intent driven.

## Documentation

- Update `docs/status/CURRENT_EXECUTION_STATUS.md`.
- Update active-round ownership/status documents only when this card actually changes them.
- Update `AGENT_NEXT_TASK.md` only after this card is verified.


## Final Ownership Evidence

Before: `selectionHub` was an empty placeholder; selection commands were only reachable through embedded controls and keyboard/page handlers.

After: `WorkbenchFloatingActionBar` renders only for non-empty single/multi selection contexts and exposes registry-filtered action buttons through a stable `floating_action` intent.

Duplicate owner removed: action visibility/rendering is owned by the generic bar; Canvas retains only the adapter that maps open/copy/group/delete intents to existing commands. Collection semantics remain deferred to R6.

Verification: focused FloatingActionBar contract tests pass; `./scripts/agent-verify.sh` passes (674 tests, 96 Python AST files, 114 JavaScript files, 4 architecture guards, clean diff check). Git Review PASS.

## Next Recommended Card

`R5-08`

Do not execute the next card in the same Agent run.
