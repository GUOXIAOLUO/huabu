# R4-39 Classic Runtime Removal Inventory

Status: active characterization for R4-39  
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
  "schema": "workbench.r4-39-classic-runtime-removal/1",
  "source": "static/js/canvas.js",
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
      "status": "MIGRATE",
      "final_owner": "UnifiedRenderHost plus registered render modules",
      "evidence": ["render", "renderNode", "renderLoopBody", "onCardDestroy"]
    },
    {
      "id": "interaction-and-viewport",
      "status": "MIGRATE",
      "final_owner": "CanvasRuntime plus InteractionController",
      "evidence": ["startBoardPan", "startNodeDrag", "startNodeResize", "renderMinimap"]
    },
    {
      "id": "graph-group-mutation",
      "status": "MIGRATE",
      "final_owner": "GraphMutationService and GroupMembershipService adapters",
      "evidence": ["createVersionedConnection", "updateGroupMembership", "deleteSelectedNodes", "createNodeByType"]
    },
    {
      "id": "prompt-workflow-ui",
      "status": "MIGRATE",
      "final_owner": "neutral compatibility UI modules",
      "evidence": ["renderPromptTemplateModal", "openWorkflowTransferModal", "insertWorkflowIntoCanvas"]
    },
    {
      "id": "media-editing-ui",
      "status": "MIGRATE",
      "final_owner": "MediaTools and neutral media editor module",
      "evidence_target": "static/js/workbench/canvas/media-editor-state.js",
      "evidence": ["presentation", "canvas.applyCrop"],
      "evidence_note": "Page DOM and media mutation remain compatibility-owned while mode rules migrate."
    },
    {
      "id": "classic-compat-host",
      "status": "MIGRATE",
      "final_owner": "bounded compatibility adapter hosted by the neutral Canvas app",
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

## Wave 5 slice 6 evidence (2026-09-08)

Image-editor Grid layout row/column metadata now delegates to
`WorkbenchCanvasMediaTools.gridLayout`; the page supplies only the generated
group id.

## Wave 5 slice 7 evidence (2026-09-08)

Workflow export filename sanitization and timestamp formatting now delegate to
`WorkbenchCanvasWorkflowTransfer.filenameForExport`; the page provides only
the Canvas title and requested extension.

## Gate

While `static/js/canvas.js` exists, R4-39 must remain `IN_PROGRESS`. At close:

- the file is absent and no active HTML/JS/Python source references it;
- `canvas.html` loads one neutral bootstrap;
- the bootstrap contains no node-type, provider, executor, package, or
  industry-specific branching;
- every manifest cluster has a final owner with focused behavior tests;
- default and all-zero rollback browser acceptance pass against an isolated
  canonical store.
