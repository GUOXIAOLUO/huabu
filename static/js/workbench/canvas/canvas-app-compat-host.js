// Provider-card controls route their Canvas state writes + save/render through
// the shared provider-controls host (card R4-32); the LLM provider body is the
// first cut over. Presentation and provider/model resolution stay page-side.
let classicProviderControls = null;
function ensureProviderControls(){
    if(!classicProviderControls){
        classicProviderControls = window.WorkbenchCanvasProviderControls.create({
            setField: (node, key, value) => { if(node) node[key] = value; },
            save: () => scheduleSave(),
            render: () => render(),
        });
    }
    return classicProviderControls;
}
// Classic non-blank provider-node factories (generator / midjourney / msgen)
// live behind a shared host seam (card R4-38 Wave 2). The page holds the
// state-supplier functions; the seam holds the type-specific default records.
let classicNodeFactories = null;
function ensureClassicNodeFactories(){
    if(!classicNodeFactories){
        classicNodeFactories = window.WorkbenchCanvasClassicNodeFactories.create({
            addNode,
            uid,
            defaultPoint,
            imageApiProviders,
            allImageModels,
            defaultApiImageResolution,
            resolveMidjourneyProviderId,
            modelscopeImageModels,
            videoApiProviders: () => vpp.videoApiProviders(),
            providerVideoModels: (id) => vpp.providerVideoModels({providerId: id}),
            videoModels: () => videoModels,
            defaultVideoModels: () => DEFAULT_VIDEO_MODELS,
        });
    }
    return classicNodeFactories;
}
// Classic provider-card body renderers (LLM / Generator / Midjourney /
// MsGen) live behind a bounded compat seam (card R4-38 Wave 5). The seam
// holds the type-specific DOM construction; the page injects the helpers
// each body needs (provider/model resolution, i18n, image helpers,
// MsGen catalog, etc.). The COMPAT/R8 boundary keeps page-side state
// (nodes, connections, scheduleSave, render) on the page; R8 owns the
// real executor-driven body rendering.
let classicCardBodyRenderer = null;
function ensureClassicCardBodyRenderer(){
    if(!classicCardBodyRenderer){
        classicCardBodyRenderer = window.WorkbenchCanvasClassicCardBodyRenderer.create({
            document,
            escapeHtml,
            tr,
            resolveChatProviderId,
            providerChatModels,
            chatModelOptions,
            chatProviderOptions,
            resolveChatModel,
            llmInputImages,
            llmInputVideos,
            renderLLMChatPane,
            renderLLMNodePane,
            bindScrollableText,
            ensureProviderControls,
            generatorSources,
            orderedSources,
            mediaKindForRef,
            sanitizeImageNodeProviderModel,
            normalizeApiNodeSizeChoice,
            providerOptions,
            imageModelOptions,
            providerImageModels,
            resolveImageModel,
            defaultApiImageResolution,
            parseSizeValue,
            isGptImageAutoSizeModel,
            ratioPartsFromDimensions,
            resolveMidjourneyProviderId,
            midjourneyProviderOptions,
            midjourneyContinuationHtml,
            midjourneyModalHtml,
            runMidjourneyAction,
            runMidjourneyModal,
            MS_GEN_MODELS,
            modelscopeImageModels,
            currentMsModelId,
            modelscopeLorasForModel,
            modelscopeLoraOptions,
            modelscopeImageModelOptions,
            getImageDimensions,
            showErrorModal,
            renderImageInputList,
            renderPromptPreview,
            cascadeBtnHtml,
            retryBarHtml,
            bindCascadeButtons,
            scheduleSave,
            render,
            runCanvasGenerate,
            parameterPresentation: window.WorkbenchParameterPresentation,
        });
    }
    return classicCardBodyRenderer;
}
// Classic Comfy workflow / field controls (addComfyNode / comfyWorkflowOptions
// / renderComfyBody / renderComfySettings / updateComfyField) live behind a
// bounded compat seam (card R4-38 Wave 6). The seam holds the type-specific
// DOM construction + field-binding; the page injects the helpers each body
// needs (page-side Comfy workflow resolvers + render-image helper + render
// composition + page-local lifecycle). The COMPAT/R8 boundary keeps page-side
// state (comfyWorkflows, nodes, connections, scheduleSave, render) on the
// page; R8 owns the real executor-driven Comfy workflow rendering.
let classicComfyControls = null;
function ensureClassicComfyControls(){
    if(!classicComfyControls){
        classicComfyControls = window.WorkbenchCanvasClassicComfyControls.create({
            document,
            escapeHtml,
            tr,
            addNode,
            uid,
            defaultPoint,
            allImageModels,
            imageApiProviders,
            getModels: () => models,
            getComfyWorkflows: () => comfyWorkflows,
            generatorSources,
            orderedSources,
            imageRefsOnly,
            comfyFields,
            validComfyWorkflowName,
            hasComfyWorkflow,
            currentComfyWorkflow,
            comfyFieldKind,
            ensureComfyWorkflow,
            render,
            scheduleSave,
            runCanvasGenerate,
            renderPromptPreview,
            renderComfyImages,
            renderComfyCustomField,
            toggleComfyRandom,
            bindCascadeButtons,
            cascadeBtnHtml,
            retryBarHtml,
        });
    }
    return classicComfyControls;
}
// ============================================================
// Wave 7: runninghub-controls COMPAT seam
// ============================================================
let classicRunningHubControls = null;
function ensureClassicRunningHubControls(){
    if(!classicRunningHubControls){
        classicRunningHubControls = window.WorkbenchCanvasClassicRunningHubControls.create({
            document,
 tr,

            rhPaymentOptions,

            runningHubEntries,

            nowMs,
 uid,

            rhExtractFieldOptions,

            rhFieldRole,
 rhFieldValue,
 rhParamKey,
 rhActiveFields,
 refreshNodes,
 scheduleSave,

            runCanvasGenerate,
 refreshIcons,
 render,
 showErrorModal,
 alert,

            getApiProviders: function() { return apiProviders; },

            getRunningHubWorkflowCache: function() { return runningHubWorkflowCache; },

            escapeHtml,

            escapeAttr,

            addNode,

            defaultPoint,

            validRunningHubWorkflowId,

            parseRunningHubEntryKey,

            runningHubEntryKey,

            runningHubAllEntries,

            runningHubEntryId,

            ensureRhNodeSelection,

            applyRhEntrySelection,

            rhSelectedEntryRef,

            rhCurrentKind,

            rhEntryOptions,

            rhModelSettingsHtml,

            bindRhModelControls,

            renderRhPromptFields,

            renderRhInputs,

            rhMediaSources,

            rhDefaultValue,

            rhRandomEnabled,

            rhRandomActive,

            toggleRhRandom,

            currentRunningHubWorkflowEntry,

            rhEntryFields,

            rhWorkflowJsonFromSources,

            bindRhParamControls,

            renderRhSettingField,

            generatorSources,

            orderedSources,

            imageRefsOnly,

            videoRefsOnly,

            audioRefsOnly,

            mediaKindForRef,

            nodeTitleForMedia,

            rhMediaPreviewHtml,

            normalizeApiNodeSizeChoice,

            defaultApiImageResolution,

            parseSizeValue,

            renderImageInputList,

            renderPromptPreview,

            bindCascadeButtons,

            cascadeBtnHtml,

            retryBarHtml});
    }
    return classicRunningHubControls;
}

