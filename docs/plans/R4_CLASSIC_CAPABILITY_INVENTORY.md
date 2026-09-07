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
| RunningHub workflow/params | COMPAT | Legacy execution seam (R8) | `addRhNode`, `renderRhBody`, `runningHubProvider`, `currentRunningHubWorkflow`, `currentRunningHubWorkflowConfig`, `renderRhParams` |

### 4. MiniMax

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| MiniMax timeline/player/generation | COMPAT | Legacy execution seam (R8, readable) | `addMiniMaxNode`, `renderMiniMaxBody`, `bindMiniMaxWorkbench`, `miniMaxEngine`, `miniMaxPlayerHtml`, `miniMaxSyncPlayerDom` |

### 5. LTX

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| LTX director timeline/relay | COMPAT | Legacy execution seam (R8) | `addLTXDirectorNode`, `renderLTXDirectorBody`, `destroyLTXEditor`, `ltxParseTimeline`, `ltxFlushTimelineToNode`, `ltxBuildContiguousRelay` |

### 6. Video

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Video node/player | MIGRATE | Unified media renderer | `addVideoNode`, `renderVideoBody` |
| Video provider/params | COMPAT | Legacy execution seam (R8) | `videoApiProviders`, `resolveVideoProviderId`, `providerVideoModels`, `renderVideoImageInputs` |

### 7. Output / log

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Output node + result grid | MIGRATE | Unified media renderer / render runtime | `addOutputNode`, `refreshOutputNodeContent`, `renderOutputGrid`, `bindOutputWrap` |
| Generation log panel | COMPAT | Legacy execution seam (R8 result tray) | `addGenerationLog`, `renderCanvasLog` |

### 8. Asset

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Asset library / manager | DEFER-R8 | Collection/asset runtime | `revealCanvasAssetControls`, `renderCanvasAssetLibrary`, `toggleCanvasAssetLibrary`, `openAssetManager`, `renderAssetManager`, `mediaKindForUpload` |

### 9. Cascade / execution

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Cascade graph resolution / run / stop | COMPAT | Legacy execution seam (R8) | `beginCascade`, `computeCascadeOrder`, `resolveCascadeLoop`, `bindCascadeButtons`, `runCascadeNodeByType`, `requestCascadeStop`, `finalizeCascade` |

## Summary

- **13 capabilities**, 9 categories, all page-owned today (Classic-only).
- **MIGRATE**: 4 — provider node creation, Comfy result normalization, video node/player, output node/grid.
- **COMPAT**: 8 — provider card bodies, Comfy/RunningHub/MiniMax/LTX controls, video params, generation log, cascade.
- **DEFER-R8**: 1 — asset library/manager (forbidden in R4).
- **KEEP / REMOVE**: none at capability granularity; the Classic runtime shell and Classic-entry deep-link are REMOVE (already tracked in the ownership matrix `Classic product runtime` row).

## Evidence manifest

Machine-readable; anchored by `tests/test_classic_capability_inventory.py`.

```json
{
  "source": "static/js/canvas.js",
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
    {"id": "provider-card-body", "category": "Provider cards", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8 Provider/Model registry)", "evidence": ["renderGeneratorBody", "renderMidjourneyBody", "renderMsGenBody", "renderLLMBody"]},

    {"id": "comfy-controls", "category": "Comfy", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["addComfyNode", "renderComfyBody", "renderComfySettings", "updateComfyField", "comfyWorkflowOptions"]},
    {"id": "comfy-result-normalization", "category": "Comfy", "disposition": "MIGRATED", "target_owner": "Unified media-result normalizer", "evidence": ["window.WorkbenchCanvasMediaResultNormalizer.extract"]},

    {"id": "runninghub", "category": "RunningHub", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["addRhNode", "renderRhBody", "runningHubProvider", "currentRunningHubWorkflow", "currentRunningHubWorkflowConfig", "renderRhParams"]},

    {"id": "minimax", "category": "MiniMax", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8, readable)", "evidence": ["addMiniMaxNode", "renderMiniMaxBody", "bindMiniMaxWorkbench", "miniMaxEngine", "miniMaxPlayerHtml", "miniMaxSyncPlayerDom"]},

    {"id": "ltx", "category": "LTX", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["addLTXDirectorNode", "renderLTXDirectorBody", "destroyLTXEditor", "ltxParseTimeline", "ltxFlushTimelineToNode", "ltxBuildContiguousRelay"]},

    {"id": "video-player", "category": "Video", "disposition": "MIGRATE", "target_owner": "Unified media renderer", "evidence": ["addVideoNode", "renderVideoBody"]},
    {"id": "video-provider-params", "category": "Video", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["videoApiProviders", "resolveVideoProviderId", "providerVideoModels", "renderVideoImageInputs"]},

    {"id": "output-node", "category": "Output / log", "disposition": "MIGRATE", "target_owner": "Unified media renderer / render runtime", "evidence": ["addOutputNode", "refreshOutputNodeContent", "renderOutputGrid", "bindOutputWrap"]},
    {"id": "generation-log", "category": "Output / log", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8 result tray)", "evidence": ["addGenerationLog", "renderCanvasLog"]},

    {"id": "asset-library", "category": "Asset", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["revealCanvasAssetControls", "renderCanvasAssetLibrary", "toggleCanvasAssetLibrary", "openAssetManager", "renderAssetManager", "mediaKindForUpload"]},

    {"id": "cascade", "category": "Cascade / execution", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["beginCascade", "computeCascadeOrder", "resolveCascadeLoop", "bindCascadeButtons", "runCascadeNodeByType", "requestCascadeStop", "finalizeCascade"]}
  ]
}
```
