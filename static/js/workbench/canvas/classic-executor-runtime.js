/*
 * static/js/workbench/canvas/classic-executor-runtime.js
 *
 * Wave 16a of R4-38 — bounded compat seam for the Classic executor /
 * transport surface: the run*Node executors (generator / midjourney /
 * msgen / comfy / runninghub / video / minimax / llm / ltx director),
 * their API transports (callCanvasLLM / midjourneyRequest /
 * createCanvas*Task / poll* / wait* / fail*), the Comfy upload path,
 * and the run-metadata helpers (runSnapshot / runTaskLabel /
 * runPlatformLabel / makePendingForRun / outputForNode /
 * refreshRunNodes).
 *
 * The function bodies are the page originals, byte-for-byte except
 * that the three mutable page bindings (nodes / connections /
 * comfyWorkflows) become host getters. Every other page-local they
 * use is host-injected via REQUIRED_OPS. canvas.js keeps a 1-line
 * wrapper per function, so all callers — page dispatchers, button
 * handlers, and the other seams' host-op injections (cascade / ltx /
 * minimax / generation-log / card-body) — keep working unchanged.
 *
 * R8 owns the real ExecutionRuntime; this is bounded COMPAT per the
 * R4-31 inventory (cascade/execution category).
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        'API_RATIO_VALUES', 'CANVAS_REFERENCE_IMAGE_MAX', 'CLIENT_ID', 'LTX_DIRECTOR_SEED_NODE', 'LTX_DIRECTOR_WF_NODE',
        'LTX_DIRECTOR_WORKFLOW', 'actionFailed', 'activeCanvasTaskPolls', 'addGenerationLog', 'appendOutputImages',
        'applyUploadedUrlToRefs', 'audioRefsOnly', 'cascadeAbortError', 'cascadeBackendRestartMessage', 'cascadeFetch',
        'cascadeStopMessage', 'cascadeTargetIdFromOptions', 'clearStuckGeneratorRunning', 'collectRunMeta', 'collectRunMetas',
        'comfyFieldKind', 'comfyFields', 'comfyNameForRef', 'comfyParamValue', 'comfyRandomActive',
        'comfyRandomEnabled', 'comfyRandomValue', 'comfyRunLabel', 'completeCanvasImageTask', 'completeMidjourneyRun',
        'ensureCascadeActive', 'ensureClassicCascadeOrchestrator', 'ensureClassicExecutionHost', 'ensureClassicLtxControls', 'ensureClassicMiniMaxControls',
        'ensureClassicVideoProviderParams', 'ensureComfyWorkflow', 'ensureRhNodeSelection', 'ensureRunningHubWorkflowConfigForNode', 'extractUpstreamTaskId',
        'findPendingTask', 'generatorSizeForRun', 'generatorSources', 'imageRefsOnly', 'isCascadeAbortError',
        'langIsEn', 'llmInputImages', 'llmInputText', 'llmInputVideos', 'ltxDirectorBuildTimelinePayload',
        'ltxDirectorSyncSeconds', 'ltxDirectorTimelineSegments', 'makePending', 'manualVideoUrlForNode', 'mediaKindForRef',
        'mergeGeneratedOutputs', 'miniMaxApplyRunningHubParams', 'miniMaxBuildRunningHubNodeInfoList', 'miniMaxBuildRunningHubWorkflowExtras', 'miniMaxDynamicParams',
        'miniMaxLogError', 'miniMaxReadableError', 'miniMaxRefsForNode', 'miniMaxRefsForSegment', 'miniMaxRunningHubPayloadError',
        'miniMaxRunningHubSettings', 'miniMaxSelectedSegment', 'miniMaxSetSegmentResult', 'noReturnedImage', 'normalizeCanvasTaskError',
        'normalizedImageQuality', 'nowMs', 'orderedSources', 'outputUrlValue', 'pendingById',
        'pendingPreviewSizeForRun', 'providerById', 'providerIdForPending', 'refreshNodes', 'requestMetaFromResult',
        'resolveChatModel', 'resolveChatProviderId', 'resolveImageModel', 'resolveImageProviderId', 'resolveMidjourneyProviderId',
        'rhActiveFields', 'rhBuildNodeInfoList', 'rhBuildWorkflowRequestExtras', 'rhCurrentEntry', 'rhCurrentKind',
        'rhMediaSources', 'rhSelectedEntryRef', 'runningHubEntryLabel', 'saveCanvas', 'scheduleSave',
        'setStatus', 'shouldCreateOutputForNode', 'showErrorModal', 'sleep', 'tempShUploadedUrlForNode',
        'tr', 'uid', 'validComfyWorkflowName', 'videoRefsOnly', 'getNodes',
        'getConnections', 'getComfyWorkflows',
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicExecutorRuntime.create: host must be an object');
        }
        for (var k = 0; k < REQUIRED_OPS.length; k++) {
            if (typeof host[REQUIRED_OPS[k]] === 'undefined') {
                throw new TypeError('WorkbenchCanvasClassicExecutorRuntime.create: missing required host op "' + REQUIRED_OPS[k] + '"');
            }
        }

        var API_RATIO_VALUES = host.API_RATIO_VALUES, CANVAS_REFERENCE_IMAGE_MAX = host.CANVAS_REFERENCE_IMAGE_MAX, CLIENT_ID = host.CLIENT_ID, LTX_DIRECTOR_SEED_NODE = host.LTX_DIRECTOR_SEED_NODE, LTX_DIRECTOR_WF_NODE = host.LTX_DIRECTOR_WF_NODE, LTX_DIRECTOR_WORKFLOW = host.LTX_DIRECTOR_WORKFLOW;
        var actionFailed = host.actionFailed, activeCanvasTaskPolls = host.activeCanvasTaskPolls, addGenerationLog = host.addGenerationLog, appendOutputImages = host.appendOutputImages, applyUploadedUrlToRefs = host.applyUploadedUrlToRefs, audioRefsOnly = host.audioRefsOnly;
        var cascadeAbortError = host.cascadeAbortError, cascadeBackendRestartMessage = host.cascadeBackendRestartMessage, cascadeFetch = host.cascadeFetch, cascadeStopMessage = host.cascadeStopMessage, cascadeTargetIdFromOptions = host.cascadeTargetIdFromOptions, clearStuckGeneratorRunning = host.clearStuckGeneratorRunning;
        var collectRunMeta = host.collectRunMeta, collectRunMetas = host.collectRunMetas, comfyFieldKind = host.comfyFieldKind, comfyFields = host.comfyFields, comfyNameForRef = host.comfyNameForRef, comfyParamValue = host.comfyParamValue;
        var comfyRandomActive = host.comfyRandomActive, comfyRandomEnabled = host.comfyRandomEnabled, comfyRandomValue = host.comfyRandomValue, comfyRunLabel = host.comfyRunLabel, completeCanvasImageTask = host.completeCanvasImageTask, completeMidjourneyRun = host.completeMidjourneyRun;
        var ensureCascadeActive = host.ensureCascadeActive, ensureClassicCascadeOrchestrator = host.ensureClassicCascadeOrchestrator, ensureClassicExecutionHost = host.ensureClassicExecutionHost, ensureClassicLtxControls = host.ensureClassicLtxControls, ensureClassicMiniMaxControls = host.ensureClassicMiniMaxControls, ensureClassicVideoProviderParams = host.ensureClassicVideoProviderParams;
        var ensureComfyWorkflow = host.ensureComfyWorkflow, ensureRhNodeSelection = host.ensureRhNodeSelection, ensureRunningHubWorkflowConfigForNode = host.ensureRunningHubWorkflowConfigForNode, extractUpstreamTaskId = host.extractUpstreamTaskId, findPendingTask = host.findPendingTask, generatorSizeForRun = host.generatorSizeForRun;
        var generatorSources = host.generatorSources, imageRefsOnly = host.imageRefsOnly, isCascadeAbortError = host.isCascadeAbortError, langIsEn = host.langIsEn, llmInputImages = host.llmInputImages, llmInputText = host.llmInputText;
        var llmInputVideos = host.llmInputVideos, ltxDirectorBuildTimelinePayload = host.ltxDirectorBuildTimelinePayload, ltxDirectorSyncSeconds = host.ltxDirectorSyncSeconds, ltxDirectorTimelineSegments = host.ltxDirectorTimelineSegments, makePending = host.makePending, manualVideoUrlForNode = host.manualVideoUrlForNode;
        var mediaKindForRef = host.mediaKindForRef, mergeGeneratedOutputs = host.mergeGeneratedOutputs, miniMaxApplyRunningHubParams = host.miniMaxApplyRunningHubParams, miniMaxBuildRunningHubNodeInfoList = host.miniMaxBuildRunningHubNodeInfoList, miniMaxBuildRunningHubWorkflowExtras = host.miniMaxBuildRunningHubWorkflowExtras, miniMaxDynamicParams = host.miniMaxDynamicParams;
        var miniMaxLogError = host.miniMaxLogError, miniMaxReadableError = host.miniMaxReadableError, miniMaxRefsForNode = host.miniMaxRefsForNode, miniMaxRefsForSegment = host.miniMaxRefsForSegment, miniMaxRunningHubPayloadError = host.miniMaxRunningHubPayloadError, miniMaxRunningHubSettings = host.miniMaxRunningHubSettings;
        var miniMaxSelectedSegment = host.miniMaxSelectedSegment, miniMaxSetSegmentResult = host.miniMaxSetSegmentResult, noReturnedImage = host.noReturnedImage, normalizeCanvasTaskError = host.normalizeCanvasTaskError, normalizedImageQuality = host.normalizedImageQuality, nowMs = host.nowMs;
        var orderedSources = host.orderedSources, outputUrlValue = host.outputUrlValue, pendingById = host.pendingById, pendingPreviewSizeForRun = host.pendingPreviewSizeForRun, providerById = host.providerById, providerIdForPending = host.providerIdForPending;
        var refreshNodes = host.refreshNodes, requestMetaFromResult = host.requestMetaFromResult, resolveChatModel = host.resolveChatModel, resolveChatProviderId = host.resolveChatProviderId, resolveImageModel = host.resolveImageModel, resolveImageProviderId = host.resolveImageProviderId;
        var resolveMidjourneyProviderId = host.resolveMidjourneyProviderId, rhActiveFields = host.rhActiveFields, rhBuildNodeInfoList = host.rhBuildNodeInfoList, rhBuildWorkflowRequestExtras = host.rhBuildWorkflowRequestExtras, rhCurrentEntry = host.rhCurrentEntry, rhCurrentKind = host.rhCurrentKind;
        var rhMediaSources = host.rhMediaSources, rhSelectedEntryRef = host.rhSelectedEntryRef, runningHubEntryLabel = host.runningHubEntryLabel, saveCanvas = host.saveCanvas, scheduleSave = host.scheduleSave, setStatus = host.setStatus;
        var shouldCreateOutputForNode = host.shouldCreateOutputForNode, showErrorModal = host.showErrorModal, sleep = host.sleep, tempShUploadedUrlForNode = host.tempShUploadedUrlForNode, tr = host.tr, uid = host.uid;
        var validComfyWorkflowName = host.validComfyWorkflowName, videoRefsOnly = host.videoRefsOnly;
        var getNodes = host.getNodes, getConnections = host.getConnections, getComfyWorkflows = host.getComfyWorkflows;

        // ── Executor + transport bodies (page originals; see header) ──

async function responseErrorMessage(response, fallback='请求失败'){
    return window.WorkbenchCanvasHttpError.responseMessage(response, fallback);
}

async function runLTXDirectorNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || node.type !== 'ltxDirector') return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    clearStuckGeneratorRunning(node);
    if(node.running && !opts.cascade) return;
    ensureClassicLtxControls().flushTimelineToNode({node});
    const sources = orderedSources(node, generatorSources(node));
    const upstreamPrompt = sources.map(s => s.prompt).filter(Boolean).join('\n\n');
    const globalPrompt = [node.globalPrompt, upstreamPrompt].filter(Boolean).join('\n\n').trim();
    const segments = ltxDirectorTimelineSegments(node);
    const hasSegPrompt = segments.some(s => (s.prompt || '').trim());
    const hasImageSeg = segments.some(s => s.type === 'image' && (s.imageFile || s.imageB64));
    if(!globalPrompt && !hasSegPrompt && !hasImageSeg){
        const msg = tr('canvas.needPromptOrImage');
        setStatus(msg);
        showErrorModal(msg, tr('canvas.ltxFailed'));
        return;
    }
    if(segments.some(s => s.type === 'image' && !s.imageFile && !s.imageB64)){
        const msg = tr('canvas.ltxImageSegNeedRef');
        setStatus(msg);
        showErrorModal(msg, tr('canvas.ltxFailed'));
        return;
    }
    ltxDirectorSyncSeconds(node);
    let out = outputForNode(node, 520);
    const pendingId = uid('p');
    const refs = sources.flatMap(s => s.refs || []);
    const run = runSnapshot(node, globalPrompt || segments.map(s => s.prompt).join(' | '), refs);
    run.taskLabel = tr('canvas.ltxDirector');
    if(out) out._pending = [...(out._pending || []), makePendingForRun(pendingId, run, node, {refs, cascadeTargetId})];
    if(!opts.cascade){
        node.running = true;
        refreshRunNodes(node, out);
        setStatus(tr('canvas.ltxRunning'));
    } else {
        refreshRunNodes(node, out);
    }
    try {
        const directorInputs = await ltxDirectorBuildTimelinePayload(node, globalPrompt);
        const params = {
            [LTX_DIRECTOR_WF_NODE]:directorInputs,
            [LTX_DIRECTOR_SEED_NODE]:{noise_seed:Number(node.noiseSeed ?? 12)}
        };
        const result = await runQueuedComfyGenerate({
            prompt:globalPrompt,
            workflow_json:LTX_DIRECTOR_WORKFLOW,
            params,
            type:'ltx-director',
            client_id:CLIENT_ID
        }, {cascadeTargetId});
        run.request = requestMetaFromResult(result);
        if(result.error) throw new Error(result.error);
        const outputs = window.WorkbenchCanvasMediaResultNormalizer.extract(result);
        if(!outputs.length) throw new Error(tr('canvas.ltxNoOutput'));
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        appendOutputImages(out, outputs, refs[0], [meta]);
        mergeGeneratedOutputs(node, outputs, Boolean(opts.cascade));
        addGenerationLog({run, outputs, runMs:meta.runMs || 0});
        node.runStatus = 'done';
        node.runError = '';
        refreshRunNodes(node, out);
        scheduleSave();
    } catch(err) {
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        addGenerationLog({run, outputs:[], runMs:meta.runMs || 0, error:err.message || String(err)});
        if(isCascadeAbortError(err)){
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed';
        node.runError = err.message || String(err);
        refreshRunNodes(node, out);
        if(opts.cascade) throw err;
        showErrorModal(err.message || tr('canvas.ltxFailed'), tr('canvas.ltxFailed'));
    } finally {
        if(!opts.cascade){
            node.running = false;
            refreshRunNodes(node, out);
        }
    }
}

function rhUseWallet(node){
    return node?.rhPayment === 'wallet';
}

async function runRhNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    ensureRhNodeSelection(node);
    const mode = rhCurrentKind(node);
    if(mode === 'model') return runRhModelNode(node, opts);
    node.rhRandomValues = {};
    if(mode === 'workflow' && !String(node.workflowId || '').trim()){ alert(tr('canvas.rhNeedWorkflowId')); return; }
    if(mode === 'app' && !String(node.webappId || '').trim()){ alert(tr('canvas.rhNeedWebappId')); return; }
    const selectedEntry = rhCurrentEntry(node);
    if(!selectedEntry){
        alert(mode === 'workflow' ? '请先在 API 设置里添加 RunningHub 工作流' : '请先在 API 设置里添加 RunningHub 应用');
        return;
    }
    if(mode === 'workflow') await ensureRunningHubWorkflowConfigForNode(node);
    if(!rhActiveFields(node).length){
        alert(mode === 'workflow' ? '请先在 API 设置里编辑并保存这个 RunningHub 工作流参数' : '请先在 API 设置里编辑并保存这个 RunningHub 应用参数');
        return;
    }
    const media = rhMediaSources(node);
    let out = outputForNode(node, 500);
    const pendingId = uid('p');
    const run = runSnapshot(node, media.prompt || 'RunningHub', media.refs);
    run.taskLabel = 'RunningHub';
    if(out) out._pending = [...(out._pending || []), makePendingForRun(pendingId, run, node, {refs:media.refs, cascadeTargetId})];
    if(!opts.cascade) node.running = true;
    refreshRunNodes(node, out);
    try {
        const nodeInfoList = await rhBuildNodeInfoList(node, media);
        const workflowExtras = mode === 'workflow' ? await rhBuildWorkflowRequestExtras(node, media, nodeInfoList) : {};
        const endpoint = mode === 'workflow' ? '/api/runninghub/workflow-submit' : '/api/runninghub/submit';
        const body = mode === 'workflow'
            ? {workflowId:node.workflowId.trim(), nodeInfoList, useWallet:rhUseWallet(node), ...workflowExtras}
            : {webappId:node.webappId.trim(), nodeInfoList, instanceType:node.instanceType || '', useWallet:rhUseWallet(node)};
        const submit = await cascadeFetch(endpoint, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(body)
        }, {cascadeTargetId}).then(async r => {
            const data = await r.json();
            if(!r.ok || data.success === false) throw new Error(data.detail || data.error || tr('canvas.rhFailed'));
            return data.data || data;
        });
        const taskId = submit.taskId;
        if(!taskId) throw new Error(tr('canvas.rhNoTaskId'));
        const useWallet = rhUseWallet(node);
        run.request = {task_id:taskId, webappId:node.webappId, workflowId:node.workflowId, backend:'runninghub', mode, useWallet};
        let result = null;
        for(let i = 0; i < 720; i++){
            if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
            await sleep(2500);
            const data = await cascadeFetch(`/api/runninghub/query?taskId=${encodeURIComponent(taskId)}&useWallet=${useWallet ? '1' : '0'}`, {}, {cascadeTargetId}).then(async r => {
                const json = await r.json();
                if(!r.ok || json.success === false) throw new Error(json.detail || json.error || tr('canvas.rhFailed'));
                return json.data || json;
            });
            if(data.status === 'SUCCESS'){
                result = data;
                break;
            }
            if(data.status === 'FAILED') throw new Error(data.failReason || tr('canvas.rhFailed'));
        }
        if(!result) throw new Error(tr('canvas.rhTimeout'));
        const outputs = result.urls || [];
        if(!outputs.length) throw new Error(tr('canvas.rhOutputsEmpty'));
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        appendOutputImages(out, outputs, media.refs[0], [meta]);
        mergeGeneratedOutputs(node, outputs, Boolean(opts.cascade));
        addGenerationLog({run, outputs, runMs:meta.runMs || 0});
        node.runStatus = 'done';
        node.runError = '';
        refreshRunNodes(node, out);
        scheduleSave();
    } catch(err) {
        const meta = collectRunMeta(out, pendingId);
        addGenerationLog({run, outputs:[], runMs:meta.runMs || 0, error:err.message || String(err)});
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        if(isCascadeAbortError(err)){
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed';
        node.runError = err.message || String(err);
        refreshRunNodes(node, out);
        if(opts.cascade) throw err;
        alert(err.message || tr('canvas.rhFailed'));
    } finally {
        node.running = false;
        refreshRunNodes(node, out);
    }
}

async function runRhModelNode(node, opts={}){
    if(!node || (node.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const selectedRef = rhSelectedEntryRef(node);
    const model = selectedRef?.id || node.rhModel || node.model || '';
    if(!model){
        alert('请先在 API 设置里添加 RunningHub 模型 API');
        return;
    }
    node.rhModel = model;
    node.model = model;
    node.apiProvider = 'runninghub';
    const media = rhMediaSources(node);
    const prompt = media.prompt || '';
    const refs = imageRefsOnly(media.refs || []);
    if(!prompt && !refs.length){ alert(tr('canvas.needPromptOrImage')); return; }
    const count = Math.max(1, Math.min(8, Number(node.count || 1)));
    let out = outputForNode(node, 500);
    const run = runSnapshot(node, prompt || 'Edit the reference images.', refs);
    run.taskLabel = 'RunningHub';
    const payload = {
        prompt:prompt || 'Edit the reference images.',
        provider_id:'runninghub',
        model,
        size:await generatorSizeForRun(node, refs),
        reference_images:refs.slice(0, CANVAS_REFERENCE_IMAGE_MAX)
    };
    const quality = normalizedImageQuality(node.quality);
    if(quality) payload.quality = quality;
    let pendingIds = [];
    const startedAt = nowMs();
    if(!opts.cascade){
        node.running = true;
        refreshRunNodes(node, out);
        setTimeout(() => { node.running = false; refreshRunNodes(node, out); }, 2000);
    }
    try {
        const taskInfos = await Promise.all(Array.from({length:count}, () => createCanvasImageTask(payload, {cascadeTargetId})));
        if(!out){
            let outputs = [];
            for(const task of taskInfos){
                const result = await waitCanvasImageTaskResult(task.task_id, {cascadeTargetId});
                outputs.push(...(result.images || []));
                run.request = requestMetaFromResult(result);
            }
            if(!outputs.length) throw new Error(tr('canvas.generationFailed'));
            mergeGeneratedOutputs(node, outputs, Boolean(opts.cascade));
            addGenerationLog({run, outputs, runMs:nowMs() - startedAt});
            node.runStatus = 'done';
            node.runError = '';
            node.running = false;
            refreshRunNodes(node, out);
            scheduleSave();
            return;
        }
        pendingIds = taskInfos.map(() => uid('p'));
        out._pending = [
            ...(out._pending || []),
            ...taskInfos.map((task, index) => makePendingForRun(pendingIds[index], run, node, {refs, requestSize:payload.size, cascadeTargetId}, {
                canvasTaskId:task.task_id,
                canvasTaskType:'online-image',
                providerId:payload.provider_id,
                model:payload.model,
                appendGenerated:Boolean(opts.cascade)
            }))
        ];
        refreshRunNodes(node, out);
        scheduleSave();
        await saveCanvas();
        const statuses = await Promise.all(taskInfos.map(task => pollCanvasImageTask(task.task_id, {cascadeTargetId})));
        if(statuses.includes('aborted')) throw cascadeAbortError(cascadeStopMessage());
        if(statuses.includes('failed')) throw new Error(node.runError || tr('canvas.generationFailed'));
    } catch(err) {
        const remainingPending = pendingIds.map(id => pendingById(out, id)).filter(Boolean);
        const removableIds = remainingPending.filter(p => !(p.failed && p.recoverTaskId)).map(p => p.id);
        if(removableIds.length){
            const metas = collectRunMetas(out, removableIds);
            addGenerationLog({run, outputs:[], runMs:Math.max(...metas.map(m => m.runMs || 0), 0), error:err.message || String(err)});
            if(out) out._pending = (out._pending || []).filter(p => !removableIds.includes(p.id));
        }
        if(isCascadeAbortError(err)){
            node.running = false;
            refreshRunNodes(node, out);
            scheduleSave();
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed';
        node.runError = err.message || String(err);
        node.running = false;
        refreshRunNodes(node, out);
        scheduleSave();
        if(remainingPending.some(p => p.failed && p.recoverTaskId) && !removableIds.length) return;
        if(opts.cascade) throw err;
        showErrorModal(err.message || tr('canvas.generationFailed'), tr('canvas.apiFailed'));
    }
}

async function runGenerator(genId, opts={}){
    const gen = getNodes().find(n => n.id === genId);
    if(!gen || (gen.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const sources = orderedSources(gen, generatorSources(gen));
    const prompt = sources.map(s => s.prompt).filter(Boolean).join('\n\n');
    const refs = imageRefsOnly(sources.flatMap(s => s.refs || []));
    if(!prompt && !refs.length){ alert(tr('canvas.needPromptOrImage')); return; }
    const count = Math.max(1, Math.min(8, Number(gen.count || 1)));
    let out = outputForNode(gen, 460);
    const run = runSnapshot(gen, prompt || 'Edit the reference images.', refs);
    const payload = {
        prompt: prompt || 'Edit the reference images.',
        provider_id:resolveImageProviderId(gen.apiProvider || 'comfly'),
        model:resolveImageModel(gen.model),
        size:await generatorSizeForRun(gen, refs),
        reference_images:refs.slice(0, CANVAS_REFERENCE_IMAGE_MAX)
    };
    const quality = normalizedImageQuality(gen.quality);
    if(quality) payload.quality = quality;
    let pendingIds = [];
    const startedAt = nowMs();
    if(!opts.cascade){
        gen.running = true;
        refreshRunNodes(gen, out);
        // API 支持并发：2s 后即可再次点击，任务仍由 pending 卡片继续追踪
        setTimeout(() => { gen.running = false; refreshRunNodes(gen, out); }, 2000);
    }
    try {
        const taskInfos = await Promise.all(Array.from({length:count}, () => createCanvasImageTask(payload, {cascadeTargetId})));
        if(!out){
            let outputs = [];
            for(const task of taskInfos){
                const result = await waitCanvasImageTaskResult(task.task_id, {cascadeTargetId});
                outputs.push(...(result.images || []));
                run.request = requestMetaFromResult(result);
            }
            if(!outputs.length) throw new Error(tr('canvas.generationFailed'));
            mergeGeneratedOutputs(gen, outputs, Boolean(opts.cascade));
            addGenerationLog({run, outputs, runMs:nowMs() - startedAt});
            gen.runStatus = 'done';
            gen.runError = '';
            gen.running = false;
            refreshRunNodes(gen, out);
            scheduleSave();
            return;
        }
        pendingIds = taskInfos.map(() => uid('p'));
        if(out) out._pending = [
            ...(out._pending || []),
            ...taskInfos.map((task, index) => makePendingForRun(pendingIds[index], run, gen, {refs, requestSize:payload.size, cascadeTargetId}, {
                canvasTaskId:task.task_id,
                canvasTaskType:'online-image',
                providerId:payload.provider_id,
                model:payload.model,
                appendGenerated:Boolean(opts.cascade)
            }))
        ];
        refreshRunNodes(gen, out);
        scheduleSave();
        await saveCanvas();
        const statuses = await Promise.all(taskInfos.map(task => pollCanvasImageTask(task.task_id, {cascadeTargetId})));
        if(statuses.includes('aborted')) throw cascadeAbortError(cascadeStopMessage());
        if(statuses.includes('failed')) throw new Error(gen.runError || tr('canvas.generationFailed'));
    } catch(err) {
        const remainingPending = pendingIds.map(id => pendingById(out, id)).filter(Boolean);
        const removableIds = remainingPending.filter(p => !(p.failed && p.recoverTaskId)).map(p => p.id);
        if(removableIds.length){
            const metas = collectRunMetas(out, removableIds);
            addGenerationLog({run, outputs:[], runMs:Math.max(...metas.map(m => m.runMs || 0), 0), error:err.message || String(err)});
            if(out) out._pending = (out._pending||[]).filter(p => !removableIds.includes(p.id));
        }
        if(isCascadeAbortError(err)){
            gen.running = false;
            refreshRunNodes(gen, out);
            scheduleSave();
            throw err;
        }
        gen.runStatus = 'failed'; gen.runError = err.message || String(err);
        gen.running = false;
        refreshRunNodes(gen, out);
        scheduleSave();
        if(remainingPending.some(p => p.failed && p.recoverTaskId) && !removableIds.length) return;
        if(opts.cascade) throw err;
        showErrorModal(err.message || tr('canvas.generationFailed'), tr('canvas.apiFailed'));
    }
}

async function runGeneratorLegacy(genId, opts={}){
    const gen = getNodes().find(n => n.id === genId);
    if(!gen || (gen.running && !opts.cascade)) return;
    const sources = orderedSources(gen, generatorSources(gen));
    const prompt = sources.map(s => s.prompt).filter(Boolean).join('\n\n');
    const refs = imageRefsOnly(sources.flatMap(s => s.refs || []));
    if(!prompt && !refs.length){ alert(tr('canvas.needPromptOrImage')); return; }
    const count = Math.max(1, Math.min(8, Number(gen.count || 1)));
    let out = outputForNode(gen, 460);
    const pendingIds = Array.from({length:count}, () => uid('p'));
    const run = runSnapshot(gen, prompt || 'Edit the reference images.', refs);
    const requestSize = await generatorSizeForRun(gen, refs);
    if(out) out._pending = [...(out._pending||[]), ...pendingIds.map(id => makePendingForRun(id, run, gen, {refs, requestSize}))];
    if(!opts.cascade){
        gen.running = true;
        refreshRunNodes(gen, out);
        setTimeout(() => { gen.running = false; refreshRunNodes(gen, out); }, 2000);
    }
    else refreshRunNodes(gen, out);
    try {
        const payload = {
            prompt: prompt || 'Edit the reference images.',
            provider_id:resolveImageProviderId(gen.apiProvider || 'comfly'),
            model:resolveImageModel(gen.model),
            size:requestSize,
            aspect_ratio:API_RATIO_VALUES[gen.ratio] || (gen.ratio === 'custom' ? String(gen.customRatio || '').trim() : ''),
            resolution:['1k','2k','4k'].includes(gen.resolution) ? gen.resolution : '',
            reference_images:refs.slice(0, CANVAS_REFERENCE_IMAGE_MAX)
        };
        const quality = normalizedImageQuality(gen.quality);
        if(quality) payload.quality = quality;
        const results = await Promise.all(Array.from({length:count}, () => fetch('/api/online-image', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(payload)
        }).then(async r => { if(!r.ok) throw new Error(await responseErrorMessage(r, tr('canvas.generationFailed'))); return r.json(); })));
        const images = results.flatMap(result => result.images || []);
        const metas = collectRunMetas(out, pendingIds);
        run.request = results[0] ? requestMetaFromResult(results[0]) : {};
        if(out) out._pending = (out._pending||[]).filter(p => !pendingIds.includes(p.id));
        appendOutputImages(out, images, refs[0], metas);
        mergeGeneratedOutputs(gen, images, Boolean(opts.cascade));
        addGenerationLog({run, outputs:images, runMs:Math.max(...metas.map(m => m.runMs || 0), 0)});
        gen.runStatus = 'done'; gen.runError = '';
        refreshRunNodes(gen, out);
        scheduleSave();
    } catch(err) {
        const metas = collectRunMetas(out, pendingIds);
        addGenerationLog({run, outputs:[], runMs:Math.max(...metas.map(m => m.runMs || 0), 0), error:err.message || String(err)});
        if(out) out._pending = (out._pending||[]).filter(p => !pendingIds.includes(p.id));
        gen.runStatus = 'failed'; gen.runError = err.message || String(err);
        refreshRunNodes(gen, out);
        if(opts.cascade) throw err;
        showErrorModal(err.message || tr('canvas.generationFailed'), tr('canvas.apiFailed'));
    }
}

async function midjourneyRequest(path, options={}){
    const {cascadeTargetId='', ...init} = options;
    const response = await cascadeFetch(path, init, cascadeTargetId ? {cascadeTargetId} : {});
    if(!response.ok) throw new Error(await responseErrorMessage(response, 'Midjourney 请求失败'));
    return response.json();
}

async function waitMidjourneyTask(providerId, taskId, options={}){
    while(true){
        const cascadeTargetId = cascadeTargetIdFromOptions(options);
        if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
        const result = await midjourneyRequest(`/api/midjourney/tasks/${encodeURIComponent(taskId)}?provider_id=${encodeURIComponent(providerId)}`, {cascadeTargetId});
        if(result.status === 'succeeded') return result;
        if(result.status === 'failed') throw new Error(result.error || 'Midjourney 任务失败');
        await sleep(2200);
    }
}

async function runMidjourneyNode(nodeId, opts={}){
    const node = getNodes().find(item => item.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const providerId = resolveMidjourneyProviderId(node.apiProvider || '');
    if(!providerId){ showErrorModal('请先在 API 设置中添加 APIMart 平台。', 'Midjourney'); return; }
    const sources = orderedSources(node, generatorSources(node));
    const prompt = sources.map(source => source.prompt).filter(Boolean).join('\n\n').trim();
    const refs = imageRefsOnly(sources.flatMap(source => source.refs || []));
    const mode = ['imagine','blend','edit'].includes(node.mode) ? node.mode : 'imagine';
    if(mode === 'blend' && (refs.length < 2 || refs.length > 4)){
        alert('多图融合需要连接 2 到 4 张图片');
        return;
    }
    if(mode !== 'blend' && !prompt){ alert(tr('canvas.needPrompt')); return; }
    if(mode === 'edit' && !refs.length){ alert('图片编辑需要连接至少一张图片'); return; }
    const out = outputForNode(node, 460);
    const run = runSnapshot(node, prompt, refs);
    run.taskLabel = mode === 'blend' ? 'Midjourney 多图融合' : mode === 'edit' ? 'Midjourney 图片编辑' : `Midjourney v${node.version || '6.1'}`;
    run.startedAt = nowMs();
    node.lastPrompt = prompt;
    node.running = true;
    node.runStatus = 'running';
    node.runError = '';
    refreshRunNodes(node, out);
    try {
        const submitted = await midjourneyRequest('/api/midjourney/submit', {
            method:'POST', headers:{'Content-Type':'application/json'}, cascadeTargetId:cascadeTargetIdFromOptions(opts),
            body:JSON.stringify({provider_id:providerId, mode, prompt, size:node.size, version:node.version, speed:node.speed, reference_images:refs.slice(0, 4)})
        });
        node.lastTaskId = submitted.task_id;
        node.lastAction = mode;
        node.lastTaskStatus = submitted.status || 'queued';
        scheduleSave();
        const result = await waitMidjourneyTask(providerId, submitted.task_id, opts);
        await completeMidjourneyRun(node, out, run, result, Boolean(opts.cascade));
    } catch(error) {
        node.running = false;
        node.runStatus = 'failed';
        node.runError = error.message || String(error);
        node.lastTaskStatus = 'FAILED';
        addGenerationLog({run, outputs:[], runMs:nowMs() - run.startedAt, error:node.runError});
        refreshRunNodes(node, out);
        scheduleSave();
        if(opts.cascade) throw error;
        showErrorModal(node.runError, 'Midjourney');
    }
}

async function runMidjourneyAction(nodeId, action, index=0, extra={}){
    const node = getNodes().find(item => item.id === nodeId);
    if(!node?.lastTaskId || node.running) return;
    const providerId = resolveMidjourneyProviderId(node.apiProvider || '');
    if(!providerId){ showErrorModal('请先在 API 设置中添加 APIMart 平台。', 'Midjourney'); return; }
    const out = outputForNode(node, 460);
    const run = runSnapshot(node, '', []);
    const actionLabels = {upscale:`U${index}`, variation:`V${index}`, low_variation:'弱变体', high_variation:'强变体', remix_subtle:`轻微重塑 ${index}`, remix_strong:`强烈重塑 ${index}`, zoom:`扩图 ${extra.zoomRatio || 2}x`, pan:`平移 ${extra.direction || ''}`, inpaint:'局部重绘', reroll:'Reroll'};
    run.taskLabel = `Midjourney ${actionLabels[action] || action}`;
    run.startedAt = nowMs();
    node.running = true;
    node.runStatus = 'running';
    refreshRunNodes(node, out);
    try {
        const submitted = await midjourneyRequest('/api/midjourney/actions', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({provider_id:providerId, task_id:node.lastTaskId, action, index, speed:node.speed, prompt:node.lastPrompt || '', direction:extra.direction || '', zoom_ratio:extra.zoomRatio || null})
        });
        node.lastTaskId = submitted.task_id;
        node.lastAction = action;
        node.lastTaskStatus = submitted.status || 'queued';
        scheduleSave();
        if(action === 'inpaint'){
            node.mjModalTaskId = submitted.task_id;
            node.mjModalPrompt = node.mjModalPrompt || node.lastPrompt || '';
            node.running = false;
            node.runStatus = '';
            refreshRunNodes(node, out);
            scheduleSave();
            return;
        }
        const result = await waitMidjourneyTask(providerId, submitted.task_id);
        await completeMidjourneyRun(node, out, run, result, true);
    } catch(error) {
        node.running = false;
        node.runStatus = 'failed';
        node.runError = error.message || String(error);
        node.lastTaskStatus = 'FAILED';
        addGenerationLog({run, outputs:[], runMs:nowMs() - run.startedAt, error:node.runError});
        refreshRunNodes(node, out);
        scheduleSave();
        showErrorModal(node.runError, 'Midjourney');
    }
}

async function runMidjourneyModal(nodeId, maskRef){
    const node = getNodes().find(item => item.id === nodeId);
    if(!node?.mjModalTaskId || !maskRef?.url || node.running) return;
    const providerId = resolveMidjourneyProviderId(node.apiProvider || '');
    if(!providerId){ showErrorModal('请先在 API 设置中添加 APIMart 平台。', 'Midjourney'); return; }
    const out = outputForNode(node, 460);
    const prompt = String(node.mjModalPrompt || node.lastPrompt || '').trim();
    const run = runSnapshot(node, prompt, [maskRef]);
    run.taskLabel = 'Midjourney 局部重绘';
    run.startedAt = nowMs();
    node.running = true;
    node.runStatus = 'running';
    refreshRunNodes(node, out);
    try {
        const submitted = await midjourneyRequest('/api/midjourney/modal', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({provider_id:providerId, task_id:node.mjModalTaskId, prompt, speed:node.speed, mask_image:maskRef})
        });
        node.lastTaskId = submitted.task_id;
        node.lastAction = 'inpaint';
        node.lastTaskStatus = submitted.status || 'submitted';
        node.mjModalTaskId = '';
        scheduleSave();
        const result = await waitMidjourneyTask(providerId, submitted.task_id);
        await completeMidjourneyRun(node, out, run, result, true);
    } catch(error) {
        node.running = false;
        node.runStatus = 'failed';
        node.runError = error.message || String(error);
        addGenerationLog({run, outputs:[], runMs:nowMs() - run.startedAt, error:node.runError});
        refreshRunNodes(node, out);
        scheduleSave();
        showErrorModal(node.runError, 'Midjourney');
    }
}

async function runVideoNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const sources = orderedSources(node, generatorSources(node));
    const prompt = sources.map(s => s.prompt).filter(Boolean).join('\n\n');
    const allRefs = sources.flatMap(s => s.refs || []);
    const mediaRefs = applyUploadedUrlToRefs((allRefs || []).filter(ref => ['image','video','audio'].includes(mediaKindForRef(ref))), node);
    const refs = imageRefsOnly(mediaRefs);
    const videoRefs = videoRefsOnly(mediaRefs);
    const audioRefs = audioRefsOnly(mediaRefs);
    if(node.useFrameRoles && refs[0]) refs[0] = {...refs[0], role:'first_frame'};
    if(node.useFrameRoles && refs[1]) refs[1] = {...refs[1], role:'last_frame'};
    if(!prompt){ alert(tr('canvas.videoNeedsPrompt')); return; }
    let out = outputForNode(node, 460);
    const pendingId = uid('p');
    const run = runSnapshot(node, prompt, refs);
    if(out) out._pending = [...(out._pending || []), makePendingForRun(pendingId, run, node, {refs, cascadeTargetId})];
    if(!opts.cascade){ node.running = true; refreshRunNodes(node, out); }
    else refreshRunNodes(node, out);
    try {
        const result = await cascadeFetch('/api/canvas-video', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                prompt,
                provider_id:ensureClassicVideoProviderParams().resolveVideoProviderId({id: node.apiProvider || 'comfly'}),
                model:node.model || 'veo3-fast',
                duration:Number(node.duration || 5),
                aspect_ratio:node.aspectRatio || '16:9',
                resolution:node.resolution || '',
                images:refs,
                videos:manualVideoUrlForNode(node)
                    ? [manualVideoUrlForNode(node)]
                    : videoRefs.map(ref => tempShUploadedUrlForNode(node, ref.url)),
                audios:audioRefs.map(ref => ref.url).filter(Boolean),
                enhance_prompt:Boolean(node.enhancePrompt),
                enable_upsample:Boolean(node.enableUpsample),
                watermark:Boolean(node.watermark),
                camerafixed:Boolean(node.cameraFixed),
                generate_audio:Boolean(node.generateAudio),
                multimodal:Boolean(node.multimodal)
            })
        }, {cascadeTargetId}).then(async r => { if(!r.ok) throw new Error(await responseErrorMessage(r, tr('canvas.videoFailed'))); return r.json(); });
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        const outputUrls = window.WorkbenchCanvasMediaResultNormalizer.extract(result).map(item => {
            const url = outputUrlValue(item);
            return item && typeof item === 'object' ? {...item, url, kind:item.kind || 'video'} : {url, kind:'video'};
        }).filter(item => item.url);
        if(!outputUrls.length) throw new Error(tr('canvas.videoFailed'));
        run.request = requestMetaFromResult(result);
        appendOutputImages(out, outputUrls, refs[0], [{...meta, kind:'video'}]);
        mergeGeneratedOutputs(node, outputUrls, Boolean(opts.cascade));
        addGenerationLog({run, outputs:outputUrls, runMs:meta.runMs || 0});
        node.runStatus = 'done'; node.runError = '';
        refreshRunNodes(node, out);
        scheduleSave();
    } catch(err) {
        const meta = collectRunMeta(out, pendingId);
        addGenerationLog({run, outputs:[], runMs:meta.runMs || 0, error:err.message || String(err)});
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        if(isCascadeAbortError(err)){
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed'; node.runError = err.message || String(err);
        refreshRunNodes(node, out);
        if(opts.cascade) throw err;
        alert(err.message || tr('canvas.videoFailed'));
    } finally {
        node.running = false;
        refreshRunNodes(node, out);
    }
}

async function runMiniMaxRunningHub(node, media, options={}){
    const {entry, workflowId, fields, rhNode} = await miniMaxRunningHubSettings(node);
    miniMaxApplyRunningHubParams(rhNode, fields, node, media.prompt);
    const nodeInfoList = await miniMaxBuildRunningHubNodeInfoList(rhNode, fields, media);
    const workflowExtras = await miniMaxBuildRunningHubWorkflowExtras(rhNode, fields, media, nodeInfoList);
    const body = {workflowId, nodeInfoList, useWallet:rhUseWallet(rhNode), ...workflowExtras};
    const cascadeTargetId = cascadeTargetIdFromOptions(options);
    const submit = await cascadeFetch('/api/runninghub/workflow-submit', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)
    }, {cascadeTargetId}).then(async r => {
        const data = await r.clone().json().catch(async () => ({detail:await r.text().catch(() => '')}));
        if(!r.ok || data.success === false) throw miniMaxRunningHubPayloadError('提交', data, 'RunningHub 工作流提交失败', {
            endpoint:'/api/runninghub/workflow-submit',
            workflowId,
            nodeInfoList:nodeInfoList.slice(0, 40),
            hasWorkflow:Boolean(body.workflow)
        });
        return data.data || data;
    });
    const taskId = submit.taskId;
    if(!taskId) throw new Error(tr('canvas.rhNoTaskId'));
    for(let i = 0; i < 720; i++){
        if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
        await sleep(2500);
        const data = await cascadeFetch(`/api/runninghub/query?taskId=${encodeURIComponent(taskId)}&useWallet=${rhUseWallet(rhNode) ? '1' : '0'}`, {}, {cascadeTargetId}).then(async r => {
            const json = await r.clone().json().catch(async () => ({detail:await r.text().catch(() => '')}));
            if(!r.ok || json.success === false) throw miniMaxRunningHubPayloadError('查询', json, 'RunningHub 查询失败', {taskId, workflowId});
            return json.data || json;
        });
        if(data.status === 'SUCCESS'){
            const outputs = window.WorkbenchCanvasMediaResultNormalizer.extract(data.image_items?.length ? data.image_items : (data.urls || []));
            if(!outputs.length) throw new Error(tr('canvas.rhOutputsEmpty'));
            return {outputs, request:{task_id:taskId, workflowId, workflowTitle:runningHubEntryLabel(entry, 'workflow'), backend:'runninghub', mode:'workflow', useWallet:rhUseWallet(rhNode)}};
        }
        if(data.status === 'FAILED') throw miniMaxRunningHubPayloadError('执行', data, data.failReason || 'RunningHub 执行失败', {taskId, workflowId});
    }
    throw new Error(tr('canvas.rhTimeout'));
}

async function runMiniMaxNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const sourceData = miniMaxRefsForNode(node);
    const seg = miniMaxSelectedSegment(node);
    const prompt = String(seg?.prompt || '').trim() || sourceData.prompt;
    const refs = miniMaxRefsForSegment(node, seg);
    const media = {
        sources:sourceData.sources,
        refs,
        image:imageRefsOnly(refs),
        video:videoRefsOnly(refs),
        audio:audioRefsOnly(refs),
        prompt
    };
    if(!media.prompt){
        const msg = 'MiniMax 需要连接提示词';
        if(opts.cascade) throw new Error(msg);
        alert(msg);
        return;
    }
    const engine = ensureClassicMiniMaxControls().getEngine({node});
    let out = outputForNode(node, 500);
    const pendingId = uid('p');
    const run = runSnapshot(node, media.prompt, media.refs);
    run.taskLabel = engine === 'runninghub' ? 'MiniMax RunningHub' : 'MiniMax ComfyUI';
    if(out) out._pending = [...(out._pending || []), makePendingForRun(pendingId, run, node, {refs:media.refs, cascadeTargetId})];
    if(!opts.cascade) node.running = true;
    refreshRunNodes(node, out);
    try {
        let outputs = [];
        if(engine === 'runninghub'){
            const rhResult = await runMiniMaxRunningHub(node, media, {cascadeTargetId});
            outputs = rhResult.outputs || [];
            run.request = rhResult.request || {};
        } else {
            const params = await miniMaxDynamicParams(node, media.prompt, media.refs);
            const result = await runQueuedComfyGenerate({
                prompt:media.prompt,
                workflow_json:node.workflow || 'MiniMax_H3.json',
                params,
                type:'minimax-h3',
                client_id:CLIENT_ID
            }, {cascadeTargetId});
            outputs = window.WorkbenchCanvasMediaResultNormalizer.extract(result);
            run.request = requestMetaFromResult(result);
        }
        const normalized = (outputs || []).map((item, i) => {
            const url = outputUrlValue(item);
            const explicitKind = typeof item === 'object' && item.kind ? item.kind : '';
            const kind = explicitKind || 'video';
            return item && typeof item === 'object' ? {...item, url, kind} : {url, kind, name:`minimax-${i + 1}.mp4`};
        }).filter(item => item.url);
        if(!normalized.length) throw new Error('MiniMax 未返回视频');
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        appendOutputImages(out, normalized, media.refs[0], [{...meta, kind:'video'}]);
        if(seg) normalized.forEach(item => miniMaxSetSegmentResult(node, seg, item));
        mergeGeneratedOutputs(node, normalized, Boolean(opts.cascade));
        addGenerationLog({run, outputs:normalized, runMs:meta.runMs || 0});
        node.runStatus = 'done';
        node.runError = '';
        refreshRunNodes(node, out);
        scheduleSave();
    } catch(err) {
        const meta = collectRunMeta(out, pendingId);
        const readable = miniMaxReadableError(err, engine);
        addGenerationLog({run, outputs:[], runMs:meta.runMs || 0, error:miniMaxLogError(err, engine)});
        if(out) out._pending = (out._pending || []).filter(p => p.id !== pendingId);
        if(isCascadeAbortError(err)){
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed';
        node.runError = readable;
        refreshRunNodes(node, out);
        if(opts.cascade) throw err;
        showErrorModal(readable, 'MiniMax H3');
    } finally {
        node.running = false;
        refreshRunNodes(node, out);
    }
}

async function uploadCanvasUrlToComfy(url){
    const blob = await fetch(url).then(r => {
        if(!r.ok) throw new Error(langIsEn() ? 'Image read failed' : '图片读取失败');
        return r.blob();
    });
    const filename = (url || '').split('/').pop()?.split('?')[0] || `canvas_${Date.now()}.png`;
    const form = new FormData();
    form.append('files', blob, filename);
    const data = await fetch('/api/upload', {method:'POST', body:form}).then(async r => {
        if(!r.ok) throw new Error(await responseErrorMessage(r, langIsEn() ? 'Image upload to ComfyUI failed' : '图片上传到 ComfyUI 失败'));
        return r.json();
    });
    return data.files?.[0]?.comfy_name || filename;
}

async function runComfyUpscale(imageUrl, resolution, options={}){
    if(!imageUrl) throw new Error(actionFailed('studio.superResolution', langIsEn() ? 'missing input image' : '缺少输入图片'));
    const nextInput = await uploadCanvasUrlToComfy(imageUrl);
    const upscale = await runQueuedComfyGenerate({
        workflow_json:'upscale.json',
        params:{
            "15": { image:nextInput },
            "172": { seed:Math.floor(Math.random() * 4294967295), resolution:Number(resolution || 2048) }
        },
        type:'enhance',
        client_id:CLIENT_ID
    }, options);
    if(upscale.error) throw new Error(actionFailed('studio.superResolution', upscale.error));
    if(!upscale.images?.length) throw new Error(noReturnedImage('studio.superResolution'));
    return upscale.images || [];
}

async function runComfyNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const sources = orderedSources(node, generatorSources(node));
    const prompt = sources.map(s => s.prompt).filter(Boolean).join('\n\n');
    const allRefs = sources.flatMap(s => s.refs || []);
    const refs = imageRefsOnly(allRefs);
    const mode = node.mode || 'text';
    const customImageFields = mode === 'custom' ? comfyFields(node, 'image') : [];
    const customVideoFields = mode === 'custom' ? comfyFields(node, 'video') : [];
    const customAudioFields = mode === 'custom' ? comfyFields(node, 'audio') : [];
    const customPromptFields = mode === 'custom' ? comfyFields(node, 'prompt') : [];
    if((mode === 'text' || (mode === 'custom' && customPromptFields.length)) && !prompt){ alert(tr('canvas.needPrompt')); return; }
    if((mode !== 'text' && mode !== 'custom' && !refs.length) || (mode === 'custom' && refs.length < customImageFields.length)){ alert(tr('canvas.needImage')); return; }
    if(mode === 'custom' && videoRefsOnly(allRefs).length < customVideoFields.length){ alert(langIsEn() ? 'Please connect enough video inputs for this ComfyUI workflow.' : '请为这个 ComfyUI 工作流连接足够的视频输入'); return; }
    if(mode === 'custom' && audioRefsOnly(allRefs).length < customAudioFields.length){ alert(langIsEn() ? 'Please connect enough audio inputs for this ComfyUI workflow.' : '请为这个 ComfyUI 工作流连接足够的音频输入'); return; }
    let out = outputForNode(node, 480);
    const pendingId = uid('p');
    const run = runSnapshot(node, prompt, refs);
    run.taskLabel = comfyRunLabel(node);
    const requestSize = mode === 'text' ? {width:Number(node.width || 1024), height:Number(node.height || 1024)} : null;
    if(out) out._pending = [...(out._pending||[]), makePendingForRun(pendingId, run, node, {refs, requestSize, cascadeTargetId})];
    if(!opts.cascade){
        node.running = true;
        refreshRunNodes(node, out);
        setTimeout(() => { node.running = false; refreshRunNodes(node, out); }, 2000);
    }
    else refreshRunNodes(node, out);
    try {
        let images = [];
        if(mode === 'text'){
            run.taskLabel = tr('canvas.comfyText');
            const result = await runQueuedComfyGenerate({
                prompt,
                width:Number(node.width || 1024),
                height:Number(node.height || 1024),
                workflow_json:'Z-Image.json',
                type:'zimage',
                client_id:CLIENT_ID
            }, {cascadeTargetId});
            run.request = requestMetaFromResult(result);
            images = window.WorkbenchCanvasMediaResultNormalizer.extract(result);
        } else if(mode === 'enhance'){
            run.taskLabel = tr('canvas.comfyEnhance');
            const inputName = await comfyNameForRef(refs[0]);
            const enhance = await runQueuedComfyGenerate({
                workflow_json:'Z-Image-Enhance.json',
                params:{
                    "15": { image:inputName },
                    "204": { value:Number(node.enhanceStrength ?? 0.5) }
                },
                type:'enhance',
                client_id:CLIENT_ID
            }, {cascadeTargetId});
            run.request = requestMetaFromResult(enhance);
            if(enhance.error) throw new Error(actionFailed('canvas.comfyEnhance', enhance.error));
            if(!enhance.images?.length) throw new Error(noReturnedImage('canvas.comfyEnhance'));
            if(node.enhanceUpscale){
                images = await runComfyUpscale(enhance.images?.[0], node.enhanceUpscaleRes || 2048, {cascadeTargetId});
            } else {
                images = enhance.images || [];
            }
        } else if(mode === 'custom'){
            const workflowName = validComfyWorkflowName(node.comfyWorkflow || getComfyWorkflows()[0]?.name || '');
            run.taskLabel = workflowName || tr('canvas.comfyCustom');
            if(node.comfyWorkflow && node.comfyWorkflow !== workflowName) node.comfyWorkflow = workflowName;
            const wf = await ensureComfyWorkflow(workflowName);
            if(!workflowName || !wf) throw new Error(tr('canvas.comfyNoWorkflow'));
            const fields = wf?.config?.fields || [];
            const params = {};
            const imageFields = fields.filter(f => comfyFieldKind(f) === 'image');
            const videoFields = fields.filter(f => comfyFieldKind(f) === 'video');
            const audioFields = fields.filter(f => comfyFieldKind(f) === 'audio');
            const promptFields = fields.filter(f => comfyFieldKind(f) === 'prompt');
            const settingFields = fields.filter(f => comfyFieldKind(f) === 'setting');
            const assignMediaFields = async (mediaFields, mediaRefs) => {
                const names = [];
                for(const ref of mediaRefs.slice(0, mediaFields.length)) names.push(await comfyNameForRef(ref));
                mediaFields.forEach((f, i) => {
                    if(!f.node || !f.input) return;
                    params[f.node] = params[f.node] || {};
                    params[f.node][f.input] = names[i] || '';
                });
            };
            await assignMediaFields(imageFields, refs);
            await assignMediaFields(videoFields, videoRefsOnly(allRefs));
            await assignMediaFields(audioFields, audioRefsOnly(allRefs));
            promptFields.forEach(f => {
                if(!f.node || !f.input) return;
                params[f.node] = params[f.node] || {};
                params[f.node][f.input] = prompt;
            });
            settingFields.forEach(f => {
                if(!f.node || !f.input) return;
                params[f.node] = params[f.node] || {};
                if(comfyRandomEnabled(f) && comfyRandomActive(node, f.id)){
                    node.comfyParams = node.comfyParams || {};
                    node.comfyParams[f.id] = comfyRandomValue(f);
                }
                params[f.node][f.input] = comfyParamValue(node, f);
            });
            const result = await runQueuedComfyGenerate({
                prompt,
                workflow_json:workflowName,
                params,
                type:'workflow-custom',
                client_id:CLIENT_ID
            }, {cascadeTargetId});
            run.request = requestMetaFromResult(result);
            if(result.error) throw new Error(actionFailed('canvas.comfyCustom', result.error));
            images = window.WorkbenchCanvasMediaResultNormalizer.extract(result);
            if(!images.length) throw new Error(noReturnedImage('canvas.comfyCustom'));
        } else {
            run.taskLabel = tr('canvas.comfyEdit');
            const names = [];
            for (const ref of refs.slice(0, 3)) names.push(await comfyNameForRef(ref));
            const result = await runQueuedComfyGenerate({
                prompt,
                workflow_json:'Flux2-Klein.json',
                type:'klein',
                params:{
                    "168": { text:prompt },
                    "158": { noise_seed:Math.floor(Math.random() * 1000000) },
                    "278": { image:names[0] || "" },
                    "270": { image:names[1] || "" },
                    "292": { image:names[2] || "" },
                    "313": { value:Boolean(names[1]) },
                    "314": { value:Boolean(names[2]) }
                },
                client_id:CLIENT_ID
            }, {cascadeTargetId});
            run.request = requestMetaFromResult(result);
            if(result.error) throw new Error(actionFailed('canvas.comfyEdit', result.error));
            if(!result.images?.length) throw new Error(noReturnedImage('canvas.comfyEdit'));
            images = node.editUpscale ? await runComfyUpscale(result.images?.[0], node.editUpscaleRes || 2048, {cascadeTargetId}) : result.images || [];
        }
        const meta = collectRunMeta(out, pendingId);
        if(out) out._pending = (out._pending||[]).filter(p => p.id !== pendingId);
        appendOutputImages(out, images, refs[0], [meta]);
        mergeGeneratedOutputs(node, images, Boolean(opts.cascade));
        addGenerationLog({run, outputs:images, runMs:meta.runMs || 0});
        node.runStatus = 'done'; node.runError = '';
        refreshRunNodes(node, out);
        scheduleSave();
    } catch(err) {
        const meta = collectRunMeta(out, pendingId);
        addGenerationLog({run, outputs:[], runMs:meta.runMs || 0, error:err.message || String(err)});
        if(out) out._pending = (out._pending||[]).filter(p => p.id !== pendingId);
        if(isCascadeAbortError(err)){
            refreshRunNodes(node, out);
            if(opts.cascade) throw err;
            return;
        }
        node.runStatus = 'failed'; node.runError = err.message || String(err);
        refreshRunNodes(node, out);
        if(opts.cascade) throw err;
        alert(err.message || actionFailed('canvas.comfyGenerate'));
    }
}

async function runQueuedComfyGenerate(payload, options={}){
    const task = await createCanvasComfyTask(payload, options);
    return waitCanvasComfyTaskResult(task.task_id, options);
}

async function callCanvasLLM(node, message, messages=[], options={}){
    const llmProv = resolveChatProviderId(node.llmProvider || 'comfly');
    const model = resolveChatModel(node.model || node.llmMsModel, llmProv);
    const images = llmInputImages(node);
    const videos = llmInputVideos(node);
    const result = await cascadeFetch('/api/canvas-llm', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
            message,
            model,
            ms_model: llmProv === 'modelscope' ? model : '',
            provider: llmProv,
            // The System switch controls whether any system message is sent.
            // Keep the default only when the user explicitly enables it.
            system_prompt:node.showSystem ? ((node.systemPrompt || '').trim() || 'You are a helpful assistant.') : '',
            messages,
            images,
            videos,
        })
    }, options).then(async r => {
        if(!r.ok){
            throw new Error(await responseErrorMessage(r, 'LLM 运行失败'));
        }
        return r.json();
    });
    return result.text || '';
}

async function runLLMNode(nodeId, opts={}){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || (node.running && !opts.cascade)) return;
    const executionHost = ensureClassicExecutionHost();
    const cascadeTargetId = cascadeTargetIdFromOptions(opts);
    const input = llmInputText(node) || node.userInput || '';
    if(!input){
        if(opts.cascade) throw new Error('LLM 缺少提示词输入');
        executionHost.notifyError(tr('canvas.needPromptToLLM')); return;
    }
    if(!opts.cascade){ executionHost.markRunning(node, true); executionHost.render(node); }
    try {
        const outputText = await callCanvasLLM(node, input, [], {cascadeTargetId});
        if(!opts.cascade) executionHost.markRunning(node, false);
        executionHost.writeOutputText(node, outputText);
        executionHost.setRunStatus(node, 'done', '');
        executionHost.render(node);
        executionHost.save();
    } catch(err) {
        if(!opts.cascade) executionHost.markRunning(node, false);
        if(isCascadeAbortError(err)){
            executionHost.render(node);
            if(opts.cascade) throw err;
            return;
        }
        executionHost.setRunStatus(node, 'failed', err.message || String(err));
        executionHost.render(node);
        if(opts.cascade) throw err;
        executionHost.notifyError(err.message || 'LLM 运行失败');
    }
}

async function runLLMChat(nodeId){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || node.running) return;
    const message = (node.chatInput || '').trim();
    if(!message) return;
    node.messages = node.messages || [];
    const history = node.messages.slice();
    node.messages.push({role:'user', content:message});
    node.chatInput = '';
    node.running = true;
    refreshNodes([node.id]);
    try {
        const text = await callCanvasLLM(node, message, history);
        node.messages.push({role:'assistant', content:text});
        node.outputText = text;
        node.running = false;
        refreshNodes([node.id]);
        scheduleSave();
    } catch(err) {
        node.running = false;
        refreshNodes([node.id]);
        alert(err.message || 'LLM 运行失败');
    }
}

function runSnapshot(node, prompt, refs=[]){
    const clone = JSON.parse(JSON.stringify(node || {}));
    delete clone.running;
    delete clone.runStatus;
    delete clone.runError;
    delete clone.inputs;
    return {
        nodeType: node?.type || '',
        node: clone,
        prompt: prompt || '',
        refs: (refs || []).map(ref => ({url:ref.url, name:ref.name || 'image'})).filter(ref => ref.url),
    };
}

function runTaskLabel(run){
    const node = run?.node || {};
    if(run?.taskLabel) return run.taskLabel;
    if(run?.nodeType === 'comfy') return comfyRunLabel(node);
    if(run?.nodeType === 'ltxDirector') return tr('canvas.ltxDirector');
    if(run?.nodeType === 'generator') return node.model || 'API Image';
    if(run?.nodeType === 'video') return node.model || 'Video';
    if(run?.nodeType === 'msgen') return node.msCustomModel || node.msgenModel || 'Modelscope';
    return run?.nodeType || 'Generate';
}

function runPlatformLabel(run){
    const node = run?.node || {};
    if(run?.nodeType === 'generator') return providerById(node.apiProvider || 'comfly')?.name || node.apiProvider || 'API';
    if(run?.nodeType === 'msgen') return 'Modelscope';
    if(run?.nodeType === 'video') return providerById(node.apiProvider || 'comfly')?.name || node.apiProvider || 'Video';
    if(run?.nodeType === 'comfy') return 'ComfyUI';
    if(run?.nodeType === 'ltxDirector') return 'ComfyUI';
    return run?.nodeType || 'Generate';
}

function makePendingForRun(id, run, node, options={}, task={}){
    const pending = makePending(id, run, task);
    const previewSize = pendingPreviewSizeForRun(node, options);
    if(previewSize) pending.previewSize = previewSize;
    if(options?.cascadeTargetId) pending.cascadeTargetId = String(options.cascadeTargetId);
    return pending;
}

async function createCanvasImageTask(payload, options={}){
    const res = await cascadeFetch('/api/canvas-image-tasks', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
    }, options);
    if(!res.ok) throw new Error(await responseErrorMessage(res, tr('canvas.generationFailed')));
    return res.json();
}

async function createCanvasComfyTask(payload, options={}){
    const res = await cascadeFetch('/api/canvas-comfy-tasks', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
    }, options);
    if(!res.ok) throw new Error(await responseErrorMessage(res, actionFailed('canvas.comfyGenerate')));
    return res.json();
}

async function waitCanvasComfyTaskResult(taskId, options={}){
    if(!taskId) throw new Error(actionFailed('canvas.comfyGenerate'));
    while(true){
        const cascadeTargetId = cascadeTargetIdFromOptions(options);
        if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
        const res = await cascadeFetch(`/api/canvas-comfy-tasks/${encodeURIComponent(taskId)}`, {}, {cascadeTargetId});
        if(!res.ok){
            if(res.status === 404) throw new Error(cascadeBackendRestartMessage());
            throw new Error(await responseErrorMessage(res, actionFailed('canvas.comfyGenerate')));
        }
        const data = await res.json();
        if(data.status === 'succeeded') return data.result || {};
        if(data.status === 'failed') throw new Error(data.error || actionFailed('canvas.comfyGenerate'));
        await sleep(1600);
    }
}

async function pollCanvasImageTask(taskId, options={}){
    if(!taskId) return 'failed';
    if(activeCanvasTaskPolls.has(taskId)) return 'running';
    activeCanvasTaskPolls.add(taskId);
    try {
        while(true){
            const found = findPendingTask(taskId);
            if(!found) return 'missing';
            const cascadeTargetId = String(options?.cascadeTargetId || found?.pending?.cascadeTargetId || '');
            if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
            const res = await cascadeFetch(`/api/canvas-image-tasks/${encodeURIComponent(taskId)}`, {}, {cascadeTargetId});
            if(!res.ok){
                if(res.status === 404) throw new Error(cascadeBackendRestartMessage());
                throw new Error(await responseErrorMessage(res, tr('canvas.generationFailed')));
            }
            const data = await res.json();
            if(data.status === 'succeeded'){
                completeCanvasImageTask(taskId, data.result || {});
                return 'succeeded';
            }
            if(data.status === 'failed'){
                failCanvasImageTask(taskId, data.error || tr('canvas.generationFailed'), data);
                return 'failed';
            }
            await sleep(1800);
        }
    } catch(err) {
        const message = normalizeCanvasTaskError(err, tr('canvas.generationFailed'));
        if(isCascadeAbortError(err)) return 'aborted';
        failCanvasImageTask(taskId, message);
        return 'failed';
    } finally {
        activeCanvasTaskPolls.delete(taskId);
    }
}

async function waitCanvasImageTaskResult(taskId, options={}){
    if(!taskId) throw new Error(tr('canvas.generationFailed'));
    while(true){
        const cascadeTargetId = cascadeTargetIdFromOptions(options);
        if(cascadeTargetId) ensureCascadeActive(cascadeTargetId);
        const res = await cascadeFetch(`/api/canvas-image-tasks/${encodeURIComponent(taskId)}`, {}, {cascadeTargetId});
        if(!res.ok){
            if(res.status === 404) throw new Error(cascadeBackendRestartMessage());
            throw new Error(await responseErrorMessage(res, tr('canvas.generationFailed')));
        }
        const data = await res.json();
        if(data.status === 'succeeded') return data.result || {};
        if(data.status === 'failed') throw new Error(data.error || tr('canvas.generationFailed'));
        await sleep(1800);
    }
}

function failCanvasImageTask(taskId, message, taskData={}){
    const found = findPendingTask(taskId);
    if(!found) return;
    const {out, pending} = found;
    const run = pending.run || {};
    const runMs = nowMs() - Number(pending.startedAt || nowMs());
    const recoverTaskId = taskData?.upstream_task_id || taskData?.task_id || extractUpstreamTaskId(message);
    const gen = getNodes().find(n => n.id === run?.node?.id);
    if(recoverTaskId){
        pending.failed = true;
        pending.querying = false;
        pending.error = message || tr('canvas.generationFailed');
        pending.recoverTaskId = recoverTaskId;
        pending.providerId = taskData?.provider_id || pending.providerId || providerIdForPending(pending);
        pending.canvasTaskStatus = 'failed';
        if(gen){
            gen.runStatus = 'failed';
            gen.runError = pending.error;
            if(pending?.cascadeTargetId) gen._cascadeFailed = true;
            gen.running = false;
        }
        addGenerationLog({run, outputs:[], runMs, error:pending.error});
        refreshRunNodes(gen, out);
        scheduleSave();
        return;
    }
    out._pending = (out._pending || []).filter(p => p.id !== pending.id);
    if(gen){
        gen.runStatus = 'failed';
        gen.runError = message || tr('canvas.generationFailed');
        if(pending?.cascadeTargetId) gen._cascadeFailed = true;
        gen.running = false;
    }
    addGenerationLog({run, outputs:[], runMs, error:message || tr('canvas.generationFailed')});
    refreshRunNodes(gen, out);
    scheduleSave();
}

function outputForNode(node, dx=460){
    if(!node || !shouldCreateOutputForNode(node)) return null;
    let out = getConnections()
        .filter(c => c.from === node.id)
        .map(c => getNodes().find(n => n.id === c.to))
        .find(n => n?.type === 'output');
    if(!out){
        out = {id:uid('out'), type:'output', x:node.x + dx, y:node.y, images:[]};
        getNodes().push(out);
        getConnections().push({id:uid('c'), from:node.id, to:out.id});
    }
    return out;
}

function refreshRunNodes(node, out=null){
    refreshNodes([node?.id, out?.id]);
}

        return Object.freeze({
            responseErrorMessage: responseErrorMessage,
            runLTXDirectorNode: runLTXDirectorNode,
            rhUseWallet: rhUseWallet,
            runRhNode: runRhNode,
            runRhModelNode: runRhModelNode,
            runGenerator: runGenerator,
            runGeneratorLegacy: runGeneratorLegacy,
            midjourneyRequest: midjourneyRequest,
            waitMidjourneyTask: waitMidjourneyTask,
            runMidjourneyNode: runMidjourneyNode,
            runMidjourneyAction: runMidjourneyAction,
            runMidjourneyModal: runMidjourneyModal,
            runVideoNode: runVideoNode,
            runMiniMaxRunningHub: runMiniMaxRunningHub,
            runMiniMaxNode: runMiniMaxNode,
            uploadCanvasUrlToComfy: uploadCanvasUrlToComfy,
            runComfyUpscale: runComfyUpscale,
            runComfyNode: runComfyNode,
            runQueuedComfyGenerate: runQueuedComfyGenerate,
            callCanvasLLM: callCanvasLLM,
            runLLMNode: runLLMNode,
            runLLMChat: runLLMChat,
            runSnapshot: runSnapshot,
            runTaskLabel: runTaskLabel,
            runPlatformLabel: runPlatformLabel,
            makePendingForRun: makePendingForRun,
            createCanvasImageTask: createCanvasImageTask,
            createCanvasComfyTask: createCanvasComfyTask,
            waitCanvasComfyTaskResult: waitCanvasComfyTaskResult,
            pollCanvasImageTask: pollCanvasImageTask,
            waitCanvasImageTaskResult: waitCanvasImageTaskResult,
            failCanvasImageTask: failCanvasImageTask,
            outputForNode: outputForNode,
            refreshRunNodes: refreshRunNodes
        });
    }

    window.WorkbenchCanvasClassicExecutorRuntime = Object.freeze({ create: create, REQUIRED_OPS: REQUIRED_OPS });
})();
