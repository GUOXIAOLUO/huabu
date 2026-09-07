# R4 Smart Native Entry

Owner: card R4-34. Makes `canvas.html` the single entry that can open a
historical Smart record natively, without redirecting to `smart-canvas.html`.
This is a routing + shared-seam-loading deliverable: it removes the Smart
handoff redirect from `canvas.js` and makes the Smart-compatibility shared
seams (Composer lifecycle, media edit math) available to the unified page so
the record opens with its retained canvas-runtime capabilities. The Smart
product runtime (`smart-canvas.html` / `smart-canvas.js`) and the
`canvas-entry-compatibility` handoff functions stay on disk (out of scope:
`R4-35` removes the handoff module; `R4-36` removes the Smart page).

## The entry-routing surface (before)

Across the page set, the Smart/Classic decision lives in three call sites:

1. **The canvas list** — `static/js/canvas-list.js:471` builds every entry
   URL through `WorkbenchCanvasEntryCompatibility.normalCanvasUrl(c.id,
   projectId)`, which always returns `/static/canvas.html?id=…&project=…`.
   The list itself does **not** redirect to `smart-canvas.html`.
2. **The unified page** — `static/js/canvas.js:2089` checks
   `WorkbenchCanvasEntryCompatibility.requiresLegacySmartHandoff(canvas)`
   inside `openCanvas` and, when the record is a Smart, calls
   `openSmartCanvasPage(canvas.id)` (defined at 1963) to build
   `/static/smart-canvas.html?id=…` and set `window.location.href`. This is
   THE redirect that this card removes.
3. **The new-canvas gate** — `static/js/canvas.js:1933` in `createCanvas`,
   after POSTing a new Smart canvas, calls `openSmartCanvasPage(data.canvas?.id)`
   so a freshly created Smart lands on the Smart product runtime. R4-34
   redirects this to `canvas.html` as well, so a new Smart and a re-opened
   historical Smart both land on the unified page (consistent contract).

The `WorkbenchCanvasEntryCompatibility` module
(`static/js/workbench/canvas/canvas-entry-compatibility.js`) is the
authoritative router: it owns `normalCanvasUrl`, `legacySmartCanvasUrl`,
`requiresLegacySmartHandoff`, and the list-project helpers. R4-34 only
removes the two consumers in `canvas.js`; the module itself is untouched
and continues to export the handoff helpers for `R4-35` to retire.

## The shared-seam gap (before)

`canvas.html` already loads the unified CanvasRuntime and every shared
workbench module needed for the Classic runtime, but it does **not** load
the two Smart-compatibility shared seams that a Smart record relies on
when rendered outside `smart-canvas.js`:

- `composer.js` — the Composer shell lifecycle (R4-28): the floating
  Composer card's container, open/close, node-relative centering, and
  sequence-guarded debounced update. Smart records use this seam for
  subject resolution + parameter rendering.
- `media-tools.js` — the Smart crop/draw/grid/resize geometry (R4-29):
  pure stateless math (`clampResizeScale`, `circledNumber`, `canvasPoint`,
  `gridSplitRects` / `gridSplitRectsCustom`, `parseCropRatio`,
  `fitCropRectToAspect`).

These two modules are pure compatibility seams (frozen handles on
`window`, no DOM coupling, no Smart/Classic branching inside the module
body). Loading them in `canvas.html` is additive: they sit idle unless
something asks for them, and a Classic record never asks for them.

The Smart execution seam (`execution-host.js`, R4-30) is **not** loaded in
`canvas.html` for this card. Smart execution paths in the unified page
would need `smart-canvas.js`'s wiring of `runPromptLLMNode` / the host,
which is explicitly out of scope (`smart-canvas.js` stays on disk until
`R4-36`); loading the bare module would dangle. Classic execution uses
`classic-execution-host.js` (R4-33) which is already loaded.

## Host cutover (this card)

This card makes two narrow changes:

1. **Remove the redirect from `canvas.js`** — the
   `requiresLegacySmartHandoff(canvas)` check inside `openCanvas` (2089)
   and the `openSmartCanvasPage` redirect it triggers (1963) are removed,
   plus the equivalent call from `createCanvas`'s Smart branch (1936),
   which now navigates to `canvas.html` via `normalCanvasUrl(id, project)`
   so a freshly created Smart also opens on the unified page. With both
   call sites gone, `openSmartCanvasPage` itself becomes dead code and is
   removed.
