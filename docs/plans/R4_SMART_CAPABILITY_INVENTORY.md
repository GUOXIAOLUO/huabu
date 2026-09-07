# R4 Smart Capability Inventory

> **Historical snapshot (R4-36).** The source file `static/js/smart-canvas.js`
> was retired by card R4-36, and the evidence-anchoring test
> `tests/test_smart_capability_inventory.py` was deleted with it. The
> evidence function names below are a frozen R4-27 artifact: they describe
> what existed in `smart-canvas.js` at 2026-09-07 and are preserved as the
> capability-classification record that informed the R4-28/29/30/32/33
> cutover sequence and the R4-34 unified-entry + R4-35 handoff-removal
> sequence. They are no longer validated against current source.

Owner: card R4-27. Classifies every Smart-only, product-relevant capability in
`static/js/smart-canvas.js` before the Smart runtime is retired (U7). This is a
characterization deliverable — no code is deleted or migrated by this card.

## Disposition vocabulary

- **KEEP** — stays Smart-only. (No product-relevant capability qualifies; the
  Smart runtime shell itself is the thing being removed.)
- **MIGRATE** — has a Unified owner to build on now or within R4 (creation /
  mutation boundary, renderer, interaction, prompt registry).
- **COMPAT** — bounded page-owned compatibility in R4; the real replacement is a
  later-Round runtime (execution / provider / media) and must not be
  re-implemented in R4.
- **REMOVE** — deleted at Smart retirement with no shared replacement. (Applies
  to the Smart-entry deep-link and runtime shell, already tracked in the
  ownership matrix `Smart handoff` / `Smart product runtime` rows, not to the
  product-relevant capabilities listed here.)
- **DEFER-R8** — the owning runtime (Collection/Asset, Executor/Execution) is
  explicitly forbidden in R4 per `CURRENT_EXECUTION_STATUS.md` "Forbidden next
  actions"; keep compatibility and defer the decision to R8.

## Target-owner vocabulary