// ============================================================
// Wave 8: minimax-controls COMPAT seam
// ============================================================
let classicMiniMaxControls = null;
function ensureClassicMiniMaxControls(){
    if(!classicMiniMaxControls){
        classicMiniMaxControls = window.WorkbenchCanvasClassicMiniMaxControls.create({
            document,
 escapeHtml,
 escapeAttr,
 tr,

            addNode,
 uid,
 defaultPoint,

            langIsEn,

            nodeTitleForMedia,
 mediaKindForRef,

            generatorSources,
 orderedSources,

            imageRefsOnly,
 videoRefsOnly,
 audioRefsOnly,

            normalizeApiNodeSizeChoice,
 defaultApiImageResolution,

            parseSizeValue,
 renderImageInputList,

            render,
 scheduleSave,
 runCanvasGenerate,
 refreshIcons,

            renderPromptPreview,
 bindCascadeButtons,

            cascadeBtnHtml,
 retryBarHtml,

            miniMaxSelectedSegment,

            miniMaxTimelineTotal,

            miniMaxActiveSegmentAt,

            miniMaxCompactSegments,

            miniMaxExplicitRefsForSegment,

            miniMaxRefsForNode,

            miniMaxUniqueRefs,

            miniMaxMediaHtml,

            miniMaxSegmentRefsByKind,

            miniMaxStartPaneResize,

            miniMaxApplyTimelineTime,

            miniMaxDownloadItem,

            miniMaxSetSegmentResult,

            mediaKindForOutputItem,

            canvasDisplayMediaUrl,

            canvasPreviewImgHtml,

            canvasVideoPlayerHtml,

            canvasFileNameFromUrl,

            pushUndo,

            refreshNodes,

            bindScrollableText,

            rhPaymentOptions,

            runMiniMaxNode});
    }
    return classicMiniMaxControls;
}

// ============================================================
// Wave 9: ltx-controls COMPAT seam
// ============================================================
let classicLtxControls = null;
function ensureClassicLtxControls(){
    if(!classicLtxControls){
        classicLtxControls = window.WorkbenchCanvasClassicLtxControls.create({
            document,
 escapeHtml,
 escapeAttr,
 tr,

            addNode,
 uid,
 defaultPoint,

            getApiProviders: function() { return apiProviders; },

            renderPromptPreview,
 runCanvasGenerate,

            render,
 refreshIcons,
 scheduleSave,
 langIsEn,

            bindCascadeButtons,
 cascadeBtnHtml,
 retryBarHtml,

            ltxMigrateLegacySegments: (window.ltxMigrateLegacySegments || function(segs){ return segs || []; }),

            ltxDirectorSyncSeconds,

            bindLTXParamsRow,

            ltxSyncConnectedImagesToTimeline,

            defaultLTXSegment,

            orderedSources,

            generatorSources,

            imageRefsOnly,

            renderComfyImages,

            updateLTXNodeElementSize,

            refreshGeometryAfterLayout,

            windowObj: window});
    }
    return classicLtxControls;
}