2. **Load the two Smart-compatibility shared seams in `canvas.html`** —
   `<script src="/static/js/workbench/canvas/composer.js">` and
   `<script src="/static/js/workbench/canvas/media-tools.js">` are
   inserted ahead of `canvas.js`, mirroring the order used by
   `smart-canvas.html` (lines 496–497).

After this card:

- Opening a historical Smart record from the list lands the user on
  `canvas.html`. The unified runtime loads the record, the shared
  Composer / media-tools seams are available for the Smart node types,
  persistence flows through the shared `WorkbenchCanvasPersistence`
  client, and the user never navigates to `smart-canvas.html`.
- Creating a new Smart canvas lands the user on `canvas.html` with the
  same unified runtime.
- The Smart product runtime files stay on disk (`out of scope` at
  R4-34; `R4-36` retired `smart-canvas.html` / `smart-canvas.js` /
  `static/css/smart-canvas.css` and the Smart i18n bundle; the
  remaining Smart runtime modules — `composer.js`, `media-tools.js`,
  `execution-host.js` — are now consumed only by the unified page and
  are retired by `R4-37`).
- The `WorkbenchCanvasEntryCompatibility` handoff helpers
  (`requiresLegacySmartHandoff`, `legacySmartCanvasUrl`) were retired
  by `R4-35`.

## Inventory

| Entry point | Disposition | Before evidence |
|---|---|---|
| `canvas-list.js` open card | unchanged | `WorkbenchCanvasEntryCompatibility.normalCanvasUrl(c.id, projectId)` at line 471 — already routes every record (Classic + Smart) to `canvas.html`. |
| `canvas.js` `openCanvas` Smart branch | **host-cutover** (this card) | lines 2089–2091: `if(requiresLegacySmartHandoff(canvas)){ openSmartCanvasPage(canvas.id); return; }` — removed. |
| `canvas.js` `createCanvas` Smart branch | **host-cutover** (this card) | lines 1933–1937: `if(isSmart){ … openSmartCanvasPage(data.canvas?.id); return; }` — `openSmartCanvasPage` call replaced by `normalCanvasUrl(data.canvas?.id, data.canvas?.project || 'default')` navigation to `canvas.html`. |
| `canvas.js` `openSmartCanvasPage` | **dead code removed** (this card) | defined at 1963; sole callers were the two cutover sites above. |
| `canvas.html` shared-seam load | **host-cutover** (this card) | `<script>` for `composer.js` + `media-tools.js` added ahead of `canvas.js`. |
| `WorkbenchCanvasEntryCompatibility` handoff helpers | **unchanged** | `requiresLegacySmartHandoff` / `legacySmartCanvasUrl` stay exported; `R4-35` retires them. |
| `smart-canvas.html` / `smart-canvas.js` | **unchanged** | out of scope: `R4-36` retires them after capability migration is verified. |

## Evidence manifest

Machine-readable; anchored by `tests/test_smart_native_entry.py` (or the
focused wiring contract in `tests/test_frontend_workbench_modules.py`).

```json
{
  "source": "static/js/canvas.js",
  "entry_points": [
    {"id": "open-canvas-smart-branch", "function": "openCanvas", "disposition": "host-cutover", "evidence": ["WorkbenchCanvasEntryCompatibility.requiresLegacySmartHandoff", "openSmartCanvasPage"]},
    {"id": "create-canvas-smart-branch", "function": "createCanvas", "disposition": "host-cutover", "evidence": ["openSmartCanvasPage", "WorkbenchCanvasEntryCompatibility.normalCanvasUrl"]},
    {"id": "open-smart-canvas-page", "function": "openSmartCanvasPage", "disposition": "dead-code-removed", "evidence": ["legacySmartCanvasUrl"]},
    {"id": "canvas-list-entry", "function": "openCanvasCard", "disposition": "unchanged", "evidence": ["WorkbenchCanvasEntryCompatibility.normalCanvasUrl"]},
    {"id": "entry-compatibility-handoff", "function": "WorkbenchCanvasEntryCompatibility.requiresLegacySmartHandoff", "disposition": "unchanged", "evidence": ["legacySmartCanvasUrl"]}
  ]
}
```
