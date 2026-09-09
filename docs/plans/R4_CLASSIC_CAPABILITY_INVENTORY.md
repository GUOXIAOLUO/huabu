# R4 Classic Capability Inventory

Owner: card R4-31. Classifies every Classic-only, product-relevant capability in
`static/js/canvas.js` before the Classic runtime is retired (U7). This is a
characterization deliverable — no code is deleted or migrated by this card
(out of scope: no blind deletion).

## Disposition vocabulary

- **KEEP** — stays Classic-only. (No product-relevant capability qualifies; the
  Classic runtime shell itself is the thing being removed.)
- **MIGRATE** — has a Unified owner to build on now or within R4 (creation /
  mutation boundary, renderer, media-result normalizer).
- **COMPAT** — bounded page-owned compatibility in R4; the real replacement is a
  later-Round runtime (execution / provider / media) and must not be
  re-implemented in R4.
- **REMOVE** — deleted at Classic retirement with no shared replacement.
  (Applies to the Classic-entry deep-link and runtime shell, already tracked in
  the ownership matrix `Classic product runtime` row, not to the
  product-relevant capabilities listed here.)
- **DEFER-R8** — the owning runtime (Collection/Asset, Executor/Execution) is
  explicitly forbidden in R4 per `CURRENT_EXECUTION_STATUS.md` "Forbidden next
  actions"; keep compatibility and defer the decision to R8.

## Target-owner vocabulary

- **Unified creation/mutation boundary** — `NodeCreationService` / `NodeMutationService` / `GraphMutationService` / `GroupMembershipService` + `WorkbenchNodeClient`.
- **Unified media renderer** — `MediaRenderer` + shared media modules (`media-preview-controls.js`, `media-result-normalizer.js`, `media-drop-payload.js`).
- **Unified media-result normalizer** — `media-result-normalizer.js` (shared result extraction).
- **Legacy execution seam** — bounded compatibility adapter; R8 `ExecutorRegistry`/`ExecutionRuntime` owns the real replacement.
- **Collection/asset runtime** — R8 (Asset / Artifact / Collection), forbidden in R4.

## Inventory

### 1. Provider cards

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Provider node creation (generator / Midjourney / ModelScope) | MIGRATED | Unified creation/mutation boundary | `addGenerator(`, `addMidjourney(`, `addMsGen(` (in `static/js/workbench/canvas/classic-node-factories.js` host seam) |
| Provider card body (provider/model dropdowns, resolution/ratio) | COMPAT | Legacy execution seam (R8 Provider/Model registry) | `renderGeneratorBody`, `renderMidjourneyBody`, `renderMsGenBody`, `renderLLMBody` |

### 2. Comfy

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Comfy workflow/field controls | COMPAT | Legacy execution seam (R8) | `addComfyNode`, `renderComfyBody`, `renderComfySettings`, `updateComfyField`, `comfyWorkflowOptions` |
| Comfy result normalization | MIGRATED | Unified media-result normalizer | `window.WorkbenchCanvasMediaResultNormalizer.extract` (6 inline call sites in `canvas.js`) |

### 3. RunningHub

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| RunningHub workflow/params | COMPAT | Legacy execution seam (R8) | `addRhNode`, `renderRhBody`, `runningHubProvider`, `currentRunningHubWorkflow`, `currentRunningHubWorkflowConfig`, `renderRhParams` (in `static/js/workbench/canvas/classic-runninghub-controls.js` host seam) |

### 4. MiniMax

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| MiniMax timeline/player/generation | COMPAT | Legacy execution seam (R8, readable) | `addMiniMaxNode`, `renderMiniMaxBody`, `bindMiniMaxWorkbench`, `miniMaxEngine`, `miniMaxPlayerHtml`, `miniMaxSyncPlayerDom` (in `static/js/workbench/canvas/classic-minimax-controls.js` host seam) |

### 5. LTX

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| LTX director timeline/relay | COMPAT | Legacy execution seam (R8) | `addLTXDirectorNode`, `renderLTXDirectorBody`, `destroyLTXEditor`, `ltxParseTimeline`, `ltxFlushTimelineToNode`, `ltxBuildContiguousRelay` (in `static/js/workbench/canvas/classic-ltx-controls.js` host seam) |

### 6. Video

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Video node creation | MIGRATED | Unified creation/mutation boundary | `addVideo(` (in `static/js/workbench/canvas/classic-node-factories.js` host seam) |
| Video card body | COMPAT | Legacy execution seam (R8) | `renderVideoBody` (in `static/js/workbench/canvas/classic-video-card-body.js`) |
| Video provider/params | COMPAT | Legacy execution seam (R8) | `videoApiProviders`, `resolveVideoProviderId`, `providerVideoModels`, `renderVideoImageInputs` (in `static/js/workbench/canvas/classic-video-provider-params.js`) |

### 7. Output / log

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Output node creation | MIGRATED | Unified creation/mutation boundary | `addOutput(` (in `static/js/workbench/canvas/classic-node-factories.js` host seam) |
| Output grid renderer | COMPAT | Unified media renderer / render runtime | `refreshOutputNodeContent`, `renderOutputGrid`, `bindOutputWrap` (in `static/js/workbench/canvas/classic-output-grid.js`) |
| Generation log panel | COMPAT | Legacy execution seam (R8 result tray) | `addGenerationLog`, `renderCanvasLog` (in `static/js/workbench/canvas/classic-generation-log.js`) |

### 8. Asset

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Asset library / manager | DEFER-R8 | Collection/asset runtime | `revealCanvasAssetControls`, `renderCanvasAssetLibrary`, `toggleCanvasAssetLibrary`, `openAssetManager`, `renderAssetManager`, `mediaKindForUpload` |

