/*
 * static/js/workbench/canvas/classic-asset-runtime.js
 *
 * Wave 16b of R4-38 — bounded compat seam for the Classic asset /
 * upload / drop / manager surface (the R4-31 `asset-library`
 * DEFER-R8 capability and its satellite helpers): the canvas asset
 * library + asset manager renderers, the file/url upload pipeline,
 * the image-drop materialization handlers, and the workflow
 * import/export helpers.
 *
 * The function bodies are the page originals, byte-for-byte except
 * that the two mutable page bindings (canvas / nodes) and the asset
 * library state lets become host getters, and the seven state lets
 * this surface writes (activeCanvasAssetCategoryId /
 * activeCanvasAssetLibraryId / activeCanvasWorkflowCategoryId /
 * activePromptLibraryId / canvasAssetLibrary /
 * canvasPromptTemplatesLoaded / localCanvasAssetLibrary) become
 * host getter+setter pairs — page state stays page-owned. canvas.js
 * keeps a 1-line wrapper per function, so all callers — page event
 * wiring, canvas.html inline handlers, and the other seams' host-op
 * injections — keep working unchanged.
 *
 * R8 owns the real Asset/Collection runtime; extraction changes who
 * hosts the code, not its DEFER-R8 disposition.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        'activeCanvasMediaCategory', 'activeCanvasWorkflowCategory', 'applyTempShUrlToCanvasRef', 'bindCanvasPreviewImageFallbacks', 'canUseVersionedImageCreation',
        'canvasMediaCategories', 'canvasMediaPreviewUrl', 'canvasPreviewImgHtml', 'canvasVideoPreviewHtml', 'canvasWorkflowCategories',
        'closeWorkflowTransferModal', 'copyTextToClipboard', 'createImageCardFromUrl', 'createImageCardsFromLocalPaths', 'createVersionedDroppedMediaNode',
        'defaultPoint', 'ensureCanvas', 'escapeAttr', 'escapeHtml', 'fillImageNode',
        'generatorSources', 'hasImageFiles', 'hasOutputImageDrag', 'insertWorkflowIntoCanvas', 'isAudioUrl',
        'isCanvasInputDrag', 'isRemoteVideoReferenceUrl', 'isVideoUrl', 'langIsEn', 'loadCanvasPromptTemplates',
        'mediaKindForRef', 'nodeBounds', 'orderedSources', 'outputImageName', 'outputUrlValue',
        'pushUndo', 'refreshIcons', 'refreshNodes', 'render', 'responseErrorMessage',
        'rhDefaultValue', 'rhParamKey', 'rhUseWallet', 'rhWorkflowNodeInfoList', 'scheduleSave',
        'screenToWorld', 'selectedWorkflowPayload', 'setImageNodeFromOutput', 'setStatus', 'showErrorModal',
        'tr', 'uid', 'updateWorkflowTransferMeta', 'workflowFilename', 'CANVAS_UPLOAD_MAX',
        'IMAGE_DROP_EXT_RE', 'IMAGE_DROP_TEXT_TYPES', 'IMAGE_DROP_TYPE_HINT_RE', 'LOCAL_CANVAS_ASSET_LIBRARY_ID', 'assetManagerBody',
        'assetManagerModal', 'canvasAssetAddCategoryBtn', 'canvasAssetCategorySelect', 'canvasAssetDropZone', 'canvasAssetGrid',
        'canvasAssetHoverPreview', 'canvasAssetLibrarySelect', 'canvasAssetPanel', 'canvasAssetToggle', 'dropOverlay',
        'missingAssetUrls', 'promptTemplateLibrarySelect', 'selected', 'workflowExportLibraryBtn', 'workflowExportMeta',
        'workflowTransferModal', 'workflowTransferSub', 'getActiveCanvasAssetCategoryId', 'getActiveCanvasAssetLibraryId', 'getActiveCanvasWorkflowCategoryId',
        'getActivePromptLibraryId', 'getAssetManagerTab', 'getCanvasAssetLibrary', 'getCanvasAssetLibraryOpen', 'getCanvasPromptLibraries', 'getCanvasPromptTemplateOverrides',
        'getCanvasPromptTemplatesLoaded', 'getLocalCanvasAssetLibrary', 'getManagerSelectedAssetIds', 'getManagerSelectedPromptIds', 'getManagerSelectedWorkflowIds',
        'setActiveCanvasAssetCategoryId', 'setActiveCanvasAssetLibraryId', 'setActiveCanvasWorkflowCategoryId', 'setActivePromptLibraryId', 'setCanvasAssetLibrary',
        'setCanvasPromptTemplatesLoaded', 'setLocalCanvasAssetLibrary', 'setCanvasAssetLibraryOpen', 'getCanvas', 'getNodes',
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicAssetRuntime.create: host must be an object');
        }
        for (var k = 0; k < REQUIRED_OPS.length; k++) {
            if (typeof host[REQUIRED_OPS[k]] === 'undefined') {
                throw new TypeError('WorkbenchCanvasClassicAssetRuntime.create: missing required host op "' + REQUIRED_OPS[k] + '"');
            }
        }

        var activeCanvasMediaCategory = host.activeCanvasMediaCategory, activeCanvasWorkflowCategory = host.activeCanvasWorkflowCategory, applyTempShUrlToCanvasRef = host.applyTempShUrlToCanvasRef, bindCanvasPreviewImageFallbacks = host.bindCanvasPreviewImageFallbacks, canUseVersionedImageCreation = host.canUseVersionedImageCreation, canvasMediaCategories = host.canvasMediaCategories;
        var canvasMediaPreviewUrl = host.canvasMediaPreviewUrl, canvasPreviewImgHtml = host.canvasPreviewImgHtml, canvasVideoPreviewHtml = host.canvasVideoPreviewHtml, canvasWorkflowCategories = host.canvasWorkflowCategories, closeWorkflowTransferModal = host.closeWorkflowTransferModal, copyTextToClipboard = host.copyTextToClipboard;
        var createImageCardFromUrl = host.createImageCardFromUrl, createImageCardsFromLocalPaths = host.createImageCardsFromLocalPaths, createVersionedDroppedMediaNode = host.createVersionedDroppedMediaNode, defaultPoint = host.defaultPoint, ensureCanvas = host.ensureCanvas, escapeAttr = host.escapeAttr;
        var escapeHtml = host.escapeHtml, fillImageNode = host.fillImageNode, generatorSources = host.generatorSources, hasImageFiles = host.hasImageFiles, hasOutputImageDrag = host.hasOutputImageDrag, insertWorkflowIntoCanvas = host.insertWorkflowIntoCanvas;
        var isAudioUrl = host.isAudioUrl, isCanvasInputDrag = host.isCanvasInputDrag, isRemoteVideoReferenceUrl = host.isRemoteVideoReferenceUrl, isVideoUrl = host.isVideoUrl, langIsEn = host.langIsEn, loadCanvasPromptTemplates = host.loadCanvasPromptTemplates;
        var mediaKindForRef = host.mediaKindForRef, nodeBounds = host.nodeBounds, orderedSources = host.orderedSources, outputImageName = host.outputImageName, outputUrlValue = host.outputUrlValue, pushUndo = host.pushUndo;
        var refreshIcons = host.refreshIcons, refreshNodes = host.refreshNodes, render = host.render, responseErrorMessage = host.responseErrorMessage, rhDefaultValue = host.rhDefaultValue, rhParamKey = host.rhParamKey;
        var rhUseWallet = host.rhUseWallet, rhWorkflowNodeInfoList = host.rhWorkflowNodeInfoList, scheduleSave = host.scheduleSave, screenToWorld = host.screenToWorld, selectedWorkflowPayload = host.selectedWorkflowPayload, setImageNodeFromOutput = host.setImageNodeFromOutput;
        var setStatus = host.setStatus, showErrorModal = host.showErrorModal, tr = host.tr, uid = host.uid, updateWorkflowTransferMeta = host.updateWorkflowTransferMeta, workflowFilename = host.workflowFilename;
        var CANVAS_UPLOAD_MAX = host.CANVAS_UPLOAD_MAX;
        var IMAGE_DROP_EXT_RE = host.IMAGE_DROP_EXT_RE;
        var IMAGE_DROP_TEXT_TYPES = host.IMAGE_DROP_TEXT_TYPES;
        var IMAGE_DROP_TYPE_HINT_RE = host.IMAGE_DROP_TYPE_HINT_RE;
        var LOCAL_CANVAS_ASSET_LIBRARY_ID = host.LOCAL_CANVAS_ASSET_LIBRARY_ID;
        var assetManagerBody = host.assetManagerBody;
        var assetManagerModal = host.assetManagerModal;
        var canvasAssetAddCategoryBtn = host.canvasAssetAddCategoryBtn;
        var canvasAssetCategorySelect = host.canvasAssetCategorySelect;
        var canvasAssetDropZone = host.canvasAssetDropZone;
        var canvasAssetGrid = host.canvasAssetGrid;
        var canvasAssetHoverPreview = host.canvasAssetHoverPreview;
        var canvasAssetLibrarySelect = host.canvasAssetLibrarySelect;
        var canvasAssetPanel = host.canvasAssetPanel;
        var canvasAssetToggle = host.canvasAssetToggle;
        var dropOverlay = host.dropOverlay;
        var missingAssetUrls = host.missingAssetUrls;
        var promptTemplateLibrarySelect = host.promptTemplateLibrarySelect;
        var selected = host.selected;
        var workflowExportLibraryBtn = host.workflowExportLibraryBtn;
        var workflowExportMeta = host.workflowExportMeta;
        var workflowTransferModal = host.workflowTransferModal;
        var workflowTransferSub = host.workflowTransferSub;
        var getActiveCanvasAssetCategoryId = host.getActiveCanvasAssetCategoryId;
        var getActiveCanvasAssetLibraryId = host.getActiveCanvasAssetLibraryId;
        var getActiveCanvasWorkflowCategoryId = host.getActiveCanvasWorkflowCategoryId;
        var getActivePromptLibraryId = host.getActivePromptLibraryId;
        var getAssetManagerTab = host.getAssetManagerTab;
        var getCanvasAssetLibrary = host.getCanvasAssetLibrary;
        var getCanvasPromptLibraries = host.getCanvasPromptLibraries;
        var getCanvasPromptTemplateOverrides = host.getCanvasPromptTemplateOverrides;
        var getCanvasPromptTemplatesLoaded = host.getCanvasPromptTemplatesLoaded;
        var getLocalCanvasAssetLibrary = host.getLocalCanvasAssetLibrary;
        var getManagerSelectedAssetIds = host.getManagerSelectedAssetIds;
        var getManagerSelectedPromptIds = host.getManagerSelectedPromptIds;
        var getManagerSelectedWorkflowIds = host.getManagerSelectedWorkflowIds;
        var setActiveCanvasAssetCategoryId = host.setActiveCanvasAssetCategoryId;
        var setActiveCanvasAssetLibraryId = host.setActiveCanvasAssetLibraryId;
        var setActiveCanvasWorkflowCategoryId = host.setActiveCanvasWorkflowCategoryId;
        var setActivePromptLibraryId = host.setActivePromptLibraryId;
        var setCanvasAssetLibrary = host.setCanvasAssetLibrary;
        var setCanvasPromptTemplatesLoaded = host.setCanvasPromptTemplatesLoaded;
        var setLocalCanvasAssetLibrary = host.setLocalCanvasAssetLibrary;
        var setCanvasAssetLibraryOpen = host.setCanvasAssetLibraryOpen;
        var getCanvasAssetLibraryOpen = host.getCanvasAssetLibraryOpen;
        var getCanvas = host.getCanvas, getNodes = host.getNodes;

        // ── Asset / upload / drop bodies (page originals; see header) ──

function activeCanvasAssetCategory(){
    const cats = canvasAssetCategories();
    return cats.find(cat => cat.id === getActiveCanvasAssetCategoryId()) || cats[0] || null;
}

function activeCanvasAssetLibrary(){
    if(canvasAssetLibraryIsLocal()) return canvasAssetSourceLibraries().find(lib => lib.id === LOCAL_CANVAS_ASSET_LIBRARY_ID);
    const libs = canvasAssetLibraries();
    return libs.find(lib => lib.id === getActiveCanvasAssetLibraryId()) || libs[0] || null;
}

function activeCanvasPromptLibrary(){
    return getCanvasPromptLibraries().find(lib => lib.id === getActivePromptLibraryId()) || getCanvasPromptLibraries()[0] || {id:'system', name:'系统提示词库', readonly:true, items:[]};
}

function activeCanvasPromptLibraryItems(){
    const lib = activeCanvasPromptLibrary();
    const hidden = new Set(getCanvasPromptTemplateOverrides().hiddenBuiltinIds || []);
    if(lib.id !== 'system'){
        return (lib.items || []).filter(t => t?.id && t?.positive).map(t => ({
            ...t,
            sourceId:t.id,
            remote:true,
            libraryId:lib.id,
            libraryName:lib.name || '提示词库',
            builtin:false,
        }));
    }
    const system = getCanvasPromptLibraries().find(item => item.id === 'system') || lib;
    const builtins = (system.items || [])
        .filter(t => t?.id && t?.positive && !hidden.has(t.id))
        .map(t => ({
            ...t,
            ...(getCanvasPromptTemplateOverrides().editedBuiltins?.[t.id] || {}),
            sourceId:t.id,
            builtin:true,
            // 系统提示词库本身是后端真实库（/api/prompt-libraries 返回的 system 库），标记为 remote，
            // 这样编辑/删除走后端 PATCH/DELETE 并同步（与智能画布一致），而不是只存本地、不同步。
            remote:true,
            libraryId:'system',
            libraryName:'系统提示词库',
        }));
    const remotes = getCanvasPromptLibraries()
        .filter(item => item.id !== 'system')
        .flatMap(item => (item.items || [])
            .filter(t => t?.id && t?.positive)
            .map(t => ({
                ...t,
                sourceId:t.id,
                remote:true,
                builtin:false,
                libraryId:item.id,
                libraryName:item.name || '提示词库',
            })));
    return [...builtins, ...remotes];
}

async function addUrlToCanvasAssetLibrary(url, name=''){
    if(canvasAssetLibraryIsLocal()){ setStatus('本地素材请在素材库管理中上传'); return; }
    const cat = activeCanvasAssetCategory();
    if(!cat){ setStatus('请先创建资产分组'); return; }
    if(String(cat.type || 'image').toLowerCase() === 'workflow'){ setStatus('当前是工作流分组，请切换到图片分组保存媒体'); return; }
    const data = await fetch('/api/asset-library/items', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({library_id:getActiveCanvasAssetLibraryId(), category_id:cat.id, url, name})
    }).then(async r => {
        if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '保存失败');
        return r.json();
    });
    setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
    renderCanvasAssetLibrary();
    setStatus('已保存到资产库');
}

function allowImageNodeDropEvent(e, highlightEl){
    if(hasImageDropData(e.dataTransfer) || hasOutputImageDrag(e.dataTransfer) || Array.from(e.dataTransfer?.types || []).includes('application/x-canvas-asset')){
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'copy';
        highlightEl?.classList.add('drag-over');
        dropOverlay.classList.remove('active');
    }
}

async function applyImageDropPayloadToBoard(payload, point){
    if(payload.type === 'files'){
        if(payload.files.length > 1) return uploadImageGroup(payload.files, point);
        return uploadImages(payload.files, point);
    }
    if(payload.type === 'localPaths') return createImageCardsFromLocalPaths(payload.localPaths, point);
    if(payload.type === 'url') {
        createImageCardFromUrl(payload.url, point, outputImageName(payload.url));
        return [];
    }
    return [];
}

async function applyImageDropPayloadToNode(nodeId, payload){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || node.type !== 'image') return;
    if(payload.type === 'files') {
        await fillImageNode(nodeId, payload.files, {group:payload.files.length > 1});
        return;
    }
    if(payload.type === 'localPaths') {
        const files = await importLocalImages((payload.localPaths || []).slice(0, CANVAS_UPLOAD_MAX));
        const file = files[0];
        if(file?.url) {
            pushUndo();
            node.url = file.url;
            node.name = file.name || outputImageName(file.url);
            node.mediaKind = 'image';
            render();
            scheduleSave();
        }
        return;
    }
    if(payload.type === 'url' && payload.url){
        pushUndo();
        node.url = payload.url;
        node.name = outputImageName(payload.url);
        node.mediaKind = isVideoUrl(payload.url) ? 'video' : isAudioUrl(payload.url) ? 'audio' : 'image';
        render();
        scheduleSave();
    }
}

function applyUploadedUrlToRefs(refs, node){
    return (refs || []).map(ref => {
        if(!ref?.url) return ref;
        const url = tempShUploadedUrlForNode(node, ref.url);
        return url && url !== ref.url ? {...ref, url, originalLocalUrl:ref.originalLocalUrl || ref.url} : ref;
    });
}

function canvasAssetCategories(){
    return (activeCanvasAssetLibrary()?.categories || getCanvasAssetLibrary().categories || []).filter(cat => {
        const type = String(cat.type || 'image').toLowerCase();
        return type === 'image' || type === 'media' || type === 'workflow';
    });
}

function canvasAssetItemKind(item){
    const explicit = String(item?.kind || item?.mediaKind || '').toLowerCase();
    if(['image','video','audio','text','file','workflow'].includes(explicit)) return explicit;
    if(String(item?.type || '').toLowerCase() === 'workflow') return 'workflow';
    const url = String(item?.url || item || '');
    if(/\.(json|zip)(\?|#|$)/i.test(url)) return 'workflow';
    if(isVideoUrl(url)) return 'video';
    if(isAudioUrl(url)) return 'audio';
    return 'image';
}

function canvasAssetLibraries(){
    return Array.isArray(getCanvasAssetLibrary().libraries) && getCanvasAssetLibrary().libraries.length ? getCanvasAssetLibrary().libraries : [{id:'default', name:'默认资产库', categories:getCanvasAssetLibrary().categories || []}];
}

function canvasAssetLibraryIsLocal(){
    return getActiveCanvasAssetLibraryId() === LOCAL_CANVAS_ASSET_LIBRARY_ID;
}

function canvasAssetSourceLibraries(){
    return [
        ...canvasAssetLibraries(),
        {id:LOCAL_CANVAS_ASSET_LIBRARY_ID, name:'本地素材', categories:localCanvasAssetFolderCategories(), readonly:true, source:'local'}
    ];
}

function canvasAssetThumbHtml(item){
    const kind = canvasAssetItemKind(item);
    const url = escapeAttr(item?.url || '');
    const thumbUrl = item?.thumbnail || item?.url || '';
    if(kind === 'video'){
        return `<div class="canvas-asset-thumb-wrap">${canvasVideoPreviewHtml(item?.url || '', 512, 'class="canvas-asset-thumb" alt=""')}<div class="canvas-asset-video-badge"><i data-lucide="play"></i><span>VIDEO</span></div></div>`;
    }
    if(kind === 'audio'){
        return `<div class="canvas-asset-thumb-wrap canvas-asset-file-thumb"><i data-lucide="file-audio" class="w-6 h-6"></i><span>${escapeHtml(item?.name || 'audio')}</span></div>`;
    }
    if(kind === 'workflow'){
        return `<div class="canvas-asset-thumb-wrap canvas-asset-file-thumb workflow-thumb"><i data-lucide="workflow" class="w-6 h-6"></i><span>${escapeHtml(item?.name || 'workflow')}</span></div>`;
    }
    return `<div class="canvas-asset-thumb-wrap">${canvasPreviewImgHtml(thumbUrl, 512, 'class="canvas-asset-thumb" alt=""')}</div>`;
}

function canvasLocalAssetUrls(){
    const urls = new Set();
    const add = value => {
        const url = outputUrlValue(value);
        if(url && (url.startsWith('/output/') || url.startsWith('/assets/'))) urls.add(url);
    };
    getNodes().forEach(node => {
        if(node.url) add(node.url);
        (node.images || []).forEach(add);
        (node.generatedOutputs || []).forEach(add);
        Object.entries(node.imageComparisons || {}).forEach(([key, value]) => {
            add(key);
            add(value);
        });
    });
    (getCanvas()?.logs || []).forEach(log => {
        (log.outputs || []).forEach(add);
        (log.refs || []).forEach(add);
        (log.run?.refs || []).forEach(add);
    });
    return [...urls];
}

function clearImageNodeDropState(e, highlightEl){
    e.preventDefault();
    e.stopPropagation();
    highlightEl?.classList.remove('drag-over');
    dropOverlay.classList.remove('active');
}

function closeAssetManager(){
    assetManagerModal?.classList.remove('open');
}

function createGroupForUploadedNodes(created, point){
    const targets = [...(created || [])].filter(n => n?.type === 'image');
    if(targets.length < 2) return null;
    render();
    const box = nodeBounds(targets.map(n => n.id));
    const fallback = point || defaultPoint(0, 0);
    const group = {
        id:uid('grp'),
        type:'group',
        x:Number.isFinite(box.x) ? box.x - 24 : fallback.x - 24,
        y:Number.isFinite(box.y) ? box.y - 58 : fallback.y - 58,
        w:Number.isFinite(box.w) ? box.w + 48 : 600,
        h:Number.isFinite(box.h) ? box.h + 90 : 420,
        items:targets.map(n => n.id)
    };
    getNodes().push(group);
    selected.clear();
    selected.add(group.id);
    return group;
}

function currentCanvasAssetItem(itemId){
    return (activeCanvasAssetCategory()?.items || []).find(item => item.id === itemId)
        || (activeCanvasWorkflowCategory()?.items || []).find(item => item.id === itemId)
        || null;
}

function currentCanvasPromptTemplateLibraryEditable(){
    // 系统库后端 readonly=false，也允许新增/编辑（走后端，与智能画布、素材库管理同步）。只按 readonly 判断。
    const lib = activeCanvasPromptLibrary();
    return Boolean(lib && !lib.readonly);
}

function defaultWorkflowAssetTarget(){
    const libs = canvasAssetLibraries();
    let lib = activeCanvasAssetLibrary() || libs[0] || null;
    if(!lib) return {libraryId:'', categoryId:''};
    let cat = (lib.categories || []).find(item => String(item.type || '').toLowerCase() === 'workflow');
    if(!cat){
        lib = libs.find(item => (item.categories || []).some(cat => String(cat.type || '').toLowerCase() === 'workflow')) || lib;
        cat = (lib.categories || []).find(item => String(item.type || '').toLowerCase() === 'workflow');
    }
    return {libraryId:lib?.id || '', categoryId:cat?.id || ''};
}

async function deleteCanvasAssetItem(itemId){
    const item = currentCanvasAssetItem(itemId);
    if(!item || !window.confirm(`删除资产「${item.name || 'asset'}」？`)) return;
    const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {method:'DELETE'}).then(r => r.json());
    setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
    getManagerSelectedAssetIds().delete(item.id);
    getManagerSelectedWorkflowIds().delete(item.id);
    hideCanvasAssetHoverPreview();
    renderCanvasAssetLibrary();
    if(assetManagerModal?.classList.contains('open')) renderAssetManager();
}

function dropDataTypes(dataTransfer){
    return [...(dataTransfer?.types || [])].map(type => String(type || ''));
}

function dropTextCandidates(dataTransfer){
    return window.WorkbenchCanvasMediaDrop.textCandidates(dataTransfer, IMAGE_DROP_TEXT_TYPES);
}

async function exportSelectedWorkflow(includeResources=false){
    if(!getCanvas()) return;
    const payload = selectedWorkflowPayload();
    if(!payload.nodes.length){
        if(workflowExportMeta) workflowExportMeta.textContent = '未选择节点，请先框选要导出的组件';
        if(workflowTransferSub) workflowTransferSub.textContent = '请先框选节点再导出；导入会追加到当前画布';
        setStatus('未选择节点，请先框选要导出的组件');
        return;
    }
    try {
        if(!includeResources){
            const filename = workflowFilename('json');
            window.WorkbenchCanvasWorkflowTransfer.downloadBlob(window.WorkbenchCanvasWorkflowTransfer.jsonExportBlob(payload), filename, {revokeAfterMs:1200});
            setStatus('已导出工作流 JSON');
            return;
        }
        const filename = workflowFilename('zip');
        const blob = await window.WorkbenchCanvasWorkflowTransfer.exportArchive(payload, filename);
        window.WorkbenchCanvasWorkflowTransfer.downloadBlob(blob, filename, {revokeAfterMs:1200});
        setStatus('已导出包含资源的工作流包');
    } catch(err) {
        showErrorModal(err.message || '导出工作流失败', '导出工作流');
    }
}

async function exportSelectedWorkflowToLibrary(){
    if(!getCanvas()) return;
    const payload = selectedWorkflowPayload();
    if(!payload.nodes.length){
        if(workflowExportMeta) workflowExportMeta.textContent = '未选择节点，请先框选要导出的组件';
        setStatus('未选择节点，请先框选要导出的组件');
        return;
    }
    try {
        setWorkflowLibraryExportState('busy', '导出中...');
        if(workflowExportMeta){
            workflowExportMeta.classList.remove('success');
            workflowExportMeta.classList.add('busy');
            workflowExportMeta.textContent = '正在导出到资产库...';
        }
        if(workflowTransferSub) workflowTransferSub.textContent = '正在保存工作流到资产库';
        setStatus('正在导出工作流到资产库...');
        if(!getCanvasAssetLibrary()?.libraries?.length) await loadCanvasAssetLibrary({renderPanel:false});
        const filename = workflowFilename('zip');
        const target = defaultWorkflowAssetTarget();
        const res = await fetch('/api/canvas-workflows/export-to-library', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({...payload, include_resources:true, filename, name:filename.replace(/\.zip$/i, ''), library_id:target.libraryId, category_id:target.categoryId})
        });
        if(!res.ok) throw new Error(await responseErrorMessage(res, '导出到资产库失败'));
        const data = await res.json();
        setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
        setActiveCanvasAssetLibraryId(target.libraryId || getCanvasAssetLibrary().active_library_id || getActiveCanvasAssetLibraryId());
        setActiveCanvasAssetCategoryId(data.item ? findCanvasAssetCategoryForItem(data.item.id)?.id || getActiveCanvasAssetCategoryId() : getActiveCanvasAssetCategoryId());
        renderCanvasAssetLibrary();
        if(assetManagerModal?.classList.contains('open')) renderAssetManager();
        const itemName = data.item?.name || '工作流';
        if(workflowExportMeta){
            workflowExportMeta.classList.remove('busy');
            workflowExportMeta.classList.add('success');
            workflowExportMeta.textContent = `已导出到资产库：${itemName}`;
        }
        if(workflowTransferSub) workflowTransferSub.textContent = '导出完成，可在资产库的工作流分组中查看';
        setWorkflowLibraryExportState('success', '已导出');
        setStatus(`已导出工作流到资产库：${itemName}`);
        setTimeout(() => {
            setWorkflowLibraryExportState('idle');
            if(workflowTransferModal?.classList.contains('open')) updateWorkflowTransferMeta();
        }, 1800);
    } catch(err) {
        setWorkflowLibraryExportState('idle');
        workflowExportMeta?.classList.remove('busy', 'success');
        showErrorModal(err.message || '导出到资产库失败', '导出工作流');
    }
}

function findCanvasAssetCategoryForItem(itemId){
    for(const lib of canvasAssetLibraries()){
        for(const cat of lib.categories || []){
            if((cat.items || []).some(item => item.id === itemId)) return cat;
        }
    }
    return null;
}

async function handleImageNodeDropEvent(e, nodeId, highlightEl){
    if(hasOutputImageDrag(e.dataTransfer)){
        clearImageNodeDropState(e, highlightEl);
        setImageNodeFromOutput(nodeId, e.dataTransfer.getData('application/x-canvas-output-image'));
        return;
    }
    const payload = await resolveImageDropPayload(e.dataTransfer);
    clearImageNodeDropState(e, highlightEl);
    if(payload.type === 'none') return;
    try {
        await applyImageDropPayloadToNode(nodeId, payload);
    } catch(err) {
        setStatus('Ready');
        showErrorModal(err.message || (langIsEn() ? 'Image import failed' : '导入图片失败'), langIsEn() ? 'Image import failed' : '导入图片失败');
    }
}

function hasCanvasAssetSaveDrop(dataTransfer){
    return hasOutputImageDrag(dataTransfer) || hasImageDropData(dataTransfer);
}

function hasImageDropData(dataTransfer){
    if(!dataTransfer) return false;
    if(isCanvasInputDrag(dataTransfer)) return false;
    if(imageFilesFromDataTransfer(dataTransfer).length) return true;
    if(hasImageFiles(dataTransfer.items)) return true;
    const types = dropDataTypes(dataTransfer);
    if(types.some(type => IMAGE_DROP_TYPE_HINT_RE.test(type.toLowerCase()))) return true;
    return imageDropPayload(dataTransfer).type !== 'none';
}

function hideCanvasAssetHoverPreview(){
    if(!canvasAssetHoverPreview) return;
    canvasAssetHoverPreview.style.display = 'none';
    canvasAssetHoverPreview.hidden = true;
    const img = canvasAssetHoverPreview.querySelector('img');
    if(img) img.removeAttribute('src');
    const video = canvasAssetHoverPreview.querySelector('video');
    if(video) {
        video.pause?.();
        video.removeAttribute('src');
    }
}

function imageDropPayload(dataTransfer){
    return window.WorkbenchCanvasMediaDrop.payload(dataTransfer, {
        textTypes:IMAGE_DROP_TEXT_TYPES,
        isSupportedFile:isSupportedUploadFile,
        isLocalValue:isLocalImageDropValue,
        isRemoteValue:isRemoteImageDropValue,
    });
}

async function importLocalImages(paths){
    if(!paths?.length) return [];
    const response = await fetch('/api/ai/import-local-image', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({paths})
    });
    if(!response.ok) throw new Error(await responseErrorMessage(response, langIsEn() ? 'Local image import failed' : '导入本地图片失败'));
    const data = await response.json();
    return data.files || [];
}

async function importWorkflowAssetUrl(url, name='workflow'){
    if(!getCanvas() || !url) return;
    try {
        const res = await fetch(url, {cache:'no-store'});
        if(!res.ok) throw new Error('读取工作流资产失败');
        const blob = await res.blob();
        const fileName = name && /\.(json|zip)$/i.test(name) ? name : (url.split('/').pop()?.split('?')[0] || `${name || 'workflow'}.zip`);
        await importWorkflowFile(new File([blob], fileName, {type:blob.type || 'application/octet-stream'}));
    } catch(err) {
        showErrorModal(err.message || '导入工作流资产失败', '导入工作流');
    }
}

async function importWorkflowFile(file){
    if(!getCanvas() || !file) return;
    try {
        const data = await window.WorkbenchCanvasWorkflowTransfer.importArchive(file);
        insertWorkflowIntoCanvas(window.WorkbenchCanvasWorkflowTransfer.normalizeImported(data));
        closeWorkflowTransferModal();
    } catch(err) {
        showErrorModal(err.message || '导入工作流失败', '导入工作流');
    }
}

function isLocalImageDropValue(value){
    const text = String(value || '').trim();
    if(!text) return false;
    let path = text;
    if(/^file:/i.test(path)){
        try {
            const url = new URL(path);
            if(url.protocol !== 'file:') return false;
            path = decodeURIComponent(url.pathname || path);
        } catch(_) {
            return false;
        }
    }
    if(/^\/[a-zA-Z]:[\\/]/.test(path)) path = path.slice(1);
    const clean = path.split(/[?#]/, 1)[0];
    const isWindowsPath = /^[a-zA-Z]:[\\/]/.test(clean);
    const isPosixPath = clean.startsWith('/');
    return (isWindowsPath || isPosixPath) && IMAGE_DROP_EXT_RE.test(clean);
}

function isMissingAssetUrl(url){
    return Boolean(url && missingAssetUrls.has(url));
}

function isRemoteImageDropValue(value){
    const text = String(value || '').trim();
    return /^https?:\/\/.+/i.test(text) || /^data:image\//i.test(text) || /^blob:/i.test(text);
}

function isSupportedUploadFile(file){
    const type = String(file?.type || '').toLowerCase();
    const name = String(file?.name || '').toLowerCase();
    return type.startsWith('image/') || type.startsWith('video/') || type.startsWith('audio/')
        || /\.(png|jpe?g|webp|gif|bmp|avif|mp4|webm|mov|m4v|avi|mkv|mp3|wav|m4a|aac|ogg|flac)(\?|$)/.test(name);
}

function layoutUploadedMediaNodes(created, base){
    const list = [...(created || [])];
    if(!list.length) return;
    const cols = Math.min(3, Math.max(1, Math.ceil(Math.sqrt(list.length))));
    const gapX = 280;
    const gapY = 250;
    const startX = base.x - ((cols - 1) * gapX) / 2;
    list.forEach((node, i) => {
        node.x = startX + (i % cols) * gapX;
        node.y = base.y + Math.floor(i / cols) * gapY;
    });
}

async function loadCanvasAssetLibrary({renderPanel=true}={}){
    try {
        const [data, localData] = await Promise.all([
            fetch('/api/asset-library').then(r => r.json()),
            fetch('/api/local-assets').then(r => r.ok ? r.json() : {items:[], tree:null}).catch(() => ({items:[], tree:null}))
        ]);
        setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
        setLocalCanvasAssetLibrary({items:Array.isArray(localData.items) ? localData.items : [], tree:localData.tree || null});
        const libs = canvasAssetLibraries();
        if(!getActiveCanvasAssetLibraryId()) setActiveCanvasAssetLibraryId(getCanvasAssetLibrary().active_library_id || libs[0]?.id || '');
        if(getActiveCanvasAssetLibraryId() !== LOCAL_CANVAS_ASSET_LIBRARY_ID && !libs.some(lib => lib.id === getActiveCanvasAssetLibraryId())) setActiveCanvasAssetLibraryId(libs[0]?.id || '');
        const cats = canvasAssetCategories();
        if(!cats.some(cat => cat.id === getActiveCanvasAssetCategoryId())) setActiveCanvasAssetCategoryId(cats[0]?.id || '');
        if(renderPanel) renderCanvasAssetLibrary();
        return data;
    } catch(e) {
        setStatus('资产库加载失败');
        return null;
    }
}

function localCanvasAssetFolderCategories(){
    const result = [];
    const walk = node => {
        if(!node) return;
        const isRoot = (node.id || node.path || '__root__') === '__root__';
        result.push({
            id: node.id || (node.path ? node.path : '__root__'),
            name: node.name || (node.path ? node.path.split('/').pop() : '全部上传'),
            type: 'image',
            items: (isRoot ? (getLocalCanvasAssetLibrary().items || []) : (node.items || [])).filter(item => canvasAssetItemKind(item) === 'image'),
            readonly: true,
            source: 'local',
        });
        (node.children || []).forEach(walk);
    };
    walk(getLocalCanvasAssetLibrary().tree || {id:'__root__', name:'全部上传', items:getLocalCanvasAssetLibrary().items || [], children:[]});
    return result.filter(cat => cat.id === '__root__' || cat.items.length || (getLocalCanvasAssetLibrary().tree?.children || []).length);
}

function mediaKindForUpload(file){
    return window.WorkbenchCanvasMediaKind.kindForFile(file, {allowText:false});
}

function missingAssetHtml(url, compact=false){
    return `<div class="missing-asset ${compact ? 'compact' : ''}" title="${escapeAttr(url || '')}"><i data-lucide="image-off" class="${compact ? 'w-4 h-4' : 'w-6 h-6'}"></i><span>${langIsEn() ? 'Missing file' : '文件缺失'}</span></div>`;
}

function openAssetManager(){
    assetManagerModal?.classList.add('open');
    getManagerSelectedAssetIds().clear();
    getManagerSelectedPromptIds().clear();
    setCanvasPromptTemplatesLoaded(false);
    Promise.all([loadCanvasAssetLibrary({renderPanel:false}), loadCanvasPromptTemplates()]).then(renderAssetManager);
}

function positionCanvasAssetHoverPreview(event){
    if(!canvasAssetHoverPreview || canvasAssetHoverPreview.hidden || canvasAssetHoverPreview.style.display === 'none') return;
    const pad = 14;
    const w = canvasAssetHoverPreview.offsetWidth || 280;
    const h = canvasAssetHoverPreview.offsetHeight || 330;
    let left = event.clientX - w - 16;
    if(left < pad) left = event.clientX + 16;
    left = Math.max(pad, Math.min(window.innerWidth - w - pad, left));
    const top = Math.max(pad, Math.min(window.innerHeight - h - pad, event.clientY + 12));
    canvasAssetHoverPreview.style.left = `${left}px`;
    canvasAssetHoverPreview.style.top = `${top}px`;
}

async function refreshMissingCanvasAssets(){
    missingAssetUrls.clear();
    const urls = canvasLocalAssetUrls();
    if(!urls.length) return;
    try {
        const data = await fetch('/api/canvas-assets/check', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({urls})
        }).then(r => r.json());
        const exists = data.exists || {};
        Object.entries(exists).forEach(([url, ok]) => { if(!ok) missingAssetUrls.add(url); });
    } catch(e) {
        console.warn('canvas asset check failed', e);
    }
}

async function renameCanvasAssetItem(itemId){
    const item = currentCanvasAssetItem(itemId);
    const name = window.prompt('资产名称', item?.name || '');
    if(!item || !String(name || '').trim()) return;
    const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {
        method:'PATCH',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name:String(name).trim()})
    }).then(r => r.json());
    setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
    renderCanvasAssetLibrary();
    if(assetManagerModal?.classList.contains('open')) renderAssetManager();
}

function renderAssetManager(){
    if(!assetManagerBody) return;
    document.querySelectorAll('[data-manager-tab]').forEach(btn => btn.classList.toggle('active', btn.dataset.managerTab === getAssetManagerTab()));
    if(getAssetManagerTab() === 'prompts') renderPromptAssetManager();
    else if(getAssetManagerTab() === 'workflows') renderWorkflowAssetManager();
    else renderImageAssetManager();
    refreshIcons();
}

function renderCanvasAssetLibrary(){
    if(!canvasAssetPanel || !canvasAssetGrid) return;
    hideCanvasAssetHoverPreview();
    const libs = canvasAssetSourceLibraries();
    if(!getActiveCanvasAssetLibraryId() || !libs.some(lib => lib.id === getActiveCanvasAssetLibraryId())) setActiveCanvasAssetLibraryId(getCanvasAssetLibrary().active_library_id || canvasAssetLibraries()[0]?.id || LOCAL_CANVAS_ASSET_LIBRARY_ID);
    if(canvasAssetLibrarySelect){
        canvasAssetLibrarySelect.innerHTML = libs.map(lib => `<option value="${escapeAttr(lib.id)}" ${lib.id === getActiveCanvasAssetLibraryId() ? 'selected' : ''}>${escapeHtml(lib.name || '资产库')}</option>`).join('');
    }
    const cats = canvasAssetCategories();
    if(!cats.some(cat => cat.id === getActiveCanvasAssetCategoryId())) setActiveCanvasAssetCategoryId(cats[0]?.id || '');
    if(canvasAssetCategorySelect){
        canvasAssetCategorySelect.innerHTML = cats.map(cat => {
            const type = String(cat.type || 'image').toLowerCase();
            const prefix = type === 'workflow' ? '工作流 / ' : '';
            return `<option value="${escapeAttr(cat.id)}" ${cat.id === getActiveCanvasAssetCategoryId() ? 'selected' : ''}>${escapeHtml(prefix + (cat.name || '默认分组'))}</option>`;
        }).join('');
    }
    const cat = activeCanvasAssetCategory();
    const catType = String(cat?.type || 'image').toLowerCase();
    const localMode = canvasAssetLibraryIsLocal();
    if(canvasAssetAddCategoryBtn) canvasAssetAddCategoryBtn.disabled = localMode;
    if(canvasAssetDropZone) {
        canvasAssetDropZone.style.display = localMode ? 'none' : 'flex';
        canvasAssetDropZone.textContent = catType === 'workflow' ? '工作流分组支持上传/导出工作流，双击卡片导入画布' : '拖入图片或输出保存到当前分组';
    }
    const items = cat?.items || [];
    canvasAssetGrid.innerHTML = items.length ? items.map(item => `
        <div class="canvas-asset-item" draggable="true" data-asset-id="${escapeAttr(item.id || '')}" data-url="${escapeAttr(item.url)}" data-name="${escapeAttr(item.name || 'asset')}" data-kind="${escapeAttr(canvasAssetItemKind(item))}">
            ${canvasAssetThumbHtml(item)}
            <div class="canvas-asset-meta">
                <span class="canvas-asset-name" title="${escapeAttr(item.name || '')}">${escapeHtml(item.name || 'asset')}</span>
                ${localMode
                    ? `<span class="canvas-asset-local-tag">本地</span>`
                    : `<button class="canvas-asset-action" type="button" data-canvas-asset-rename="${escapeAttr(item.id || '')}" title="重命名" aria-label="重命名"><i data-lucide="pencil" class="w-4 h-4"></i></button>
                       <button class="canvas-asset-action danger" type="button" data-canvas-asset-delete="${escapeAttr(item.id || '')}" title="删除" aria-label="删除"><i data-lucide="trash-2" class="w-4 h-4"></i></button>`}
            </div>
        </div>
    `).join('') : `<div class="canvas-asset-empty">${escapeHtml(localMode ? '暂无本地素材，请在素材库管理中上传' : '当前分组还没有资产')}</div>`;
    bindCanvasPreviewImageFallbacks(canvasAssetGrid);
    canvasAssetGrid.querySelectorAll('.canvas-asset-item').forEach(card => {
        card.addEventListener('dragstart', event => {
            event.dataTransfer.effectAllowed = 'copy';
            event.dataTransfer.setData('application/x-canvas-asset', JSON.stringify({url:card.dataset.url, name:card.dataset.name, kind:card.dataset.kind || ''}));
            event.dataTransfer.setData('text/plain', card.dataset.url || '');
        });
        card.addEventListener('dblclick', () => {
            if(card.dataset.kind === 'workflow') importWorkflowAssetUrl(card.dataset.url, card.dataset.name || 'workflow');
            else createImageCardFromUrl(card.dataset.url, defaultPoint(0, 0), card.dataset.name || 'asset');
        });
        const item = items.find(entry => entry.id === card.dataset.assetId);
        card.addEventListener('mouseenter', event => showCanvasAssetHoverPreview(event, item));
        card.addEventListener('mousemove', positionCanvasAssetHoverPreview);
        card.addEventListener('mouseleave', hideCanvasAssetHoverPreview);
        card.querySelectorAll('.canvas-asset-action').forEach(btn => {
            btn.addEventListener('pointerdown', event => event.stopPropagation());
            btn.addEventListener('dblclick', event => event.stopPropagation());
        });
        card.querySelector('[data-canvas-asset-rename]')?.addEventListener('click', async event => {
            event.preventDefault();
            event.stopPropagation();
            hideCanvasAssetHoverPreview();
            await renameCanvasAssetItem(event.currentTarget.dataset.canvasAssetRename || '');
        });
        card.querySelector('[data-canvas-asset-delete]')?.addEventListener('click', async event => {
            event.preventDefault();
            event.stopPropagation();
            await deleteCanvasAssetItem(event.currentTarget.dataset.canvasAssetDelete || '');
        });
    });
    refreshIcons();
}

function renderCanvasPromptLibrarySelect(){
    if(!promptTemplateLibrarySelect) return;
    promptTemplateLibrarySelect.innerHTML = getCanvasPromptLibraries().map(lib => `<option value="${escapeAttr(lib.id)}" ${lib.id === getActivePromptLibraryId() ? 'selected' : ''}>${escapeHtml(lib.name || '提示词库')}</option>`).join('');
}

function renderImageAssetManager(){
    const libs = canvasAssetLibraries();
    const library = activeCanvasAssetLibrary();
    const cats = canvasMediaCategories();
    if(!cats.some(cat => cat.id === getActiveCanvasAssetCategoryId())) setActiveCanvasAssetCategoryId(cats[0]?.id || '');
    const cat = activeCanvasMediaCategory();
    const items = cat?.items || [];
    const canEditLibrary = !!library;
    const canEditCategory = !!cat;
    assetManagerBody.innerHTML = `
        <div class="asset-manager-side">
            <div class="asset-manager-tools">
                <button type="button" class="primary" data-manager-asset-lib-new><i data-lucide="plus" class="w-4 h-4"></i><span>新资产库</span></button>
                <button type="button" ${!canEditLibrary ? 'disabled' : ''} data-manager-asset-lib-rename><i data-lucide="pencil" class="w-4 h-4"></i><span>重命名</span></button>
                <button type="button" class="danger" ${libs.length <= 1 ? 'disabled' : ''} data-manager-asset-lib-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除库</span></button>
            </div>
            <div class="asset-manager-list">
                ${libs.map(lib => `<button type="button" class="${lib.id === getActiveCanvasAssetLibraryId() ? 'active' : ''}" data-manager-asset-lib="${escapeAttr(lib.id)}"><span>${escapeHtml(lib.name || '资产库')}</span><small>${(lib.categories || []).reduce((n,c)=>n+(c.items || []).length,0)}</small></button>`).join('')}
            </div>
            <div class="asset-manager-tools">
                <button type="button" class="primary" data-manager-asset-cat-new><i data-lucide="folder-plus" class="w-4 h-4"></i><span>新分组</span></button>
                <button type="button" ${!canEditCategory ? 'disabled' : ''} data-manager-asset-cat-rename><i data-lucide="pencil" class="w-4 h-4"></i><span>重命名</span></button>
                <button type="button" class="danger" ${!canEditCategory ? 'disabled' : ''} data-manager-asset-cat-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除组</span></button>
            </div>
            <div class="asset-manager-list">
                ${cats.map(item => `<button type="button" class="${item.id === getActiveCanvasAssetCategoryId() ? 'active' : ''}" data-manager-asset-cat="${escapeAttr(item.id)}"><span>${escapeHtml(item.name || '分组')}</span><small>${(item.items || []).length}</small></button>`).join('')}
            </div>
        </div>
        <div class="asset-manager-main">
            <div class="asset-manager-tools">
                <label class="${!cat ? 'disabled' : ''}"><i data-lucide="upload" class="w-4 h-4"></i><span>批量上传</span><input id="managerAssetUpload" type="file" multiple accept="image/*" ${!cat ? 'disabled' : ''}></label>
                <button type="button" class="danger" ${getManagerSelectedAssetIds().size ? '' : 'disabled'} data-manager-asset-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除所选 ${getManagerSelectedAssetIds().size ? getManagerSelectedAssetIds().size : ''}</span></button>
            </div>
            <div class="asset-manager-grid">
                ${items.length ? items.map(item => `<div class="asset-manager-card">
                    <input type="checkbox" data-manager-asset-check="${escapeAttr(item.id)}" ${getManagerSelectedAssetIds().has(item.id) ? 'checked' : ''}>
                    ${canvasPreviewImgHtml(item.thumbnail || item.url || '', 512, 'alt=""')}
                    <span class="asset-manager-card-name" title="${escapeAttr(item.name || '')}">${escapeHtml(item.name || 'asset')}</span>
                    <div class="asset-manager-card-actions">
                        <button type="button" data-manager-asset-rename="${escapeAttr(item.id)}"><i data-lucide="pencil" class="w-3.5 h-3.5"></i><span>重命名</span></button>
                        <button type="button" class="danger" data-manager-asset-remove="${escapeAttr(item.id)}"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i><span>删除</span></button>
                    </div>
                </div>`).join('') : `<div class="canvas-asset-empty">当前分组为空</div>`}
            </div>
        </div>
    `;
    bindCanvasPreviewImageFallbacks(assetManagerBody);
    const upload = document.getElementById('managerAssetUpload');
    upload?.addEventListener('change', async () => {
        if(!upload.files?.length || !cat) return;
        const data = await uploadFilesToLibrary(upload.files, library.id, cat.id);
        if(data?.library) setCanvasAssetLibrary(data.library);
        getManagerSelectedAssetIds().clear();
        renderAssetManager();
        renderCanvasAssetLibrary();
    });
}

function renderPromptAssetManager(){
    const libs = getCanvasPromptLibraries().filter(lib => lib.id !== 'system');
    if(!getCanvasPromptLibraries().some(lib => lib.id === getActivePromptLibraryId())) setActivePromptLibraryId(libs[0]?.id || getCanvasPromptLibraries()[0]?.id || 'system');
    const lib = getCanvasPromptLibraries().find(item => item.id === getActivePromptLibraryId()) || libs[0] || null;
    const items = lib?.items || [];
    const canEditLibrary = !!lib && !lib.readonly;
    assetManagerBody.innerHTML = `
        <div class="asset-manager-side">
            <div class="asset-manager-tools">
                <button type="button" class="primary" data-manager-prompt-lib-new><i data-lucide="plus" class="w-4 h-4"></i><span>新提示词库</span></button>
                <button type="button" ${!canEditLibrary ? 'disabled' : ''} data-manager-prompt-lib-rename><i data-lucide="pencil" class="w-4 h-4"></i><span>重命名</span></button>
                <button type="button" class="danger" ${!canEditLibrary || getCanvasPromptLibraries().length <= 1 ? 'disabled' : ''} data-manager-prompt-lib-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除库</span></button>
            </div>
            <div class="asset-manager-list">
                ${getCanvasPromptLibraries().map(library => `<button type="button" class="${library.id === getActivePromptLibraryId() ? 'active' : ''}" data-manager-prompt-lib="${escapeAttr(library.id)}"><span>${escapeHtml(library.name || '提示词库')}</span><small>${(library.items || []).length}</small></button>`).join('')}
            </div>
        </div>
        <div class="asset-manager-main">
            <div class="asset-manager-tools">
                <button type="button" class="primary" ${!lib || lib.readonly ? 'disabled' : ''} data-manager-prompt-new><i data-lucide="file-plus-2" class="w-4 h-4"></i><span>新增提示词</span></button>
                <button type="button" class="danger" ${!lib || lib.readonly || !getManagerSelectedPromptIds().size ? 'disabled' : ''} data-manager-prompt-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除所选 ${getManagerSelectedPromptIds().size ? getManagerSelectedPromptIds().size : ''}</span></button>
            </div>
            <div class="asset-manager-grid">
                ${items.length ? items.map(item => `<div class="asset-manager-card">
                    <input type="checkbox" data-manager-prompt-check="${escapeAttr(item.id)}" ${getManagerSelectedPromptIds().has(item.id) ? 'checked' : ''} ${lib?.readonly ? 'disabled' : ''}>
                    <div class="asset-manager-card-text">${escapeHtml(item.positive || '')}</div>
                    <span class="asset-manager-card-name" title="${escapeAttr(item.name || '')}">${escapeHtml(item.name || '提示词')}</span>
                    <div class="asset-manager-card-actions">
                        <button type="button" ${lib?.readonly ? 'disabled' : ''} data-manager-prompt-edit="${escapeAttr(item.id)}"><i data-lucide="pencil" class="w-3.5 h-3.5"></i><span>编辑</span></button>
                        <button type="button" class="danger" ${lib?.readonly ? 'disabled' : ''} data-manager-prompt-remove="${escapeAttr(item.id)}"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i><span>删除</span></button>
                    </div>
                </div>`).join('') : `<div class="canvas-asset-empty">当前提示词库为空</div>`}
            </div>
        </div>
    `;
}

function renderWorkflowAssetManager(){
    const libs = canvasAssetLibraries();
    const library = activeCanvasAssetLibrary();
    const cats = canvasWorkflowCategories();
    if(!cats.some(cat => cat.id === getActiveCanvasWorkflowCategoryId())) setActiveCanvasWorkflowCategoryId(cats[0]?.id || '');
    const cat = activeCanvasWorkflowCategory();
    const items = cat?.items || [];
    assetManagerBody.innerHTML = `
        <div class="asset-manager-side">
            <div class="asset-manager-tools">
                <button type="button" class="primary" data-manager-workflow-cat-new><i data-lucide="folder-plus" class="w-4 h-4"></i><span>新分组</span></button>
            </div>
            <div class="asset-manager-list">
                ${libs.map(lib => `<button type="button" class="${lib.id === getActiveCanvasAssetLibraryId() ? 'active' : ''}" data-manager-workflow-lib="${escapeAttr(lib.id)}"><span>${escapeHtml(lib.name || '资产库')}</span><small>${(lib.categories || []).filter(c => String(c.type || '') === 'workflow').reduce((n,c)=>n+(c.items || []).length,0)}</small></button>`).join('')}
            </div>
            <div class="asset-manager-list">
                ${cats.map(item => `<button type="button" class="${item.id === getActiveCanvasWorkflowCategoryId() ? 'active' : ''}" data-manager-workflow-cat="${escapeAttr(item.id)}"><span>${escapeHtml(item.name || '工作流')}</span><small>${(item.items || []).length}</small></button>`).join('') || '<div class="canvas-asset-empty">暂无工作流分组</div>'}
            </div>
        </div>
        <div class="asset-manager-main">
            <div class="asset-manager-tools">
                <label class="${!cat ? 'disabled' : ''}"><i data-lucide="upload" class="w-4 h-4"></i><span>上传工作流</span><input id="managerWorkflowUpload" type="file" multiple accept=".json,.zip,application/json,application/zip" ${!cat ? 'disabled' : ''}></label>
                <button type="button" ${!getManagerSelectedWorkflowIds().size ? 'disabled' : ''} data-manager-workflow-export><i data-lucide="download" class="w-4 h-4"></i><span>导出所选 ${getManagerSelectedWorkflowIds().size ? getManagerSelectedWorkflowIds().size : ''}</span></button>
                <button type="button" class="danger" ${getManagerSelectedWorkflowIds().size ? '' : 'disabled'} data-manager-workflow-delete><i data-lucide="trash-2" class="w-4 h-4"></i><span>删除所选 ${getManagerSelectedWorkflowIds().size ? getManagerSelectedWorkflowIds().size : ''}</span></button>
            </div>
            <div class="asset-manager-grid">
                ${items.length ? items.map(item => `<div class="asset-manager-card">
                    <input type="checkbox" data-manager-workflow-check="${escapeAttr(item.id)}" ${getManagerSelectedWorkflowIds().has(item.id) ? 'checked' : ''}>
                    ${workflowAssetThumbHtml(item)}
                    <span class="asset-manager-card-name" title="${escapeAttr(item.name || '')}">${escapeHtml(item.name || 'workflow')}</span>
                    <div class="asset-manager-card-actions">
                        <button type="button" data-manager-workflow-rename="${escapeAttr(item.id)}"><i data-lucide="pencil" class="w-3.5 h-3.5"></i><span>重命名</span></button>
                        <button type="button" class="danger" data-manager-workflow-remove="${escapeAttr(item.id)}"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i><span>删除</span></button>
                    </div>
                </div>`).join('') : `<div class="canvas-asset-empty">当前分组为空</div>`}
            </div>
        </div>
    `;
    const upload = document.getElementById('managerWorkflowUpload');
    upload?.addEventListener('change', async () => {
        if(!upload.files?.length || !cat) return;
        const form = new FormData();
        form.append('library_id', library?.id || '');
        form.append('category_id', cat.id || '');
        [...upload.files].forEach(file => form.append('files', file));
        const data = await fetch('/api/asset-library/workflows/upload', {method:'POST', body:form}).then(r => r.json());
        setCanvasAssetLibrary(data.library || getCanvasAssetLibrary());
        getManagerSelectedWorkflowIds().clear();
        renderAssetManager();
        renderCanvasAssetLibrary();
    });
}

async function resolveImageDropPayload(dataTransfer){
    return window.WorkbenchCanvasMediaDrop.resolvePayload(dataTransfer, {
        textTypes:IMAGE_DROP_TEXT_TYPES,
        isSupportedFile:isSupportedUploadFile,
        isLocalValue:isLocalImageDropValue,
        isRemoteValue:isRemoteImageDropValue,
        shouldTraverse:transfer => hasImageFiles(transfer?.items),
    });
}

function revealCanvasAssetControls(){
    [canvasAssetToggle, canvasAssetPanel, assetManagerModal].forEach(el => {
        if(!el) return;
        el.hidden = false;
        if(el.style?.display === 'none') el.style.display = '';
    });
}

async function rhImportWorkflowJson(nodeId, file){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node || !file) return;
    try {
        const text = await file.text();
        const json = JSON.parse(text);
        const nodeInfoList = rhWorkflowNodeInfoList(json);
        if(!nodeInfoList.length) throw new Error(tr('canvas.rhWorkflowJsonInvalid'));
        node.rhMode = 'workflow';
        node.rhWorkflowInfo = {fileName:file.name || 'api.json', nodeInfoList};
        node.rhParams = node.rhParams || {};
        nodeInfoList.forEach(field => {
            const key = rhParamKey(field.nodeId, field.fieldName);
            if(!node.rhParams[key]) node.rhParams[key] = {value:rhDefaultValue(field)};
        });
        node.runStatus = '';
        node.runError = '';
        render();
        scheduleSave();
    } catch(err) {
        alert(err.message || tr('canvas.rhWorkflowJsonInvalid'));
    }
}

async function rhUploadValueIfNeeded(value, node=null){
    const text = String(value || '').trim();
    if(!text) return '';
    if(!/^https?:\/\//i.test(text) && !text.startsWith('/output/') && !text.startsWith('/assets/')) return text;
    const res = await fetch('/api/runninghub/upload-asset', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url:text, useWallet:rhUseWallet(node)})
    });
    const data = await res.json();
    if(!res.ok || data.success === false) throw new Error(data.detail || data.error || tr('canvas.rhUploadFailed'));
    return data.data?.fileName || text;
}

function setWorkflowLibraryExportState(state='idle', text='导出到资产库'){
    if(!workflowExportLibraryBtn) return;
    workflowExportLibraryBtn.disabled = state === 'busy';
    workflowExportLibraryBtn.classList.toggle('busy', state === 'busy');
    workflowExportLibraryBtn.classList.toggle('success', state === 'success');
    const icon = state === 'busy' ? 'loader-2' : state === 'success' ? 'check' : 'library-big';
    workflowExportLibraryBtn.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4"></i><span>${escapeHtml(text)}</span>`;
    refreshIcons();
}

function showCanvasAssetHoverPreview(event, item){
    if(!canvasAssetHoverPreview || !item?.url) return;
    if(canvasAssetItemKind(item) === 'workflow') return;
    const img = canvasAssetHoverPreview.querySelector('img');
    const video = canvasAssetHoverPreview.querySelector('video');
    const isVideo = canvasAssetItemKind(item) === 'video';
    const name = canvasAssetHoverPreview.querySelector('.canvas-asset-hover-name');
    if(img){
        img.style.display = 'block';
        img.src = canvasMediaPreviewUrl(isVideo ? item.url : (item.thumbnail || item.url || ''), 768);
        img.dataset.previewSrc = img.src || '';
        img.dataset.originalSrc = item.url || item.thumbnail || '';
        img.dataset.url = item.url || item.thumbnail || '';
        img.dataset.previewKind = isVideo ? 'video' : '';
        img.dataset.videoFallbackAttrs = '';
        img.alt = item.name || 'asset preview';
    }
    if(video){
        video.style.display = 'none';
        video.removeAttribute('src');
    }
    bindCanvasPreviewImageFallbacks(canvasAssetHoverPreview);
    if(name) name.textContent = item.name || 'asset';
    canvasAssetHoverPreview.hidden = false;
    canvasAssetHoverPreview.style.display = 'block';
    positionCanvasAssetHoverPreview(event);
}

function tempShUploadedUrlForNode(node, url){
    const match = (node?.tempShLinks || []).find(item => item?.source === url && item?.url);
    return match?.url || url;
}

function toggleCanvasAssetLibrary(open=!getCanvasAssetLibraryOpen()){
    setCanvasAssetLibraryOpen(!!open);
    if(getCanvasAssetLibraryOpen() && workflowTransferModal?.classList.contains('open')) closeWorkflowTransferModal();
    canvasAssetPanel?.classList.toggle('open', getCanvasAssetLibraryOpen());
    canvasAssetToggle?.classList.toggle('active', getCanvasAssetLibraryOpen());
    if(!getCanvasAssetLibraryOpen()) hideCanvasAssetHoverPreview();
    if(getCanvasAssetLibraryOpen()) loadCanvasAssetLibrary();
}

async function uploadCanvasMediaRefToCloud(node, ref){
    const kind = mediaKindForRef(ref);
    if(!ref?.url) throw new Error('没有可上传的媒体');
    if(/^https?:\/\//i.test(ref.url)) return ref.url;
    const response = await fetch('/api/cloud-video/upload', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url:ref.url, service:'auto'})
    });
    if(!response.ok) throw new Error(await responseErrorMessage(response, '云端上传失败'));
    const data = await response.json();
    const uploadedUrl = data.url || '';
    if(!uploadedUrl) throw new Error('云端没有返回链接');
    node.tempShLinks = [
        ...(node.tempShLinks || []).filter(item => item?.source !== ref.url),
        {source:ref.url, url:uploadedUrl, expires:data.expires || '3 days', kind}
    ];
    applyTempShUrlToCanvasRef(ref, uploadedUrl);
    return uploadedUrl;
}

async function uploadCanvasVideosToCloud(nodeId){
    const node = getNodes().find(n => n.id === nodeId);
    if(!node) return [];
    const refs = orderedSources(node, generatorSources(node)).flatMap(src => src.refs || [])
        .filter(ref => ref?.url && ['image','video'].includes(mediaKindForRef(ref)));
    const localRefs = refs.filter(ref => ref?.url && !isRemoteVideoReferenceUrl(ref.url));
    if(!localRefs.length){
        showErrorModal('没有需要上传的本地图片或视频', '上传云端');
        return [];
    }
    node.tempShUploading = true;
    refreshNodes([node.id]);
    try {
        const urls = [];
        for(const ref of localRefs){
            urls.push(await uploadCanvasMediaRefToCloud(node, ref));
        }
        node.tempShUploading = false;
        refreshNodes([node.id, ...localRefs.map(ref => ref.nodeId).filter(Boolean)]);
        scheduleSave();
        await copyTextToClipboard(urls[0]);
        showErrorModal(`已上传 ${urls.length} 个媒体文件到云端，首个链接已复制。链接约 3 天有效。`, '上传云端');
        return urls;
    } catch(e) {
        node.tempShUploading = false;
        refreshNodes([node.id]);
        throw e;
    }
}

async function uploadCroppedBlob(blob, name){
    const form = new FormData();
    form.append('files', blob, name);
    const data = await fetch('/api/ai/upload', {method:'POST', body:form}).then(r=>r.json());
    return data.files?.[0];
}

async function uploadFilesFromDataTransfer(dataTransfer){
    return window.WorkbenchCanvasMediaDrop.filesFromDataTransfer(dataTransfer, isSupportedUploadFile);
}

async function uploadFilesToLibrary(files, libraryId, categoryId){
    const form = new FormData();
    [...files].forEach(file => form.append('files', file));
    const uploaded = await fetch('/api/ai/upload', {method:'POST', body:form}).then(r => r.json());
    const items = (uploaded.files || []).filter(file => file?.url).map(file => ({library_id:libraryId, category_id:categoryId, url:file.url, name:file.name || 'asset'}));
    if(!items.length) return null;
    return fetch('/api/asset-library/items/batch', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({library_id:libraryId, category_id:categoryId, items})
    }).then(r => r.json());
}

async function uploadImageBlobs(blobs){
    const form = new FormData();
    blobs.forEach(item => form.append('files', item.blob, item.name));
    const data = await fetch('/api/ai/upload', {method:'POST', body:form}).then(r=>r.json());
    return data.files || [];
}

async function uploadImageGroup(files, point){
    return uploadMediaFiles(files, point, false, {group:true});
}

async function uploadImages(files, point){
    return uploadMediaFiles(files, point, false);
}

async function uploadMediaFiles(files, point, onlyImages=false, opts={}){
    if(!ensureCanvas()) return;
    const supported = [...files].filter(file => {
        const kind = mediaKindForUpload(file);
        return onlyImages ? kind === 'image' : ['image','video','audio'].includes(kind);
    }).slice(0, CANVAS_UPLOAD_MAX);
    if(!supported.length) return [];
    const uploaded = await window.WorkbenchCanvasMediaDrop.uploadFiles(supported);
    const base = point || screenToWorld(window.innerWidth / 2, window.innerHeight / 2);
    const created = [];
    for(const [i, file] of uploaded.entries()) {
        const kind = file.kind || mediaKindForUpload(supported[i]);
        const position = {x:base.x + i * 36, y:base.y + i * 36};
        if(canUseVersionedImageCreation()){
            const createdThroughController = await createVersionedDroppedMediaNode({...file, kind}, position);
            created.push(createdThroughController);
            continue;
        }
        const node = {
            id:uid('img'),
            type:'image',
            x:position.x,
            y:position.y,
            url:file.url,
            name:file.name,
            mediaKind:kind
        };
        getNodes().push(node);
        created.push(node);
    }
    if(opts.group && created.length > 1){
        layoutUploadedMediaNodes(created, base);
        created.group = createGroupForUploadedNodes(created, base);
    }
    render();
    if(!canUseVersionedImageCreation() || opts.group) scheduleSave();
    return created;
}

function workflowAssetThumbHtml(item){
    return `<div class="asset-manager-card-text workflow-manager-thumb"><i data-lucide="workflow" class="w-6 h-6"></i><span>${escapeHtml(item?.format === 'json' ? 'JSON 工作流' : 'ZIP 工作流包')}</span></div>`;
}

        return Object.freeze({
            activeCanvasAssetCategory: activeCanvasAssetCategory,
            activeCanvasAssetLibrary: activeCanvasAssetLibrary,
            activeCanvasPromptLibrary: activeCanvasPromptLibrary,
            activeCanvasPromptLibraryItems: activeCanvasPromptLibraryItems,
            addUrlToCanvasAssetLibrary: addUrlToCanvasAssetLibrary,
            allowImageNodeDropEvent: allowImageNodeDropEvent,
            applyImageDropPayloadToBoard: applyImageDropPayloadToBoard,
            applyImageDropPayloadToNode: applyImageDropPayloadToNode,
            applyUploadedUrlToRefs: applyUploadedUrlToRefs,
            canvasAssetCategories: canvasAssetCategories,
            canvasAssetItemKind: canvasAssetItemKind,
            canvasAssetLibraries: canvasAssetLibraries,
            canvasAssetLibraryIsLocal: canvasAssetLibraryIsLocal,
            canvasAssetSourceLibraries: canvasAssetSourceLibraries,
            canvasAssetThumbHtml: canvasAssetThumbHtml,
            canvasLocalAssetUrls: canvasLocalAssetUrls,
            clearImageNodeDropState: clearImageNodeDropState,
            closeAssetManager: closeAssetManager,
            createGroupForUploadedNodes: createGroupForUploadedNodes,
            currentCanvasAssetItem: currentCanvasAssetItem,
            currentCanvasPromptTemplateLibraryEditable: currentCanvasPromptTemplateLibraryEditable,
            defaultWorkflowAssetTarget: defaultWorkflowAssetTarget,
            deleteCanvasAssetItem: deleteCanvasAssetItem,
            dropDataTypes: dropDataTypes,
            dropTextCandidates: dropTextCandidates,
            exportSelectedWorkflow: exportSelectedWorkflow,
            exportSelectedWorkflowToLibrary: exportSelectedWorkflowToLibrary,
            findCanvasAssetCategoryForItem: findCanvasAssetCategoryForItem,
            handleImageNodeDropEvent: handleImageNodeDropEvent,
            hasCanvasAssetSaveDrop: hasCanvasAssetSaveDrop,
            hasImageDropData: hasImageDropData,
            hideCanvasAssetHoverPreview: hideCanvasAssetHoverPreview,
            imageDropPayload: imageDropPayload,
            importLocalImages: importLocalImages,
            importWorkflowAssetUrl: importWorkflowAssetUrl,
            importWorkflowFile: importWorkflowFile,
            isLocalImageDropValue: isLocalImageDropValue,
            isMissingAssetUrl: isMissingAssetUrl,
            isRemoteImageDropValue: isRemoteImageDropValue,
            isSupportedUploadFile: isSupportedUploadFile,
            layoutUploadedMediaNodes: layoutUploadedMediaNodes,
            loadCanvasAssetLibrary: loadCanvasAssetLibrary,
            localCanvasAssetFolderCategories: localCanvasAssetFolderCategories,
            mediaKindForUpload: mediaKindForUpload,
            missingAssetHtml: missingAssetHtml,
            openAssetManager: openAssetManager,
            positionCanvasAssetHoverPreview: positionCanvasAssetHoverPreview,
            refreshMissingCanvasAssets: refreshMissingCanvasAssets,
            renameCanvasAssetItem: renameCanvasAssetItem,
            renderAssetManager: renderAssetManager,
            renderCanvasAssetLibrary: renderCanvasAssetLibrary,
            renderCanvasPromptLibrarySelect: renderCanvasPromptLibrarySelect,
            renderImageAssetManager: renderImageAssetManager,
            renderPromptAssetManager: renderPromptAssetManager,
            renderWorkflowAssetManager: renderWorkflowAssetManager,
            resolveImageDropPayload: resolveImageDropPayload,
            revealCanvasAssetControls: revealCanvasAssetControls,
            rhImportWorkflowJson: rhImportWorkflowJson,
            rhUploadValueIfNeeded: rhUploadValueIfNeeded,
            setWorkflowLibraryExportState: setWorkflowLibraryExportState,
            showCanvasAssetHoverPreview: showCanvasAssetHoverPreview,
            tempShUploadedUrlForNode: tempShUploadedUrlForNode,
            toggleCanvasAssetLibrary: toggleCanvasAssetLibrary,
            uploadCanvasMediaRefToCloud: uploadCanvasMediaRefToCloud,
            uploadCanvasVideosToCloud: uploadCanvasVideosToCloud,
            uploadCroppedBlob: uploadCroppedBlob,
            uploadFilesFromDataTransfer: uploadFilesFromDataTransfer,
            uploadFilesToLibrary: uploadFilesToLibrary,
            uploadImageBlobs: uploadImageBlobs,
            uploadImageGroup: uploadImageGroup,
            uploadImages: uploadImages,
            uploadMediaFiles: uploadMediaFiles,
            workflowAssetThumbHtml: workflowAssetThumbHtml
        });
    }

    window.WorkbenchCanvasClassicAssetRuntime = Object.freeze({ create: create, REQUIRED_OPS: REQUIRED_OPS });
})();
