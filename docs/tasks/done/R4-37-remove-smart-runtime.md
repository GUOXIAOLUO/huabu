# CARD R4-37 — Delete smart-canvas.js Product Runtime

- Round: R4
- Priority: P0
- Status: DONE
- Activated: 2026-09-07T15:23+08:00
- Closed: 2026-09-07T15:23+08:00
- Depends on: R4-36

> **Pre-emption note.** R4-36's commit
> (`a4552ee R4-36: delete smart-canvas product page`) explicitly expanded its
> scope to delete `static/js/smart-canvas.js` along with the page itself, after
> R4-34/R4-35 had already moved every retained Smart behavior behind a
> compat seam. By the time R4-37 was activated, `static/js/smart-canvas.js`
> had already been removed from disk; R4-37 is therefore an accounting close
> that verifies the documented DoD, pins regression parity, and forwards to
> `R4-38`.

## Goal

Remove Smart monolith as a product runtime.

## Before Owner

smart-canvas.js (full Smart product runtime: page surface, editor, group /
media lifecycle, Composer shell, prompt presets/skills, dynamic provider /
media / MiniMax controls, video workflow, asset UX, and cascade/execution
orchestration, ~6 kloc of JS).

## After Owner

Unified runtime + bounded compatibility seams:

- shared `canvas.html` page surface (R4-34/R4-36);
- `WorkbenchCanvasComposer` shell-lifecycle seam (R4-28);
- `WorkbenchCanvasMediaTools` crop/draw/grid/resize geometry seam (R4-29);
- `WorkbenchCanvasExecutionHost` execution-lifecycle seam (R4-30);
- `WorkbenchCanvasEntryCompatibility` entry normalisation, with the Smart
  handoff branch retired (R4-34/R4-35);
- shared `LegacyJSONGraphCompatibilityRepository` graph commit path
  (R4-25/R4-26);
- shared `WorkbenchNodeClient` versioned command surface (R4-21+).

## In Scope

- Verify no retained capability depends on Smart monolith.
- Delete runtime.
- Update imports/tests.

## Out of Scope

- Do not replace it with another monolith.

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

Add or run the smallest behavioral tests that prove this card's exact goal.
Do not rely only on source-string checks when runtime behavior can be tested.

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

## Definition of Done

- [x] smart-canvas.js no longer exists as product runtime. (pre-empted by
  R4-36; verified at activation 2026-09-07T15:23+08:00.)
- [x] No functional reference to `smart-canvas.html` / `smart-canvas.js` /
  `smart-canvas.css` survives in active JS, HTML, CSS, or Python. (full-repo
  grep returned zero hits at activation.)
- [x] The Smart product-runtime ownership row in
  `docs/plans/R4_OWNERSHIP_MATRIX.md` carries the R4-36 retirement pointer
  (`(retired)`) and was not re-touched on this card.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.
R4-37 does not re-touch the matrix: R4-36 already updated the Smart product
runtime row to `(retired)`.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`static/js/smart-canvas.js` was the Smart product runtime — page lifecycle,
editor, Composer shell, group / media lifecycle, prompt presets/skills,
dynamic provider / media / MiniMax controls, video workflow, asset UX, and
the cascade / execution orchestration. The Classic page
(`static/js/canvas.js`) was the parallel product runtime.

After:

`static/js/smart-canvas.js` is deleted. Every retained Smart behavior has a
named bounded seam documented in `docs/plans/R4_OWNERSHIP_MATRIX.md` (Smart
product-runtime row already at `(retired)` since R4-36). A full-repo grep of
`smart-canvas\.(html|js|css)` patterns against `*.{js,html,css,py}` returns
zero functional hits; the surviving `smart-canvas` tokens are all
historical comments (`canvas-list.js` viewport-math note, `media-tools.js`
geometry-history note, `canvas-entry-compatibility.js` navigation-history
note) or the board-row CSS class identifier in `canvas.js` for Smart-kind
records.

Duplicate owner removed:

The Smart product runtime is retired. The Unified runtime
(`canvas.html` + shared Canvas modules) is the sole canvas runtime;
`canvas.js` (Classic) is the next duplicate to remove (R4-38).

## Regression Evidence

- `./scripts/agent-verify.sh` PASS at 343 tests (was 343 after R4-36;
  unchanged — confirming pre-emption).
- Python AST parse: 76 files, OK.
- JavaScript syntax: 71 files, OK.
- Architecture guards (`tests/test_architecture_guards.py`): 4 tests, OK.
- `git diff --check`: clean.

## Next Recommended Card

`R4-38 — Reduce canvas.js to Bootstrap/Compatibility Only`
(`docs/tasks/backlog/R4-38-shrink-classic-runtime.md`).

Do not execute the next card in the same Agent run.
