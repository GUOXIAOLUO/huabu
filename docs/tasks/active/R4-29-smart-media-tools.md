# CARD R4-29 — Extract Smart Media Tools

- Round: R4
- Priority: P1
- Status: DONE
- Activated: 2026-09-07T11:30+08:00 (Owner authorization via in-conversation
  "提交并开发下一任务")
- Closed: 2026-09-07T12:05+08:00
- Depends on: R4-28 (DONE 2026-09-07T11:40+08:00)

## Goal

Detach retained Smart crop/edit/draw/grid/panorama tools from Smart Canvas runtime.

## Before Owner

smart-canvas.js

## After Owner

compatibility workspace/capability modules

## In Scope

- Extract retained tools.
- Use unified selection/render lifecycle.
- Preserve behavior.

## Out of Scope

- Do not build future Media Package yet.

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

- `test_media_tools_module_owns_crop_grid_draw_math` — vm-sandbox behavioral
  test over the real `media-tools.js` source: `clampResizeScale` (default
  0.5 / cap 1 / floor 0.05 / round 0.377→0.38), `circledNumber` (①/⑳/"21"),
  `canvasPoint` mapping (110,60 → {20,20}), `gridSplitRects` uniform 2×2
  (four 150×150 rects, and with a 20px gap four 140×140 rects inset by 10px),
  `gridSplitRectsCustom` equals the uniform 2×2 for a single interior cut,
  `parseCropRatio` ('free'→null, '16:9'→16/9, 'source'→1.5, invalid→null),
  and `fitCropRectToAspect` (square-fit centers to {50,0,200,200}; null-ratio
  clamps to {60,70,300,200}).
- `test_media_tools_is_loaded_before_the_smart_page_and_owned` — the module
  loads by `smart-canvas.html` ahead of `smart-canvas.js`; the page delegates
  all seven functions to `mediaTools`; the raw geometry bodies no longer
  survive in the page (`Math.round(num * 100)` / `0x2460` / `topLine + halfGap`
  / `nextW / nextH > ratio` all absent); and `media-tools.js` has zero Smart
  leak (`imageEditModal` / `cropImage` / `editDrawCanvas` / `panoramaState` /
  `gridJoinLayout` / `cropState` / `selectedNode` / `replaceEditedImage` /
  `scheduleSave` / `gridCustomLines` all absent).

## Regression

Run:

```bash
./scripts/agent-verify.sh
```

Result: PASS at 396 Python unit tests (baseline 394; +2), PASS Python AST
parse, PASS JavaScript syntax, PASS Architecture guards (4), PASS
`git diff --check`. `AGENT VERIFY: PASS`.

## Definition of Done

- [x] Retained tools no longer require Smart product runtime.

## Documentation

Update `docs/status/CURRENT_EXECUTION_STATUS.md`.

Update `docs/plans/R4_OWNERSHIP_MATRIX.md` only when this card changes ownership.

Update `AGENT_NEXT_TASK.md` after the card is actually verified.

## Final Ownership Evidence

Before:

`smart-canvas.js` owned the media-tool geometry inline — resize-scale clamp
(`clampImageResizeScale`), circled labels (`circledNumber`), pointer→canvas
mapping (`editDrawPoint`), uniform/custom grid-split rectangles
(`gridSplitRects`/`gridSplitRectsCustom`), and crop aspect parsing/fitting
(`cropRatioFromPreset`/`fitCropRectToAspect`).

After:

`static/js/workbench/canvas/media-tools.js` (`window.WorkbenchCanvasMediaTools`)
owns the pure, stateless tool geometry. Smart keeps only the editor modal,
canvas 2D rendering, the mode/state machine and node mutation, and delegates
the math to a `mediaTools` handle (R4-29).

Duplicate owner removed:

The raw geometry bodies in `smart-canvas.js` are removed — each math function
now has exactly one owner (`media-tools.js`), with no redundant page-side
copy. Panorama (Three.js) remains Smart-owned compatibility, out of scope.

## Next Recommended Card

`R4-30`

Do not execute the next card in the same Agent run.
