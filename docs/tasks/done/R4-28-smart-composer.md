# CARD R4-28 — Extract Smart Composer

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T11:15+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T11:40+08:00
- Depends on: R4-27 (DONE 2026-09-07T11:05+08:00)

## Goal

Detach Smart Composer from smart-canvas product runtime.

## Before Owner

smart-canvas.js

## After Owner

mountable compatibility capability

## In Scope

- Extract lifecycle/dependencies.
- Connect through unified creation/render boundaries.
- Remove Smart runtime ownership.

## Out of Scope

- Do not redesign Composer.

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

- `test_composer_lifecycle_owns_position_open_and_debounced_schedule` —
  vm-sandbox behavioral test over the real `composer.js` source (with stubbed
  `setTimeout`/`clearTimeout`/`window`): asserts `setOpen`/`isOpen` toggle the
  `open` class, default position math (rect `{x:100,y:200,width:300,height:50}`
  → `540px` width / `-20px` left / `264px` top), custom `{gap:8,cardWidth:200}`
  → `200px` / `-40px` / `68px`, the debounce cancels the first timer, the second
  fires exactly once, and `cancelPending()` clears the timer + bumps the
  sequence guard.
- `test_composer_lifecycle_is_loaded_before_the_smart_page_and_owned` — the
  module is loaded by `smart-canvas.html` ahead of `smart-canvas.js`; the page
  delegates position/open/close/debounce to `composerLifecycle`
  (`positionForRect(nodeRect(node))`, `scheduleUpdate(delay, updateComposer)`,
  `cancelPending()`, `setOpen(`); no residual `composerUpdateTimer` /
  `composerUpdateSeq` remain; and `composer.js` has zero Smart leak
  (`smart-minimax` / `imageInput` / `cascadeRunBtn` / `selectedNode` /
  `renderDynamicParams` / `promptInput` all absent).

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 394 Python unit tests (baseline 392; +2), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

## Definition of Done

- [x] Composer works without Smart product runtime ownership.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`smart-canvas.js` owned the Composer shell lifecycle directly — the floating
card container, its open/close state, node-relative positioning
(`positionComposerForNode`), and the debounced update scheduling
(`scheduleComposerUpdate` / `composerUpdateTimer` / `composerUpdateSeq` /
`updateComposer`).

After:

`static/js/workbench/canvas/composer.js` (`window.WorkbenchCanvasComposer`)
owns the shell lifecycle: container, `setOpen`/`isOpen`, `positionForRect`,
`cancelPending`, `scheduleUpdate` (sequence-guarded debounce). Smart
`smart-canvas.js` keeps only subject resolution (`selectedNode()`) and dynamic
provider/media/prompt parameter rendering inside `updateComposer`, and routes
the shell through a `composerLifecycle` handle.

Duplicate owner removed:

The page-level `composerUpdateTimer`/`composerUpdateSeq` state and the direct
`composer.classList` open/close mutations are removed; there is now exactly one
owner for the open/close/position/debounce lifecycle (`composer.js`), with no
redundant Smart-side scheduling state.

## Next Recommended Card

`R4-29`

Do not execute the next card in the same Agent run.