// ============================================================
// Wave 10: video-card-body COMPAT seam
// ============================================================
let classicVideoCardBody = null;
function ensureClassicVideoCardBody(){
    if(!classicVideoCardBody){
        classicVideoCardBody = window.WorkbenchCanvasClassicVideoCardBody.create({
            document, tr,
            generatorSources, orderedSources, mediaKindForRef,
            sanitizeVideoNodeProviderModel, videoProviderOptions, videoModelOptions,
            vpp: function() { return ensureClassicVideoProviderParams(); },
            renderPromptPreview,
            scheduleSave, runCanvasGenerate,
            bindCascadeButtons, cascadeBtnHtml, retryBarHtml,
            render, showErrorModal, uploadCanvasVideosToCloud,
            providerVideoModels: function(providerId){ return vpp.providerVideoModels({providerId: providerId}); },
            renderVideoImageInputs: function(arg){ return vpp.renderVideoImageInputs(arg); },
            setCanvasManualVideoUrl,
            refreshIcons,
        });
    }
    return classicVideoCardBody;
}

// ============================================================
// Wave 11: video-provider-params COMPAT seam
// ============================================================
let classicVideoProviderParams = null;
function ensureClassicVideoProviderParams(){
    if(!classicVideoProviderParams){
        classicVideoProviderParams = window.WorkbenchCanvasClassicVideoProviderParams.create({
            tr,
            getApiProviders: function() { return apiProviders; },
            document,
            escapeHtml,
            mediaKindForRef,
            canvasVideoPreviewHtml,
            canvasPreviewImgHtml,
            isMissingAssetUrl,
            missingAssetHtml,
            getInternalDrag: function(){ return internalDrag; },
            setInternalDrag: function(value){ internalDrag = value; },
            uniqueModels,
            defaultApiProviders,
            reorderInput,
            refreshIcons,
        });
    }
    return classicVideoProviderParams;
}

// ============================================================
// Wave 12: output-grid COMPAT seam
// ============================================================
let classicOutputGrid = null;
function ensureClassicOutputGrid(){
    if(!classicOutputGrid){
        classicOutputGrid = window.WorkbenchCanvasClassicOutputGrid.create({
            document, escapeHtml,
            getApiProviders: function() { return apiProviders; },
            renderPendingOutput,
            outputUrlValue, canvasVideoPlayerHtml, canvasPreviewImgHtml,
            outputGridLayout, downloadUrl, outputDownloadName, queryRecoverPendingOutput,
            setOutputDragPreview, openOutputLightbox, renderOutputMedia,
            bindCanvasPreviewImageFallbacks, syncCanvasSelectedImageResolution,
            refreshOutputTimer, outputDomKeyForItem, outputDomKeyForPending,
            refreshNodes, scheduleSave,
            nodesEl,
            canvasActivateVideoPreview,
        });
    }
    return classicOutputGrid;
}

// ============================================================
// Wave 13: generation-log COMPAT seam
// ============================================================
let classicGenerationLog = null;
function ensureClassicGenerationLog(){
    if(!classicGenerationLog){
        classicGenerationLog = window.WorkbenchCanvasClassicGenerationLog.create({
            document, escapeHtml, escapeAttr, tr, langIsEn,
            getCanvas: function() { return (typeof canvas !== 'undefined' ? canvas : null); },
            isMissingAssetUrl,
            mediaKindForOutputItem, canvasVideoPreviewHtml, canvasPreviewImgHtml,
            outputUrlValue,
            runPlatformLabel, runTaskLabel, logTaskLabel, formatRunDuration,
            playGenerationCompleteSound, copyTextToClipboard, refreshIcons,
            bindCanvasPreviewImageFallbacks, openOutputLightbox,
            uid, nowMs,
            windowObj: window,
        });
    }
    return classicGenerationLog;
}

