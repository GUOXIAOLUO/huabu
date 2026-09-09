# R4-39 Classic Runtime Removal Inventory

Status: completed on 2026-09-09
Source: `static/js/canvas.js`
Authority: `docs/status/CURRENT_EXECUTION_STATUS.md` and
`docs/plans/R4_OWNERSHIP_MATRIX.md`

## Purpose

R4-39 removes the remaining Classic product runtime. Renaming `canvas.js`,
moving bodies into another Classic module, or adding a wide pass-through host
does not satisfy this card. A responsibility is removable only when its final
owner can run without page-global state from `canvas.js` and has focused
behavior plus browser parity evidence.

## Characterized baseline (2026-09-08)

- `canvas.js`: 12,754 lines after the R4-38 post-review repair.
- It still declares the Canvas/page state, DOM handles, bootstrap sequence,
  persistence orchestration, rendering dispatch, interaction lifecycle,
  graph/group compatibility, prompt/workflow UI, media editing, and the host
  adapters for the extracted Classic compatibility seams.
- The extracted `classic-*.js` files are not independent replacement owners:
  executor and asset seams alone require 107 and 101 host operations,
  respectively, and are instantiated from `canvas.js`.
- `canvas.html` still loads `canvas.js`; deleting it now produces no runnable
  Canvas application.

## Residual ownership manifest

```json
{
  "schema": "workbench.r4-39-classic-runtime-removal/2",
  "sources": [
    "static/js/workbench/canvas/canvas-app-state.js",
    "static/js/workbench/canvas/canvas-app-records.js",
    "static/js/workbench/canvas/canvas-app-media-editor.js",
    "static/js/workbench/canvas/canvas-app-compat-host.js",
    "static/js/workbench/canvas/canvas-app-provider-ui.js",
    "static/js/workbench/canvas/canvas-app-execution.js",
    "static/js/workbench/canvas/canvas-app-output-ui.js",
    "static/js/workbench/canvas/canvas-app-interaction.js",
    "static/js/workbench/canvas/canvas-app-bootstrap.js"
  ],
  "clusters": [
    {
      "id": "app-bootstrap-entry",
      "status": "MIGRATED",
      "final_owner": "neutral Canvas app bootstrap",
      "evidence_target": "static/js/workbench/canvas/app-bootstrap.js",
      "evidence": ["WorkbenchCanvasAppBootstrap", "async function start", "URLSearchParams"]
    },
    {
      "id": "canvas-state-persistence",
      "status": "MIGRATED",
      "final_owner": "CanvasRuntime plus Canvas persistence modules",
      "evidence_target": "static/js/workbench/canvas/canvas-session.js",
      "evidence": ["WorkbenchCanvasSession", "async function saveNow", "async function sync", "function handleUpdate"]
    },
    {
      "id": "render-node-media-lifecycle",
      "status": "MIGRATED",
      "final_owner": "UnifiedRenderHost plus registered render modules",
      "evidence_target": "static/js/workbench/canvas/canvas-app-media-editor.js",
      "evidence": ["function render", "function renderNode", "function renderLoopBody"]
    },
    {
      "id": "interaction-and-viewport",
      "status": "MIGRATED",
      "final_owner": "CanvasRuntime plus InteractionController",
      "evidence_target": "static/js/workbench/canvas/canvas-app-interaction.js",
      "evidence": ["function startBoardPan", "function startNodeDrag", "function startNodeResize"]
    },
    {
      "id": "graph-group-mutation",
      "status": "MIGRATED",
      "final_owner": "GraphMutationService and GroupMembershipService adapters",
      "evidence_target": "static/js/workbench/canvas/canvas-app-interaction.js",
      "evidence": ["function createVersionedConnection", "function updateGroupMembership", "function deleteSelectedNodes"]
    },
    {
      "id": "prompt-workflow-ui",
      "status": "MIGRATED",
      "final_owner": "neutral compatibility UI modules",
      "evidence_target": "static/js/workbench/canvas/canvas-app-interaction.js",
      "evidence": ["function openWorkflowTransferModal", "function insertWorkflowIntoCanvas"]
    },
    {
      "id": "media-editing-ui",
      "status": "MIGRATED",
      "final_owner": "MediaTools and neutral media editor module",
      "evidence_target": "static/js/workbench/canvas/media-editor-state.js",
      "evidence": ["presentation", "canvas.applyCrop"],
      "evidence_note": "Page DOM and media mutation remain compatibility-owned while mode rules migrate."
    },
    {
      "id": "classic-compat-host",
      "status": "MIGRATED",
      "final_owner": "bounded compatibility adapter hosted by the neutral Canvas app",
      "evidence_target": "static/js/workbench/canvas/canvas-app-compat-host.js",
      "evidence": ["ensureClassicAssetRuntime", "ensureClassicExecutorRuntime", "ensureClassicCascadeOrchestrator"]
    }
  ]
}
```

## Removal order

1. Move application bootstrap and record-open orchestration behind a neutral,
   small interface; keep existing behavior and rollback query handling.
2. Converge page state, persistence and remote polling on the existing shared
   modules so Classic globals cease to be authority.
3. Move interaction, rendering and graph/group lifecycle to their existing
   shared owners, one characterized behavior at a time.
4. Move prompt/workflow/media editing UI into bounded neutral modules; do not
   create R5+ registries or R8/R9 runtimes.
5. Replace the wide Classic seam host with a bounded compatibility adapter
   driven by the neutral app state.
6. Delete `canvas.js`, prove legacy records on the default path and rollback
   path, then close R4-39. Do not activate R4-40 in the same run.

## Wave 3 evidence (2026-09-08)

`WorkbenchCanvasSession.create(options)` is the single owner of the mutable
record-session cursor, dirty/save scheduling, canonical CAS conflict handling,
remote-version polling and update-message deferral. Its frozen interface is
limited to `open`, `scheduleSave`, `flush`, `sync`, `handleUpdate`,
`adoptRevision`, `close`, and `snapshot`; the page adapter supplies graph
serialization and record projection only. `canvas.js` no longer constructs the
save scheduler or remote-sync coordinator and no longer calls persistence save,
metadata, remote-sync, or update-message primitives directly.

The canonical persistence adapter now advances its revision cursor only after a
successful write. A 409 may report the server revision for diagnostics, but it
does not authorize an unchanged stale payload for automatic retry. The session
keeps that local state dirty and exposes `Save conflict` instead.

## Wave 4 slice 1 evidence (2026-09-08)

The interaction cluster's residual direct window mouse-slot ownership moved to
the existing InteractionController session lifecycle: `llm-pane-resize`,
`box-selection`, `selection-link`, and `knife-drag` sessions now begin through
`ensureInteractionController().begin(...)`, and the three cleanup sites
(`finishSelection`, `endDrag`, the window blur guard) unwire through
`controller.end()`. `canvas.js` no longer assigns `window.onmousemove` or
`window.onmouseup` directly. Render (`render`/`renderNode`/`renderLoopBody`)
and graph/group (`createVersionedConnection`/`updateGroupMembership`/
`createNodeByType`) clusters remain page-owned pending their own slices.

## Wave 4 slice 2 evidence (2026-09-08)

The graph/group cluster's move-driven membership transition moved to its
existing shared owner: `WorkbenchCanvasGroupMembership.resolveMembershipTransition`
now owns geometric containment detection, membership add/remove across the
supplied group records, and the generator-edge handoff from an absorbed child
to its containing group. `canvas.js` `updateGroupMembership` keeps only the
product policy inputs (child/group type pairs, DOM-backed geometry, handoff
eligibility, `canConnect` policy, edge-id factory) and the post-change side
effects (generator syncs, render, save). The inline `handoffGroupConnections`
logic is deleted from the page. A behavior test drives the real module over
add/remove/handoff/veto/promptGroup-suppression/no-op shapes; a wiring
contract pins the delegation and the absence of the inline logic.

## Wave 4 slice 3 evidence (2026-09-08)

`WorkbenchCanvasRenderSweep` delegates mounted-card lifecycle to
`WorkbenchRenderRuntime`: reconciliation retains current node ids, releases
old renderer handles before page builders initialize replacement bodies,
cleans resources after a builder throws, removes nodes absent from a remote
record, and clears the container/session on Canvas close. The page no longer
performs renderer unmounts in individual delete paths. `canConnect` now calls
the shared `WorkbenchLegacyGraphCompatibility.canClassicConnect`; generator
and media-output classifications remain in that compatibility module so
historical edge admission survives removal of provider body code.

Behavior tests cover partial refresh's output fast path separately from the
missing-DOM full-sweep fallback, teardown-before-build, remote removal,
failed-build cleanup, repeated clear, cycle admission and page delegation.
An isolated browser acceptance over the 15-node Classic fixture passed on the
default and all-zero rollback URLs; repeated full and targeted LTX rebuilds
left one active connected editor and produced no console errors.

## Wave 4 slice 4 evidence (2026-09-08)

Selected image/prompt grouping now calls the shared
`WorkbenchCanvasGroupMembership.handoffChildEdgesToGroup` for child-to-
generator edge removal and group-edge reuse. The same module owns the
move-driven handoff from slice 2, so `canvas.js` no longer contains a second
edge-reparenting algorithm. The page retains group creation, selection and
save/render effects only. Behavior coverage proves idempotent removal,
existing group-edge reuse, target filtering and page delegation.

## Wave 4 slice 5 evidence (2026-09-08)

Versioned ordinary port-drop commits now use
`WorkbenchNodeClient.applyConnectionResult` for returned-edge validation,
undo-snapshot retention and canvas-revision adoption. `canvas.js` retains the
compatibility side-effect projection plus save/render effects; the raw commit
is still an explicit rollback adapter. Behavior coverage exercises the real
projection, endpoint rejection, bounded undo retention and revision callback.

## Wave 4 slice 6 evidence (2026-09-08)

Raw and versioned single-node deletion adapters now project node and incident
edge removal through `WorkbenchCanvasGraphFragment.removeGraphRecords`. The
page retains undo, selection, render and save effects only. Behavior coverage
exercises incident-edge removal, nested group expansion and the page's use of
the shared projection across all single-node deletion paths.

## Wave 4 slice 7 evidence (2026-09-08)

Link deletion now uses `WorkbenchCanvasGraphFragment.removeConnection` for the
local edge projection. The page retains undo, generator-input synchronization,
render and save effects only; the shared behavior rejects no-op ids without
mutating the source array.

## Wave 4 slice 8 evidence (2026-09-08)

Output-to-input-group conversion and grouped upload replacement now use
`WorkbenchCanvasGraphFragment.removeGraphRecords` for local replacement
projection. Page-specific downstream edge reattachment, selection, sync,
render and save behavior remains local.

## Wave 4 slice 9 evidence (2026-09-08)

Alt-drag duplication now delegates root/child cloning, id remapping and
optional incoming-edge projection to
`WorkbenchCanvasGraphFragment.duplicateSubgraph`. The page retains insertion
ordering, duplicate-edge suppression and the Classic `canConnect` admission
policy.

## Wave 5 slice 1 evidence (2026-09-08)

Workflow-transfer modal open/close state and selection metadata now live in
`WorkbenchCanvasWorkflowTransferUi`. The page supplies only the current
payload, Canvas-availability check, asset-library close callback and status
sink; import/export transport remains in the existing client.

