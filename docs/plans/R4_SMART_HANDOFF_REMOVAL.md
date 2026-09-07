# R4 Smart Handoff Removal

Owner: card R4-35. Retires the Smart product-page handoff surface in the
`WorkbenchCanvasEntryCompatibility` module. After R4-34 stopped consuming
the handoff (the unified `canvas.html` now opens every record natively), the
handoff helpers are dead surface — no JS code routes to `smart-canvas.html`
any more — so this card deletes the helpers and the last `/static/smart-canvas.html`
string. The `smart-canvas.html` / `smart-canvas.js` product page stays on
disk (out of scope at R4-35; `R4-36` retired the page after the Smart-capability
migration is verified).

## What gets removed

From `static/js/workbench/canvas/canvas-entry-compatibility.js`:

- The function `requiresLegacySmartHandoff(canvas)` — the Smart/Classic
  kind discriminator. Its sole post-R4-34 consumer was
  `test_canvas_entry.py::test_entry_compatibility_keeps_one_normal_entry_and_scopes_smart_handoff`.
- The function `legacySmartCanvasUrl(canvasId, search)` — the URL builder
  for `/static/smart-canvas.html?id=…`. Its sole post-R4-34 consumer was
  the same test.
- The string literal `/static/smart-canvas.html` — currently appears once,
  inside `legacySmartCanvasUrl`. Removing the function is the only place
  it lives.

From the frozen export, the two functions drop out of
`global.WorkbenchCanvasEntryCompatibility`.

## What stays (the compatibility module's retained surface)

The module continues to provide the non-handoff surface that
`canvas.js`, `canvas-list.js`, `asset-manager.js`, and `smart-canvas.js`
still consume:

- `normalCanvasUrl(canvasId, projectId)` — the single entry URL, returns
  `/static/canvas.html?id=…&project=…`. Used by `canvas.js`
  (R4-34 createCanvas Smart branch), `canvas-list.js` (the list entry
  URL), and `asset-manager.js`.
- `rememberCanvasListProject(projectId, options)` and
  `rememberedCanvasListProject(options)` — the list-project persistence
  helpers. Used by `canvas.js` and `smart-canvas.js`.
- `canvasListUrl(projectId, options)` — the list-page URL builder. Used
  by `canvas.js` and `smart-canvas.js`.

These are required compatibility helpers (out of scope: do not delete
the module or its retained surface).

## Why the removal is safe

After R4-34, a static-JS audit (`grep smart-canvas.html static/js/**/*.js`)
finds exactly one hit — the `legacySmartCanvasUrl` body. The Smart
product page itself (`smart-canvas.js`) does not reference its own URL
(it is reached only by direct navigation, which is also out of scope for
this card). With `legacySmartCanvasUrl` removed, **no JS file constructs
a navigation to `smart-canvas.html`**, and the DoD "No Smart product
page routing remains" is satisfied at the source level.

The pre-existing test
`test_entry_compatibility_keeps_one_normal_entry_and_scopes_smart_handoff`
is updated to pin the post-removal surface (the module exports the
four non-handoff functions, the handoff helpers are gone, and the
`smart-canvas.html` URL string is gone from the module). The pre-existing
`test_product_openers_confine_smart_page_urls_to_the_compatibility_boundary`
is updated from "the URL is confined to the compatibility module" to
"the URL is gone from every JS file" — i.e. the compatibility boundary
itself no longer carries the URL.

## Inventory

| Surface | Disposition | Before evidence |
|---|---|---|
| `WorkbenchCanvasEntryCompatibility.requiresLegacySmartHandoff` | **removed** (this card) | sole consumer: `test_canvas_entry.py` |
| `WorkbenchCanvasEntryCompatibility.legacySmartCanvasUrl` | **removed** (this card) | sole consumer: `test_canvas_entry.py`; only holder of the `/static/smart-canvas.html` URL string |
| `WorkbenchCanvasEntryCompatibility.normalCanvasUrl` | unchanged | `canvas.js` (R4-34), `canvas-list.js`, `asset-manager.js` |
| `WorkbenchCanvasEntryCompatibility.rememberCanvasListProject` / `rememberedCanvasListProject` | unchanged | `canvas.js`, `smart-canvas.js` |
| `WorkbenchCanvasEntryCompatibility.canvasListUrl` | unchanged | `canvas.js`, `smart-canvas.js` |
| `smart-canvas.html` / `smart-canvas.js` (product page) | retired by R4-36 | R4-36 deleted the page and the editor; R4-37 retires the remaining Smart runtime modules (composer, media-tools, execution-host) |