### 9. Cascade / execution

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Cascade graph resolution / run / stop | COMPAT | Legacy execution seam (R8) | `classic-cascade-orchestrator.js` seam module (`beginCascade` / `computeCascadeOrder` / `resolveCascadeLoop` / `bindCascadeButtons` / `runCascadeNodeByType` / `requestCascadeStop` / `finalizeCascade` + 33 helpers) |

## Summary

- **15 capabilities**, 9 categories, all page-owned today (Classic-only).
- **MIGRATED**: 4 — provider node creation, Comfy result normalization, video node creation, output node creation.
- **MIGRATE**: 0 — none at this granularity (output node/grid was split in R4-38 Wave 4 into output-node-creation MIGRATED + output-grid-renderer COMPAT).
- **COMPAT**: 10 — provider card bodies, Comfy/RunningHub/MiniMax/LTX controls, video card body, video params, output grid renderer, generation log, cascade.
- **DEFER-R8**: 1 — asset library/manager (forbidden in R4).
- **KEEP / REMOVE**: none at capability granularity; the Classic runtime shell and Classic-entry deep-link are REMOVE (already tracked in the ownership matrix `Classic product runtime` row).

## Evidence manifest

Machine-readable; anchored by `tests/test_classic_capability_inventory.py`.

```json
{
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
  "categories": [
    "Provider cards",
    "Comfy",
    "RunningHub",
    "MiniMax",
    "LTX",
    "Video",
    "Output / log",
    "Asset",
    "Cascade / execution"
  ],
  "capabilities": [
    {"id": "provider-node-creation", "category": "Provider cards", "disposition": "MIGRATED", "target_owner": "Unified creation/mutation boundary", "evidence_target": "static/js/workbench/canvas/classic-node-factories.js", "evidence": ["addGenerator(", "addMidjourney(", "addMsGen("]},
    {"id": "provider-card-body", "category": "Provider cards", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8 Provider/Model registry)", "evidence_target": "static/js/workbench/canvas/classic-card-body-renderer.js", "evidence": ["renderGeneratorBody", "renderMidjourneyBody", "renderMsGenBody", "renderLLMBody"]},

    {"id": "comfy-controls", "category": "Comfy", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence_target": "static/js/workbench/canvas/classic-comfy-controls.js", "evidence": ["addComfyNode", "renderComfyBody", "renderComfySettings", "updateComfyField", "comfyWorkflowOptions"]},
    {"id": "comfy-result-normalization", "category": "Comfy", "disposition": "MIGRATED", "target_owner": "Unified media-result normalizer", "evidence_target": "static/js/workbench/canvas/classic-executor-runtime.js", "evidence": ["window.WorkbenchCanvasMediaResultNormalizer.extract"]},

    {"id": "runninghub", "category": "RunningHub", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence_target": "static/js/workbench/canvas/classic-runninghub-controls.js", "evidence": ["addRhNode", "renderRhBody", "runningHubProvider", "currentRunningHubWorkflow", "currentRunningHubWorkflowConfig", "renderRhParams"]},

    {"id": "minimax", "category": "MiniMax", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8, readable)", "evidence_target": "static/js/workbench/canvas/classic-minimax-controls.js", "evidence": ["addMiniMaxNode", "renderMiniMaxBody", "bindMiniMaxWorkbench", "miniMaxEngine", "miniMaxPlayerHtml", "miniMaxSyncPlayerDom"]},

    {"id": "ltx", "category": "LTX", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence_target": "static/js/workbench/canvas/classic-ltx-controls.js", "evidence": ["addLTXDirectorNode", "renderLTXDirectorBody", "destroyLTXEditor", "ltxParseTimeline", "ltxFlushTimelineToNode", "ltxBuildContiguousRelay"]},

    {"id": "video-node-creation", "category": "Video", "disposition": "MIGRATED", "target_owner": "Unified creation/mutation boundary", "evidence_target": "static/js/workbench/canvas/classic-node-factories.js", "evidence": ["addVideo("]},
    {"id": "video-card-body", "category": "Video", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["renderVideoBody"], "evidence_target": "static/js/workbench/canvas/classic-video-card-body.js"},
    {"id": "video-provider-params", "category": "Video", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["videoApiProviders", "resolveVideoProviderId", "providerVideoModels", "renderVideoImageInputs"], "evidence_target": "static/js/workbench/canvas/classic-video-provider-params.js"},

    {"id": "output-node-creation", "category": "Output / log", "disposition": "MIGRATED", "target_owner": "Unified creation/mutation boundary", "evidence_target": "static/js/workbench/canvas/classic-node-factories.js", "evidence": ["addOutput("]},
    {"id": "output-grid-renderer", "category": "Output / log", "disposition": "COMPAT", "target_owner": "Unified media renderer / render runtime", "evidence": ["refreshOutputNodeContent", "renderOutputGrid", "bindOutputWrap"], "evidence_target": "static/js/workbench/canvas/classic-output-grid.js"},
    {"id": "generation-log", "category": "Output / log", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8 result tray)", "evidence": ["addGenerationLog", "renderCanvasLog"], "evidence_target": "static/js/workbench/canvas/classic-generation-log.js"},

    {"id": "asset-library", "category": "Asset", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["revealCanvasAssetControls", "renderCanvasAssetLibrary", "toggleCanvasAssetLibrary", "openAssetManager", "renderAssetManager", "mediaKindForUpload"], "evidence_target": "static/js/workbench/canvas/classic-asset-runtime.js"},

    {"id": "cascade", "category": "Cascade / execution", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence_target": "static/js/workbench/canvas/classic-cascade-orchestrator.js", "evidence": ["WorkbenchCanvasClassicCascadeOrchestrator"]}
  ]
}
```
