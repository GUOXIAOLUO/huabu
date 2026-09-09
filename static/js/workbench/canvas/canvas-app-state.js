function refreshIcons(){ if(window.lucide) lucide.createIcons(); }
refreshIcons();
function tr(key){ return window.StudioI18n ? StudioI18n.t(key) : key; }
function trf(key, values={}){
    return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), tr(key));
}
function langIsEn(){ return window.StudioI18n?.lang?.() === 'en'; }
const CANVAS_UPLOAD_MAX = 20;
const CANVAS_REFERENCE_IMAGE_MAX = 20;
const CANVAS_MINIMAX_REF_IMAGE_MAX = 9;
const CANVAS_MINIMAX_REF_VIDEO_MAX = 3;
const CANVAS_MINIMAX_REF_AUDIO_MAX = 3;
const CANVAS_MINIMAX_DEFAULT_ENGINE = 'comfyui';
const CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID = '2084608321469898754';
const CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_TITLE = 'Minimax-多参视频生成';
const CANVAS_GENERATOR_TYPES = window.WorkbenchLegacyGraphCompatibility.CLASSIC_GENERATOR_TYPES;
const CANVAS_MEDIA_OUTPUT_TYPES = window.WorkbenchLegacyGraphCompatibility.CLASSIC_MEDIA_OUTPUT_TYPES;
function actionFailed(labelKey, detail=''){
    const label = tr(labelKey);
    return langIsEn() ? `${label} failed${detail ? `: ${detail}` : ''}` : `${label}失败${detail ? `：${detail}` : ''}`;
}
function noReturnedImage(labelKey){ return langIsEn() ? `${tr(labelKey)} failed: no image returned` : `${tr(labelKey)}失败：未返回图片`; }
function canvasOriginalMediaUrl(url){
    return window.WorkbenchCanvasMediaUrl.originalUrl(url, window.location.origin);
}
function canvasFileNameFromUrl(url=''){
    try {
        const parsed = new URL(String(url || ''), window.location.href);
        return decodeURIComponent(parsed.pathname.split('/').filter(Boolean).pop() || '');
    } catch(e) {
        return decodeURIComponent(String(url || '').split('?')[0].split('#')[0].split('/').filter(Boolean).pop() || '');
    }
}
function canvasProxiedMediaUrl(url, name=''){
    const raw = canvasOriginalMediaUrl(url);
    if(!raw || raw.startsWith('/assets/') || raw.startsWith('/output/') || raw.startsWith('data:') || raw.startsWith('blob:')) return raw;
    if(!/^https?:\/\//i.test(raw)) return raw;
    const filename = name || canvasFileNameFromUrl(raw) || 'preview';
    return `/api/download-output?inline=1&url=${encodeURIComponent(raw)}&name=${encodeURIComponent(filename)}`;
}
function canvasDisplayMediaUrl(url, name=''){
    const raw = canvasOriginalMediaUrl(url);
    return /^https?:\/\//i.test(raw) ? canvasProxiedMediaUrl(raw, name) : raw;
}
function canvasMediaPreviewUrl(url, size=512){
    return window.WorkbenchCanvasMediaUrl.previewUrl(url, {
        locationOrigin:window.location.origin,
        size,
        displayUrl:raw => canvasDisplayMediaUrl(raw),
        keepInlineUrl:true,
        keepUnsupportedUrl:true,
        extensions:/\.(png|jpe?g|webp|gif|bmp|avif|tiff?|mp4|webm|mov|m4v|avi|mkv|flv)(\?|#|$)/i,
    });
}
function canvasPreviewImgHtml(url, size=512, attrs=''){
    const original = canvasOriginalMediaUrl(url);
    const preview = canvasMediaPreviewUrl(original, size);
    // loading=lazy：画布内容多时，视口外的缩略图不加载/不解码，避免一次性解码上百张图卡顿；
    // decoding=async：解码放到主线程外，渲染时不阻塞。
    return `<img loading="lazy" decoding="async" src="${escapeAttr(preview)}" data-preview-src="${escapeAttr(preview)}" data-original-src="${escapeAttr(original)}" data-url="${escapeAttr(original)}"${attrs ? ` ${attrs}` : ''}>`;
}
function loadCanvasOriginalImageDimensions(url){
    return window.WorkbenchCanvasMediaPreviewControls.loadImageDimensions(String(url || ''));
}
function canvasVideoPreviewHtml(url, size=512, attrs=''){
    const original = canvasOriginalMediaUrl(url);
    const preview = canvasMediaPreviewUrl(original, size);
    return `<img loading="lazy" decoding="async" src="${escapeAttr(preview)}" data-preview-src="${escapeAttr(preview)}" data-original-src="${escapeAttr(original)}" data-url="${escapeAttr(original)}" data-preview-kind="video"${attrs ? ` ${attrs}` : ''}>`;
}
function canvasVideoFallbackHtml(url, attrs=''){
    const original = canvasOriginalMediaUrl(url);
    const src = canvasDisplayMediaUrl(original);
    return `<video src="${escapeAttr(src)}" data-url="${escapeAttr(original)}" muted preload="metadata" playsinline disablepictureinpicture controlslist="nodownload noplaybackrate noremoteplayback"${attrs ? ` ${attrs}` : ''}></video>`;
}
function canvasVideoPlayerHtml(url, attrs=''){
    const original = canvasOriginalMediaUrl(url);
    const src = canvasDisplayMediaUrl(original);
    return `<video src="${escapeAttr(src)}" data-url="${escapeAttr(original)}" controls autoplay playsinline preload="metadata" disablepictureinpicture controlslist="nodownload noplaybackrate noremoteplayback"${attrs ? ` ${attrs}` : ''}></video>`;
}
function bindCanvasVideoOverlay(video){
    return window.WorkbenchCanvasMediaPreviewControls.bindVideoOverlay(video, {
        boundKey:'canvasVideoOverlayBound',
        overlaySelector:'.canvas-video-play',
    });
}
function canvasActivateVideoPreview(img){
    if(!img) return false;
    const target = img.matches?.('img[data-preview-kind="video"]') ? img : img.querySelector?.('img[data-preview-kind="video"]');
    if(!target) {
        const fallback = img.matches?.('video[data-url]') ? img : img.querySelector?.('video[data-url]');
        if(fallback){
            fallback.controls = true;
            fallback.muted = false;
            fallback.play?.().catch(() => {});
            return true;
        }
        return false;
    }
    const original = canvasOriginalMediaUrl(target.dataset.originalSrc || target.dataset.url || target.getAttribute('src') || '');
    if(!original) return false;
    const tpl = document.createElement('template');
    tpl.innerHTML = canvasVideoPlayerHtml(original, target.dataset.videoPlayerAttrs || '');
    const video = tpl.content.firstElementChild;
    if(!video) return false;
    target.replaceWith(video);
    bindCanvasVideoOverlay(video);
    video.parentElement?.querySelector?.('.canvas-video-play')?.style?.setProperty('display', 'none');
    video.play?.().catch(() => {});
    return true;
}
function isCanvasPreviewImage(img){
    return img?.tagName?.toLowerCase?.() === 'img'
        && img.dataset?.previewSrc
        && img.dataset?.originalSrc
        && img.dataset.previewSrc !== img.dataset.originalSrc
        && img.getAttribute('src') !== img.dataset.originalSrc;
}
function bindCanvasPreviewImageFallbacks(root=document){
    return window.WorkbenchCanvasMediaPreviewControls.bindPreviewImageFallbacks(root, {
        originalUrl:img => img.dataset.originalSrc || img.dataset.url || '',
        videoFallbackHtml:canvasVideoFallbackHtml,
        bindVideoOverlay:bindCanvasVideoOverlay,
    });
}
const CANVAS_SELECTED_HIGH_RES_DELAY = 320;
const CANVAS_HIGH_RES_ZOOM_THRESHOLD = 0.86;
let canvasSelectedHighResTimer = 0;
let canvasSelectedHighResSeq = 0;
let canvasImageResolutionSyncTimer = 0;
const canvasSelectedHighResLoaded = new Set();
const canvasSelectedHighResLoading = new Map();
function canvasImageEditorIsOpen(){
    return Boolean(document.getElementById('imageEditModal')?.classList.contains('open'));
}
function preloadCanvasSelectedHighRes(src){
    if(!src || canvasSelectedHighResLoaded.has(src)) return Promise.resolve(true);
    if(canvasSelectedHighResLoading.has(src)) return canvasSelectedHighResLoading.get(src);
    const task = window.WorkbenchCanvasMediaPreviewControls.preloadImage(src)
        .then(loaded => {
            if(loaded) canvasSelectedHighResLoaded.add(src);
            return loaded;
        })
        .finally(() => canvasSelectedHighResLoading.delete(src));
    canvasSelectedHighResLoading.set(src, task);
    return task;
}
function canvasViewportWantsHighRes(){
    return Number(viewport?.scale || 1) >= CANVAS_HIGH_RES_ZOOM_THRESHOLD;
}
function canvasImageNearViewport(img){
    if(!img?.isConnected || !board) return false;
    const boardRect = board.getBoundingClientRect();
    const rect = img.getBoundingClientRect();
    const margin = 220;
    return rect.right >= boardRect.left - margin && rect.left <= boardRect.right + margin
        && rect.bottom >= boardRect.top - margin && rect.top <= boardRect.bottom + margin;
}
function syncCanvasSelectedImageResolution(root=nodesEl){
    const selectedImages = window.WorkbenchCanvasMediaPreviewControls.collectHighResCandidates({
        root,
        selector:'.node img[data-preview-src][data-original-src]',
        wantHighRes:canvasViewportWantsHighRes(),
        isNearViewport:canvasImageNearViewport,
        originalUrl:img => img.dataset.originalSrc || img.dataset.url || '',
        resolveTarget:canvasDisplayMediaUrl,
        isLoaded:target => canvasSelectedHighResLoaded.has(target),
    });
    if(canvasSelectedHighResTimer) clearTimeout(canvasSelectedHighResTimer);
    const seq = ++canvasSelectedHighResSeq;
    if(!selectedImages.length || canvasImageEditorIsOpen()) return;
    canvasSelectedHighResTimer = setTimeout(async () => {
        canvasSelectedHighResTimer = 0;
        if(seq !== canvasSelectedHighResSeq || canvasImageEditorIsOpen()) return;
        await Promise.all(selectedImages.map(item => preloadCanvasSelectedHighRes(item.target)));
        if(seq !== canvasSelectedHighResSeq || canvasImageEditorIsOpen()) return;
        selectedImages.forEach(({img, target}) => {
            if(!img.isConnected || img.dataset.selectedHighResTarget !== target) return;
            if(!canvasViewportWantsHighRes() || !canvasImageNearViewport(img)) return;
            if(canvasSelectedHighResLoaded.has(target) && img.getAttribute('src') !== target) img.src = target;
        });
    }, CANVAS_SELECTED_HIGH_RES_DELAY);
}
function scheduleCanvasImageResolutionSync(root=nodesEl, delay=120){
    if(canvasImageResolutionSyncTimer) clearTimeout(canvasImageResolutionSyncTimer);
    canvasImageResolutionSyncTimer = setTimeout(() => {
        canvasImageResolutionSyncTimer = 0;
        syncCanvasSelectedImageResolution(root);
    }, Math.max(0, Number(delay) || 0));
}
function applyLanguage(lang){
    if(lang && window.StudioI18n) StudioI18n.set(lang);
    document.title = tr('canvas.title');
    refreshGateViewControls();
    if(canvas) {
        currentCanvasTitle.textContent = canvas?.title || tr('canvas.untitled');
    }
    renderCanvasList();
    render();
}
async function refreshCanvasConfigFromSettings(){
    await loadConfig();
    pruneMissingComfyWorkflows();
    (nodes || []).forEach(node => {
        sanitizeImageNodeProviderModel(node);
        sanitizeVideoNodeProviderModel(node);
    });
    if(typeof render === 'function') render();
}
window.addEventListener('message', event => {
    if(event.origin && event.origin !== location.origin) return;
    if(event.data?.type === 'studio-lang') applyLanguage(event.data.lang);
    if(event.data?.type === 'canvas_updated') handleCanvasUpdatedMessage(event.data);
    if(event.data?.type === 'providers-changed' || event.data?.type === 'workflows-changed' || event.data?.type === 'comfy-instances-changed'){
        refreshCanvasConfigFromSettings();
    }
    if(event.data?.type === 'canvas-focus'){
        // 从其他标签页切换回画布时，重新拉取工作流列表并刷新节点
        refreshCanvasConfigFromSettings();
        if(canvas) syncRemoteCanvasNow();
    }
});
window.addEventListener('studio-lang-change', () => {
    document.title = tr('canvas.title');
    refreshGateViewControls();
    if(canvas) currentCanvasTitle.textContent = canvas?.title || tr('canvas.untitled');
    renderCanvasList();
    render();
});
window.addEventListener('studio-ui-scale-change', applyQuickToolbarState);
const shell = document.getElementById('shell');
const canvasGate = document.getElementById('canvasGate');
const board = document.getElementById('board');
const world = document.getElementById('world');
const nodesEl = document.getElementById('nodes');
const minimap = document.getElementById('minimap');
const minimapContent = document.getElementById('minimapContent');
const canvasArrangeBtn = document.getElementById('canvasArrangeBtn');
let minimapViewport = document.getElementById('minimapViewport');
const linksEl = document.getElementById('links');
const linkControlsEl = document.getElementById('linkControls');
const dropOverlay = document.getElementById('dropOverlay');
const createMenu = document.getElementById('createMenu');
const linkCreateMenu = document.getElementById('linkCreateMenu');
const nodeInputMenu = document.getElementById('nodeInputMenu');
const nodeOutputMenu = document.getElementById('nodeOutputMenu');
const imageNodeMenu = document.getElementById('imageNodeMenu');
const selectionBox = document.getElementById('selectionBox');
const selectionHub = document.getElementById('selectionHub');
const gateStatus = document.getElementById('gateStatus');
const gateCreateBtn = document.getElementById('gateCreateBtn');
const gateCreateSmartBtn = document.getElementById('gateCreateSmartBtn');
const gateRefreshBtn = document.getElementById('gateRefreshBtn');
const gateBackBtn = document.getElementById('gateBackBtn');
const gateTrashBtn = document.getElementById('gateTrashBtn');
const gateAssetManagerBtn = document.getElementById('gateAssetManagerBtn');
const gateTrashCount = document.getElementById('gateTrashCount');
const gateTitleText = document.getElementById('gateTitleText');
const gateSubtitle = document.getElementById('gateSubtitle');
const gateCanvasList = document.getElementById('gateCanvasList');
const gateTitleInput = document.getElementById('gateTitleInput');
const gateConfirmBtn = document.getElementById('gateConfirmBtn');
const gateCancelBtn = document.getElementById('gateCancelBtn');
const backToManagerBtn = document.getElementById('backToManagerBtn');
const currentCanvasTitle = document.getElementById('currentCanvasTitle');
const currentCanvasTime = document.getElementById('currentCanvasTime');
const outputLightbox = document.getElementById('outputLightbox');
const outputPreview = document.getElementById('outputPreview');
const outputLightboxImg = document.getElementById('outputLightboxImg');
const outputCompareContainer = document.getElementById('outputCompareContainer');
const outputCompareResult = document.getElementById('outputCompareResult');
const outputCompareOriginal = document.getElementById('outputCompareOriginal');
const outputCompareOriginalWrap = document.getElementById('outputCompareOriginalWrap');
const outputCompareSlider = document.getElementById('outputCompareSlider');
const outputResolution = document.getElementById('outputResolution');
const outputDownloadBtn = document.getElementById('outputDownloadBtn');
const outputDownloadAllBtn = document.getElementById('outputDownloadAllBtn');
const outputLightboxVideo = document.getElementById('outputLightboxVideo');
const outputPromptPanel = document.getElementById('outputPromptPanel');
const outputPromptText = document.getElementById('outputPromptText');
const outputCopyPromptBtn = document.getElementById('outputCopyPromptBtn');
const outputRerunBtn = document.getElementById('outputRerunBtn');
const promptTemplateModal = document.getElementById('promptTemplateModal');
const promptTemplatePanel = document.getElementById('promptTemplatePanel') || promptTemplateModal?.querySelector('.prompt-template-panel');
const promptTemplateClose = document.getElementById('promptTemplateClose');
const promptTemplateSearch = document.getElementById('promptTemplateSearch');
const promptTemplateLibrarySelect = document.getElementById('promptTemplateLibrarySelect');
const promptTemplateCats = document.getElementById('promptTemplateCats');
const promptTemplateBody = document.getElementById('promptTemplateBody');
const canvasAssetToggle = document.getElementById('canvasAssetToggle');
const canvasAssetPanel = document.getElementById('canvasAssetPanel');
const canvasAssetCloseBtn = document.getElementById('canvasAssetCloseBtn');
const canvasAssetLibrarySelect = document.getElementById('canvasAssetLibrarySelect');
const canvasAssetCategorySelect = document.getElementById('canvasAssetCategorySelect');
const canvasAssetAddCategoryBtn = document.getElementById('canvasAssetAddCategoryBtn');
const canvasAssetDropZone = document.getElementById('canvasAssetDropZone');
const canvasAssetGrid = document.getElementById('canvasAssetGrid');
const canvasAssetHoverPreview = document.getElementById('canvasAssetHoverPreview');
const workflowTransferToggle = document.getElementById('workflowTransferToggle');
const canvasLogToggle = document.getElementById('canvasLogToggle');
const workflowTransferModal = document.getElementById('workflowTransferModal');
const workflowTransferSub = document.getElementById('workflowTransferSub');
const workflowExportMeta = document.getElementById('workflowExportMeta');
const workflowImportInput = document.getElementById('workflowImportInput');
const workflowImportDropZone = document.getElementById('workflowImportDropZone');
const workflowExportLibraryBtn = document.getElementById('workflowExportLibraryBtn');
const assetManagerModal = document.getElementById('assetManagerModal');
const assetManagerBody = document.getElementById('assetManagerBody');
function revealCanvasAssetControls(){ return ensureClassicAssetRuntime().revealCanvasAssetControls(); }
const logModal = document.getElementById('logModal');
const logList = document.getElementById('logList');
const errorModal = document.getElementById('errorModal');
const errorTitle = document.getElementById('errorTitle');
const errorMessage = document.getElementById('errorMessage');
let canvases = [];
let deletedCanvases = [];
let canvas = null;
let nodes = [];
let connections = [];
let viewport = {x: -1800, y: -1000, scale: 1};
let dragNode = null;
let dragBoard = null;
let minimapDrag = false;
let minimapState = null;
let minimapRenderQueued = false;
let minimapViewportQueued = false;
let linksRenderQueued = false;
let zoomPreviewState = null;
let resizeNode = null;
let llmPaneDrag = null;
let tempLink = null;
let knifeActive = false;
let knifePoint = null;
let knifeTrail = [];
let knifeChanged = false;
let knifeNeedsRender = false;
let selectDrag = null;
let isRKeyDown = false;
let menuPoint = null;
let linkCreateState = null;
let internalDrag = false;
const selected = window.WorkbenchInteractionController.createSelectionStore();
// Unified Canvas runtime is the sole product path after R4 flag retirement.
const canvasUnifiedRuntimeEnabled = Boolean(window.WorkbenchCanvasRuntime);
let canvasUnifiedRuntime = null;
function canvasRuntimeGeometry(){
    return nodes.map(node => {
        const size = defaultNodeSize(node.type);
        return {id:node.id, x:Number(node.x) || 0, y:Number(node.y) || 0, w:Number(node.w) || size.w, h:Number(node.h) || size.h};
    });
}
function ensureCanvasUnifiedRuntime(){
    if(!canvasUnifiedRuntimeEnabled) return null;
    if(!canvasUnifiedRuntime){
        canvasUnifiedRuntime = window.WorkbenchCanvasRuntime.create({
            viewport, geometry:canvasRuntimeGeometry(), selectedIds:[...selected], minScale:0.12, maxScale:8,
        });
    }
    return canvasUnifiedRuntime;
}
function syncCanvasRuntimeGeometry(runtime=ensureCanvasUnifiedRuntime()){
    if(!runtime) return null;
    runtime.dispatch({type:window.WorkbenchCanvasRuntime.COMMANDS.GEOMETRY_REPLACE, geometry:canvasRuntimeGeometry()});
    return runtime;
}
function adoptCanvasRuntimeState(nextViewport){
    if(nextViewport) viewport = nextViewport;
    // Canvas state swaps (open/create/remote-replace/return/delete) must reset the
    // runtime: a surviving instance would keep the previous canvas's viewport,
    // geometry and selection and compute zoom-at against a stale base.
    canvasUnifiedRuntime = null;
    return viewport;
}
function applyCanvasRuntimeSelection(ids, toggleId=''){
    const runtime = syncCanvasRuntimeGeometry();
    if(!runtime) return false;
    runtime.dispatch(toggleId
        ? {type:window.WorkbenchCanvasRuntime.COMMANDS.SELECTION_TOGGLE, id:toggleId}
        : {type:window.WorkbenchCanvasRuntime.COMMANDS.SELECTION_REPLACE, ids});
    selected.replace(runtime.snapshot().selectedIds);
    return true;
}
function clearCanvasRuntimeSelection(){
    const runtime = ensureCanvasUnifiedRuntime();
    if(!runtime) return false;
    runtime.dispatch({type:window.WorkbenchCanvasRuntime.COMMANDS.SELECTION_CLEAR});
    selected.clear();
    return true;
}
function applyCanvasRuntimeNodeMove(node){
    const runtime = ensureCanvasUnifiedRuntime();
    if(!runtime || !node?.id) return false;
    const command = {type:window.WorkbenchCanvasRuntime.COMMANDS.NODE_MOVE, id:node.id, x:Number(node.x) || 0, y:Number(node.y) || 0};
    try { runtime.dispatch(command); }
    catch(error) { syncCanvasRuntimeGeometry(runtime); runtime.dispatch(command); }
    return true;
}
function applyCanvasRuntimeNodeResize(node){
    const runtime = ensureCanvasUnifiedRuntime();
    if(!runtime || !node?.id) return false;
    const size = defaultNodeSize(node.type);
    const command = {type:window.WorkbenchCanvasRuntime.COMMANDS.NODE_RESIZE, id:node.id, width:Number(node.w) || size.w, height:Number(node.h) || size.h};
    try { runtime.dispatch(command); }
    catch(error) { syncCanvasRuntimeGeometry(runtime); runtime.dispatch(command); }
    return true;
}
let creatingCanvas = false;
let createCanvasKind = 'classic';
let trashMode = false;
let pendingDeleteCanvasId = null;
let pendingPurgeCanvasId = null;
let emojiPickerCanvasId = null;
let canvasMetaAnchorId = '';
let canvasSortMode = (() => { try { return localStorage.getItem('canvasSortMode') || 'recent'; } catch(e){ return 'recent'; } })();
const CANVAS_LIST_PROJECT_KEY = 'canvasListCurrentProjectId';
const CANVAS_COLOR_OPTIONS = ['red','orange','amber','green','teal','blue','violet','pink','slate'];
// 先绑定返回，避免编辑器后续初始化较慢时丢失来源项目。
backToManagerBtn?.addEventListener('click', () => {
    window.location.href = canvasListUrlForProject(canvas?.project || requestedCanvasListProject() || rememberedCanvasListProject());
});
let canvasSession = null;
function ensureCanvasSession(){
    if(!canvasSession){
        canvasSession = window.WorkbenchCanvasSession.create({
            clientId:CLIENT_ID,
            serialize:serializeCanvasSession,
            applyRecord:applyCanvasSessionRecord,
            setStatus,
            isVisible:() => !document.hidden,
            debounceMs:500,
            remoteApplyDelayMs:1000,
            remotePollIntervalMs:2500,
        });
    }
    return canvasSession;
}
function currentCanvasRevision(){
    const state = canvasSession?.snapshot();
    return Number(state?.revision || state?.updatedAt || canvas?.updated_at || 0);
}
function adoptCanvasRevision(revision, missingFallback){
    return ensureCanvasSession().adoptRevision(revision, missingFallback);
}
let models = {gpt:'gpt-image-2', nano:'nano-banana-pro'};
let imageModels = ['gpt-image-2', 'nano-banana-pro'];
let chatModels = ['gpt-4o-mini'];
let videoModels = [];
let msChatModels = [];
let apiProviders = [];
let comfyBackendCount = 1;
let comfyWorkflows = [];
let comfyWorkflowCache = {};
let runningHubWorkflowCache = {};
let managedProviderId = 'comfly';
let localImageModels = [];
let localChatModels = [];
const MS_GEN_MODELS = {
    zimage:    { label: 'ZImage',     modelId: 'Tongyi-MAI/Z-Image-Turbo',            supportsImage: false, endpoint: '/generate'            },
    qwen_edit: { label: 'Qwen Edit',  modelId: 'Qwen/Qwen-Image-Edit-2511',            supportsImage: true,  endpoint: '/api/angle/generate'  },
    klein_edit:{ label: 'Klein',      modelId: 'black-forest-labs/FLUX.2-klein-9B',   supportsImage: true,  endpoint: '/api/ms/generate'     },
    custom:    { label: '自定义', labelKey: 'canvas.custom', modelId: '',                acceptsImage: true,   endpoint: '/api/ms/generate'     }
};
let hasManagedImageModels = false;
let hasManagedChatModels = false;
let outputCompareDrag = false;
let outputPreviewZoom = 1;
let outputPreviewPan = {x: 0, y: 0};
let outputPreviewPanDrag = null;
let currentOutputCompareUrl = '';
let currentOutputMeta = null;
let currentOutputLightboxOutId = '';
let currentOutputLightboxUrl = '';
const missingAssetUrls = new Set();
let outputTimer = null;
let clipboard = null;
let lastImagePasteAt = 0;
let promptTemplateNodeId = '';
let promptTemplateCategory = 'all';
let promptTemplateSelectedId = '';
let promptTemplateQuery = '';
let promptTemplateEditing = false;
let canvasPromptTemplates = [];
let canvasPromptTemplatesLoaded = false;
let canvasPromptLibraries = [];
let activePromptLibraryId = 'system';
const CANVAS_PROMPT_TEMPLATE_GROUPS_KEY = 'canvas_prompt_template_groups_v1';
const CANVAS_PROMPT_TEMPLATE_OVERRIDES_KEY = 'canvas_prompt_template_overrides';
let promptTemplateGroups = [];
let promptTemplateGroupEditMode = false;
let canvasPromptTemplateOverrides = {hiddenBuiltinIds:[], editedBuiltins:{}};
let canvasAssetLibrary = {categories:[]};
let canvasAssetLibraryOpen = false;
let activeCanvasAssetLibraryId = '';
let activeCanvasAssetCategoryId = '';
const LOCAL_CANVAS_ASSET_LIBRARY_ID = '__local_assets__';
let localCanvasAssetLibrary = {items:[], tree:null};
let assetManagerTab = 'assets';
let managerSelectedAssetIds = new Set();
let managerSelectedWorkflowIds = new Set();
let managerSelectedPromptIds = new Set();
let activeCanvasWorkflowCategoryId = '';
const activeCanvasTaskPolls = new Set();
let hoveredConnectionId = '';
let lastMouseBoard = {x: 0, y: 0};
let undoStack = [];
const UNDO_MAX = 30;
// cascade state moved to classic-cascade-orchestrator.js seam
let cropState = null;
let cropDrag = null;
let cropAspectPreset = 'free';
let cropAspectRatio = null;
let imageEditMode = 'crop';
let imageEditModeTouched = false;
let imageResizeScale = 0.5;
let editDrawState = null;
let editTextItems = [];
let editTextSelectedId = '';
let editTextDrag = null;
let editTextDirty = false;
let editTextInlineEditor = null;
let editDrawUndoStack = [];
let editDrawRedoStack = [];
const EDIT_DRAW_HISTORY_MAX = 40;
let brushTool = 'free';
let brushLabelCounter = 1;
let gridCustomMode = false;
let gridCustomLines = []; // [{type:'h'|'v', pos:0-1}] 相对图片尺寸的分数位置
let gridCustomOrientation = 'h'; // 当前点击放置方向
let gridCustomHistory = []; // 撤销栈：每次放线前快照
let gridCustomDrag = null; // {index, pointerId}
let imageEditZoom = 1.0;
let imageEditBaseW = 0; // zoom=1 时图片显示宽度
let imageEditBaseH = 0;
let textSelectionGuard = null;
const PROMPT_TEXT_MAX_LENGTH = 20000;
const CLIENT_ID = 'canvas_' + Math.random().toString(36).slice(2);
const ZOOM_PREVIEW_NODE_DEFAULT_SCALE = 1;
const ZOOM_PREVIEW_NODE_MAX_SCALE = 1.15;
const LTX_DIRECTOR_WORKFLOW = 'LTXDirectorv2-API.json';
const LTX_DIRECTOR_WF_NODE = '46';
const LTX_DIRECTOR_SEED_NODE = '94:28';
const LTX_SEGMENT_COLORS = ['#e07b3a', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b'];
const CANVAS_EMOJIS = ['layers','sparkles','image','palette','wand-2','star','heart','rocket','flame','moon','cloud','leaf','gem','compass','pin','flag','bookmark','crown'];
function renderCanvasIcon(icon, size = 14) {
    // 旧的默认 emoji 或空值都映射为 layers
    if(!icon || icon === '🧩') return `<i data-lucide="layers" style="width:${size}px;height:${size}px"></i>`;
    // 含非 ASCII 字符（用户旧选过的 emoji）继续按文本渲染
    if(/[^\x00-\x7F]/.test(icon)) return escapeHtml(icon);
    return `<i data-lucide="${escapeHtml(icon)}" style="width:${size}px;height:${size}px"></i>`;
}

const SIZE_MAP = {
    square: { '1k':'1024x1024', '2k':'2048x2048', '4k':'4096x4096' },
    portrait: { '1k':'1024x1536', '2k':'1360x2048', '4k':'2352x3520' },
    portrait43: { '1k':'1008x1344', '2k':'1536x2048', '4k':'2448x3264' },
    landscape43: { '1k':'1344x1008', '2k':'2048x1536', '4k':'3264x2448' },
    landscape: { '1k':'1536x1024', '2k':'2048x1360', '4k':'3520x2352' },
    story: { '1k':'720x1280', '2k':'1152x2048', '4k':'2160x3840' },
    wide: { '1k':'1280x720', '2k':'2048x1152', '4k':'3840x2160' },
    ultrawide: { '1k':'1280x544', '2k':'2048x880', '4k':'3840x1648' },
    ultratall: { '1k':'544x1280', '2k':'880x2048', '4k':'1648x3840' }
};
const API_RATIO_VALUES = {
    square:'1:1',
    portrait:'2:3',
    landscape:'3:2',
    portrait43:'3:4',
    landscape43:'4:3',
    story:'9:16',
    wide:'16:9',
    ultrawide:'21:9',
    ultratall:'9:21'
};
const RES_LONG_SIDE = { '1k':1536, '2k':2048, '4k':3840 };
const RES_PIXEL_LIMIT = { '1k':1572864, '2k':4194304, '4k':8294400 };
const CUSTOM_IMAGE_MODELS_KEY = 'canvas_custom_image_models';
const MANAGED_IMAGE_MODELS_KEY = 'canvas_image_models_ordered';
const MANAGED_CHAT_MODELS_KEY = 'canvas_chat_models_ordered';
const CANVAS_THEME_KEY = 'canvas_theme';
const QUICK_TOOLBAR_COLLAPSED_KEY = 'canvas_quick_toolbar_collapsed';
const CANVAS_SESSION_VIEWPORTS_KEY = 'canvas_session_viewports_v1';
let canvasSessionViewportFallback = {};
let quickToolbarExpanded = false;
const DEFAULT_VIDEO_MODELS = [
    // Veo
    'veo2', 'veo2-fast', 'veo2-pro',
    'veo3', 'veo3-fast', 'veo3-pro',
    'veo3.1', 'veo3.1-fast', 'veo3.1-quality', 'veo3.1-lite',
    // Sora
    'sora-2', 'sora-2-pro',
    // 通义万相
    'wan2.6-t2v', 'wan2.6-i2v',
    'wan2.5-t2v-preview', 'wan2.5-i2v-preview',
    'wan2.2-t2v-plus', 'wan2.2-i2v-plus', 'wan2.2-i2v-flash',
    // Seedance
    'doubao-seedance-2-0-260128',
    'doubao-seedance-2-0-fast-260128',
    'doubao-seedance-1-5-pro-251215',
    'doubao-seedance-1-0-pro-250528',
    'doubao-seedance-1-0-lite-t2v-250428',
    'doubao-seedance-1-0-lite-i2v-250428',
    // Agnes
    'agnes-video-v2.0'
];

function uid(prefix='n'){ return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`; }
function loadLocalViewportMap(){
    try {
        const data = JSON.parse(sessionStorage.getItem(CANVAS_SESSION_VIEWPORTS_KEY) || '{}');
        return data && typeof data === 'object' ? data : {};
    } catch(e) {
        return canvasSessionViewportFallback;
    }
}
function localViewportForCanvas(canvasId, fallback={x:0, y:0, scale:1}){
    const item = loadLocalViewportMap()[canvasId || ''];
    if(!item || typeof item !== 'object') return {...fallback};
    return {
        x:Number.isFinite(Number(item.x)) ? Number(item.x) : Number(fallback.x || 0),
        y:Number.isFinite(Number(item.y)) ? Number(item.y) : Number(fallback.y || 0),
        scale:Number.isFinite(Number(item.scale)) ? Math.max(.12, Math.min(8, Number(item.scale))) : Number(fallback.scale || 1)
    };
}
function saveLocalViewport(){
    if(!canvas?.id) return;
    const map = loadLocalViewportMap();
    map[canvas.id] = {
        x:Number(viewport.x || 0),
        y:Number(viewport.y || 0),
        scale:Number(viewport.scale || 1),
        updatedAt:Date.now()
    };
    canvasSessionViewportFallback = map;
    try {
        sessionStorage.setItem(CANVAS_SESSION_VIEWPORTS_KEY, JSON.stringify(map));
    } catch(e) {}
}
function applyTheme(theme){
    const dark = theme === 'dark';
    document.documentElement.classList.toggle('studio-theme-dark', dark);
    document.documentElement.classList.toggle('theme-dark', dark);
    document.body.classList.toggle('studio-theme-dark', dark);
    document.body.classList.toggle('theme-dark', dark);
    shell.classList.toggle('theme-dark', dark);
}
function applyQuickToolbarState(){
    const toolbar = document.getElementById('quickToolbar');
    if(!toolbar) return;
    const uiScale = Number(getComputedStyle(document.documentElement).getPropertyValue('--studio-ui-scale')) || 1;
    const isScaledUi = uiScale < 0.995;
    const collapsed = !quickToolbarExpanded;
    toolbar.classList.toggle('scale-expanded', isScaledUi && quickToolbarExpanded);
    toolbar.classList.toggle('collapsed', collapsed);
    const btn = toolbar.querySelector('.toolbar-toggle');
    if(btn){
        btn.title = collapsed ? '展开快捷菜单' : '折叠快捷菜单';
        btn.setAttribute('aria-label', btn.title);
    }
    refreshIcons();
}
function toggleQuickToolbar(){
    const toolbar = document.getElementById('quickToolbar');
    quickToolbarExpanded = Boolean(toolbar?.classList.contains('collapsed'));
    applyQuickToolbarState();
}
function loadLocalModelLists(){
    try {
        const managedRaw = localStorage.getItem(MANAGED_IMAGE_MODELS_KEY);
        const raw = JSON.parse(managedRaw || localStorage.getItem(CUSTOM_IMAGE_MODELS_KEY) || '[]');
        localImageModels = Array.isArray(raw) ? raw.filter(Boolean) : [];
        hasManagedImageModels = Boolean(managedRaw);
    } catch(e) {
        localImageModels = [];
        hasManagedImageModels = false;
    }
    try {
        const managedRaw = localStorage.getItem(MANAGED_CHAT_MODELS_KEY);
        const raw = JSON.parse(managedRaw || '[]');
        localChatModels = Array.isArray(raw) ? raw.filter(Boolean) : [];
        hasManagedChatModels = Boolean(managedRaw);
    } catch(e) {
        localChatModels = [];
        hasManagedChatModels = false;
    }
}
function uniqueModels(list){
    const seen = new Set();
    return list.map(item => String(item || '').trim()).filter(item => {
        if(!item || seen.has(item)) return false;
        seen.add(item);
        return true;
    });
}
function defaultApiProviders(){
    return [{id:'comfly', name:'Comfly', base_url:'', enabled:true, image_models:imageModels, chat_models:chatModels, video_models:videoModels.length ? videoModels : DEFAULT_VIDEO_MODELS, has_key:false, key_preview:''}];
}
function isRunningHubProvider(provider){
    const id = String(provider?.id || '').trim().toLowerCase();
    const protocol = String(provider?.protocol || '').trim().toLowerCase();
    const name = String(provider?.name || '').trim().toLowerCase();
    return id === 'runninghub' || protocol === 'runninghub' || name === 'runninghub' || id === 'rh';
}
function normalizeProviderId(value){
    return String(value || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-').slice(0, 40);
}
function imageApiProviders(){
    const providers = (apiProviders.length ? apiProviders : defaultApiProviders())
        .filter(p => p.id !== 'modelscope' && p.enabled !== false && (p.image_models || []).length);
    return providers;
}
function midjourneyApiProviders(){
    return (apiProviders.length ? apiProviders : [])
        .filter(provider => provider.enabled !== false && (
            String(provider.protocol || '').toLowerCase() === 'apimart'
            || /(^|\.)apimart\.ai(?:\/|$)/i.test(String(provider.base_url || ''))
        ));
}
function resolveMidjourneyProviderId(id){
    const providers = midjourneyApiProviders();
    return providers.find(provider => provider.id === id)?.id || providers[0]?.id || '';
}
function midjourneyProviderOptions(selectedId){
    const selected = resolveMidjourneyProviderId(selectedId);
    const providers = midjourneyApiProviders();
    if(!providers.length) return '<option value="" disabled selected>请先配置 APIMart 平台</option>';
    return providers.map(provider => `<option value="${escapeHtml(provider.id)}" ${provider.id === selected ? 'selected' : ''}>${escapeHtml(provider.name || provider.id)}</option>`).join('');
}
function providerById(id){
    return (apiProviders.length ? apiProviders : defaultApiProviders()).find(p => p.id === id) || imageApiProviders()[0] || defaultApiProviders()[0];
}
function resolveProviderId(id){
    return providerById(id)?.id || 'comfly';
}
function chatApiProviders(){
    const providers = (apiProviders.length ? apiProviders : defaultApiProviders())
        .filter(p => p.enabled !== false && (p.chat_models || []).length);
    return providers.length ? providers : defaultApiProviders();
}
function resolveChatProviderId(id){
    const providers = chatApiProviders();
    return providers.find(p => p.id === id)?.id || providers[0]?.id || 'comfly';
}
function chatProviderOptions(selectedId){
    const selected = resolveChatProviderId(selectedId);
    return chatApiProviders().map(provider => `<option value="${escapeHtml(provider.id)}" ${provider.id === selected ? 'selected' : ''}>${escapeHtml(provider.name || provider.id)}</option>`).join('');
}
function providerChatModels(providerId){
    const provider = apiProviders.find(p => p.id === providerId);
    return uniqueModels(provider?.chat_models || []);
}
function resolveImageProviderId(id){
    const providers = imageApiProviders();
    return providers.find(p => p.id === id)?.id || providers[0]?.id || '';
}
function providerOptions(selectedId){
    const selected = resolveImageProviderId(selectedId);
    const providers = imageApiProviders();
    if(!providers.length) return `<option value="" disabled selected>${tr('canvas.noApiProviders') || '暂无 API 平台'}</option>`;
    return providers.map(provider => `<option value="${escapeHtml(provider.id)}" ${provider.id === selected ? 'selected' : ''}>${escapeHtml(provider.name || provider.id)}</option>`).join('');
}
function providerImageModels(providerId){
    // 不走 providerById（会 fallback 到第一个 provider，造成串台），直接查精确匹配
    const provider = apiProviders.find(p => p.id === providerId);
    return uniqueModels(provider?.image_models || []);
}
function sanitizeImageNodeProviderModel(node){
    if(!node || node.type !== 'generator') return;
    node.apiProvider = resolveImageProviderId(node.apiProvider || '');
    const models = providerImageModels(node.apiProvider);
    if(!models.length) node.model = '';
    else if(!models.includes(resolveImageModel(node.model))) node.model = models[0] || '';
}
// `vpp` is a lazily-forwarding object handle (NOT a function). The page-side
// thin wrappers below call `vpp.<method>({...})` with property access, so this
// must expose the seam methods as object properties rather than being callable.
// Declared before its consumers to avoid any temporal-dead-zone exposure.
const vpp = {
    videoApiProviders: function(){ return ensureClassicVideoProviderParams().videoApiProviders(); },
    resolveVideoProviderId: function(arg){ return ensureClassicVideoProviderParams().resolveVideoProviderId(arg || {}); },
    providerVideoModels: function(arg){ return ensureClassicVideoProviderParams().providerVideoModels(arg || {}); },
    renderVideoImageInputs: function(arg){ return ensureClassicVideoProviderParams().renderVideoImageInputs(arg || {}); },
};
function videoProviderOptions(selectedId){
    const selected = vpp.resolveVideoProviderId({id: selectedId});
    return vpp.videoApiProviders().map(provider => `<option value="${escapeHtml(provider.id)}" ${provider.id === selected ? 'selected' : ''}>${escapeHtml(provider.name || provider.id)}</option>`).join('');
}
function allImageModels(providerId){
    const providerModels = providerImageModels(providerId || managedProviderId);
    return uniqueModels(providerModels);
}
function modelscopeImageModels(selected = ''){
    const provider = (apiProviders.length ? apiProviders : []).find(p => p.id === 'modelscope');
    return uniqueModels([
        selected,
        ...((provider?.image_models || []).length ? provider.image_models : []),
        'Tongyi-MAI/Z-Image-Turbo',
        'black-forest-labs/FLUX.2-klein-9B'
    ]);
}
function modelscopeImageModelOptions(selectedModel){
    const selectedValue = selectedModel || modelscopeImageModels()[0] || 'Tongyi-MAI/Z-Image-Turbo';
    return modelscopeImageModels(selectedValue).map(model => `<option value="${escapeHtml(model)}" ${model === selectedValue ? 'selected' : ''}>${escapeHtml(model)}</option>`).join('');
}
function currentMsModelId(modelKey, node){
    if(modelKey === 'custom') return node.msCustomModel || modelscopeImageModels()[0] || 'Tongyi-MAI/Z-Image-Turbo';
    return (MS_GEN_MODELS[modelKey] || MS_GEN_MODELS.zimage).modelId;
}
function modelscopeLorasForModel(modelId){
    const provider = (apiProviders.length ? apiProviders : []).find(p => p.id === 'modelscope');
    const list = Array.isArray(provider?.ms_loras) ? provider.ms_loras : [];
    return list.filter(lora =>
        lora && lora.enabled !== false &&
        String(lora.id || '').trim() &&
        String(lora.target_model || lora.model || '').trim() === String(modelId || '').trim()
    );
}
function modelscopeLoraOptions(loras, selectedId){
    return loras.map(lora => {
        const id = String(lora.id || '').trim();
        const label = String(lora.name || id).trim();
        return `<option value="${escapeHtml(id)}" ${id === selectedId ? 'selected' : ''}>${escapeHtml(label)}</option>`;
    }).join('');
}
function allChatModels(){
    const providerModels = chatApiProviders().flatMap(p => p.chat_models || []);
    return uniqueModels(hasManagedChatModels ? localChatModels : [...providerModels, ...chatModels, ...localChatModels]);
}
function resolveImageModel(value){
    if(value === 'gpt') return models.gpt;
    if(value === 'nano') return models.nano;
    return value || allImageModels(managedProviderId)[0] || models.gpt;
}
function isGptImageAutoSizeModel(model){
    const raw = String(model || '').trim().toLowerCase();
    const normalized = raw.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    const compact = raw.replace(/[^a-z0-9]+/g, '');
    return normalized === 'gpt-image-2'
        || normalized.startsWith('gpt-image-2-')
        || normalized.endsWith('-gpt-image-2')
        || normalized.includes('-gpt-image-2-')
        || compact === 'gptimage2'
        || compact.startsWith('gptimage2')
        || compact.endsWith('gptimage2');
}
function defaultApiImageResolution(model){
    return isGptImageAutoSizeModel(resolveImageModel(model)) ? '4k' : '1k';
}
function normalizedImageQuality(value){
    const quality = String(value || 'auto').trim().toLowerCase();
    return ['low','medium','high'].includes(quality) ? quality : '';
}
function resolveChatModel(value, providerId=''){
    const providerModels = providerId ? providerChatModels(providerId) : [];
    return value || providerModels[0] || allChatModels()[0] || chatModels[0] || 'gpt-4o-mini';
}
function showErrorModal(message, title=tr('canvas.generationFailed')){
    if(!errorModal || !errorMessage){
        alert(message || title);
        return;
    }
    errorTitle.textContent = title || tr('canvas.generationFailed');
    errorMessage.textContent = message || title;
    errorModal.classList.add('open');
    refreshIcons();
}
function apiErrorMessage(data, fallback='请求失败'){
    return window.WorkbenchCanvasHttpError.message(data, fallback);
}
async function responseErrorMessage(response, fallback='请求失败'){ return ensureClassicExecutorRuntime().responseErrorMessage(response, fallback); }
function closeErrorModal(){
    if(errorModal) errorModal.classList.remove('open');
}
async function copyErrorMessage(){
    const text = errorMessage?.textContent || '';
    if(!text) return;
    if(!(await copyTextToClipboard(text))){
        const range = document.createRange();
        range.selectNodeContents(errorMessage);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
}
function copyTextWithCopyEvent(value){
    return WorkbenchCanvasClipboard.copyWithCopyEvent(value);
}
function copyTextWithTextarea(value){
    return WorkbenchCanvasClipboard.copyWithTextarea(value);
}
async function clipboardMatchesText(value){
    return WorkbenchCanvasClipboard.matchesText(value);
}
async function copyTextToClipboard(text){
    return WorkbenchCanvasClipboard.copyText(text);
}
function parseRatioValue(value){
    const raw = String(value || '').trim();
    if(!raw) return null;
    if(raw.includes(':')){
        const [w,h] = raw.split(':').map(Number);
        if(w > 0 && h > 0) return w / h;
    }
    const n = Number(raw);
    return n > 0 ? n : null;
}
function parseSizeValue(value){
    const match = String(value || '').trim().match(/^(\d+)\s*[xX*]\s*(\d+)$/);
    return match ? {width:match[1], height:match[2]} : null;
}
function gcdInt(a, b){
    a = Math.abs(Math.round(Number(a) || 0));
    b = Math.abs(Math.round(Number(b) || 0));
    while(b){ const t = b; b = a % b; a = t; }
    return a || 1;
}
function ratioPartsFromDimensions(width, height){
    const w = Math.max(1, Math.round(Number(width) || 1));
    const h = Math.max(1, Math.round(Number(height) || 1));
    const target = w / h;
    let best = {width:1, height:1, score:Infinity};
    const maxPart = 21;
    for(let rw = 1; rw <= maxPart; rw++){
        for(let rh = 1; rh <= maxPart; rh++){
            const ratio = rw / rh;
            const relativeError = Math.abs(ratio - target) / target;
            const complexityPenalty = Math.max(rw, rh) * 0.0008;
            const score = relativeError + complexityPenalty;
            if(score < best.score) best = {width:rw, height:rh, score};
        }
    }
    const g = gcdInt(best.width, best.height);
    return {width:best.width / g, height:best.height / g};
}
function apiImageSize(ratioValue, resolutionValue, customRatioValue = '', customSizeValue = ''){
    return WorkbenchCanvasImageSize.apiImageSize(ratioValue, resolutionValue, {
        customRatio:customRatioValue,
        customSize:customSizeValue,
        parseRatio:parseRatioValue,
        longSideByResolution:RES_LONG_SIDE,
        pixelLimitByResolution:RES_PIXEL_LIMIT,
        sizeMap:SIZE_MAP,
    });
}
function parseSizePair(value){
    const match = String(value || '').match(/(\d+)\s*x\s*(\d+)/i);
    return match ? {width:Number(match[1]), height:Number(match[2])} : null;
}
function nearestFourKSizeFor(width, height){
    const w = Math.max(1, Number(width) || 1);
    const h = Math.max(1, Number(height) || 1);
    const ratio = w / h;
    let best = null;
    Object.entries(SIZE_MAP).forEach(([key, values]) => {
        const size = parseSizePair(values?.['4k']);
        if(!size) return;
        const score = Math.abs(Math.log(ratio / (size.width / size.height)));
        if(!best || score < best.score) best = {...size, key, score};
    });
    return best;
}
function exceedsFourKStandard(width, height){
    const standard = nearestFourKSizeFor(width, height);
    if(!standard) return false;
    return Number(width) > standard.width || Number(height) > standard.height;
}
function normalizeApiNodeSizeChoice(node){
    if(!node) return;
    const allowAuto = isGptImageAutoSizeModel(resolveImageModel(node.model));
    if(allowAuto && node._apiResolutionUserSet !== true && (!node.resolution || node.resolution === '1k' || node.resolution === 'auto')) node.resolution = defaultApiImageResolution(node.model);
    else if(!node.resolution) node.resolution = defaultApiImageResolution(node.model);
    if(!allowAuto && node.resolution === 'auto') node.resolution = '1k';
}
async function generatorSizeForRun(gen, refs){
    if((gen.ratio || 'square') === 'source'){
        const ref = refs?.[0];
        if(ref?.url){
            try {
                const dims = await getImageDimensions(ref.url);
                const parts = ratioPartsFromDimensions(dims.width, dims.height);
                gen.customRatioWidth = String(parts.width);
                gen.customRatioHeight = String(parts.height);
                gen.customRatio = `${parts.width}:${parts.height}`;
            } catch(_) {}
        }
    }
    const ratio = (gen.ratio === 'source' && !gen.customRatio)
        ? 'square'
        : (gen.ratio ?? 'square');
    return apiImageSize(ratio, gen.resolution || defaultApiImageResolution(gen.model), gen.customRatio || '', gen.customSize || '');
}
function normalizeApiNodeLayout(node){
    if(!node || node.type !== 'generator') return;
    if(Number(node.w || 0) === 418) node.w = 380;
}
function imageModelOptions(selectedModel, providerId){
    if(!imageApiProviders().length){
        return `<option value="" disabled selected>${tr('canvas.noApiProvidersHint') || '暂无 API 平台，请到 API 设置添加'}</option>`;
    }
    const models = allImageModels(providerId);
    if(!models.length){
        return `<option value="" disabled selected>${tr('canvas.noImageModelsHint') || '暂无生图模型，请到 API 设置添加'}</option>`;
    }
    const selectedValue = resolveImageModel(selectedModel);
    const options = models.map(model => `<option value="${escapeHtml(model)}" ${model === selectedValue ? 'selected' : ''}>${escapeHtml(model)}</option>`).join('');
    const hasSelected = models.includes(selectedValue);
    return `${hasSelected || !selectedValue ? '' : `<option value="${escapeHtml(selectedValue)}" selected>${escapeHtml(selectedValue)}</option>`}${options}`;
}
function chatModelOptions(selectedModel, providerId=''){
    const models = providerId ? providerChatModels(providerId) : allChatModels();
    if(!models.length){
        return `<option value="" disabled selected>${tr('canvas.noModelsHint') || '暂无模型，请到 API 设置添加'}</option>`;
    }
    const selectedValue = resolveChatModel(selectedModel, providerId);
    const options = models.map(model => `<option value="${escapeHtml(model)}" ${model === selectedValue ? 'selected' : ''}>${escapeHtml(model)}</option>`).join('');
    const hasSelected = models.includes(selectedValue);
    return `${hasSelected || !selectedValue ? '' : `<option value="${escapeHtml(selectedValue)}" selected>${escapeHtml(selectedValue)}</option>`}${options}`;
}
function formatCanvasTime(value){
    if(!value) return '--';
    const raw = Number(value);
    const time = raw < 10000000000 ? raw * 1000 : raw;
    const date = new Date(time);
    if(Number.isNaN(date.getTime())) return '--';
    return date.toLocaleString(window.StudioI18n?.lang() === 'en' ? 'en-US' : 'zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' });
}
function setStatus(text){
    document.getElementById('saveState').textContent = text;
    if(gateStatus) gateStatus.textContent = text;
}
let generationCompleteSoundAt = 0;
function playGenerationCompleteSound(){
    const now = Date.now();
    if(now - generationCompleteSoundAt < 1200) return;
    generationCompleteSoundAt = now;
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if(!AudioCtx) return;
        const ctx = playGenerationCompleteSound._ctx || (playGenerationCompleteSound._ctx = new AudioCtx());
        const play = () => {
            const start = ctx.currentTime + 0.015;
            [
                {freq:660, at:0, duration:0.12},
                {freq:880, at:0.12, duration:0.16}
            ].forEach(tone => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(tone.freq, start + tone.at);
                gain.gain.setValueAtTime(0.0001, start + tone.at);
                gain.gain.exponentialRampToValueAtTime(0.075, start + tone.at + 0.018);
                gain.gain.exponentialRampToValueAtTime(0.0001, start + tone.at + tone.duration);
                osc.connect(gain).connect(ctx.destination);
                osc.start(start + tone.at);
                osc.stop(start + tone.at + tone.duration + 0.02);
            });
        };
        if(ctx.state === 'suspended') ctx.resume().then(play).catch(() => {});
        else play();
    } catch(e) {}
}
function refreshGateViewControls(){
    if(!canvasGate) return;
    canvasGate.classList.toggle('trash-mode', trashMode);
    if(gateTitleText) gateTitleText.textContent = trashMode ? tr('canvas.trash') : tr('canvas.selectCanvas');
    if(gateSubtitle) gateSubtitle.textContent = trashMode ? tr('canvas.trashSubtitle') : tr('canvas.subtitle');
    const trashCount = deletedCanvases.length;
    if(gateTrashCount){
        gateTrashCount.textContent = String(trashCount);
        gateTrashCount.classList.toggle('visible', trashCount > 0);
    }
    const countPill = document.getElementById('gateCountPill');
    if(countPill){
        const items = trashMode ? deletedCanvases : canvases;
        const suffix = tr('canvas.countSuffix');
        countPill.textContent = suffix ? `${items.length} ${suffix}` : String(items.length);
    }
    const sortSwitch = document.getElementById('gateSortSwitch');
    if(sortSwitch){
        sortSwitch.classList.toggle('hidden', trashMode);
        sortSwitch.querySelectorAll('[data-sort]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.sort === canvasSortMode);
        });
    }
}
function setCanvasMode(open){
    shell.classList.toggle('no-canvas', !open);
    if(!open){
        nodesEl.innerHTML = '';
        linksEl.innerHTML = '';
        linkControlsEl.innerHTML = '';
        selectionHub.classList.remove('open');
    } else if(currentCanvasTitle) {
        currentCanvasTitle.textContent = canvas?.title || tr('canvas.untitled');
        currentCanvasTime.textContent = formatCanvasTime(canvas?.updated_at || canvas?.created_at);
    }
    refreshIcons();
}
function ensureCanvas(){
    if(canvas) return true;
    setStatus(tr('canvas.needCanvas'));
    return false;
}
function setCreateMode(active, kind='classic'){
    creatingCanvas = active;
    createCanvasKind = active ? ((kind === 'smart') ? 'smart' : 'classic') : 'classic';
    if(active) trashMode = false;
    canvasGate.classList.toggle('creating', active);
    refreshGateViewControls();
    setStatus(active ? tr('canvas.enterCanvasName') : (canvases.length ? tr('canvas.chooseFirst') : tr('canvas.noCanvasCreateFirst')));
    if(active) {
        gateTitleInput.placeholder = createCanvasKind === 'smart'
            ? (tr('canvas.newSmartCanvasPlaceholder') || tr('canvas.newCanvasPlaceholder'))
            : tr('canvas.newCanvasPlaceholder');
        gateTitleInput.focus();
        gateTitleInput.select();
    } else {
        gateTitleInput.value = '';
        gateTitleInput.placeholder = tr('canvas.newCanvasPlaceholder');
    }
    refreshIcons();
}
function screenToWorld(clientX, clientY){
    const rect = board.getBoundingClientRect();
    return { x:(clientX - rect.left - viewport.x) / viewport.scale, y:(clientY - rect.top - viewport.y) / viewport.scale };
}
function applyViewport(){
    world.style.transform = `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`;
    applyCanvasNodeShellSemanticZoom();
    scheduleMinimapViewportUpdate();
    scheduleCanvasImageResolutionSync(nodesEl, 120);
}
function canvasNodeShellSemanticZoomEnabled(){
    return window.WorkbenchNodeClient?.isLoopback?.()
        && window.WorkbenchSemanticZoom;
}
function applyCanvasNodeShellSemanticZoom(){
    if(!nodesEl) return;
    const enabled = canvasNodeShellSemanticZoomEnabled();
    nodesEl.classList.toggle('node-shell-semantic-zoom', Boolean(enabled));
    const existingIndicator = shell?.querySelector?.('#canvasSemanticZoomIndicator');
    // Semantic zoom is a default-on, page-load feature. Avoid walking every
    // Legacy/NodeShell card on ordinary pan and minimap updates when it is off.
    if(!enabled){
        existingIndicator?.remove();
        return;
    }
    const presentation = window.WorkbenchSemanticZoom.presentationForScale(viewport.scale);
    window.WorkbenchSemanticZoomApply.ensureIndicator({
        container: shell,
        id: 'canvasSemanticZoomIndicator',
        className: 'canvas-semantic-zoom-indicator',
        scale: viewport.scale,
        presentation,
        labels: {full:'完整', summary:'摘要'},
        count: nodes.length,
    });
    nodesEl.querySelectorAll('.node.node-shell-mounted').forEach(nodeEl => {
        const shellEl = nodeEl.querySelector('.workbench-node-shell');
        const node = nodes.find(item => item.id === nodeEl.dataset.id);
        if(!shellEl || !node) return;
        window.WorkbenchSemanticZoomApply.applyShellPresentation({
            shellEl,
            outerEl: nodeEl,
            model: window.WorkbenchSemanticZoom.viewModel(node, viewport.scale),
            portElements: [...nodeEl.querySelectorAll(':scope > .workbench-node-shell__port')],
        });
    });
    nodesEl.querySelectorAll('.node:not(.node-shell-mounted)').forEach(nodeEl => {
        const node = nodes.find(item => item.id === nodeEl.dataset.id);
        if(!node) return;
        window.WorkbenchSemanticZoomApply.applyLegacyPresentation({
            nodeEl,
            model: window.WorkbenchSemanticZoom.viewModel(node, viewport.scale),
            targets: {
                head:nodeEl.querySelector(':scope > .node-head'),
                body:nodeEl.querySelector(':scope > .node-body'),
                resize:nodeEl.querySelector(':scope > .resize-handle'),
            },
            portElements: [...nodeEl.querySelectorAll(':scope > .port')],
            headDisplay: 'flex',
        });
    });
}
function estimatedNodeRect(n){
    const el = nodesEl?.querySelector?.(`.node[data-id="${CSS.escape(n.id)}"]`);
    const size = defaultNodeSize(n.type);
    const w = el?.offsetWidth || n.w || size.w || 260;
    const h = el?.offsetHeight || n.h || size.h || 160;
    return {x:n.x || 0, y:n.y || 0, w, h};
}
function currentWorldViewRect(){
    const rect = board.getBoundingClientRect();
    const scale = viewport.scale || 1;
    return {
        x:-viewport.x / scale,
        y:-viewport.y / scale,
        w:rect.width / scale,
        h:rect.height / scale
    };
}
function minimapBounds(){
    const rects = (nodes || []).map(estimatedNodeRect);
    rects.push(currentWorldViewRect());
    if(!rects.length) return {x:0, y:0, w:1000, h:700};
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    rects.forEach(r => {
        minX = Math.min(minX, r.x);
        minY = Math.min(minY, r.y);
        maxX = Math.max(maxX, r.x + r.w);
        maxY = Math.max(maxY, r.y + r.h);
    });
    const pad = Math.max(240, Math.max(maxX - minX, maxY - minY) * 0.08);
    return {x:minX - pad, y:minY - pad, w:Math.max(1, maxX - minX + pad * 2), h:Math.max(1, maxY - minY + pad * 2)};
}
function scheduleMinimapRender(){
    if(minimapRenderQueued) return;
    minimapRenderQueued = true;
    requestAnimationFrame(() => {
        minimapRenderQueued = false;
        renderMinimap();
    });
}
// Viewport-only movement must not rebuild every minimap node. Geometry changes
// still use scheduleMinimapRender so bounds and node rectangles stay accurate.
function scheduleMinimapViewportUpdate(){
    if(!minimapViewport || !minimapState){
        scheduleMinimapRender();
        return;
    }
    if(minimapViewportQueued) return;
    minimapViewportQueued = true;
    requestAnimationFrame(() => {
        minimapViewportQueued = false;
        if(!minimapViewport || !minimapState){
            scheduleMinimapRender();
            return;
        }
        updateMinimapViewport();
    });
}
// 拖动/缩放节点时每个 mousemove 都全量重建连线 SVG 会掉帧；用 rAF 合并成每帧最多刷新一次。
function scheduleLinksRender(){
    if(linksRenderQueued) return;
    linksRenderQueued = true;
    requestAnimationFrame(() => {
        linksRenderQueued = false;
        renderLinks();
    });
}
function renderMinimap(){
    if(!minimapContent || !minimapViewport) return;
    canvasArrangeBtn?.classList.toggle('visible', selected.size > 0);
    const bounds = minimapBounds();
    const cw = minimapContent.clientWidth || 172;
    const ch = minimapContent.clientHeight || 110;
    const scale = Math.min(cw / bounds.w, ch / bounds.h);
    const mapW = bounds.w * scale;
    const mapH = bounds.h * scale;
    const ox = (cw - mapW) / 2;
    const oy = (ch - mapH) / 2;
    minimapState = {bounds, scale, ox, oy, cw, ch};
    const nodeHtml = (nodes || []).map(n => {
        const r = estimatedNodeRect(n);
        return `<div class="minimap-node ${selected.has(n.id) ? 'selected' : ''}" style="left:${ox + (r.x - bounds.x) * scale}px;top:${oy + (r.y - bounds.y) * scale}px;width:${Math.max(3, r.w * scale)}px;height:${Math.max(3, r.h * scale)}px"></div>`;
    }).join('');
    minimapContent.innerHTML = `${nodeHtml}${nodes?.length ? '' : '<div class="minimap-empty">EMPTY</div>'}<div id="minimapViewport" class="minimap-viewport"></div>`;
    minimapViewport = document.getElementById('minimapViewport');
    updateMinimapViewport();
}
function updateMinimapViewport(){
    if(!minimapViewport || !minimapState) return;
    const r = currentWorldViewRect();
    const {bounds, scale, ox, oy} = minimapState;
    minimapViewport.style.left = `${ox + (r.x - bounds.x) * scale}px`;
    minimapViewport.style.top = `${oy + (r.y - bounds.y) * scale}px`;
    minimapViewport.style.width = `${Math.max(8, r.w * scale)}px`;
    minimapViewport.style.height = `${Math.max(8, r.h * scale)}px`;
}
function minimapEventToWorld(e){
    if(!minimapState) renderMinimap();
    const state = minimapState;
    const rect = minimapContent.getBoundingClientRect();
    const sharedPoint = canvasUnifiedRuntimeEnabled
        ? window.WorkbenchCanvasRuntime?.worldPointFromMinimapPointer?.({x:e.clientX, y:e.clientY}, {
            screenOrigin:{x:rect.left, y:rect.top}, worldOrigin:{x:state.bounds.x, y:state.bounds.y}, offset:{x:state.ox, y:state.oy}, scale:state.scale,
        })
        : null;
    if(sharedPoint) return sharedPoint;
    const x = (e.clientX - rect.left - state.ox) / state.scale + state.bounds.x;
    const y = (e.clientY - rect.top - state.oy) / state.scale + state.bounds.y;
    return {x, y};
}
function centerViewportOnWorldPoint(point){
    const rect = board.getBoundingClientRect();
    const size = {width:rect.width, height:rect.height};
    const shared = canvasUnifiedRuntimeEnabled ? ensureCanvasViewportController().centerOn(point, size) : null;
    if(!shared){
        viewport.x = rect.width / 2 - point.x * viewport.scale;
        viewport.y = rect.height / 2 - point.y * viewport.scale;
    }
    applyViewport();
    renderLinks();
    renderSelectionHub();
}
function safeViewportScale(value){
    const n = Number(value);
    return Number.isFinite(n) && n > 0 ? n : 1;
}
function fitAllNodesViewport(){
    const rect = board.getBoundingClientRect();
    if(window.WorkbenchCanvasViewportRecovery){
        const fitted = window.WorkbenchCanvasViewportRecovery.fit(nodes.map(estimatedNodeRect), {width:rect.width, height:rect.height}, {padding:180, inset:80, minScale:.06, maxScale:.82, emptyScale:.45});
        if(!ensureCanvasViewportController().set(fitted)) viewport = {...fitted};
        applyViewport();
        renderLinks();
        renderSelectionHub();
        scheduleViewportSave();
        return;
    }
    if(!nodes.length){
        viewport.scale = 0.45;
        viewport.x = rect.width / 2;
        viewport.y = rect.height / 2;
        applyViewport();
        renderLinks();
        renderSelectionHub();
        scheduleViewportSave();
        return;
    }
    const rects = nodes.map(estimatedNodeRect);
    const minX = Math.min(...rects.map(r => r.x));
    const minY = Math.min(...rects.map(r => r.y));
    const maxX = Math.max(...rects.map(r => r.x + r.w));
    const maxY = Math.max(...rects.map(r => r.y + r.h));
    const pad = 180;
    const width = Math.max(1, maxX - minX + pad * 2);
    const height = Math.max(1, maxY - minY + pad * 2);
    const nextScale = Math.max(0.06, Math.min(0.82, (rect.width - 80) / width, (rect.height - 80) / height));
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    viewport.scale = nextScale;
    viewport.x = rect.width / 2 - cx * viewport.scale;
    viewport.y = rect.height / 2 - cy * viewport.scale;
    applyViewport();
    renderLinks();
    renderSelectionHub();
    scheduleViewportSave();
}
function enterZoomPreview(){
    if(zoomPreviewState || !canvas) return;
    zoomPreviewState = {...viewport};
    shell.classList.add('zoom-preview');
    document.body.classList.add('canvas-zoom-preview');
    closeCreateMenu();
    closeLinkCreateMenu();
    fitAllNodesViewport();
}
function exitZoomPreview(point=null){
    if(!zoomPreviewState) return false;
    const prev = zoomPreviewState;
    zoomPreviewState = null;
    shell.classList.remove('zoom-preview');
    document.body.classList.remove('canvas-zoom-preview');
    const restoredScale = safeViewportScale(prev.scale);
    let restoredViewport = {x:prev.x, y:prev.y, scale:restoredScale};
    if(point){
        const rect = board.getBoundingClientRect();
        restoredViewport = (canvasUnifiedRuntimeEnabled
            ? window.WorkbenchCanvasRuntime?.viewportCenteredOnWorldPoint?.(restoredViewport, point, {width:rect.width, height:rect.height})
            : null) || {x:rect.width / 2 - point.x * restoredScale, y:rect.height / 2 - point.y * restoredScale, scale:restoredScale};
    }
    if(!ensureCanvasViewportController().set(restoredViewport)) viewport = restoredViewport;
    applyViewport();
    renderLinks();
    renderSelectionHub();
    scheduleViewportSave();
    return true;
}
function exitZoomPreviewToNode(nodeId){
    if(!zoomPreviewState) return false;
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return exitZoomPreview();
    const prev = zoomPreviewState;
    const boardRect = board.getBoundingClientRect();
    const rect = estimatedNodeRect(node);
    const cx = rect.x + rect.w / 2;
    const cy = rect.y + rect.h / 2;
    const fitW = Math.max(1, boardRect.width - 160);
    const fitH = Math.max(1, boardRect.height - 160);
    const fitScale = Math.min(
        ZOOM_PREVIEW_NODE_MAX_SCALE,
        fitW / Math.max(1, rect.w),
        fitH / Math.max(1, rect.h)
    );
    const readableScale = Math.min(ZOOM_PREVIEW_NODE_MAX_SCALE, Math.max(ZOOM_PREVIEW_NODE_DEFAULT_SCALE, fitScale));
    zoomPreviewState = null;
    shell.classList.remove('zoom-preview');
    document.body.classList.remove('canvas-zoom-preview');
    const targetScale = Math.max(safeViewportScale(prev.scale), readableScale);
    const targetViewport = (canvasUnifiedRuntimeEnabled
        ? window.WorkbenchCanvasRuntime?.viewportCenteredOnWorldPoint?.({...prev, scale:targetScale}, {x:cx, y:cy}, {width:boardRect.width, height:boardRect.height})
        : null) || {x:boardRect.width / 2 - cx * targetScale, y:boardRect.height / 2 - cy * targetScale, scale:targetScale};
    if(!ensureCanvasViewportController().set(targetViewport)) viewport = targetViewport;
    applyViewport();
    renderLinks();
    renderSelectionHub();
    scheduleViewportSave();
    return true;
}
function toggleZoomPreview(){
    if(zoomPreviewState) exitZoomPreview();
    else enterZoomPreview();
}
function refreshGeometry(){
    renderLinks();
    renderSelectionHub();
}
function refreshGeometryAfterLayout(){
    requestAnimationFrame(() => {
        refreshGeometry();
        requestAnimationFrame(refreshGeometry);
    });
}
function scheduleSave(){
    return ensureCanvasSession().scheduleSave();
}
function scheduleViewportSave(){
    saveLocalViewport();
}
function refreshOutputTimer(){
    const hasPending = nodes.some(n => n.type === 'output' && (n._pending || []).length);
    if(hasPending && !outputTimer){
        outputTimer = setInterval(() => {
            const pendingById = new Map();
            nodes.filter(n => n.type === 'output').forEach(node => {
                (node._pending || []).forEach(p => pendingById.set(p.id, p));
            });
            if(pendingById.size){
                document.querySelectorAll('.output-time-pill.running').forEach(pill => {
                    const pendingId = pill.closest('[data-pending-id]')?.dataset.pendingId;
                    const pending = pendingById.get(pendingId);
                    if(pending) pill.textContent = formatRunDuration(nowMs() - Number(pending.startedAt || nowMs()));
                });
            } else {
                clearInterval(outputTimer);
                outputTimer = null;
            }
        }, 1000);
    } else if(!hasPending && outputTimer){
        clearInterval(outputTimer);
        outputTimer = null;
    }
}
function serializableCanvasNode(node){
    const copy = {...(node || {})};
    delete copy._ltxEditor;
    delete copy.running;
    delete copy.runStatus;
    delete copy.runError;
    delete copy._cascadeIdx;
    delete copy._cascadeFailed;
    delete copy._activeLoopCtx;
    return copy;
}
function serializableCanvasNodes(list=nodes){
    return (list || []).map(serializableCanvasNode);
}
async function saveCanvas(){
    return ensureCanvasSession().flush();
}
async function saveCanvasNow(){
    return ensureCanvasSession().flush();
}
function serializeCanvasSession(){
    if(!canvas) return {};
    sanitizeConnections();
    return {
        title:canvas.title,
        icon:canvas.icon || '🧩',
        nodes:serializableCanvasNodes(),
        connections,
        viewport:{...viewport},
        logs:canvas.logs || [],
    };
}

async function loadConfig(){
    loadLocalModelLists();
    try {
        const cfg = await fetch('/api/config').then(r=>r.json());
        imageModels = cfg.image_models?.length ? cfg.image_models : imageModels;
        chatModels = cfg.chat_models?.length ? cfg.chat_models : chatModels;
        videoModels = cfg.video_models?.length ? cfg.video_models : DEFAULT_VIDEO_MODELS;
        msChatModels = cfg.ms_chat_models?.length ? cfg.ms_chat_models : msChatModels;
        comfyBackendCount = Math.max(1, (cfg.comfy_instances || []).length || 1);
        apiProviders = Array.isArray(cfg.api_providers) && cfg.api_providers.length ? cfg.api_providers : defaultApiProviders();
        models.nano = imageModels.find(m => m.toLowerCase().includes('nano')) || 'nano-banana-pro';
        models.gpt = imageModels.find(m => !m.toLowerCase().includes('nano')) || cfg.image_model || 'gpt-image-2';
        try {
            const wf = await fetch('/api/workflows').then(r=>r.json());
            comfyWorkflows = wf.workflows || [];
        } catch(_) {
            comfyWorkflows = [];
        }
        runningHubWorkflowCache = {};
        const rhProvider = apiProviders.find(p => p.id === 'runninghub');
        const rhWorkflowIds = (rhProvider?.rh_workflows || [])
            .filter(rhWorkflowEntryHasSavedConfig)
            .map(item => String(item.workflowId || item.id || '').trim())
            .filter(Boolean);
        await Promise.all(rhWorkflowIds.map(async workflowId => {
            try { await ensureRunningHubWorkflow(workflowId); } catch(_) {}
        }));
    } catch(e) {
        apiProviders = defaultApiProviders();
    }
}