## Wave 5 slice 2 evidence (2026-09-08)

Classic image-editor math now delegates crop-ratio parsing/fitting, grid
rectangle splitting, resize-scale clamping and circled labels to
`WorkbenchCanvasMediaTools`. The page retains editor DOM state, pointer state
and upload/node mutation behavior.

## Wave 5 slice 3 evidence (2026-09-08)

Prompt-template name/scene localization, positive/full text composition,
search indexing, category filtering and default-name derivation now live in
`WorkbenchCanvasPromptTemplateData`. The page retains library I/O, modal DOM
and prompt-node mutation.

## Wave 5 slice 4 evidence (2026-09-08)

Image-editor resize dimensions now delegate source-size normalization and
scale clamping to `WorkbenchCanvasMediaTools.resizeDimensions`; the page keeps
DOM lookup and editor mutation behavior.

## Wave 5 slice 5 evidence (2026-09-08)

System/remote prompt-template category-label resolution now delegates to
`WorkbenchCanvasPromptTemplateData.categoryLabel`; translations and library
records are supplied by the page adapter.

## Wave 5 slice 8 evidence (2026-09-08)

Image-editor mode normalization and presentation mapping now live in
`WorkbenchCanvasMediaEditorState`; the page retains DOM class toggles, editor
state transitions and media mutations.

## Wave 5 slice 9 evidence (2026-09-08)

Image-editor mode-to-action dispatch now delegates to
`WorkbenchCanvasMediaEditorState.applyAction`; action implementations and
media mutations remain in the compatibility page until their own seams are
migrated.

## Wave 5 slice 10 evidence (2026-09-08)

Image-editor output-node positioning now delegates to
`WorkbenchCanvasMediaTools.outputPoint`; node lookup/creation and graph effects
remain page-owned.

## Wave 5 slice 11 evidence (2026-09-08)

Media output extension extraction, filename sanitization and Group-image
download naming now delegate to `WorkbenchCanvasMediaTools`; the page supplies
only the optional output-name fallback.

## Wave 5 slice 12 evidence (2026-09-08)

Output-image URL filtering and Group-image item projection now delegate to
`WorkbenchCanvasMediaTools.imageOutputUrls` and `groupImageItems`; the page
supplies media-kind and missing-asset policies.

## Wave 5 slice 13 evidence (2026-09-08)

Aspect-ratio crop-boundary geometry now delegates to
`WorkbenchCanvasMediaTools.aspectCropToBounds`; the page retains pointer
handling and crop-state mutation.

## Wave 5 slice 14 evidence (2026-09-08)

Prompt-template modal event routing now lives in
`WorkbenchCanvasPromptTemplateInteraction`; the page supplies state callbacks
for search, library, close, apply, edit, category and selection behavior.
Focused behavior coverage proves normalized query/library input and apply
dispatch without reintroducing page-owned event routing.

## Wave 5 slice 15 evidence (2026-09-08)

Prompt-template node text mutation and modal close now delegate to
`WorkbenchCanvasPromptTemplateApplication`; the page retains lookup and
post-application save/render effects. Focused behavior coverage proves both
successful application and missing-input rejection.

## Wave 5 slice 16 evidence (2026-09-08)

Drawn-alpha mask projection now delegates to
`WorkbenchCanvasMediaTools.maskFromCanvas`; the page retains canvas lookup and
upload/application effects. Focused behavior coverage proves the alpha
threshold and opaque mask output.

## Wave 5 slice 17 evidence (2026-09-08)

Outpaint crop-state minimum-size and position clamping now delegate to
`WorkbenchCanvasMediaTools.clampOutpaintState`; the page retains crop-state
lookup and editor rendering effects. Focused behavior coverage proves bounds
normalization.

## Wave 5 slice 18 evidence (2026-09-08)

Drawn-pixel detection now delegates to `WorkbenchCanvasMediaTools.canvasHasPixels`;
the page retains the optional text-layer check. Focused behavior coverage
proves empty and painted alpha buffers.

## Wave 5 slice 19 evidence (2026-09-08)

Outpaint reset-to-bounds state mutation now delegates to
`WorkbenchCanvasMediaTools.resetOutpaintState`; the page retains crop-bound
lookup and editor rendering. Focused behavior coverage proves deterministic
reset.

## Wave 5 slice 20 evidence (2026-09-08)

Prompt-template modal scroll snapshot and restoration now delegate to
`WorkbenchCanvasPromptTemplateInteraction`; the page retains only the panel
reference and animation-frame adapter. Focused behavior coverage proves nested
scroll positions survive rerender.

## Wave 5 slice 21 evidence (2026-09-08)

Prompt-template open-button active state and ARIA projection now delegate to
`WorkbenchCanvasPromptTemplateInteraction`; the page retains only the DOM
reference and selected node id. Focused behavior coverage proves active and
inactive button states.

## Wave 5 slice 22 evidence (2026-09-08)

Outpaint natural-size projection now delegates to
`WorkbenchCanvasMediaTools.outpaintNaturalSize`; the page retains image and
crop-state lookup. Focused behavior coverage proves CSS-to-natural scaling.

## Wave 5 slice 23 evidence (2026-09-08)

Resized-image Blob generation now delegates to
`WorkbenchCanvasMediaTools.resizedImageBlob`; the page retains editor lookup
and resize-dimension selection. Focused behavior coverage proves target size,
smoothing and Blob output.

## Wave 5 slice 6 evidence (2026-09-08)

Image-editor Grid layout row/column metadata now delegates to
`WorkbenchCanvasMediaTools.gridLayout`; the page supplies only the generated
group id.

## Wave 5 slice 7 evidence (2026-09-08)

Workflow export filename sanitization and timestamp formatting now delegate to
`WorkbenchCanvasWorkflowTransfer.filenameForExport`; the page provides only
the Canvas title and requested extension.

## Wave 5 slice 24 evidence (2026-09-08)

Brush image/draw/text layer composition now delegates to
`WorkbenchCanvasMediaTools.composeBrushCanvas`; the page retains upload and
node mutation effects. Focused behavior coverage proves layer order and output
dimensions.

## Wave 5 slice 25 evidence (2026-09-08)

Crop image Canvas/Blob generation now delegates to
`WorkbenchCanvasMediaTools.cropImageBlob`; the page retains coordinate
conversion, upload and node mutation effects. Focused behavior coverage proves
crop rectangle and PNG Blob output.

## Wave 5 slice 26 evidence (2026-09-08)

Outpaint white-canvas, offset and PNG Blob generation now delegates to
`WorkbenchCanvasMediaTools.outpaintImageBlob`; the page retains bounds
calculation, upload and node mutation effects. Focused behavior coverage proves
canvas sizing, fill and image placement.

## Wave 5 slice 27 evidence (2026-09-08)

Grid-split multi-image Canvas/Blob generation now delegates to
`WorkbenchCanvasMediaTools.splitImageBlobs`; the page retains upload naming
and output-node projection. Focused behavior coverage proves rectangle order,
metadata and Blob output.

## Wave 5 slice 28 evidence (2026-09-08)

PNG Blob encoding now uses the shared `WorkbenchCanvasMediaTools.toPngBlob`
boundary across crop, outpaint, mask, brush and Grid-split paths. Focused
behavior coverage proves the `image/png` MIME contract.

## Wave 5 slice 29 evidence (2026-09-08)

Prompt-template category count aggregation now delegates to
`WorkbenchCanvasPromptTemplateData.categoryCounts`; the page retains category
markup and translation rendering. Focused behavior coverage proves default
category normalization and totals.

## Wave 5 slice 30 evidence (2026-09-08)

Prompt-template selected-item fallback now delegates to
`WorkbenchCanvasPromptTemplateData.selectedId`; the page retains only selection
state assignment. Focused behavior coverage proves retained, missing and empty
selection handling.

## Wave 5 slice 31 evidence (2026-09-08)

Current prompt-node text projection now delegates to
`WorkbenchCanvasPromptTemplateData.nodeText`; the page retains node collection
and selected id state. Focused behavior coverage proves prompt-type filtering
and whitespace trimming.

## Wave 5 slice 32 evidence (2026-09-08)

Prompt-template parameter summary projection now delegates to
`WorkbenchCanvasPromptTemplateData.paramsText`; the page retains preview markup
and escaping. Focused behavior coverage proves ordered multi-parameter and
empty summaries.

## Wave 5 slice 33 evidence (2026-09-08)

Selected prompt-template item resolution now delegates to
`WorkbenchCanvasPromptTemplateData.selectedItem`; the page retains only the
current selection id and item collection. Focused behavior coverage proves
current-id, first-item and empty-list paths.

## Wave 5 slice 34 evidence (2026-09-08)

Prompt-template source labels now delegate to
`WorkbenchCanvasPromptTemplateData.sourceLabel`; the page retains translation
lookup and markup escaping. Focused behavior coverage proves built-in and
user-template labels.

## Wave 5 slice 35 evidence (2026-09-08)

Prompt-template detail source labels now delegate to
`WorkbenchCanvasPromptTemplateData.detailSourceLabel`; the page retains
translation lookup and preview markup. Focused behavior coverage proves
built-in and user-template detail labels.

## Wave 5 slice 38 evidence (2026-09-08)

Prompt-template display scene fallback now delegates to
`WorkbenchCanvasPromptTemplateData.displayScene`; the page retains preview
markup and escaping. Focused behavior coverage proves scene preservation and
positive-text fallback.

## Wave 5 slice 36 evidence (2026-09-08)

Display-to-natural crop rectangle conversion now delegates to
`WorkbenchCanvasMediaTools.cropRectFromDisplay`; the page retains image and
crop-state lookup. Focused behavior coverage proves scale, rounding and
minimum dimensions.

## Wave 5 slice 37 evidence (2026-09-08)

Display-to-natural outpaint rectangle conversion now delegates to
`WorkbenchCanvasMediaTools.outpaintRectFromDisplay`; the page retains image and
crop-state lookup. Focused behavior coverage proves offset scaling and minimum
natural dimensions.

## Wave 5 slice 39 evidence (2026-09-08)

Prompt-template negative text normalization now delegates to
`WorkbenchCanvasPromptTemplateData.negativeText`; the page retains preview
markup and escaping. Focused behavior coverage proves whitespace trimming and
empty suppression.

## Wave 5 slice 41 evidence (2026-09-08)

Media output base-name parsing now delegates to
`WorkbenchCanvasMediaTools.baseNameWithoutExtension`; the page retains suffix
selection and upload effects. Focused behavior coverage proves extension
removal and fallback naming.

## Wave 5 slice 40 evidence (2026-09-08)

Prompt-template positive text normalization now delegates to
`WorkbenchCanvasPromptTemplateData.positiveText`; the page retains preview
markup and escaping. Focused behavior coverage proves whitespace trimming and
empty suppression.

## Wave 5 slice 42 evidence (2026-09-08)

Media output suffix and extension composition now delegates to
`WorkbenchCanvasMediaTools.outputFileName`; the page retains operation-specific
suffixes. Focused behavior coverage proves crop and custom-extension naming.

## Wave 5 slice 43 evidence (2026-09-08)