// ============================================================
// Wave 14: cascade-orchestrator COMPAT seam
// ============================================================
let classicCascadeOrchestrator = null;
function ensureClassicCascadeOrchestrator(){
    if(!classicCascadeOrchestrator){
        classicCascadeOrchestrator = window.WorkbenchCanvasClassicCascadeOrchestrator.create({
            tr,
 langIsEn,
 nowMs,
 uid,
 escapeHtml,
 escapeAttr,

            loopCount,

            getNodes: function() { return nodes; },

            getConnections: function() { return connections; },

            refreshNodes,
            setNodeRunStatus: (node, status, error) => ensureClassicExecutionHost().setRunStatus(node, status, error),

            runGenerator,
 runMidjourneyNode,
 runMsGenNode,
 runComfyNode,

            runLTXDirectorNode,
 runLLMNode,
 runVideoNode,
 runRhNode,
 runMiniMaxNode,

            setStatus,
 showErrorModal,
 alert,

            computeCascadeOrderTarget: computeCascadeOrder,

            comfyBackendCount: typeof comfyBackendCount !== 'undefined' ? comfyBackendCount : 1,

            setLoopContextMirror: setLoopContextMirror});
    }
    return classicCascadeOrchestrator;
}
// ── Wave 14 thin page-side wrappers (called by 30+ cascade execution sites) ──
// These exist so callers can use the original short names and so the seam-routed
// pattern strings live in canvas.js for the source-contract test.
function cancelCascade(nodeId){ ensureClassicCascadeOrchestrator().cancelCascade({nodeId}); }
function beginCascade(targetId, order, options){ return ensureClassicCascadeOrchestrator().beginCascade({targetId, order, options: options || {}}); }
async function runNodeCascade(nodeId){ await ensureClassicCascadeOrchestrator().runNodeCascade({nodeId}); }
async function retryNodeAndDownstream(nodeId){ await ensureClassicCascadeOrchestrator().retryNodeAndDownstream({nodeId}); }
function requestCascadeStop(targetId, reason){ ensureClassicCascadeOrchestrator().requestCascadeStop({targetId, reason: reason || ''}); }
function ensureCascadeActive(targetId, reason){ return ensureClassicCascadeOrchestrator().ensureCascadeActive({targetId, reason: reason || ''}); }
function isCascadeActive(targetId){ return ensureClassicCascadeOrchestrator().isCascadeActive(targetId); }
function isCascadeStopping(targetId){ return ensureClassicCascadeOrchestrator().isCascadeStopping(targetId); }
function cascadeAbortError(arg){ return ensureClassicCascadeOrchestrator().cascadeAbortError(typeof arg === 'string' ? {message: arg} : (arg || {})); }
function isCascadeAbortError(err){ return ensureClassicCascadeOrchestrator().isCascadeAbortError(err); }
function cascadeStopMessage(arg){ return ensureClassicCascadeOrchestrator().cascadeStopMessage(arg || {}); }
function resetCascadeRuntimeState(){ ensureClassicCascadeOrchestrator().resetCascadeRuntimeState(); }
function cascadeTargetIdFromOptions(opts){ return ensureClassicCascadeOrchestrator().cascadeTargetIdFromOptions({options: opts || {}}); }
function cascadeContextFromOptions(opts){ return ensureClassicCascadeOrchestrator().cascadeContextFromOptions({options: opts || {}}); }
function computeCascadeOrder(targetId){ return ensureClassicCascadeOrchestrator().computeCascadeOrder({targetId}); }
function bindCascadeButtons(wrap, nodeId){ return ensureClassicCascadeOrchestrator().bindCascadeButtons({wrap, nodeId}); }
// Review repair (2026-09-07): the Wave 7-14 reapply deleted these five
// cascade helpers page-side while live page transports still call them with
// their HEAD shapes; they are 1-line adapters so the call sites keep working.
function cascadeBackendRestartMessage(){ return ensureClassicCascadeOrchestrator().cascadeBackendRestartMessage(); }
function normalizeCanvasTaskError(err, fallback){ return ensureClassicCascadeOrchestrator().normalizeCanvasTaskError({err, fallback: fallback || ''}); }
async function cascadeFetch(input, init, options){ return ensureClassicCascadeOrchestrator().cascadeFetch({input, init: init || {}, options: options || {}}); }
function canvasRunTypes(){ return ensureClassicCascadeOrchestrator().canvasRunTypes(); }
function resolveCascadeLoop(targetId){ return ensureClassicCascadeOrchestrator().resolveCascadeLoop({targetId}); }
// ── Wave 16b: Classic asset/upload/drop seam factory ──
let classicAssetRuntime = null;
function ensureClassicAssetRuntime(){
    if(!classicAssetRuntime){
        classicAssetRuntime = window.WorkbenchCanvasClassicAssetRuntime.create({
            activeCanvasMediaCategory, activeCanvasWorkflowCategory, applyTempShUrlToCanvasRef, bindCanvasPreviewImageFallbacks, canUseVersionedImageCreation,
            canvasMediaCategories, canvasMediaPreviewUrl, canvasPreviewImgHtml, canvasVideoPreviewHtml, canvasWorkflowCategories,
            closeWorkflowTransferModal, copyTextToClipboard, createImageCardFromUrl, createImageCardsFromLocalPaths, createVersionedDroppedMediaNode,
            defaultPoint, ensureCanvas, escapeAttr, escapeHtml, fillImageNode,
            generatorSources, hasImageFiles, hasOutputImageDrag, insertWorkflowIntoCanvas, isAudioUrl,
            isCanvasInputDrag, isRemoteVideoReferenceUrl, isVideoUrl, langIsEn, loadCanvasPromptTemplates,
            mediaKindForRef, nodeBounds, orderedSources, outputImageName, outputUrlValue,
            pushUndo, refreshIcons, refreshNodes, render, responseErrorMessage,
            rhDefaultValue, rhParamKey, rhUseWallet, rhWorkflowNodeInfoList, scheduleSave,
            screenToWorld, selectedWorkflowPayload, setImageNodeFromOutput, setStatus, showErrorModal,
            tr, uid, updateWorkflowTransferMeta, workflowFilename,
            CANVAS_UPLOAD_MAX,
            IMAGE_DROP_EXT_RE,
            IMAGE_DROP_TEXT_TYPES,
            IMAGE_DROP_TYPE_HINT_RE,
            LOCAL_CANVAS_ASSET_LIBRARY_ID,
            assetManagerBody,
            assetManagerModal,
            canvasAssetAddCategoryBtn,
            canvasAssetCategorySelect,
            canvasAssetDropZone,
            canvasAssetGrid,
            canvasAssetHoverPreview,
            canvasAssetLibrarySelect,
            canvasAssetPanel,
            canvasAssetToggle,
            dropOverlay,
            missingAssetUrls,
            promptTemplateLibrarySelect,
            selected,
            workflowExportLibraryBtn,
            workflowExportMeta,
            workflowTransferModal,
            workflowTransferSub,
            getActiveCanvasAssetCategoryId: () => activeCanvasAssetCategoryId,
            getActiveCanvasAssetLibraryId: () => activeCanvasAssetLibraryId,
            getActiveCanvasWorkflowCategoryId: () => activeCanvasWorkflowCategoryId,
            getActivePromptLibraryId: () => activePromptLibraryId,
            getAssetManagerTab: () => assetManagerTab,
            getCanvasAssetLibrary: () => canvasAssetLibrary,
            getCanvasAssetLibraryOpen: () => canvasAssetLibraryOpen,
            getCanvasPromptLibraries: () => canvasPromptLibraries,
            getCanvasPromptTemplateOverrides: () => canvasPromptTemplateOverrides,
            getCanvasPromptTemplatesLoaded: () => canvasPromptTemplatesLoaded,
            getLocalCanvasAssetLibrary: () => localCanvasAssetLibrary,
            getManagerSelectedAssetIds: () => managerSelectedAssetIds,
            getManagerSelectedPromptIds: () => managerSelectedPromptIds,
            getManagerSelectedWorkflowIds: () => managerSelectedWorkflowIds,
            setActiveCanvasAssetCategoryId: (v) => { activeCanvasAssetCategoryId = v; },
            setActiveCanvasAssetLibraryId: (v) => { activeCanvasAssetLibraryId = v; },
            setActiveCanvasWorkflowCategoryId: (v) => { activeCanvasWorkflowCategoryId = v; },
            setActivePromptLibraryId: (v) => { activePromptLibraryId = v; },
            setCanvasAssetLibrary: (v) => { canvasAssetLibrary = v; },
            setCanvasPromptTemplatesLoaded: (v) => { canvasPromptTemplatesLoaded = v; },
            setLocalCanvasAssetLibrary: (v) => { localCanvasAssetLibrary = v; },
            setCanvasAssetLibraryOpen: (v) => { canvasAssetLibraryOpen = v; },
            getCanvas: () => canvas,
            getNodes: () => nodes,
        });
    }
    return classicAssetRuntime;
}