- **Unified card/render runtime** — `WorkbenchRenderRuntime` / `UnifiedRenderHost` / renderer registry (`static/js/workbench/canvas/`).
- **Unified interaction** — `InteractionController` / `CanvasRuntime` / drag-resize-selection-viewport controllers.
- **Unified creation/mutation boundary** — `NodeCreationService` / `NodeMutationService` / `GraphMutationService` / `GroupMembershipService` + `WorkbenchNodeClient`.
- **Unified media renderer** — `MediaRenderer` + shared media modules (`media-preview-controls.js`, `media-result-normalizer.js`, `media-drop-payload.js`).
- **Unified media edit runtime** — a new shared module to be built (no shared editor exists today).
- **PromptRegistry** — Prompt as a first-class resource (AGENTS.md constraint #9).
- **Collection/asset runtime** — R8 (Asset / Artifact / Collection), forbidden in R4.
- **Legacy execution seam** — bounded compatibility adapter; R8 `ExecutorRegistry`/`ExecutionRuntime` owns the real replacement.

## Inventory

### 1. Composer

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Composer shell / positioning / refresh | MIGRATE | Unified card/render runtime | `updateComposer`, `positionComposerForNode`, `scheduleComposerUpdate`, `activeComposerNode` |
| Composer dynamic provider/media controls | COMPAT | Legacy execution seam (R8) | `renderDynamicParams` |
| Composer @-mention picker | MIGRATE | Unified composer (shares asset mention) | `placeMentionPickerInComposerCard` |

### 2. Prompt presets / templates / skills

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Prompt preset CRUD + panel | MIGRATE | PromptRegistry | `loadPromptPresets`, `savePromptPresets`, `openPromptPresetPanel`, `savePromptNodeAsPreset` |
| Prompt template CRUD + panel | MIGRATE | PromptRegistry | `loadPromptTemplates`, `renderPromptTemplatePanel`, `applyPromptTemplateToNode`, `deletePromptTemplate` |
| Prompt node body (skill / separator / segments UI) | MIGRATE | Unified prompt card renderer | `promptNodeBodyHtml`, `bindPromptNodeControls`, `promptSkillVisual` |
| Prompt separator / multi-segment split | MIGRATE | Unified prompt card | `splitSmartPromptItems`, `smartLoopPromptFieldValues` |
| Prompt LLM / skill execution | COMPAT | Legacy execution seam (R8) | `runPromptLLMNode`, `buildPromptRequest` |

### 3. Asset UX

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Asset library UI (grid / categories / tabs / rename / preview) | DEFER-R8 | Collection/asset runtime | `renderAssetLibrary`, `assetCategories`, `openAssetNameDialog` |
| Asset load + WebSocket sync | DEFER-R8 | Collection/asset runtime | `loadAssetLibrary`, `connectAssetLibrarySyncSocket` |
| Local asset folder + URL intake | DEFER-R8 | Collection/asset runtime | `addFilesToLocalAssetLibrary`, `addUrlToAssetLibrary` |
| Asset @-mention / drag-in | MIGRATE | Unified creation (media-drop) | `assetMentionCandidateImages`, `toggleAssetMentionPickerFromThumbs` |
| Asset inbox paste | DEFER-R8 | Collection/asset runtime | `pasteAssetsFromInbox` |

### 4. Media edit / crop / draw / panorama

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Image editor modal + mode dispatch | MIGRATE | Unified media edit runtime | `openImageEditor`, `closeImageEditor`, `setImageEditMode` |
| Crop | MIGRATE | Unified media edit runtime | `renderCropBox`, `applyImageCrop`, `setCropAspectPreset` |
| Draw (brush / label / undo) | MIGRATE | Unified media edit runtime | `beginEditDraw`, `strokeFreeDrawPoint`, `undoEditDrawing` |
| Grid join / split | MIGRATE | Unified media edit runtime | `applyGridJoinPreset`, `applyImageGridSplit` |
| Panorama viewer | MIGRATE | Unified media edit runtime | `ensurePanoramaRenderer`, `renderPanoramaFrame`, `exportPanoramaFrame` |

### 5. Smart group actions

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Group membership (absorb / add / ungroup / prune) | MIGRATE | GroupMembershipService boundary | `absorbImageNodeIntoSmartGroup`, `addNodeToSmartGroup`, `ungroupNode`, `pruneSmartGroupMembershipsForNode` |
| Group arrange / layout | MIGRATE | Unified group render/layout | `arrangeSmartGroupMembers`, `smartGroupThumbLayout` |
| Group toolbar / body | MIGRATE | Unified group render | `smartGroupBodyHtml`, `runSmartGroupToolbarAction` |
| Group media record | MIGRATE | Unified group render (mountGroupCard) | `smartGroupMediaRecord` |

### 6. Cascade / execution UI

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Cascade graph resolution / state | COMPAT | Legacy execution seam (R8) | `resolveSmartCascadeLoop`, `smartCascadeGraphForTail`, `activeSmartCascadeCount` |
| Cascade run / stop / parallel limit | COMPAT | Legacy execution seam (R8) | `runSmartCascade`, `requestSmartCascadeStop`, `smartCascadeParallelLimit` |
| Comfy queue generation | COMPAT | Legacy execution seam (R8) | `runQueuedSmartComfyGenerate`, `runCascadeStepIntoNode` |

### 7. Provider / media / MiniMax dynamic controls

| Capability | Disposition | Target owner | Key functions |
|---|---|---|---|
| Provider/model metadata + dropdowns | COMPAT | Legacy execution seam (R8 Provider/Model registry) | `imageProviders`, `chatProviderOptions`, `renderProviderControl` |
| Comfy workflow / field controls | COMPAT | Legacy execution seam (R8) | `renderComfyParams`, `renderComfyWorkflowControl`, `ensureComfyWorkflow` |
| Video player / preview | MIGRATE | Unified media renderer | `smartVideoPlayerHtml`, `bindSmartVideoOverlay` |
| Video parameter controls | COMPAT | Legacy execution seam (R8) | `renderVideoProviderControl`, `renderApiVideoParams` |
| MiniMax timeline / segments / player | COMPAT | Legacy execution seam (R8, readable) | `smartMinimaxBodyHtml`, `smartMinimaxPlayerHtml`, `handleMinimaxTimelineDrop`, `exportMinimaxTimeline` |
| Manual video URL / cloud upload | COMPAT | Legacy execution seam (upload → media-drop) | `manualSmartVideoLink`, `uploadCurrentSmartVideosToCloud` |

## Summary

- **31 capabilities**, 7 categories, all page-owned today (Smart-only).
- **MIGRATE**: 18 — prompt registry/card, media edit, group actions, composer shell, video player, asset mention/drag.
- **COMPAT**: 13 — execution/provider/media controls that R8 owns the real replacement for.
- **DEFER-R8**: 5 — asset/collection runtime, forbidden in R4.
- **KEEP / REMOVE**: none at capability granularity; the Smart runtime shell and Smart-entry deep-link are REMOVE (already tracked in the ownership matrix).

## Evidence manifest

Machine-readable; anchored by `tests/test_smart_capability_inventory.py`.

```json
{
  "source": "static/js/smart-canvas.js",
  "categories": [
    "Composer",
    "Prompt presets/templates/skills",
    "Asset UX",
    "Media edit/crop/draw/panorama",
    "Smart group actions",
    "Cascade/execution",
    "Provider/media/MiniMax controls"
  ],
  "capabilities": [
    {"id": "composer-shell", "category": "Composer", "disposition": "MIGRATE", "target_owner": "Unified card/render runtime", "evidence": ["updateComposer", "positionComposerForNode", "scheduleComposerUpdate", "activeComposerNode"]},
    {"id": "composer-dynamic-controls", "category": "Composer", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["renderDynamicParams"]},
    {"id": "composer-mention-picker", "category": "Composer", "disposition": "MIGRATE", "target_owner": "Unified composer (shares asset mention)", "evidence": ["placeMentionPickerInComposerCard"]},

    {"id": "prompt-presets", "category": "Prompt presets/templates/skills", "disposition": "MIGRATE", "target_owner": "PromptRegistry", "evidence": ["loadPromptPresets", "savePromptPresets", "openPromptPresetPanel", "savePromptNodeAsPreset"]},
    {"id": "prompt-templates", "category": "Prompt presets/templates/skills", "disposition": "MIGRATE", "target_owner": "PromptRegistry", "evidence": ["loadPromptTemplates", "renderPromptTemplatePanel", "applyPromptTemplateToNode", "deletePromptTemplate"]},
    {"id": "prompt-node-body", "category": "Prompt presets/templates/skills", "disposition": "MIGRATE", "target_owner": "Unified prompt card renderer", "evidence": ["promptNodeBodyHtml", "bindPromptNodeControls", "promptSkillVisual"]},
    {"id": "prompt-separator-split", "category": "Prompt presets/templates/skills", "disposition": "MIGRATE", "target_owner": "Unified prompt card", "evidence": ["splitSmartPromptItems", "smartLoopPromptFieldValues"]},
    {"id": "prompt-llm-execution", "category": "Prompt presets/templates/skills", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["runPromptLLMNode", "buildPromptRequest"]},

    {"id": "asset-library-ui", "category": "Asset UX", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["renderAssetLibrary", "assetCategories", "openAssetNameDialog"]},
    {"id": "asset-load-sync", "category": "Asset UX", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["loadAssetLibrary", "connectAssetLibrarySyncSocket"]},
    {"id": "asset-local-folder", "category": "Asset UX", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["addFilesToLocalAssetLibrary", "addUrlToAssetLibrary"]},
    {"id": "asset-mention-drag", "category": "Asset UX", "disposition": "MIGRATE", "target_owner": "Unified creation (media-drop)", "evidence": ["assetMentionCandidateImages", "toggleAssetMentionPickerFromThumbs"]},
    {"id": "asset-inbox-paste", "category": "Asset UX", "disposition": "DEFER-R8", "target_owner": "Collection/asset runtime", "evidence": ["pasteAssetsFromInbox"]},

    {"id": "image-editor-modal", "category": "Media edit/crop/draw/panorama", "disposition": "MIGRATE", "target_owner": "Unified media edit runtime", "evidence": ["openImageEditor", "closeImageEditor", "setImageEditMode"]},
    {"id": "crop", "category": "Media edit/crop/draw/panorama", "disposition": "MIGRATE", "target_owner": "Unified media edit runtime", "evidence": ["renderCropBox", "applyImageCrop", "setCropAspectPreset"]},
    {"id": "draw", "category": "Media edit/crop/draw/panorama", "disposition": "MIGRATE", "target_owner": "Unified media edit runtime", "evidence": ["beginEditDraw", "strokeFreeDrawPoint", "undoEditDrawing"]},
    {"id": "grid-join-split", "category": "Media edit/crop/draw/panorama", "disposition": "MIGRATE", "target_owner": "Unified media edit runtime", "evidence": ["applyGridJoinPreset", "applyImageGridSplit"]},
    {"id": "panorama", "category": "Media edit/crop/draw/panorama", "disposition": "MIGRATE", "target_owner": "Unified media edit runtime", "evidence": ["ensurePanoramaRenderer", "renderPanoramaFrame", "exportPanoramaFrame"]},

    {"id": "group-membership", "category": "Smart group actions", "disposition": "MIGRATE", "target_owner": "GroupMembershipService boundary", "evidence": ["absorbImageNodeIntoSmartGroup", "addNodeToSmartGroup", "ungroupNode", "pruneSmartGroupMembershipsForNode"]},
    {"id": "group-arrange", "category": "Smart group actions", "disposition": "MIGRATE", "target_owner": "Unified group render/layout", "evidence": ["arrangeSmartGroupMembers", "smartGroupThumbLayout"]},
    {"id": "group-toolbar", "category": "Smart group actions", "disposition": "MIGRATE", "target_owner": "Unified group render", "evidence": ["smartGroupBodyHtml", "runSmartGroupToolbarAction"]},
    {"id": "group-media-record", "category": "Smart group actions", "disposition": "MIGRATE", "target_owner": "Unified group render (mountGroupCard)", "evidence": ["smartGroupMediaRecord"]},

    {"id": "cascade-graph", "category": "Cascade/execution", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["resolveSmartCascadeLoop", "smartCascadeGraphForTail", "activeSmartCascadeCount"]},
    {"id": "cascade-run-stop", "category": "Cascade/execution", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["runSmartCascade", "requestSmartCascadeStop", "smartCascadeParallelLimit"]},
    {"id": "comfy-queue", "category": "Cascade/execution", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["runQueuedSmartComfyGenerate", "runCascadeStepIntoNode"]},

    {"id": "provider-model-metadata", "category": "Provider/media/MiniMax controls", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8 Provider/Model registry)", "evidence": ["imageProviders", "chatProviderOptions", "renderProviderControl"]},
    {"id": "comfy-controls", "category": "Provider/media/MiniMax controls", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["renderComfyParams", "renderComfyWorkflowControl", "ensureComfyWorkflow"]},
    {"id": "video-player", "category": "Provider/media/MiniMax controls", "disposition": "MIGRATE", "target_owner": "Unified media renderer", "evidence": ["smartVideoPlayerHtml", "bindSmartVideoOverlay"]},
    {"id": "video-params", "category": "Provider/media/MiniMax controls", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8)", "evidence": ["renderVideoProviderControl", "renderApiVideoParams"]},
    {"id": "minimax-timeline", "category": "Provider/media/MiniMax controls", "disposition": "COMPAT", "target_owner": "Legacy execution seam (R8, readable)", "evidence": ["smartMinimaxBodyHtml", "smartMinimaxPlayerHtml", "handleMinimaxTimelineDrop", "exportMinimaxTimeline"]},
    {"id": "manual-video-url", "category": "Provider/media/MiniMax controls", "disposition": "COMPAT", "target_owner": "Legacy execution seam (upload -> media-drop)", "evidence": ["manualSmartVideoLink", "uploadCurrentSmartVideosToCloud"]}
  ]
}
```