Grid-split output filenames now reuse `WorkbenchCanvasMediaTools.outputFileName`;
the page retains only row/column suffix selection. Existing behavior coverage
and the full verification gate remain passing.

## Wave 5 slice 45 evidence (2026-09-08)

Node run-status label projection now delegates to
`WorkbenchCanvasNodePresentation.statusLabel`; the page retains status markup
and visibility policy. Focused behavior coverage proves known and unknown
status handling.

## Wave 5 slice 49 evidence (2026-09-08)

Node CSS class projection now delegates to
`WorkbenchCanvasNodePresentation.className`; the page retains DOM creation and
attribute assignment. Focused behavior coverage proves type, media, size and
selection class composition.

## Wave 5 slice 50 evidence (2026-09-08)

Media-kind title mapping now delegates to
`WorkbenchCanvasNodePresentation.mediaTitle`; the page retains media-kind
resolution. Focused behavior coverage proves video, audio and image fallback
labels.

## Wave 5 slice 57 evidence (2026-09-08)

Prompt-template empty-list placeholder HTML now delegates to
`WorkbenchCanvasPromptTemplateData.emptyState`; the page retains list container
and event wiring. Focused behavior coverage proves escaping and empty-state
markup.

## Wave 5 slice 51 evidence (2026-09-08)

Default node-size mapping now delegates to
`WorkbenchCanvasNodePresentation.defaultSize`; the page retains DOM sizing
application. Focused behavior coverage proves image, LLM and unknown-type
sizes.

## Wave 5 slice 53 evidence (2026-09-08)

Prompt-template detail preview data now delegates to
`WorkbenchCanvasPromptTemplateData.preview`; the page retains markup and
escaping. Focused behavior coverage proves normalized positive, negative and
parameter fields.

## Wave 5 slice 54 evidence (2026-09-08)

Node dimension projection now delegates to
`WorkbenchCanvasNodePresentation.dimensions`; the page retains DOM style
application. Focused behavior coverage proves explicit-size and default-size
paths.

## Wave 5 slice 55 evidence (2026-09-08)

Node position projection now delegates to
`WorkbenchCanvasNodePresentation.position`; the page retains DOM style
application. Focused behavior coverage proves numeric coordinates and zero
fallback.

## Wave 5 slice 52 evidence (2026-09-08)

Fixed node-size policy now delegates to
`WorkbenchCanvasNodePresentation.isFixedSize`; the page retains DOM style
application. Focused behavior coverage proves explicit and default fixed-height
paths.

## Wave 5 slice 48 evidence (2026-09-08)

Media-node title override now delegates to
`WorkbenchCanvasNodePresentation.displayTitle`; the page retains media-title
lookup and title markup. Focused behavior coverage proves media, non-media and
missing-URL paths.

## Wave 5 slice 47 evidence (2026-09-08)

Node run-status badge HTML now delegates to
`WorkbenchCanvasNodePresentation.statusMarkup`; the page retains only the
insertion point. Focused behavior coverage proves escaping, status class and
cascade suffix.

## Wave 5 slice 46 evidence (2026-09-08)

Node run-status badge visibility now delegates to
`WorkbenchCanvasNodePresentation.shouldShowStatus`; the page retains status
markup. Focused behavior coverage proves normal, failed and cascade-failed
states.

## Wave 5 slice 56 evidence (2026-09-08)

Prompt-template list-card HTML now delegates to
`WorkbenchCanvasPromptTemplateData.itemCard`; the page retains the list
container and event wiring. Focused behavior coverage proves selection class,
escaping, source and category labels.

## Wave 5 slice 58 evidence (2026-09-08)

Prompt-template category navigation, list cards, detail preview, edit fields,
and action markup now render through
`WorkbenchCanvasPromptTemplateRenderer`; `canvas.js` retains state and event
effects only. Focused behavior coverage proves category selection, escaping,
selected-card/detail output, and apply actions. Full verification: PASS (428
tests, 78 Python AST files, 94 JavaScript files, 4 architecture guards, clean
diff check).

## Wave 5 slice 59 evidence (2026-09-08)

Prompt-template renderer detail output now accepts the shared normalized text
projections for positive, negative and parameter fields. This preserves the
existing display contract while keeping markup ownership outside `canvas.js`.
Focused coverage proves trimmed detail values. Full verification: PASS (428
tests, 78 Python AST files, 94 JavaScript files, 4 architecture guards, clean
diff check).

## Wave 5 slice 60 evidence (2026-09-08)