// ── Wave 16a: Classic executor/transport seam factory ──
let classicExecutorRuntime = null;
function ensureClassicExecutorRuntime(){
    if(!classicExecutorRuntime){
        classicExecutorRuntime = window.WorkbenchCanvasClassicExecutorRuntime.create({
            API_RATIO_VALUES, CANVAS_REFERENCE_IMAGE_MAX, CLIENT_ID, LTX_DIRECTOR_SEED_NODE, LTX_DIRECTOR_WF_NODE,
            LTX_DIRECTOR_WORKFLOW, actionFailed, activeCanvasTaskPolls, addGenerationLog, appendOutputImages,
            applyUploadedUrlToRefs, audioRefsOnly, cascadeAbortError, cascadeBackendRestartMessage, cascadeFetch,
            cascadeStopMessage, cascadeTargetIdFromOptions, clearStuckGeneratorRunning, collectRunMeta, collectRunMetas,
            comfyFieldKind, comfyFields, comfyNameForRef, comfyParamValue, comfyRandomActive,
            comfyRandomEnabled, comfyRandomValue, comfyRunLabel, completeCanvasImageTask, completeMidjourneyRun,
            ensureCascadeActive, ensureClassicCascadeOrchestrator, ensureClassicExecutionHost, ensureClassicLtxControls, ensureClassicMiniMaxControls,
            ensureClassicVideoProviderParams, ensureComfyWorkflow, ensureRhNodeSelection, ensureRunningHubWorkflowConfigForNode, extractUpstreamTaskId,
            findPendingTask, generatorSizeForRun, generatorSources, imageRefsOnly, isCascadeAbortError,
            langIsEn, llmInputImages, llmInputText, llmInputVideos, ltxDirectorBuildTimelinePayload,
            ltxDirectorSyncSeconds, ltxDirectorTimelineSegments, makePending, manualVideoUrlForNode, mediaKindForRef,
            mergeGeneratedOutputs, miniMaxApplyRunningHubParams, miniMaxBuildRunningHubNodeInfoList, miniMaxBuildRunningHubWorkflowExtras, miniMaxDynamicParams,
            miniMaxLogError, miniMaxReadableError, miniMaxRefsForNode, miniMaxRefsForSegment, miniMaxRunningHubPayloadError,
            miniMaxRunningHubSettings, miniMaxSelectedSegment, miniMaxSetSegmentResult, noReturnedImage, normalizeCanvasTaskError,
            normalizedImageQuality, nowMs, orderedSources, outputUrlValue, pendingById,
            pendingPreviewSizeForRun, providerById, providerIdForPending, refreshNodes, requestMetaFromResult,
            resolveChatModel, resolveChatProviderId, resolveImageModel, resolveImageProviderId, resolveMidjourneyProviderId,
            rhActiveFields, rhBuildNodeInfoList, rhBuildWorkflowRequestExtras, rhCurrentEntry, rhCurrentKind,
            rhMediaSources, rhSelectedEntryRef, runningHubEntryLabel, saveCanvas, scheduleSave,
            setStatus, shouldCreateOutputForNode, showErrorModal, sleep, tempShUploadedUrlForNode,
            tr, uid, validComfyWorkflowName, videoRefsOnly,
            getNodes: () => nodes,
            getConnections: () => connections,
            getComfyWorkflows: () => comfyWorkflows,
        });
    }
    return classicExecutorRuntime;
}





// Wave 14: `runMsGenNode` (ModelScope generate) has had no page-side
// implementation since an early refactor, but the cascade seam declares it
// REQUIRED and dispatches msgen nodes through it. ModelScope is an API
// image provider, and `runGenerator` is the API generator runner, so we
// forward to it instead of leaving the cascade factory unable to resolve
// the identifier (which would ReferenceError on every cascade start).
async function runMsGenNode(nodeId, opts={}){ return runGenerator(nodeId, opts); }

async function runLTXDirectorNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runLTXDirectorNode(nodeId, opts); }

// runCanvasGenerate is the shared "run this node" entrypoint used by the
// card-body / comfy / runninghub / ltx / video seams. Wave 14 moved its body
// into the cascade seam, so the page keeps a thin forwarding wrapper.
// (bindCascadeButtons' 2-arg page wrapper lives with the other Wave 14
// wrappers; the seam's bindCascadeButtons reads {wrap, nodeId}.)
function runCanvasGenerate(nodeId, opts){ return ensureClassicCascadeOrchestrator().runCanvasGenerate({nodeId: nodeId, opts: opts || {}}); }

// ── Thin page-side wrappers for Wave 11 / 13 / 14 / 8 ──
// Wave 11: vpp shorthand + sanitizeVideoNodeProviderModel / videoProviderOptions / videoModelOptions
// Wave 13: addGenerationLog / renderCanvasLog (page-side, called by 22 callers)
// Wave 14: beginCascade / cancelCascade / computeCascadeOrder / isCascadeActive / etc.
// Wave 8-9: destroyLTXEditor + onCardDestroy pattern

function sanitizeVideoNodeProviderModel(node){
    if(!node || node.type !== 'video') return;
    node.apiProvider = vpp.resolveVideoProviderId({id: node.apiProvider || 'comfly'});
    const models = vpp.providerVideoModels({providerId: node.apiProvider});
    if(!models.length) node.model = '';
    else if(!models.includes(node.model)) node.model = models[0] || '';
}
function videoModelOptions(selectedModel, providerId){
    const models = vpp.providerVideoModels({providerId: providerId});
    if(!models.length){
        return '<option value="" disabled selected>' + (tr('canvas.noModelsHint') || '暂无模型，请到 API 设置添加') + '</option>';
    }
    const selected = selectedModel || models[0];
    return uniqueModels([selected, ...models]).filter(Boolean).map(model => '<option value="' + escapeHtml(model) + '" ' + (model === selected ? 'selected' : '') + '>' + escapeHtml(model) + '</option>').join('');
}

// Wave 13 thin wrappers (page-side, called by 22 callers)
function addGenerationLog(arg){
    ensureClassicGenerationLog().addGenerationLog(arg);
}
function renderCanvasLog(){
    ensureClassicGenerationLog().renderCanvasLog();
}

// Wave 14 thin wrappers (page-side shorthand for cascade orchestrator)


// ── Restored page-side helper (required as a host op by its seam) ──
function currentRunningHubWorkflowEntry(node){
    const workflowId = validRunningHubWorkflowId(node?.workflowId || '');
    if(!workflowId) return null;
    return runningHubEntries('workflow').find(workflow => runningHubEntryId(workflow, 'workflow') === workflowId) || null;
}