Image-editor text overlay records and geometry now delegate to
`WorkbenchCanvasMediaTextOverlay`; `canvas.js` retains Canvas rendering and
mutation effects. Focused coverage proves creation normalization, measurement,
and hit testing. Full verification: PASS (429 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 slice 61 evidence (2026-09-08)

Custom grid-line hit testing and position normalization now delegate to
`WorkbenchCanvasMediaTools`; pointer capture and preview effects remain page
owned. Focused coverage proves nearest-line selection and clamped movement.
Full verification: PASS (430 tests, 78 Python AST files, 95 JavaScript files,
4 architecture guards, clean diff check).

## Wave 5 slice 62 evidence (2026-09-08)

Regular grid row, column and gap settings now normalize through
`WorkbenchCanvasMediaTools`; page code retains DOM reads and label updates.
Focused coverage proves bounded and invalid-value behavior. Full verification:
PASS (431 tests, 78 Python AST files, 95 JavaScript files, 4 architecture
guards, clean diff check).

## Wave 5 media-drawing cluster evidence (2026-09-08)

Brush, mask and number-label style rules now delegate to
`WorkbenchCanvasMediaTools`; Canvas drawing operations remain page-owned.
Focused coverage proves normal/mask styles and label typography. Full
verification: PASS (432 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 crop-geometry cluster evidence (2026-09-08)

Outpaint growth and free-crop resize geometry now delegate to
`WorkbenchCanvasMediaTools`; page code retains state mutation and clamping.
Focused coverage proves centered expansion and minimum-size free resizing. Full
verification: PASS (433 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 aspect-crop geometry cluster evidence (2026-09-08)

Fixed-ratio edge and corner resize geometry now delegates to
`WorkbenchCanvasMediaTools`; page code retains crop-state application and
rendering. Focused coverage proves edge limits and corner anchor behavior. Full
verification: PASS (434 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 custom-grid geometry cluster evidence (2026-09-08)

Custom grid line classification, deduplication, sorting and gap-aware rectangle
generation now delegate to `WorkbenchCanvasMediaTools`; DOM reads and preview
effects remain page-owned. Focused coverage proves duplicate-line collapse and
row/column output. Full verification: PASS (435 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 workflow-transfer cluster evidence (2026-09-08)

Selected workflow export envelope construction now delegates to
`WorkbenchCanvasWorkflowTransfer`; page code retains subgraph selection and
serialization callbacks. Focused coverage proves format/version/timestamp and
safe defaults. Full verification: PASS (436 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 crop-state geometry cluster evidence (2026-09-08)

Crop initialization and ordinary crop-boundary clamping now delegate to
`WorkbenchCanvasMediaTools`; outpaint branching and redraw effects remain page
owned. Focused coverage proves inset initialization and boundary/min-size
clamping. Full verification: PASS (437 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 editor-zoom geometry cluster evidence (2026-09-08)

Crop rectangle scaling during image-editor zoom now delegates to
`WorkbenchCanvasMediaTools`; DOM resizing, clamping and preview effects remain
page-owned. Focused coverage proves positive scaling and invalid-scale fallback.
Full verification: PASS (438 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 editor-pointer cluster evidence (2026-09-08)

Client-to-Canvas pointer coordinate projection now delegates to
`WorkbenchCanvasMediaTools`; pointer event handling remains page-owned. Focused
coverage proves scaled coordinates. Full verification: PASS (439 tests, 78
Python AST files, 95 JavaScript files, 4 architecture guards, clean diff
check).

## Wave 5 resize-control cluster evidence (2026-09-08)

Resize control projection now returns normalized scale, target dimensions and
display text from `WorkbenchCanvasMediaTools`; DOM synchronization remains page-
owned. Focused coverage proves dimensions and formatted label. Full
verification: PASS (440 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 media-action dispatch cluster evidence (2026-09-08)

Image-editor mode-to-action dispatch now delegates to
`WorkbenchCanvasMediaEditorState`; concrete callbacks remain page-owned.
Focused coverage proves known and normalized fallback modes. Full verification:
PASS (441 tests, 78 Python AST files, 95 JavaScript files, 4 architecture
guards, clean diff check).

## Wave 5 workflow-import normalization cluster evidence (2026-09-08)

Legacy array, direct object and nested workflow import shapes now normalize
through `WorkbenchCanvasWorkflowTransfer`, removing empty records at the
boundary. Focused coverage proves all supported shapes. Full verification:
PASS (442 tests, 78 Python AST files, 95 JavaScript files, 4 architecture
guards, clean diff check).

## Wave 5 crop-handle interaction cluster evidence (2026-09-08)

Crop box edge/corner hit classification now delegates to
`WorkbenchCanvasMediaTools`; explicit handles and drag initiation remain page-
owned. Focused coverage proves corner, edge and interior mapping. Full
verification: PASS (443 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 crop-pointer delta cluster evidence (2026-09-08)

Crop drag client-coordinate delta calculation now delegates to
`WorkbenchCanvasMediaTools`; mode-specific state application and redraw remain
page-owned. Focused coverage proves signed x/y deltas. Full verification: PASS
(444 tests, 78 Python AST files, 95 JavaScript files, 4 architecture guards,
clean diff check).

## Wave 5 crop-drag snapshot cluster evidence (2026-09-08)

Crop drag mode, pointer origin and immutable crop snapshot creation now delegate
to `WorkbenchCanvasMediaTools`; event guards and lifecycle state remain page-
owned. Focused coverage proves normalized mode and copied geometry. Full
verification: PASS (445 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 workflow-export normalization cluster evidence (2026-09-08)

Exported workflow envelopes now remove empty nodes and connections at the
`WorkbenchCanvasWorkflowTransfer` boundary, matching import normalization.
Focused coverage proves safe filtering. Full verification: PASS (445 tests, 78
Python AST files, 95 JavaScript files, 4 architecture guards, clean diff
check).

## Wave 5 media-output download cluster evidence (2026-09-08)

Downloadable output URL filtering now delegates to
`WorkbenchCanvasMediaTools`; download invocation and missing-asset policy
remain page-owned. Focused coverage proves output/asset acceptance and remote
exclusion. Full verification: PASS (446 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 output-metadata cluster evidence (2026-09-08)

Output resolution and run-duration metadata normalization now delegates to
`WorkbenchCanvasMediaTools`; localized formatting and DOM insertion remain
page-owned. Focused coverage proves fallback resolution and non-positive
duration handling. Full verification: PASS (447 tests, 78 Python AST files, 95
JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 output-download naming cluster evidence (2026-09-08)

Output download extension parsing and timestamped filename generation now
delegate to `WorkbenchCanvasMediaTools`; actual download invocation remains
page-owned. Focused coverage proves query stripping and PNG fallback. Full
verification: PASS (448 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 run-duration formatting cluster evidence (2026-09-08)

Seconds/minutes duration formatting now delegates to
`WorkbenchCanvasMediaTools`; metadata markup insertion remains page-owned.
Focused coverage proves zero, sub-minute and minute-plus output. Full
verification: PASS (449 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-data projection cluster evidence (2026-09-08)

Output URL extraction and URL-to-metadata lookup now delegate to
`WorkbenchCanvasMediaTools`; output lightbox and download effects remain page-
owned. Focused coverage proves string/object records and missing metadata. Full
verification: PASS (450 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-name projection cluster evidence (2026-09-08)

Output filename extraction and URL decoding now delegate to
`WorkbenchCanvasMediaTools`; card rendering and download effects remain page-
owned. Focused coverage proves query stripping, decoding and fallback. Full
verification: PASS (451 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-grid validation cluster evidence (2026-09-08)

Grid split output-layout validation now delegates to
`WorkbenchCanvasMediaTools`; pending-run gating and rendering remain page-owned.
Focused coverage proves matching, mismatched and empty layouts. Full
verification: PASS (452 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-grid placement cluster evidence (2026-09-08)

Grid item row, column and aspect-ratio placement normalization now delegates to
`WorkbenchCanvasMediaTools`; HTML insertion remains page-owned. Focused coverage
proves lower-bound clamping and empty placement. Full verification: PASS (453
tests, 78 Python AST files, 95 JavaScript files, 4 architecture guards, clean
diff check).

## Wave 5 output-presentation cluster evidence (2026-09-08)

Output URL, media kind, display name, run duration and optional grid placement
now project through `WorkbenchCanvasMediaTools`; type-specific HTML and effects
remain page-owned. Focused coverage proves combined presentation output. Full
verification: PASS (454 tests, 78 Python AST files, 95 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-media renderer cluster evidence (2026-09-08)

Type-specific output card HTML for missing, video, audio, file and image items
now delegates to `WorkbenchCanvasMediaOutputRenderer`; preview, missing-asset and
localization callbacks remain page-owned. Focused coverage proves audio card
markup and duration pill. Full verification: PASS (455 tests, 78 Python AST
files, 96 JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 output-append lifecycle cluster evidence (2026-09-08)

Output record append, metadata normalization, grid-layout replacement and
comparison indexing now delegate to `WorkbenchCanvasMediaTools`; node mutation
and persistence effects remain page-owned. Focused coverage proves grid
replacement and comparison metadata. Full verification: PASS (456 tests, 78
Python AST files, 96 JavaScript files, 4 architecture guards, clean diff
check).

## Wave 5 output-viewed lifecycle cluster evidence (2026-09-08)

Immutable output viewed-state updates now delegate to
`WorkbenchCanvasMediaTools`; render/save effects remain page-owned and only run
on change. Focused coverage proves changed and already-viewed paths. Full
verification: PASS (457 tests, 78 Python AST files, 96 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 output-compare lifecycle cluster evidence (2026-09-08)

Comparison URL resolution now delegates to `WorkbenchCanvasMediaTools`, with
explicit string/object mappings and run-reference fallback centralized. Lightbox
and compare effects remain page-owned. Focused coverage proves all three paths.
Full verification: PASS (458 tests, 78 Python AST files, 96 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 lightbox-source cluster evidence (2026-09-08)

Lightbox item collection and source priority now delegate to
`WorkbenchCanvasMediaTools`; navigation and rendering effects remain page-owned.
Focused coverage proves current-source, output-node and log fallback paths. Full
verification: PASS (459 tests, 78 Python AST files, 96 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 lightbox-navigation cluster evidence (2026-09-08)

Current item lookup and cyclic direction navigation now delegate to
`WorkbenchCanvasMediaTools`; target-node lookup and lightbox rendering remain
page-owned. Focused coverage proves forward, backward, wrap and empty paths.
Full verification: PASS (460 tests, 78 Python AST files, 96 JavaScript files, 4
architecture guards, clean diff check).

## Wave 5 group-lightbox index cluster evidence (2026-09-08)

Group lightbox index clamping now delegates to `WorkbenchCanvasMediaTools`; group
lookup and lightbox opening remain page-owned. Focused coverage proves lower,
upper and empty-list bounds. Full verification: PASS (461 tests, 78 Python AST
files, 96 JavaScript files, 4 architecture guards, clean diff check).

## Wave 5 lightbox index projection cluster evidence (2026-09-08)

Group lightbox index normalization now uses the shared list-index boundary;
focused coverage proves lower, upper and empty-list handling. Full verification:
PASS (461 tests, 78 Python AST files, 96 JavaScript files, 4 architecture
guards, clean diff check).

## Wave 5 lightbox visibility cluster evidence (2026-09-08)

Image vs video lightbox visibility projection now delegates to
`WorkbenchCanvasMediaTools`; DOM display updates and resource loading remain
page-owned. Focused coverage proves video/image compare visibility. Full
verification: PASS (462 tests, 78 Python AST files, 96 JavaScript files, 4
architecture guards, clean diff check).

Wave 5 crop-box projection cluster evidence (2026-09-08): `cropBoxProjection`
is now neutralized in `WorkbenchCanvasMediaTools`; the page adapter only applies
the returned DOM projection for crop/outpaint modes. Focused tests cover both
branches; full verification passed at 463 tests, 78 Python AST files, 96
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 media-editor mode projection evidence (2026-09-08): normalized mode
flags, apply visibility, labels, and cleanup signals now come from
`WorkbenchCanvasMediaEditorState.uiProjection`; the page retains DOM and media
effects. Focused tests cover preview, grid, and outpaint; full verification
passed at 464 tests, 78 Python AST files, 96 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 media-editor zoom/overflow projection evidence (2026-09-08): scaled
editor dimensions, zoom label, and stage overflow flags now delegate to
`WorkbenchCanvasMediaTools`; the page retains DOM updates and crop-state
synchronization. Focused tests cover scaled and overflow/non-overflow cases;
full verification passed at 465 tests, 78 Python AST files, 96 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 brush-tool projection evidence (2026-09-08): tool normalization and
text-mode eligibility now delegate to
`WorkbenchCanvasMediaEditorState.brushToolProjection`; the page retains
inline-editor cleanup and DOM class updates. Focused tests cover valid,
fallback, and non-brush text cases; full verification passed at 466 tests, 78
Python AST files, 96 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 MiniMax segment-compaction projection evidence (2026-09-08): timeline
sorting, minimum duration normalization, total duration, and playhead clamping
now delegate to `WorkbenchCanvasMediaTools.minimaxCompactSegments`; the page
retains node mutation. Focused tests cover ordering, minimum duration, and
upper-bound clamping; full verification passed at 491 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax reference projection evidence (2026-09-08): aspect parsing,
reference normalization, deduplication, and image/video/audio summary
formatting now delegate to `WorkbenchCanvasMediaTools`; the page retains source
collection. Focused tests cover aspect fallback, duplicate removal, and summary
counts; full verification passed at 490 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax playhead projection evidence (2026-09-08): time clamping,
timeline percentage, and duration-label formatting now delegate to
`WorkbenchCanvasMediaTools.minimaxPlayheadProjection`; the page retains DOM
updates and selected-segment effects. Focused tests cover fractional,
upper-bound, and zero-duration cases; full verification passed at 489 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check.

Wave 5 RunningHub legacy request-path batch evidence (2026-09-09): the
remaining image-only workflow request path now reuses the neutral media
input-state projection for required/optional classification; the page retains
error text and pruning side effects. Full verification remained green at 523
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 RunningHub current-entry batch evidence (2026-09-09): current entry
extraction and model/workflow/app mode fallback now delegate to the neutral
renderer; the page retains selected-reference lookup. Focused tests cover entry
and mode fallback; full verification passed at 540 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub workflow-source batch evidence (2026-09-09): workflow entry
field extraction, saved-config detection, and first-nonempty workflow source
selection now delegate to the neutral renderer. Focused tests cover
field/config/source fallback rules; full verification passed at 539 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 residual ownership sweep (2026-09-09): remaining RunningHub/Loop page
functions are limited to provider reads, node-state writes, UI/HTML composition,
and executor side effects; no additional pure projection remains safe to move
without crossing the current compatibility boundary. Full verification remains
green at 540 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

Residual RunningHub/Loop page-owned behavior evidence (2026-09-09): the focused
frontend workbench module suite passes all 127 tests, including RunningHub
controls seam wiring, classic compatibility boundaries, and Loop runtime
integration. No new ownership removal is justified by this suite.

Wave 5 RunningHub visible-entry batch evidence (2026-09-09): provider entry
filtering for disabled and hidden items now delegates to the neutral renderer;
the page retains provider access. Focused tests cover visible-entry filtering;
full verification passed at 538 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub entry-reference batch evidence (2026-09-09): current entry
resolution by configuration key, workflow ID, and app ID fallback now delegates
to the neutral renderer; the page retains node-state reads. Focused tests cover
key and ID fallback resolution; full verification passed at 537 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub entry-collection batch evidence (2026-09-09): model/app/
workflow entry aggregation and normalized identity projection now delegate to
the neutral renderer; the page retains provider reads. Focused tests cover
cross-kind ordering and ID filtering; full verification passed at 536 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 RunningHub entry-identity batch evidence (2026-09-09): workflow/app/
model ID extraction, display-label fallback, configuration-key creation, and
key parsing now delegate to the neutral renderer. Focused tests cover identity
and label fallbacks; full verification passed at 535 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub workflow-field-list batch evidence (2026-09-09): workflow
input enumeration and image/video/audio/number/boolean/text type inference now
delegate to the neutral renderer; the page retains link-recognition
compatibility wiring. Focused tests cover link exclusion and type inference;
full verification passed at 534 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub source-summary batch evidence (2026-09-09): reference
filtering, image/video/audio grouping, image-limit enforcement, and prompt
aggregation now delegate to the neutral renderer; the page retains source
ordering. Focused tests cover grouping, limiting, and prompt joining; full
verification passed at 533 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 Loop token-insertion batch evidence (2026-09-09): token chip creation,
selection replacement, and fallback append behavior now delegate to the neutral
Loop prompt renderer; the page supplies DOM and selection handles. Focused tests
cover fallback insertion; full verification passed at 532 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub random-state batch evidence (2026-09-09): random state read
semantics now delegate to the neutral renderer; the page retains state
initialization, writes, and refresh side effects. Focused tests cover default,
disabled, and enabled states; full verification passed at 531 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub random-eligibility batch evidence (2026-09-09): numeric
random-field eligibility now delegates to the neutral renderer; the page
retains random-state toggling and generated-value persistence. Focused tests
cover numeric/type and flag gating; full verification passed at 530 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 Loop prompt-counter batch evidence (2026-09-09): prompt length and
counter-markup projection now delegate to the neutral Loop prompt renderer; the
page retains DOM counter updates. Focused tests cover Unicode length and
over-limit markup; full verification passed at 529 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub option-extraction batch evidence (2026-09-09): field option
extraction from primitive lists, labeled objects, typed values, and known-field
fallbacks now delegates to the neutral renderer. Focused tests cover object and
fallback extraction; full verification passed at 528 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field-metadata batch evidence (2026-09-09): parameter-key
construction, field-kind detection, field-role detection, and default-value
normalization now delegate to the neutral renderer; the page retains
compatibility wrappers. Focused tests cover media type, prompt role, and
array-default handling; full verification passed at 527 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field-catalog batch evidence (2026-09-09): enabled-field
fallback filtering and deterministic image-first field sorting now delegate to
neutral renderer helpers; the page retains source selection. Focused tests cover
enabled fallback and image-order sorting; full verification passed at 526 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check.

Wave 5 RunningHub workflow-support batch evidence (2026-09-09): field error
labels and workflow-link recognition now delegate to neutral renderer helpers
used by validation and pruning. Focused tests cover label fallbacks and strict
link recognition; full verification passed at 525 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub workflow-pruning batch evidence (2026-09-09): missing-field
deletion, empty-node removal, and dangling-link cleanup now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.pruneWorkflowForMissingFields`; the
page supplies only workflow-node/link recognition callbacks. Focused tests cover
node and link pruning; full verification passed at 524 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field-value ownership batch evidence (2026-09-09): page-side
field value lookup now delegates media, prompt, default, and disabled-upstream
precedence to `WorkbenchCanvasRunningHubFieldRenderer.fieldValue`; random-value
generation remains page-owned. Focused tests cover manual media precedence; full
verification passed at 522 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 RunningHub media-index batch evidence (2026-09-09): ordered image,
video, and audio field indexing now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.mediaIndexes`; the page retains only
the compatibility wrapper. Focused tests cover image-order sorting and
per-kind counters; full verification passed at 523 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax pane-size projection evidence (2026-09-08): library, preview,
video-track, and reference-lane clamp rules now delegate to
`WorkbenchCanvasMediaTools.minimaxPaneProjection`; the page retains pointer
events, node mutation, and CSS variable effects. Focused tests cover lower and
upper bounds; full verification passed at 488 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax media-card rendering evidence (2026-09-08): image/video/audio/
file thumbnail type branches and labels now delegate to
`WorkbenchCanvasMediaOutputRenderer.renderLite`; the page retains media-kind
and preview callbacks. Focused tests cover video lite-card markup; full
verification passed at 487 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 loop-input prompt-selection projection evidence (2026-09-08):
current-round selection, start-index normalization, cycling, and empty fallback
now delegate to `WorkbenchCanvasLoopInputProjection.select`; the page retains
prompt source collection. Focused tests cover sequential, cyclic, and empty
selection; full verification passed at 486 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 loop-count and prompt-splitting projection evidence (2026-09-08): count
bounds and numbered/line-based prompt splitting now delegate to
`WorkbenchCanvasLoopPromptRenderer`; the page retains graph traversal and
source collection. Focused tests cover lower/upper bounds, numbered items, and
single-item fallback; full verification passed at 485 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 loop-layout projection evidence (2026-09-08): opening/closing
dimensions and prompt/media panel height rules now delegate to
`WorkbenchCanvasLoopLayoutProjection`; the page retains node mutation and
rerender effects. Focused tests cover open, closed, combined-panel, and
empty-panel sizes; full verification passed at 484 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub media-input-state batch evidence (2026-09-09): required,
optional, and present media classification now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.mediaInputState`; the page retains
localized required-error text and optional workflow pruning side effects.
Focused tests cover all three paths; full verification passed at 521 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check.

Wave 5 loop-token label projection evidence (2026-09-08): localized token-label
fallback mapping now delegates to `WorkbenchCanvasLoopPromptRenderer.tokenLabel`;
the page retains translation lookup only. Focused tests cover localized and
unknown-token fallback behavior; full verification passed at 483 tests, 78
Python AST files, 102 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 loop-editor token markup evidence (2026-09-08): token-chip and
variable-text markup, escaping, labels, and deletion affordances now delegate
to `WorkbenchCanvasLoopPromptRenderer`; the page retains editor DOM behavior.
Focused tests cover chip and variable composition; full verification passed at
482 tests, 78 Python AST files, 102 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 5 loop-input batching projection evidence (2026-09-08): image/video batch
size, start-index, current-round slicing, and filtering now delegate to
`WorkbenchCanvasLoopInputProjection.batch`; the page retains source
collection. Focused tests cover current-round slicing and fallback batch
normalization; full verification passed at 481 tests, 78 Python AST files, 102
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 loop-prompt projection evidence (2026-09-08): counter/total/progress
token replacement, selected-input precedence, and hidden-state fallback now
delegate to `WorkbenchCanvasLoopPromptRenderer`; the page retains loop input
collection. Focused tests cover translated tokens and hidden prompts; full
verification passed at 480 tests, 78 Python AST files, 101 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 Comfy field rendering evidence (2026-09-08): boolean, slider, dropdown,
textarea, random-number, and scalar parameter markup now delegate to
`WorkbenchCanvasComfyFieldRenderer`; the page retains value resolution,
random-state policy, and event binding. Focused tests cover boolean and
dropdown rendering; full verification passed at 479 tests, 78 Python AST
files, 100 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub prompt-field rendering evidence (2026-09-08): prompt
textarea markup and escaping now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.promptMarkup`; the page retains field
resolution and control binding. Focused tests cover escaped labels and values;
full verification passed at 478 tests, 78 Python AST files, 99 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field rendering evidence (2026-09-08): boolean, slider,
select, random-number, and scalar parameter markup now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains field value
resolution, control binding, and validation. Focused tests cover boolean and
select rendering; full verification passed at 477 tests, 78 Python AST files,
99 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 LLM-pane rendering evidence (2026-09-08): LLM input/output and chat
panel markup, escaping, empty state, and running labels now delegate to
`WorkbenchCanvasLlmPaneRenderer`; the page retains input, run, copy, retry, and
cascade event wiring. Focused tests cover escaped panel values and chat empty
state; full verification passed at 476 tests, 78 Python AST files, 98
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 Comfy media-input rendering evidence (2026-09-08): Comfy grouped media
inputs now reuse `WorkbenchCanvasMediaInputRenderer` for empty-state, ordered
markup, preview, audio, video, and missing-item branches; the page retains kind
selection and drag/reorder effects. Focused coverage proves shared renderer
wiring; full verification passed at 475 tests, 78 Python AST files, 97
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub media-input rendering evidence (2026-09-08): grouped
RunningHub media inputs now reuse `WorkbenchCanvasMediaInputRenderer`; the page
retains media-kind selection, preview callbacks, and list binding. Focused
coverage proves the shared renderer path and removal of duplicate inline markup;
full verification passed at 474 tests, 78 Python AST files, 97 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 media-input list rendering evidence (2026-09-08): empty-state and
ordered item markup, escaping, and preview/missing projections now delegate to
`WorkbenchCanvasMediaInputRenderer`; the page retains DOM event wiring and
reorder callbacks. Focused tests cover empty, escaped, preview, and missing-item
markup; full verification passed at 473 tests, 78 Python AST files, 97
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 prompt-preview rendering evidence (2026-09-08): prompt preview list
markup and escaping now delegate to
`WorkbenchCanvasPromptTemplateRenderer.renderPreviewInputs`; the page retains
container binding. Focused tests cover empty-state, escaped labels, and
null-item handling; full verification passed at 472 tests, 78 Python AST
files, 96 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 output-preview zoom/pan projection evidence (2026-09-08): wheel zoom
anchoring, bounds, reset, and drag translation now delegate to
`WorkbenchCanvasMediaTools.previewZoomProjection` and
`previewPanProjection`; the page retains event wiring and DOM application.
Focused tests cover zoom-in, reset, and pan translation; full verification
passed at 471 tests, 78 Python AST files, 96 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 output-compare slider projection evidence (2026-09-08): clamped
position and clip-path formatting now delegate to
`WorkbenchCanvasMediaTools.compareSliderProjection`; the page retains DOM style
application. Focused tests cover centered, lower-bound, and zero-width cases;
full verification passed at 470 tests, 78 Python AST files, 96 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 output-preview transform projection evidence (2026-09-08): preview
transform formatting and zoomed-state thresholding now delegate to
`WorkbenchCanvasMediaTools.previewTransformProjection`; the page retains DOM
transform application. Focused tests cover translated, scaled, and default
states; full verification passed at 469 tests, 78 Python AST files, 96
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 brush-control projection evidence (2026-09-08): brush/mask size,
color, and alpha normalization now delegate to
`WorkbenchCanvasMediaTools.brushControlProjection`; the page retains DOM reads
and Canvas drawing effects. Focused tests cover brush, mask, and fallback
controls; full verification passed at 468 tests, 78 Python AST files, 96
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 editor-canvas sizing projection evidence (2026-09-08): natural/client
dimension fallback and CSS sizing for draw/text layers now delegate to
`WorkbenchCanvasMediaTools.editorCanvasProjection`; the page retains canvas
mutation and redraw effects. Focused tests cover natural-size and fallback
cases; full verification passed at 467 tests, 78 Python AST files, 96
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax active-segment projection evidence (2026-09-08): playhead hit
selection and selected-segment fallback now delegate to
`WorkbenchCanvasMediaTools.minimaxActiveSegment`; the page retains node
initialization and playback effects. Focused tests cover time-hit,
selected-id fallback, and empty segments; full verification passed at 492
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 MiniMax segment-reference projection evidence (2026-09-08): segment
local-reference precedence, upstream fallback, deduplication, capping, and
media-kind filtering now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentRefs` and
`minimaxSegmentRefsByKind`; the page retains node-specific source lookup.
Focused tests cover local, fallback, and kind-filter paths; full verification
passed at 493 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 MiniMax segment-result projection evidence (2026-09-08): result
normalization and unique-prepend behavior now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentResult` and
`minimaxPrependUnique`; the page retains node/segment persistence and
timestamps. Focused tests cover string/object normalization and duplicate
suppression; full verification passed at 494 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax source aggregation projection evidence (2026-09-08): ordered
source-to-prompt and source-to-reference projection now delegates to
`WorkbenchCanvasMediaTools.minimaxSourceProjection`; the page retains
node-specific source resolution. Focused tests cover prompt joining,
empty-source filtering, and reference collection; full verification passed at
495 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 5 MiniMax segment-timing projection evidence (2026-09-08): start/duration
clamping, sequential start enforcement, and trim boundary normalization now
delegate to `WorkbenchCanvasMediaTools.minimaxSegmentTiming`; the page
retains segment object mutation and other field normalization. Focused tests
cover default, clamped, and sequential timing cases; full verification passed
at 496 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 5 MiniMax segment-visual projection evidence (2026-09-08): aspect-ratio
and megapixel fallback/normalization now delegate to
`WorkbenchCanvasMediaTools.minimaxSegmentVisuals`; the page retains segment
field writes. Focused tests cover normalized explicit values and node-level
fallbacks; full verification passed at 497 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax reference-migration projection evidence (2026-09-08): legacy
array/refItems/type-bucket merging, normalization, deduplication, and capacity
limiting now delegate to
`WorkbenchCanvasMediaTools.minimaxReferenceMigration`; the page retains
segment mutation. Focused tests preserve legacy merge order and cap behavior;
full verification passed at 498 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax output-collection projection evidence (2026-09-08): current-
result type completion and valid-URL filtering for segment results/materials
now delegate to `WorkbenchCanvasMediaTools.minimaxOutputProjection`; the
page retains collection assignment. Focused tests cover current-result
normalization and invalid-item filtering; full verification passed at 499
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 MiniMax node-config projection evidence (2026-09-08): workflow,
RunningHub workflow, payment mode, aspect-ratio, and megapixel default
normalization now delegate to
`WorkbenchCanvasMediaTools.minimaxNodeConfig`; the page retains engine
resolution and field writes. Focused tests cover defaults and explicit
overrides; full verification passed at 500 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax segment-list projection evidence (2026-09-08): empty list
initialization, default segment timing fields, and missing-ID generation now
delegate to `WorkbenchCanvasMediaTools.minimaxSegmentList`; the page retains
per-segment business-field normalization. Focused tests cover generated
defaults and existing-list preservation; full verification passed at 501
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 MiniMax selection-duration projection evidence (2026-09-08): selected-
segment fallback and timeline duration aggregation now delegate to
`WorkbenchCanvasMediaTools.minimaxSelectionProjection`; the page retains
node state assignment. Focused tests cover valid selection, missing-selection
fallback, and duration floor behavior; full verification passed at 502 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check.

Wave 5 Loop upstream-prompt projection evidence (2026-09-08): prompt,
promptGroup, loop, and LLM upstream text collection with trimming and cycle
protection now delegate to
`WorkbenchCanvasLoopInputProjection.promptItems`; the page retains context
and render callbacks. Focused tests cover all upstream source types; full
verification passed at 503 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check.

Wave 5 media-input and page field-value evidence (2026-09-09): required/
optional RunningHub media presence and page-side field-value precedence now
delegate to `WorkbenchCanvasRunningHubFieldRenderer`; focused behavior coverage
passes for required/optional/present media and disabled-upstream precedence.
Full verification passed at 544 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 Comfy field-projection evidence (2026-09-09): field-kind
classification, workflow field filtering, parameter/default precedence, random
enablement/active state, and bounded random-value policy now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains node mutation, event
handling, and side effects. Focused behavior coverage passes; full verification
passed at 545 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 LLM pane-state evidence (2026-09-09): connected-input read-only
projection, manual-input fallback, and bounded input/output pane dimensions now
belong to `WorkbenchCanvasLlmPaneRenderer`; the page retains DOM event wiring,
copy/run actions, and persistence side effects. Focused behavior coverage and
full verification passed at 546 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 LLM chat-state evidence (2026-09-09): message-list normalization,
chat-input normalization, running state, and send-label selection now belong to
`WorkbenchCanvasLlmPaneRenderer`; the page retains chat DOM event wiring and
run/copy side effects. Focused behavior coverage and full verification passed at
547 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 5 RunningHub media-input-list evidence (2026-09-09): reference-list
normalization and empty-state classification now belong to
`WorkbenchCanvasMediaInputRenderer`; the page retains preview construction,
DOM insertion, and provider-specific labels. Focused behavior coverage and full
verification passed at 548 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 shared media-input-list wiring evidence (2026-09-09): generic
image-input rendering and RunningHub input rendering now share the same neutral
list-state projection; page-specific preview and drag/event effects remain
local. Wiring coverage passes, with full verification at 549 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub prompt-field projection evidence (2026-09-09): prompt field
filtering, key/label derivation, and value projection now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains markup insertion,
control binding, and save/render side effects. Focused behavior coverage and
full verification passed at 550 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub setting-field projection evidence (2026-09-09): boolean,
slider, option, and random-number descriptor normalization now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains final markup calls,
control binding, and side effects. Focused behavior coverage and full
verification passed at 551 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 prompt-preview input-state evidence (2026-09-09): prompt preview input
filtering and empty-state classification now belong to
`WorkbenchCanvasPromptTemplateRenderer`; the page retains container updates and
markup insertion. Focused behavior coverage and full verification passed at 552
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 shared media-input-list wiring completion (2026-09-09): generic, Comfy,
and RunningHub media-input paths now share the neutral list-state projection;
provider-specific preview, labels, drag handling, and DOM effects remain local.
Existing wiring coverage and full verification remain PASS at 552 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 Loop body-state evidence (2026-09-09): loop image/prompt visibility,
input count, prompt count, and upstream-prompt classification now belong to
`WorkbenchCanvasLoopLayoutProjection`; the page retains cascade markup, DOM
updates, and interaction effects. Focused behavior coverage and full
verification passed at 553 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check.

Wave 5 Loop cascade-run-state evidence (2026-09-09): cascade target presence,
active/stopping state, order length, and bounded round count now belong to
`WorkbenchCanvasLoopLayoutProjection`; the page retains cascade button markup
and event effects. Focused behavior coverage and full verification passed at
554 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 5 Comfy random-toggle transition evidence (2026-09-09): the neutral Comfy
field renderer now owns the random-active state transition calculation; the
page retains node assignment, refresh, and save effects. Focused behavior
coverage and full verification passed at 555 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub random-toggle transition evidence (2026-09-09): the neutral
RunningHub field renderer now owns random-active state transition calculation;
the page retains node assignment, refresh, and save effects. Focused behavior
coverage and full verification passed at 556 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub entry-options evidence (2026-09-09): model/app/workflow
option-group markup and empty-provider fallback now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains provider entry
loading and selection effects. Focused behavior coverage and full verification
passed at 557 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 RunningHub payment-options evidence (2026-09-09): free-key/wallet-key
option markup and missing-capability labels now belong to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains provider capability
reads and selection effects. Focused behavior coverage and full verification
passed at 558 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check.

Wave 5 Comfy workflow-name selection evidence (2026-09-09): requested-name
validation and first-available fallback now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains workflow cache access and
async loading. Focused behavior coverage and full verification passed at 559
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 Comfy workflow-presence evidence (2026-09-09): workflow existence checks
now belong to `WorkbenchCanvasComfyFieldRenderer`; the page retains workflow
registry access. Focused behavior coverage and full verification passed at 560
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 Comfy workflow-load evidence (2026-09-09): valid-name resolution, cache
hits, failed-load cleanup, and JSON response projection now belong to
`WorkbenchCanvasComfyFieldRenderer`; the page retains the network entry point.
Focused behavior coverage and full verification passed at 561 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub workflow-load evidence (2026-09-09): workflow ID
normalization, cache hits, failed-load cleanup, and response.workflow projection
now belong to `WorkbenchCanvasRunningHubFieldRenderer`; the page retains the
network entry point. Focused behavior coverage and full verification passed at
562 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check.

Wave 6 browser acceptance recheck (2026-09-09, isolated `127.0.0.1:3045`):
default canonical routing rendered the persisted two-node fixture after a
cache-busting reload with no new browser errors; the all-zero rollback URL
rendered the same Canvas title and both node cards with no new browser errors.
This confirms the current execution-host wiring only; it does not satisfy the
deletion gate while `static/js/canvas.js` remains.

Wave 5 Loop connected-media batch projection evidence (2026-09-08): enabled-
state checking, connection traversal, URL filtering, and image/video batch
projection now delegate to
`WorkbenchCanvasLoopInputProjection.connectedBatch`; the page retains
node-type media extraction. Focused tests cover enabled and disabled paths;
full verification passed at 504 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax download projection evidence (2026-09-08): valid URL checks and
safe download-name projection now delegate to
`WorkbenchCanvasMediaTools.minimaxDownloadProjection`; the page retains link
creation and click side effects. Focused tests cover valid and empty URL paths;
full verification passed at 505 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 Loop output-media reference projection evidence (2026-09-08):
output-item type filtering, URL/name projection, fallback naming, and
output-index metadata now delegate to
`WorkbenchCanvasLoopInputProjection.outputMediaRefs`; the page retains
node-specific media classification. Focused tests cover image/video mappings
and legacy index semantics; full verification passed at 506 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 Loop node-media reference projection evidence (2026-09-08):
image/group/output/generated-node reference projection now delegates to
`WorkbenchCanvasLoopInputProjection.nodeMediaRefs`; the page retains
node-specific callback wiring. Focused tests cover group media mapping and
generated/output paths; full verification passed at 507 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 MiniMax timeline-interaction batch evidence (2026-09-09): playhead
clamping, active-segment hit testing, and selection-change detection now
delegate to `WorkbenchCanvasMediaTools.minimaxTimelineInteraction`; the page
retains DOM updates, refresh/save, and player synchronization. Focused tests
cover timeline hit and selection transition; full verification passed at 508
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 5 Loop configuration batch evidence (2026-09-09): count, start index,
batch-size, mode, and input-toggle normalization now delegate to
`WorkbenchCanvasLoopInputProjection.config`; the page retains node
assignment and UI effects. Focused tests cover bounded defaults and
mode/toggle preservation; full verification passed at 509 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 Loop prompt-context batch evidence (2026-09-09): variable text, count,
current index, and total-round normalization now delegate to
`WorkbenchCanvasLoopPromptRenderer.contextProjection`; the page retains
selected-input lookup and render side effects. Focused tests cover trimming and
bounded context defaults; full verification passed at 510 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 Loop editor-text batch evidence (2026-09-09): token-chip, line-break,
text-node, and non-breaking-space projection now delegates to
`WorkbenchCanvasLoopPromptRenderer.editorText`; the page retains token
insertion DOM effects. Focused tests prove editor-text parity; full
verification passed at 511 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check.

Wave 5 Loop input-summary batch evidence (2026-09-09): image/prompt counts and
upstream-prompt presence now delegate to
`WorkbenchCanvasLoopInputProjection.summary`; the page retains template
rendering and event handling. Focused tests cover positive and empty summaries;
full verification passed at 512 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field-projection batch evidence (2026-09-09): field text
indexing, pattern matching, aspect labels, option matching, and parameter
assignment now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains provider
callbacks. Focused tests cover matching, aspect conversion, and parameter
writes; full verification passed at 513 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub diagnostics batch evidence (2026-09-09): compact JSON and
detailed-error construction now delegate to
`WorkbenchCanvasRunningHubFieldRenderer`; the page retains error display and
logging side effects. Focused tests cover truncation and detail preservation;
full verification passed at 514 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub readable-error batch evidence (2026-09-09): structured
ComfyUI/RunningHub error parsing and user-facing message projection now
delegate to `WorkbenchCanvasRunningHubFieldRenderer.readableError`; the
page retains display and logging side effects. Focused tests cover provider
prefixes and node details; full verification passed at 515 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub payload-error batch evidence (2026-09-09): detail/raw/code/
taskId extraction and message assembly now delegate to
`WorkbenchCanvasRunningHubFieldRenderer.payloadError`; the page retains
error propagation. Focused tests cover detail preservation and metadata
extraction; full verification passed at 516 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub log-detail batch evidence (2026-09-09): task/code/stage/
workflow/raw detail-line assembly now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.logErrorText`; the page retains
logging calls. Focused tests cover detail ordering and compact raw output;
full verification passed at 517 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub entry-selection batch evidence (2026-09-09): title,
current-ID, and default-ID fallback selection now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.selectEntry`; the page retains
registry access. Focused tests cover title priority and ID fallbacks; full
verification passed at 518 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check.

Wave 5 RunningHub aspect-field ownership cleanup (2026-09-09): full-aspect
field detection now delegates to
`WorkbenchCanvasRunningHubFieldRenderer.isFullAspectField`; focused field
projection coverage remains green. Full verification passed at 518 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 5 RunningHub preset-parameter batch evidence (2026-09-09): MiniMax
prompt, duration, aspect, and megapixel field-write composition now delegates
to `WorkbenchCanvasRunningHubFieldRenderer.applyPresetParams`; the page
retains node/segment value selection. Focused tests cover preset matching and
writes; full verification passed at 519 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check.

Wave 5 RunningHub field-value batch evidence (2026-09-09): upstream media,
parameter/default precedence, skip rules, upload intent, and numeric
normalization now delegate to `WorkbenchCanvasRunningHubFieldRenderer.fieldValue`;
the page retains required checks and upload effects. Focused tests cover media
and numeric paths; full verification passed at 520 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check.

## Gate

## Wave 5 slice 44 evidence (2026-09-08)

Neutral node title projection now delegates to
`WorkbenchCanvasNodePresentation`; the page retains title markup and media
display overrides. Focused behavior coverage proves localized and fallback
title mapping.

While `static/js/canvas.js` exists, R4-39 must remain `IN_PROGRESS`. At close:

- the file is absent and no active HTML/JS/Python source references it;
- `canvas.html` loads one neutral bootstrap;
- the bootstrap contains no node-type, provider, executor, package, or
  industry-specific branching;
- every manifest cluster has a final owner with focused behavior tests;
- default and all-zero rollback browser acceptance pass against an isolated
  canonical store.

Wave 6 Classic LLM chat lifecycle batch evidence (2026-09-09): chat message
append, input clearing, running-state transitions, output projection, render,
save, and error notification now delegate through the neutral Classic chat
execution-host contract; the runtime retains only input/history reads and the
LLM call. Focused behavior coverage and full verification passed at 564 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. `static/js/canvas.js` remains present, so the deletion gate is
still open.

Wave 6 cascade cleanup ownership batch evidence (2026-09-09): cascade node-state
cleanup now delegates status/error clearing through the execution-status seam;
the cascade adapter no longer directly owns that cleanup write. Full
verification passed at 588 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. Classic runtime deletion remains
outstanding.

Wave 6 entry-chain cache-bust browser recheck evidence (2026-09-09):
`index.html` -> `canvas-list.html` -> `canvas-list.js` -> `canvas.html` now
propagates fresh versions; isolated browser logs confirmed
`classic-execution-host.js?v=2026.09.09.2` was fetched and the two-node Canvas
rendered successfully. Full verification passed at 586 tests. Classic runtime
deletion remains outstanding.

Wave 6 Cascade main-pass status batch evidence (2026-09-09): queued, running,
success, and failure transitions in the main Cascade pass now delegate through
the execution-status seam. Focused coverage and full verification passed at
589 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. Classic runtime deletion remains outstanding.

Wave 6 execution-adapter cache-bust batch evidence (2026-09-09):
`canvas.html` now references `classic-execution-host.js?v=2026.09.09.2` after
fallback removal, preventing stale browser code from masking neutral
delegation. Focused coverage and full verification passed at 585 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check.

Wave 6 Classic execution-adapter deduplication evidence (2026-09-09):
`classic-execution-host.js` no longer contains a duplicate fallback
implementation; it requires and delegates to the neutral execution host,
matching the canonical HTML load order. Full verification passes after the
contract test was updated to load both modules; the deletion gate remains open.

Wave 6 RunningHub config-status cleanup batch evidence (2026-09-09): app and
workflow configuration refreshes now clear execution status through the
Classic execution-host contract instead of direct page writes. Focused source
coverage and full verification passed at 583 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. Classic runtime
deletion remains outstanding.

Wave 6 execution-state confinement guard evidence (2026-09-09): remaining
`running/runStatus/runError` writes in `canvas.js` are confined to
execution-host callback implementations; no page/runtime path writes those
fields directly. Focused source coverage and full verification passed at 584
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check.

Wave 6 transient run-state reset batch evidence (2026-09-09): Canvas
load/reconnect cleanup now delegates running/status/error reset through the
Classic execution-host contract instead of writing node execution fields
directly. Focused source coverage and full verification passed at 582 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check. Classic runtime deletion remains outstanding.

Wave 6 stuck-generator cleanup batch evidence (2026-09-09): stale running-state
reset now delegates through the Classic execution-host contract instead of
writing `node.running` directly. Focused source coverage and full verification
passed at 581 tests, 78 Python AST files, 103 JavaScript files, 4 architecture
guards, and clean diff check. Classic runtime deletion remains outstanding.

Wave 6 source-reference audit evidence (2026-09-09): execution entry points in
`canvas.js` are compatibility wrappers that call
`ensureClassicExecutorRuntime()`; concrete generator implementations remain in
`classic-executor-runtime.js`, with no direct execution-state writes there.
Classic cascade orchestration remains a bounded compatibility adapter, so the
deletion gate is still open.

Canonical browser acceptance recheck evidence (2026-09-09, isolated
`127.0.0.1:3045`): PASS — root entry loaded the Canvas manager iframe;
record `c29d2daf364a4c7fa5b5632f60e9903d` rendered its title and two nodes, and
the canonical static Canvas URL with all six explicit zero flags rendered the
same title and both node cards. No mutating user action was performed. The
Classic runtime remains, so the deletion gate is still open.

Wave 6 Midjourney execution lifecycle batch evidence (2026-09-09): start,
success-completion, failure, running-state, render, and save transitions now
delegate through the Classic execution-host contract; Midjourney request,
polling, and output composition remain in the runtime. Focused behavior
coverage and full verification passed at 571 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 6 execution-host ownership guard evidence (2026-09-09): the Classic
executor runtime now contains no direct `running`, `runStatus`, or `runError`
assignments for node/generator execution state; focused source guard and full
verification passed at 580 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check. This proves runtime ownership
removal for migrated execution paths, not Classic runtime deletion; the gate
remains open.

Wave 6 recovered pending-output completion batch evidence (2026-09-09):
recovered task success status, running-state reset, render, and save now
delegate through the Classic execution-host contract; recovery query and
result/output composition remain in the page/runtime. Focused behavior
coverage and full verification passed at 579 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 6 shared image-task completion lifecycle batch evidence (2026-09-09):
successful pending-task completion, status finalization, running-state reset,
render, and save now delegate through the Classic execution-host contract;
result normalization and output/log composition remain in the page/runtime.
Focused behavior coverage and full verification passed at 578 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so the deletion gate is still open.

Wave 6 shared image-task failure lifecycle batch evidence (2026-09-09):
pending task recovery/failure status, running-state reset, render, and save now
delegate through the Classic execution-host contract; task lookup, recovery
metadata, and generation-log composition remain in the runtime. Focused
behavior coverage and full verification passed at 577 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 6 Midjourney action/inpaint lifecycle batch evidence (2026-09-09): action
and modal start, running-state, success/failure status, render, and save
transitions now delegate through the Classic execution-host contract;
Midjourney action submission, polling, and output composition remain in the
runtime. Focused behavior coverage and full verification passed at 576 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 6 RunningHub workflow/application execution lifecycle batch evidence
(2026-09-09): running-state, success/failure status, render, and save
transitions now delegate through the Classic execution-host contract;
RunningHub submission, polling, and output composition remain in the runtime.
Focused behavior coverage and full verification passed at 574 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so the deletion gate is still open.

Wave 6 LTX Director execution lifecycle batch evidence (2026-09-09): running,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; timeline preparation, Comfy request, and
output composition remain in the runtime. Focused behavior coverage and full
verification passed at 573 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check. The Classic runtime remains, so
the deletion gate is still open.

Wave 6 video execution lifecycle batch evidence (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; video request, media normalization, and
output composition remain in the runtime. Focused behavior coverage and full
verification passed at 572 tests, 78 Python AST files, 103 JavaScript files,
4 architecture guards, and clean diff check. The Classic runtime remains, so
the deletion gate is still open.

Wave 6 legacy generator execution lifecycle batch evidence (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; the legacy online-image
request and output composition remain in the runtime. Focused behavior coverage
and full verification passed at 569 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so the deletion gate is still open.

Wave 6 generic generator execution lifecycle batch evidence (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; provider request,
pending-task, polling, and output composition remain in the runtime. Focused
behavior coverage and full verification passed at 568 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 6 RunningHub model execution lifecycle batch evidence (2026-09-09):
running-state, success/failure status, render, and save transitions now
delegate through the Classic execution-host contract; RunningHub request,
pending-task, polling, and output composition remain in the runtime. Focused
behavior coverage and full verification passed at 567 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 6 MiniMax execution lifecycle batch evidence (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; MiniMax request/output composition remains in
the runtime. Focused behavior coverage and full verification passed at 565
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 6 Comfy execution lifecycle batch evidence (2026-09-09): running-state,
success/failure status, render, and save transitions now delegate through the
Classic execution-host contract; Comfy request/workflow/output composition
remains in the runtime. Focused behavior coverage and full verification passed
at 566 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so the deletion gate is
still open.

Wave 5 cascade loop lifecycle batch evidence (2026-09-09): PASS — parallel and
serial loop rounds route queued/running/done/failed/cleanup state transitions
through the cascade execution-status seam while loop scheduling remains in the
bounded adapter. Full verification passed at 589 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 media-kind node projection batch evidence (2026-09-09): PASS — node
media-kind explicit values and URL fallback classification now use the neutral
`WorkbenchCanvasMediaKind.kindForNode` owner, with adapter-only original-URL
normalization and Classic FLV policy. Full verification passed at 589 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 media-reference projection batch evidence (2026-09-09): PASS — image,
group, output, and generated-media reference assembly now uses neutral
`WorkbenchCanvasMediaTools.mediaRefsFromNode`; adapter callbacks provide node
lookup and classification policy. Full verification passed at 590 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 latest-output reference batch evidence (2026-09-09): PASS — generator
 input projection now uses neutral `WorkbenchCanvasMediaTools.latestOutputReference`
 for newest non-empty output selection and reference construction, with adapter
 classification callback. Full verification passed at 591 tests, 78 Python AST
 files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
 Classic runtime remains, so the deletion gate is still open.

Wave 5 generated-media source projection batch evidence (2026-09-09): PASS —
generator input projection now uses neutral
`WorkbenchCanvasMediaTools.generatedMediaSources` for deterministic generated
reference source wrapping; reference discovery remains an adapter callback.
Full verification passed at 592 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so the deletion gate is still open.

Wave 5 image-source projection batch evidence (2026-09-09): PASS — generator
input projection now uses neutral `WorkbenchCanvasMediaTools.imageMediaSource`
for single-image upstream source construction, with adapter media-kind callback.
Full verification passed at 593 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so the deletion gate is still open.

Wave 5 group-source projection batch evidence (2026-09-09): PASS — generator
input projection now uses neutral `WorkbenchCanvasMediaTools.groupMediaSources`
for group image-member and prompt-summary source construction; node lookup and
media-kind policy remain adapter callbacks. Full verification passed at 594
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 prompt-source projection batch evidence (2026-09-09): PASS — generator
input projection now uses neutral `WorkbenchCanvasMediaTools.promptMediaSource`
for single-prompt upstream source construction; prompt text remains unchanged
and execution stays in the adapter. Full verification passed at 595 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 prompt-group source projection batch evidence (2026-09-09): PASS —
generator input projection now uses neutral
`WorkbenchCanvasMediaTools.promptGroupMediaSource` for promptGroup filtering and
text-summary construction; node lookup remains an adapter callback. Full
verification passed at 596 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so the
deletion gate is still open.

Wave 5 LLM source projection batch evidence (2026-09-09): PASS — generator
input projection now uses neutral `WorkbenchCanvasMediaTools.llmMediaSource`
for node-mode LLM output-text source construction; chat-mode and empty outputs
remain excluded. Full verification passed at 597 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 loop fallback source projection batch evidence (2026-09-09): PASS —
generator input projection now uses neutral
`WorkbenchCanvasMediaTools.loopFallbackSource` for no-image loop fallback source
construction; loop context and image-batch projection remain in the adapter.
Full verification passed at 598 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so the deletion gate is still open.

Wave 5 loop-image source projection batch evidence (2026-09-09): PASS —
generator input projection now uses neutral
`WorkbenchCanvasMediaTools.loopImageMediaSources` for loop image-reference
source list construction; context, discovery, and localized labels remain
adapter inputs. Full verification passed at 599 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 ordered-input projection batch evidence (2026-09-09): PASS — generator
input reconciliation now uses neutral
`WorkbenchCanvasMediaTools.orderedInputSources` for stale-id removal,
existing-order retention, and new-source append behavior; the adapter retains
the mutation boundary. Full verification passed at 600 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 5 input-reorder projection batch evidence (2026-09-09): PASS — media input
reorder now uses neutral `WorkbenchCanvasMediaTools.reorderInputIds` for
media-before-prompt ordering and invalid-target rejection; render and save
effects remain local. Full verification passed at 601 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 5 image-input projection batch evidence (2026-09-09): PASS — generator
view input projection now uses neutral
`WorkbenchCanvasMediaTools.imageInputSources` for reference
normalization/filtering; renderer selection and page effects remain local. Full
verification passed at 602 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so the
deletion gate is still open.

Wave 5 prompt-input projection batch evidence (2026-09-09): PASS — generator
view projection now uses neutral `WorkbenchCanvasMediaTools.promptInputSources`
for prompt-only source filtering; renderer selection and page effects remain
local. Full verification passed at 603 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 reference-source ID projection batch evidence (2026-09-09): PASS — input
reorder now uses neutral `WorkbenchCanvasMediaTools.refSourceIds` for
media-reference source ID extraction; ordering mutation and UI effects remain
local. Full verification passed at 604 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 connected-input projection batch evidence (2026-09-09): PASS —
generator input projection now uses neutral
`WorkbenchCanvasMediaTools.connectedInputNodes` for target-connection source
node collection; type-specific mapping remains in the adapter. Full
verification passed at 605 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so the
deletion gate is still open.

Wave 5 generated-media reference batch evidence (2026-09-09): PASS — generated
output reference normalization, naming, and image/type filtering now use
neutral `WorkbenchCanvasMediaTools.generatedMediaRefs`; output classification
and naming remain callbacks. Full verification passed at 606 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so the deletion gate is still open.

Wave 5 output-resolution markup batch evidence (2026-09-09): PASS — output
resolution and optional duration markup now use neutral
`WorkbenchCanvasMediaTools.outputResolutionMarkup`; page code only assigns the
resulting markup. Full verification passed at 607 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 compare-mode style projection batch evidence (2026-09-09): PASS — output
compare mode initial clip-path and slider position now use neutral
`WorkbenchCanvasMediaTools.compareModeStyles`; page code only applies the
returned styles. Full verification passed at 608 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 output-rerun projection batch evidence (2026-09-09): PASS — rerun-from-
output node, prompt, image-reference, and connection construction now uses
neutral `WorkbenchCanvasMediaTools.rerunOutputProjection`; insertion, lightbox
close, render, and save effects remain local. Full verification passed at 609
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 output-image node projection batch evidence (2026-09-09): PASS —
image-node data construction from output URLs now uses neutral
`WorkbenchCanvasMediaTools.outputImageNodeProjection`; media validation,
insertion, render, and save effects remain local. Full verification passed at
610 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 editor-output node projection batch evidence (2026-09-09): PASS — image
editor missing-output node data construction now uses neutral
`WorkbenchCanvasMediaTools.outputNodeProjection`; connection lookup, insertion,
and editor effects remain local. Full verification passed at 611 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 editor-generated-image projection batch evidence (2026-09-09): PASS —
generated image node data construction now uses neutral
`WorkbenchCanvasMediaTools.generatedImageNodeProjection`; editor insertion,
selection, render, and save effects remain local. Full verification passed at
612 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 output-workflow panel batch evidence (2026-09-09): PASS — output
prompt-panel open/text projection and rerun availability now use neutral
`WorkbenchCanvasMediaTools.outputPromptProjection` and
`outputRerunAvailable`; DOM binding and rerun action remain local. Full
verification passed at 613 tests, 78 Python AST files, 103 JavaScript files, 4
architecture guards, and clean diff check. The Classic runtime remains, so the
deletion gate is still open.

Wave 5 editor-output lookup batch evidence (2026-09-09): PASS — editor output
reuse now uses neutral `WorkbenchCanvasMediaTools.findOutputNodeForSource` for
source-to-output connection lookup; output creation and insertion remain local.
Full verification passed at 614 tests, 78 Python AST files, 103 JavaScript
files, 4 architecture guards, and clean diff check. The Classic runtime
remains, so the deletion gate is still open.

Wave 5 output dedupe batch evidence (2026-09-09): PASS — latest generated-
output selection and output URL duplicate detection now use neutral
`WorkbenchCanvasMediaTools.latestGeneratedOutputItem` and `outputHasUrl`; output
mutation and persistence remain local. Full verification passed at 615 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 output-lifecycle projection batch evidence (2026-09-09): PASS —
output-node connection lookup, non-empty output filtering, and duplicate-safe
append input preparation now use neutral `WorkbenchCanvasMediaTools.outputNodesForSource`,
`outputItemsWithUrl`, and `uniqueOutputItems`; mutation and persistence remain
local. Full verification passed at 616 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 unique-output append batch evidence (2026-09-09): PASS — duplicate
filtering and output-record append composition now use neutral
`WorkbenchCanvasMediaTools.appendUniqueOutputRecords`; page code applies the
returned images, layout, comparisons, and count. Full verification passed at
617 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 output-to-input group projection batch evidence (2026-09-09): PASS —
image-node placement, group geometry, and item membership construction now use
neutral `WorkbenchCanvasMediaTools.inputGroupProjection`; graph mutation, undo,
and persistence remain local. Full verification passed at 618 tests, 78 Python
AST files, 103 JavaScript files, 4 architecture guards, and clean diff check.
The Classic runtime remains, so the deletion gate is still open.

Wave 5 output-to-input downstream projection batch evidence (2026-09-09): PASS —
downstream connection target extraction now uses neutral
`WorkbenchCanvasMediaTools.downstreamTargetIds`; graph replacement, undo, and
persistence remain local. Full verification passed at 619 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

Wave 5 output-download filename batch evidence (2026-09-09): PASS — output/group
archive filename projection now uses neutral
`WorkbenchCanvasMediaTools.archiveDownloadFilename`; network request and
browser download effects remain local. Full verification passed at 620 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 generator-source orchestration batch evidence (2026-09-09): PASS —
complete connected input source projection across output, generated media,
image, group, prompt, loop, promptGroup, and LLM branches now uses neutral
`WorkbenchCanvasMediaTools.generatorSourceProjection`; context and
classification remain callbacks. Full verification passed at 621 tests, 78
Python AST files, 103 JavaScript files, 4 architecture guards, and clean diff
check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 input-view projection batch evidence (2026-09-09): PASS — generator and
RunningHub input views now obtain coordinated image/prompt source projections
from neutral `WorkbenchCanvasMediaTools.inputViewProjection`; renderer dispatch
remains local. Full verification passed at 622 tests, 78 Python AST files, 103
JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 RunningHub source-summary batch evidence (2026-09-09): PASS — RunningHub
media source ordering and image/video/audio/prompt summary now use neutral
`WorkbenchCanvasRunningHubFieldRenderer.sourceProjection`; ordering and kind
remain callbacks. Full verification passed at 623 tests, 78 Python AST files,
103 JavaScript files, 4 architecture guards, and clean diff check. The Classic
runtime remains, so the deletion gate is still open.

Wave 5 output-download projection batch evidence (2026-09-09): PASS — output
image URL and downloadable URL projections now use neutral
`WorkbenchCanvasMediaTools.outputDownloadProjection`; menu, network, and
browser-download effects remain local. Full verification passed at 624 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 archive-payload batch evidence (2026-09-09): PASS — output/group
download request payload construction now uses neutral
`WorkbenchCanvasMediaTools.archiveDownloadPayload`; fetch, response handling,
and browser download effects remain local. Full verification passed at 625
tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards, and
clean diff check. The Classic runtime remains, so the deletion gate is still
open.

Wave 5 single-download href batch evidence (2026-09-09): PASS — media download
href construction now uses neutral `WorkbenchCanvasMediaTools.downloadHref`,
preserving data/blob/API passthrough and encoded server-download fallback; link
creation and click effects remain local. Full verification passed at 626 tests,
78 Python AST files, 103 JavaScript files, 4 architecture guards, and clean
diff check. The Classic runtime remains, so the deletion gate is still open.

Wave 5 workflow-export projection batch evidence (2026-09-09): PASS — selected
workflow payload and export filename are now composed through neutral
`WorkbenchCanvasWorkflowTransfer.exportProjection`; graph selection and actual
export/download effects remain in page/asset adapters. Full verification passed
at 627 tests, 78 Python AST files, 103 JavaScript files, 4 architecture guards,
and clean diff check. The Classic runtime remains, so the deletion gate is still
open.
Wave 5 output-lightbox state batch evidence (2026-09-09): PASS — lightbox media
mode, comparison visibility, and group-download affordance now use neutral
`WorkbenchCanvasMediaTools.lightboxProjection`; DOM/media loading and download
effects remain local. Full verification passed at 628 tests, 78 Python AST
files, 103 JavaScript files, 4 architecture guards, and clean diff check. The
Classic runtime remains, so the deletion gate is still open.

## Final deletion gate (2026-09-09)

PASS — `static/js/canvas.js` and its HTML script reference are absent. The
Canvas page natively loads the nine declared responsibility sources in manifest
order and finishes in the small `canvas-app-bootstrap.js`; it does not fetch,
concatenate, or evaluate source at runtime. Focused behavior proves the native
ordering and absence of `eval`/`new Function`; a source guard proves every HTML
inline action is explicitly exported by the bootstrap.
Post-deletion browser acceptance on an isolated SQLite copy rendered the same
two-node record on both default and all-six-zero URLs. The workflow-transfer
modal opened and closed through the compatibility action export, and no new
console error appeared after that repair. Full `./scripts/agent-verify.sh`:
PASS (630 tests, 80 Python AST files, 111 JavaScript files, 4 architecture
guards, clean diff check). All eight manifest clusters are `MIGRATED`; the
duplicate Classic product runtime owner is removed. R4-40 was not started.