// ── Restored page-side helper (required as a host op by its seam) ──
function defaultLTXSegment(start=0, length=120){
    return {
        id:uid('ltxseg'),
        type:'text',
        prompt:'',
        start,
        length,
        color:LTX_SEGMENT_COLORS[0],
        strength:1,
        imageRef:null
    };
}

// ── Restored page-side helper (required as a host op by its seam) ──
function ltxDirectorSyncSeconds(node){
    const fps = Math.max(1, Number(node?.frameRate) || 24);
    node.durationSeconds = Math.round((Number(node.durationFrames) || 120) / fps * 1000) / 1000;
}

// ── Restored page-side helpers (review repair 2026-09-07): the Wave 7-14
// reapply deleted these three compositions page-side while runLTXDirectorNode
// / ltxSyncConnectedImagesToTimeline still call them. They are page-owned
// compositions over the LTX seam (parse/flush/buildContiguousRelay) plus the
// page's Comfy upload transport, so they stay here verbatim from HEAD —
// only the deleted seam-owned calls are rerouted through the seam handle. ──
function ltxDirectorTimelineSegments(node){
    ensureClassicLtxControls().flushTimelineToNode({node});
    if(node?._ltxEditor?.timeline?.segments) return node._ltxEditor.timeline.segments;
    try {
        const t = JSON.parse(node.ltxTimelineData || '{}');
        return t.segments || [];
    } catch(e) {
        return [];
    }
}
function ltxRefreshTimelineEditor(node){
    if(!node?._ltxEditor || typeof window.LTXParseInitial !== 'function') return;
    node._ltxEditor.timeline = window.LTXParseInitial(node.ltxTimelineData || '{}');
    node._ltxEditor.loadImages?.();
    node._ltxEditor.commitChanges?.(true);
    node._ltxEditor.render?.();
}
async function ltxDirectorBuildTimelinePayload(node, globalPromptFallback=''){
    ltxDirectorSyncSeconds(node);
    let timeline = {segments: [], audioSegments: []};
    try { timeline = JSON.parse(node.ltxTimelineData || '{}'); } catch(e) {}
    const relay = ensureClassicLtxControls().buildContiguousRelay({node, globalPromptFallback});
    const segments = [...relay.sortedSegments];
    for(const seg of segments){
        if(seg.type === 'image' && !seg.imageFile){
            const url = seg.imageB64 || '';
            if(url){
                const fullUrl = url.startsWith('http') ? url : (location.origin + (url.startsWith('/') ? url : '/' + url));
                seg.imageFile = await uploadCanvasUrlToComfy(fullUrl);
            }
        }
        if(seg.imgObj) delete seg.imgObj;
    }
    const timelineJson = JSON.stringify({segments, audioSegments: timeline.audioSegments || []});
    node.ltxLocalPrompts = relay.local_prompts;
    node.ltxSegmentLengths = relay.segment_lengths;
    node.ltxGuideStrength = relay.guide_strength;
    node.ltxTimelineData = timelineJson;
    return {
        global_prompt:(globalPromptFallback || node.globalPrompt || '').trim(),
        duration_frames:Number(node.durationFrames) || 120,
        duration_seconds:Number(node.durationSeconds) || 5,
        timeline_data:timelineJson,
        local_prompts:relay.local_prompts,
        segment_lengths:relay.segment_lengths,
        guide_strength:relay.guide_strength,
        epsilon:Number(node.epsilon) || 0.001,
        frame_rate:Number(node.frameRate) || 24,
        use_custom_audio:Boolean(node.useCustomAudio),
        display_mode:node.displayMode || 'seconds',
        custom_width:Math.max(0, Number(node.customWidth) || 0),
        custom_height:Math.max(0, Number(node.customHeight) || 0),
        resize_method:'maintain aspect ratio',
        divisible_by:Math.max(1, Number(node.divisibleBy) || 32),
        img_compression:Number(node.imgCompression) ?? 18,
        timeline_ui:''
    };
}

// ── Restored page-side helper (required as a host op by its seam) ──
function ltxSyncConnectedImagesToTimeline(node){
    if(!node || node.type !== 'ltxDirector') return;
    const hadTimeline = Boolean(node.ltxTimelineData);
    const sources = orderedSources(node, generatorSources(node));
    const imageInputs = sources.filter(src => imageRefsOnly(src.refs || []).length);
    const timeline = ensureClassicLtxControls().parseTimeline({node});
    const fps = Math.max(1, Number(node.frameRate) || 24);
    const defaultLen = Math.max(6, fps);
    const manual = (timeline.segments || []).filter(s => !s.canvasSourceId);
    const existingAuto = new Map((timeline.segments || []).filter(s => s.canvasSourceId).map(s => [s.canvasSourceId, s]));
    const autoSegs = [];
    let cursor = 0;
    for(const src of imageInputs){
        const ref = imageRefsOnly(src.refs || [])[0];
        const url = ref?.url;
        if(!url) continue;
        let seg = existingAuto.get(src.id);
        if(seg){
            if(seg.imageB64 !== url){
                seg.imageB64 = url;
                seg.imageFile = null;
                delete seg.imgObj;
            }
            if(!seg.length || seg.length < 1) seg.length = defaultLen;
        } else {
            seg = {
                id:uid('ltxseg'),
                start:cursor,
                length:defaultLen,
                prompt:src.prompt || '',
                type:'image',
                imageB64:url,
                canvasSourceId:src.id,
                guideStrength:1
            };
        }
        seg.start = cursor;
        cursor += Math.max(1, Number(seg.length) || defaultLen);
        autoSegs.push(seg);
    }
    let nextStart = cursor;
    const reflowedManual = [...manual].sort((a, b) => (Number(a.start) || 0) - (Number(b.start) || 0));
    for(const seg of reflowedManual){
        seg.start = nextStart;
        nextStart += Math.max(1, Number(seg.length) || defaultLen);
    }
    const allSegs = [...autoSegs, ...reflowedManual];
    const maxEnd = allSegs.reduce((m, s) => Math.max(m, (Number(s.start) || 0) + (Number(s.length) || 0)), 0);
    if(maxEnd > (Number(node.durationFrames) || 0)){
        node.durationFrames = Math.ceil(maxEnd);
        ltxDirectorSyncSeconds(node);
    }
    const prevTimeline = node.ltxTimelineData;
    node.ltxTimelineData = JSON.stringify({segments: allSegs, audioSegments: timeline.audioSegments || []});
    ltxRefreshTimelineEditor(node);
    if(hadTimeline && node.ltxTimelineData !== prevTimeline) scheduleSave();
}

// ── Restored page-side helper (required as a host op by its seam) ──
function bindLTXParamsRow(container, node){
    const row = container.querySelector('[data-ltx-params]');
    if(!row) return;
    const fps = () => Math.max(1, Number(node.frameRate) || 24);
    const bindNum = (sel, apply) => {
        const inp = row.querySelector(sel);
        if(!inp) return;
        inp.onmousedown = e => e.stopPropagation();
        inp.onclick = e => e.stopPropagation();
        inp.onchange = () => {
            apply(inp);
            ltxDirectorSyncSeconds(node);
            if(node._ltxEditor){
                node._ltxEditor.commitChanges?.(true);
                node._ltxEditor.render?.();
            }
            scheduleSave();
        };
    };
    const sec = row.querySelector('[data-ltx-duration-seconds]');
    const frames = row.querySelector('[data-ltx-duration-frames]');
    const rate = row.querySelector('[data-ltx-frame-rate]');
    const width = row.querySelector('[data-ltx-width]');
    const height = row.querySelector('[data-ltx-height]');
    if(sec) sec.value = Number(node.durationSeconds) || 5;
    if(frames) frames.value = Number(node.durationFrames) || 120;
    if(rate) rate.value = Number(node.frameRate) || 24;
    if(width) width.value = Number(node.customWidth) || 0;
    if(height) height.value = Number(node.customHeight) || 0;
    bindNum('[data-ltx-duration-seconds]', inp => {
        const v = Math.max(0.1, Math.min(1000, parseFloat(inp.value) || node.durationSeconds || 5));
        node.durationSeconds = Math.round(v * 1000) / 1000;
        node.durationFrames = Math.max(1, Math.round(node.durationSeconds * fps()));
        inp.value = node.durationSeconds;
        if(frames) frames.value = node.durationFrames;
    });
    bindNum('[data-ltx-duration-frames]', inp => {
        node.durationFrames = Math.max(1, Math.min(10000, parseInt(inp.value, 10) || 120));
        if(sec) sec.value = Math.round((node.durationFrames / fps()) * 1000) / 1000;
        inp.value = node.durationFrames;
    });
    bindNum('[data-ltx-frame-rate]', inp => {
        node.frameRate = Math.max(1, Math.min(240, parseInt(inp.value, 10) || 24));
        if(sec) sec.value = Math.round((node.durationFrames / fps()) * 1000) / 1000;
    });
    bindNum('[data-ltx-width]', inp => {
        node.customWidth = Math.max(0, Math.min(8192, parseInt(inp.value, 10) || 0));
        inp.value = node.customWidth;
    });
    bindNum('[data-ltx-height]', inp => {
        node.customHeight = Math.max(0, Math.min(8192, parseInt(inp.value, 10) || 0));
        inp.value = node.customHeight;
    });
}

// ── Restored page-side helper (required as a host op by its seam) ──
function updateLTXNodeElementSize(node){
    const el = document.querySelector(`.node[data-id="${CSS.escape(node.id)}"]`);
    if(!el) return;
    if(node.w) el.style.width = `${node.w}px`;
    if(node.h) el.style.height = `${node.h}px`;
    refreshGeometryAfterLayout();
}

// ── loopContext mirror ──
// The authoritative cascade loop context now lives inside the
// classic-cascade-orchestrator seam closure. The seam pushes each round's
// context back out through `setLoopContextMirror` so the page-side
// render helpers below (which default `ctx = loopContext`) keep seeing it.
let loopContext = null;
function setLoopContextMirror(value){ loopContext = value || null; }
