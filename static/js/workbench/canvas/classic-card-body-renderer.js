/*
 * static/js/workbench/canvas/classic-card-body-renderer.js
 *
 * Wave 5 of R4-38 — bounded compat seam for the four Classic provider-card
 * body renderers (`renderLLMBody`, `renderGeneratorBody`, `renderMidjourneyBody`,
 * `renderMsGenBody`). The function bodies are owned by this seam module; the
 * page injects a host shape carrying every page-local helper / const the
 * function bodies need (provider / model resolution, i18n, image helpers,
 * MsGen catalog, etc.).
 *
 * Page-side usage (canvas.js):
 *     const cb = ensureClassicCardBodyRenderer();
 *     if(node.type === 'llm')        body.appendChild(cb.renderLLM({node}));
 *     if(node.type === 'generator')  body.appendChild(cb.renderGenerator({node}));
 *     if(node.type === 'midjourney') body.appendChild(cb.renderMidjourney({node}));
 *     if(node.type === 'msgen')      body.appendChild(cb.renderMsGen({node}));
 *
 * R8 owns the real executor-driven body rendering. R4-38 Wave 5 establishes
 * the bounded compat boundary; the four function bodies stay page-side
 * helpers (page-owned per the COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reached only through
 * this module so the dispatcher and seam-call shape is explicit.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM + i18n
        'document', 'escapeHtml', 'tr',
        // LLM provider resolution + chat helpers
        'resolveChatProviderId', 'providerChatModels', 'chatModelOptions',
        'chatProviderOptions', 'resolveChatModel',
        'llmInputImages', 'llmInputVideos',
        'renderLLMChatPane', 'renderLLMNodePane', 'bindScrollableText',
        'ensureProviderControls',
        // Source / media helpers (shared across generator / midjourney / msgen)
        'generatorSources', 'orderedSources', 'mediaKindForRef',
        // API generator + LLM-side size + ratio helpers
        'sanitizeImageNodeProviderModel', 'normalizeApiNodeSizeChoice',
        'providerOptions', 'imageModelOptions',
        'providerImageModels', 'resolveImageModel',
        'defaultApiImageResolution', 'parseSizeValue',
        'isGptImageAutoSizeModel', 'ratioPartsFromDimensions',
        // Midjourney helpers
        'resolveMidjourneyProviderId', 'midjourneyProviderOptions',
        'midjourneyContinuationHtml', 'midjourneyModalHtml',
        'runMidjourneyAction', 'runMidjourneyModal',
        // MsGen (ModelScope) helpers + const catalog
        'MS_GEN_MODELS', 'modelscopeImageModels',
        'currentMsModelId', 'modelscopeLorasForModel',
        'modelscopeLoraOptions', 'modelscopeImageModelOptions',
        // Image / error helpers
        'getImageDimensions', 'showErrorModal',
        // Render composition helpers (shared by all four bodies)
        'renderImageInputList', 'renderPromptPreview',
        'cascadeBtnHtml', 'retryBarHtml',
        'bindCascadeButtons',
        // Page-side lifecycle (kept page-side per COMPAT boundary)
        'scheduleSave', 'render', 'runCanvasGenerate',
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicCardBodyRenderer.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicCardBodyRenderer.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var escapeHtml = host.escapeHtml;
        var tr = host.tr;
        var resolveChatProviderId = host.resolveChatProviderId;
        var providerChatModels = host.providerChatModels;
        var chatModelOptions = host.chatModelOptions;
        var chatProviderOptions = host.chatProviderOptions;
        var resolveChatModel = host.resolveChatModel;
        var llmInputImages = host.llmInputImages;
        var llmInputVideos = host.llmInputVideos;
        var renderLLMChatPane = host.renderLLMChatPane;
        var renderLLMNodePane = host.renderLLMNodePane;
        var bindScrollableText = host.bindScrollableText;
        var ensureProviderControls = host.ensureProviderControls;
        var generatorSources = host.generatorSources;
        var orderedSources = host.orderedSources;
        var mediaKindForRef = host.mediaKindForRef;
        var sanitizeImageNodeProviderModel = host.sanitizeImageNodeProviderModel;
        var normalizeApiNodeSizeChoice = host.normalizeApiNodeSizeChoice;
        var providerOptions = host.providerOptions;
        var imageModelOptions = host.imageModelOptions;
        var providerImageModels = host.providerImageModels;
        var resolveImageModel = host.resolveImageModel;
        var defaultApiImageResolution = host.defaultApiImageResolution;
        var parseSizeValue = host.parseSizeValue;
        var isGptImageAutoSizeModel = host.isGptImageAutoSizeModel;
        var ratioPartsFromDimensions = host.ratioPartsFromDimensions;
        var resolveMidjourneyProviderId = host.resolveMidjourneyProviderId;
        var midjourneyProviderOptions = host.midjourneyProviderOptions;
        var midjourneyContinuationHtml = host.midjourneyContinuationHtml;
        var midjourneyModalHtml = host.midjourneyModalHtml;
        var runMidjourneyAction = host.runMidjourneyAction;
        var runMidjourneyModal = host.runMidjourneyModal;
        var MS_GEN_MODELS = host.MS_GEN_MODELS;
        var modelscopeImageModels = host.modelscopeImageModels;
        var currentMsModelId = host.currentMsModelId;
        var modelscopeLorasForModel = host.modelscopeLorasForModel;
        var modelscopeLoraOptions = host.modelscopeLoraOptions;
        var modelscopeImageModelOptions = host.modelscopeImageModelOptions;
        var getImageDimensions = host.getImageDimensions;
        var showErrorModal = host.showErrorModal;
        var renderImageInputList = host.renderImageInputList;
        var renderPromptPreview = host.renderPromptPreview;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var bindCascadeButtons = host.bindCascadeButtons;
        var scheduleSave = host.scheduleSave;
        var render = host.render;
        var runCanvasGenerate = host.runCanvasGenerate;

        function renderLLMBody(node) {
            const providerControls = ensureProviderControls();
            const wrap = document.createElement('div');
            wrap.className = 'llm-body';
            const mode = node.mode || 'node';
            node.llmProvider = resolveChatProviderId(node.llmProvider || 'comfly');
            const llmProv = node.llmProvider;
            if (llmProv === 'modelscope') node.model = node.llmMsModel || node.model;
            if (!providerChatModels(llmProv).includes(node.model)) node.model = providerChatModels(llmProv)[0] || node.model;
            const modelOpts = chatModelOptions(node.model, llmProv);
            const imgs = llmInputImages(node);
            const videos = llmInputVideos(node);
            const mediaBadgeText = [
                imgs.length ? `${imgs.length} 张图片` : '',
                videos.length ? `${videos.length} 个视频` : ''
            ].filter(Boolean).join(' · ');
            const imgBadge = mediaBadgeText ? `<div style="display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:8px;background:rgba(16,185,129,.12);color:#047857;font-size:10.5px;font-weight:700;width:fit-content;line-height:1.4"><i data-lucide="${videos.length && !imgs.length ? 'video' : 'image'}" class="w-3 h-3"></i>已连接 ${mediaBadgeText} · 需选支持视觉/视频的模型</div>` : '';
            node.showSystem = Boolean(node.showSystem);
            wrap.innerHTML = `
                <div class="llm-row">
                    <select class="select-lite llm-provider-select" style="flex:1">${chatProviderOptions(llmProv)}</select>
                    <select class="select-lite llm-model">${modelOpts}</select>
                    <div class="llm-mode"><button data-mode="node">${tr('canvas.nodeMode')}</button><button data-mode="chat">${tr('canvas.chatMode')}</button></div>
                    <button class="llm-sys-toggle ${node.showSystem ? 'active' : ''}" type="button">System</button>
                </div>
                ${imgBadge}
                ${node.showSystem ? `<textarea class="llm-system" placeholder="${tr('canvas.systemPrompt')}">${escapeHtml(node.systemPrompt || '')}</textarea>` : ''}
                <div class="llm-node-pane"></div>
                <div class="llm-chat-pane"></div>
            `;
            const providerSelect = wrap.querySelector('.llm-provider-select');
            const modelSelect = wrap.querySelector('.llm-model');
            providerSelect.value = llmProv;
            modelSelect.value = resolveChatModel(node.model, llmProv);
            [providerSelect, modelSelect].forEach(input => {
                input.onmousedown = e => e.stopPropagation();
                input.onclick = e => e.stopPropagation();
            });
            providerSelect.onchange = e => {
                e.stopPropagation();
                const value = e.target.value;
                providerControls.setField(node, 'llmProvider', value);
                const models = providerChatModels(value);
                providerControls.setField(node, 'model', models[0] || '');
                if (value === 'modelscope') providerControls.setField(node, 'llmMsModel', node.model);
                providerControls.render();
                providerControls.save();
            };
            modelSelect.onchange = e => {
                e.stopPropagation();
                providerControls.setField(node, 'model', e.target.value);
                if ((node.llmProvider || 'comfly') === 'modelscope') providerControls.setField(node, 'llmMsModel', e.target.value);
                providerControls.save();
            };
            wrap.querySelector('.llm-sys-toggle').onclick = e => { e.stopPropagation(); providerControls.setField(node, 'showSystem', !node.showSystem); providerControls.render(); providerControls.save(); };
            const sysEl = wrap.querySelector('.llm-system');
            if (sysEl) {
                sysEl.oninput = e => { providerControls.setField(node, 'systemPrompt', e.target.value); providerControls.save(); };
                bindScrollableText(sysEl);
            }
            wrap.querySelectorAll('[data-mode]').forEach(btn => {
                btn.classList.toggle('active', mode === btn.dataset.mode);
                btn.onclick = e => { e.stopPropagation(); providerControls.setField(node, 'mode', btn.dataset.mode); providerControls.render(); providerControls.save(); };
            });
            const nodePane = wrap.querySelector('.llm-node-pane');
            const chatPane = wrap.querySelector('.llm-chat-pane');
            if (mode === 'chat') {
                nodePane.style.display = 'none';
                renderLLMChatPane(chatPane, node);
            } else {
                chatPane.style.display = 'none';
                renderLLMNodePane(nodePane, node);
            }
            return wrap;
        }

        function renderGeneratorBody(node) {
            const wrap = document.createElement('div');
            wrap.className = 'generator-body';
            const inputSources = generatorSources(node);
            const ordered = orderedSources(node, inputSources);
            const mediaInputs = ordered.filter(src => src.refs?.some(ref => ['image', 'video', 'audio'].includes(mediaKindForRef(ref))));
            const promptInputs = ordered.filter(src => src.prompt && !src.refs?.length);
            sanitizeImageNodeProviderModel(node);
            normalizeApiNodeSizeChoice(node);
            wrap.innerHTML = `
                <div class="prompt-list mb-3"></div>
                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">${tr('canvas.images')}</div>
                <div class="input-list"></div>
                <div class="gen-settings">
                    <div class="gen-settings-row">
                        <select class="select-lite provider-select">${providerOptions(node.apiProvider)}</select>
                        <select class="select-lite model-select">${imageModelOptions(node.model, node.apiProvider)}</select>
                    </div>
                    <div class="gen-settings-row api-size-row">
                        <select class="select-lite resolution compact-select" data-field="resolution">
                            <option value="auto">自动</option>
                            <option value="1k">1K</option>
                            <option value="2k">2K</option>
                            <option value="4k">4K</option>
                            <option value="custom">${tr('canvas.custom')}</option>
                        </select>
                        <select class="select-lite ratio compact-select" data-field="ratio">
                            <option value="square">1:1</option>
                            <option value="portrait">2:3</option>
                            <option value="landscape">3:2</option>
                            <option value="portrait43">3:4</option>
                            <option value="landscape43">4:3</option>
                            <option value="story">9:16</option>
                            <option value="wide">16:9</option>
                            <option value="ultrawide">21:9</option>
                            <option value="ultratall">9:21</option>
                            <option value="source">${tr('canvas.adaptiveRatio')}</option>
                            <option value="custom">${tr('canvas.custom')}</option>
                        </select>
                        <select class="select-lite quality-select">
                            <option value="auto">Q auto</option>
                            <option value="low">Q low</option>
                            <option value="medium">Q med</option>
                            <option value="high">Q high</option>
                        </select>
                        <div class="gen-count-row">
                            <div class="gen-stepper">
                                <button class="gen-step-btn" data-step="-1" type="button" title="${tr('canvas.decrease')}" aria-label="${tr('canvas.decreaseCount')}"><i data-lucide="chevron-left" class="w-3.5 h-3.5"></i></button>
                                <input class="gen-count-input" type="text" inputmode="numeric" pattern="[0-9]*" value="${Math.max(1, Math.min(8, Number(node.count || 1)))}">
                                <button class="gen-step-btn" data-step="1" type="button" title="${tr('canvas.increase')}" aria-label="${tr('canvas.increaseCount')}"><i data-lucide="chevron-right" class="w-3.5 h-3.5"></i></button>
                            </div>
                        </div>
                    </div>
                    <div class="gen-settings-row custom-ratio-row" style="display:none">
                        <label class="field">
                            <div class="setting-title">${tr('canvas.ratioWidth')}</div>
                            <input class="setting-input custom-ratio-w-input" type="number" min="1" step="1" value="${escapeHtml(node.customRatioWidth || '')}" placeholder="4">
                        </label>
                        <label class="field">
                            <div class="setting-title">${tr('canvas.ratioHeight')}</div>
                            <input class="setting-input custom-ratio-h-input" type="number" min="1" step="1" value="${escapeHtml(node.customRatioHeight || '')}" placeholder="3">
                        </label>
                    </div>
                    <div class="gen-settings-row custom-size-row" style="display:none">
                        <label class="field">
                            <div class="setting-title">${tr('canvas.width')}</div>
                            <input class="setting-input custom-w-input" type="number" min="64" step="64" value="${escapeHtml(node.customWidth || '')}" placeholder="Auto">
                        </label>
                        <label class="field">
                            <div class="setting-title">${tr('canvas.height')}</div>
                            <input class="setting-input custom-h-input" type="number" min="64" step="64" value="${escapeHtml(node.customHeight || '')}" placeholder="Auto">
                        </label>
                        <button class="secondary-btn fit-size-btn" type="button" style="height:32px;align-self:flex-end;padding:0 10px;font-size:11px">${tr('canvas.fitImageSize')}</button>
                    </div>
                </div>
                <div class="gen-run-row">
                    <button class="gen-btn ${node.running ? 'running' : ''}" ${node.running ? 'disabled' : ''}><i data-lucide="zap" class="w-4 h-4"></i>${node.running ? tr('canvas.generating') : tr('canvas.apiGenerate')}</button>
                    ${cascadeBtnHtml(node)}
                </div>
                ${retryBarHtml(node)}
            `;
            const providerSelect = wrap.querySelector('.provider-select');
            const modelSelect = wrap.querySelector('.model-select');
            providerSelect.onmousedown = e => e.stopPropagation();
            providerSelect.onclick = e => e.stopPropagation();
            providerSelect.onchange = e => {
                e.stopPropagation();
                node.apiProvider = e.target.value;
                const providerModels = providerImageModels(node.apiProvider);
                if (!providerModels.includes(resolveImageModel(node.model))) node.model = providerModels[0] || '';
                node._apiResolutionUserSet = false;
                node.resolution = defaultApiImageResolution(node.model);
                modelSelect.innerHTML = imageModelOptions(node.model, node.apiProvider);
                syncSizeControls();
                syncQualityControls();
                scheduleSave();
            };
            modelSelect.onmousedown = e => e.stopPropagation();
            modelSelect.onclick = e => e.stopPropagation();
            modelSelect.onchange = e => {
                e.stopPropagation();
                node.model = e.target.value;
                node._apiResolutionUserSet = false;
                if (node.resolution !== 'custom') node.resolution = defaultApiImageResolution(node.model);
                syncSizeControls();
                syncQualityControls();
                scheduleSave();
            };
            const ratioSelect = wrap.querySelector('.ratio');
            const resolutionSelect = wrap.querySelector('.resolution');
            const qualitySelect = wrap.querySelector('.quality-select');
            const customRatioRow = wrap.querySelector('.custom-ratio-row');
            const customSizeRow = wrap.querySelector('.custom-size-row');
            const customRatioWInput = wrap.querySelector('.custom-ratio-w-input');
            const customRatioHInput = wrap.querySelector('.custom-ratio-h-input');
            const customWInput = wrap.querySelector('.custom-w-input');
            const customHInput = wrap.querySelector('.custom-h-input');
            const fitSizeBtn = wrap.querySelector('.fit-size-btn');
            const referenceImages = ordered.flatMap(src => src.refs || []);
            const syncQualityControls = () => {
                qualitySelect.disabled = false;
                if (!['auto', 'low', 'medium', 'high'].includes(String(node.quality || 'auto'))) node.quality = 'auto';
                qualitySelect.value = node.quality || 'auto';
            };
            const hydrateCustomParts = () => {
                if ((!node.customRatioWidth || !node.customRatioHeight) && node.customRatio) {
                    const raw = String(node.customRatio || '');
                    if (raw.includes(':')) {
                        const [w, h] = raw.split(':');
                        node.customRatioWidth = node.customRatioWidth || w;
                        node.customRatioHeight = node.customRatioHeight || h;
                    }
                }
                if ((!node.customWidth || !node.customHeight) && node.customSize) {
                    const parsed = parseSizeValue(node.customSize);
                    node.customWidth = node.customWidth || parsed?.width || '';
                    node.customHeight = node.customHeight || parsed?.height || '';
                }
            };
            hydrateCustomParts();
            let sourceRatioRequest = 0;
            const updateSourceRatioFromFirstRef = async () => {
                if (node.ratio !== 'source') return;
                const ref = referenceImages.find(item => item.url);
                const requestId = ++sourceRatioRequest;
                if (!ref) {
                    node.customRatio = '';
                    node.customRatioWidth = '';
                    node.customRatioHeight = '';
                    customRatioWInput.value = '';
                    customRatioHInput.value = '';
                    return;
                }
                try {
                    const dims = await getImageDimensions(ref.url);
                    if (requestId !== sourceRatioRequest || node.ratio !== 'source') return;
                    const parts = ratioPartsFromDimensions(dims.width, dims.height);
                    node.customRatioWidth = String(parts.width);
                    node.customRatioHeight = String(parts.height);
                    node.customRatio = `${parts.width}:${parts.height}`;
                    customRatioWInput.value = node.customRatioWidth;
                    customRatioHInput.value = node.customRatioHeight;
                    scheduleSave();
                } catch (_) { /* keep prior ratio on error */ }
            };
            const syncSizeControls = () => {
                normalizeApiNodeSizeChoice(node);
                const autoOption = resolutionSelect.querySelector('option[value="auto"]');
                if (autoOption) autoOption.disabled = !isGptImageAutoSizeModel(resolveImageModel(node.model));
                const squareOption = ratioSelect.querySelector('option[value="square"]');
                if (squareOption) {
                    squareOption.disabled = false;
                    squareOption.title = '';
                }
                const ratioValue = node.ratio && [...ratioSelect.options].some(opt => opt.value === node.ratio) ? node.ratio : 'square';
                ratioSelect.value = ratioValue;
                resolutionSelect.value = node.resolution || defaultApiImageResolution(node.model);
                ratioSelect.disabled = node.resolution === 'custom' || node.resolution === 'auto';
                customRatioRow.style.display = (node.resolution !== 'auto' && (node.ratio === 'custom' || node.ratio === 'source')) ? 'flex' : 'none';
                customSizeRow.style.display = node.resolution === 'custom' ? 'flex' : 'none';
                customRatioWInput.disabled = node.ratio === 'source';
                customRatioHInput.disabled = node.ratio === 'source';
                customRatioWInput.value = node.customRatioWidth || '';
                customRatioHInput.value = node.customRatioHeight || '';
                customWInput.value = node.customWidth || '';
                customHInput.value = node.customHeight || '';
                if (fitSizeBtn) fitSizeBtn.disabled = !referenceImages.some(ref => ref.url);
                syncQualityControls();
                if (node.ratio === 'source') updateSourceRatioFromFirstRef();
            };
            qualitySelect.onmousedown = e => e.stopPropagation();
            qualitySelect.onclick = e => e.stopPropagation();
            qualitySelect.onchange = e => {
                e.stopPropagation();
                node.quality = e.target.value;
                scheduleSave();
            };
            ratioSelect.onmousedown = e => e.stopPropagation();
            ratioSelect.onclick = e => e.stopPropagation();
            ratioSelect.onchange = e => {
                e.stopPropagation();
                node.ratio = e.target.value;
                normalizeApiNodeSizeChoice(node);
                if (node.ratio !== 'custom' && node.ratio !== 'source') {
                    node.customRatio = '';
                    node.customRatioWidth = '';
                    node.customRatioHeight = '';
                } else if (node.ratio === 'source') {
                    node.customRatio = '';
                    node.customRatioWidth = '';
                    node.customRatioHeight = '';
                }
                syncSizeControls();
                scheduleSave();
            };
            resolutionSelect.onmousedown = e => e.stopPropagation();
            resolutionSelect.onclick = e => e.stopPropagation();
            resolutionSelect.onchange = e => {
                e.stopPropagation();
                node.resolution = e.target.value;
                node._apiResolutionUserSet = true;
                if (node.resolution === 'custom') {
                    node.ratio = '';
                } else if (node.resolution === 'auto') {
                    if (!node.ratio) node.ratio = 'square';
                    node.customSize = '';
                    node.customWidth = '';
                    node.customHeight = '';
                } else if (!node.ratio) {
                    node.ratio = 'square';
                    node.customSize = '';
                    node.customWidth = '';
                    node.customHeight = '';
                } else {
                    node.customSize = '';
                    node.customWidth = '';
                    node.customHeight = '';
                }
                normalizeApiNodeSizeChoice(node);
                syncSizeControls();
                scheduleSave();
            };
            [customRatioWInput, customRatioHInput].forEach(input => {
                input.onmousedown = e => e.stopPropagation();
                input.onclick = e => e.stopPropagation();
                input.oninput = e => {
                    node.customRatioWidth = customRatioWInput.value;
                    node.customRatioHeight = customRatioHInput.value;
                    node.customRatio = node.customRatioWidth && node.customRatioHeight ? `${node.customRatioWidth}:${node.customRatioHeight}` : '';
                    node.ratio = 'custom';
                    syncSizeControls();
                    scheduleSave();
                };
            });
            [customWInput, customHInput].forEach(input => {
                input.onmousedown = e => e.stopPropagation();
                input.onclick = e => e.stopPropagation();
                input.oninput = e => {
                    node.customWidth = customWInput.value;
                    node.customHeight = customHInput.value;
                    node.customSize = node.customWidth && node.customHeight ? `${node.customWidth}x${node.customHeight}` : '';
                    node.resolution = 'custom';
                    node._apiResolutionUserSet = true;
                    node.ratio = '';
                    syncSizeControls();
                    scheduleSave();
                };
            });
            if (fitSizeBtn) {
                fitSizeBtn.onmousedown = e => e.stopPropagation();
                fitSizeBtn.onclick = async e => {
                    e.stopPropagation();
                    const ref = referenceImages.find(item => item.url);
                    if (!ref) return;
                    try {
                        const dims = await getImageDimensions(ref.url);
                        node.customWidth = dims.width;
                        node.customHeight = dims.height;
                        node.customSize = `${dims.width}x${dims.height}`;
                        node.resolution = 'custom';
                        node._apiResolutionUserSet = true;
                        node.ratio = '';
                        syncSizeControls();
                        scheduleSave();
                    } catch (err) {
                        showErrorModal(tr('canvas.imageReadFailed'));
                    }
                };
            }
            syncSizeControls();
            const countInput = wrap.querySelector('.gen-count-input');
            countInput.onmousedown = e => e.stopPropagation();
            countInput.onclick = e => e.stopPropagation();
            countInput.oninput = e => {
                const value = Math.max(1, Math.min(8, Number(e.target.value) || 1));
                node.count = value;
                scheduleSave();
            };
            countInput.onblur = e => { e.target.value = String(Math.max(1, Math.min(8, Number(node.count || 1)))); };
            wrap.querySelectorAll('[data-step]').forEach(btn => {
                btn.onclick = e => {
                    e.stopPropagation();
                    const next = Math.max(1, Math.min(8, Number(node.count || 1) + Number(btn.dataset.step || 0)));
                    node.count = next;
                    countInput.value = String(next);
                    scheduleSave();
                };
            });
            if (host.parameterPresentation) {
                host.parameterPresentation.create({
                    document,
                    container: wrap,
                    node,
                    advancedSelector: '.gen-settings',
                    onChange: (field, value) => {
                        if (field === 'count') {
                            node.count = Math.max(1, Math.min(8, Number(value) || 1));
                            countInput.value = String(node.count);
                            scheduleSave();
                            return;
                        }
                        const control = field === 'ratio' ? ratioSelect : field === 'resolution' ? resolutionSelect : null;
                        if (control) {
                            control.value = value;
                            control.dispatchEvent(new Event('change', {bubbles: false}));
                        }
                    },
                });
            }
            const list = wrap.querySelector('.input-list');
            renderImageInputList(list, node, mediaInputs);
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            wrap.querySelector('.gen-btn').onclick = e => { e.stopPropagation(); runCanvasGenerate(node.id); };
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        function renderMidjourneyBody(node) {
            const wrap = document.createElement('div');
            wrap.className = 'generator-body midjourney-body';
            node.apiProvider = resolveMidjourneyProviderId(node.apiProvider || '');
            node.mode = ['imagine', 'blend', 'edit'].includes(node.mode) ? node.mode : 'imagine';
            node.size = /^\d{1,2}:\d{1,2}$/.test(String(node.size || '')) ? node.size : '1:1';
            node.version = String(node.version || '6.1');
            node.speed = ['relax', 'fast', 'turbo'].includes(node.speed) ? node.speed : 'relax';
            const sources = orderedSources(node, generatorSources(node));
            const mediaInputs = sources.filter(src => src.refs?.some(ref => mediaKindForRef(ref) === 'image'));
            const promptInputs = sources.filter(src => src.prompt && !src.refs?.length);
            const maskRef = mediaInputs.flatMap(source => source.refs || []).find(ref => String(ref.role || '').toLowerCase() === 'mask') || null;
            const hasProvider = Boolean(node.apiProvider);
            const taskText = node.lastTaskId ? `任务 ${escapeHtml(node.lastTaskId.slice(-14))}` : '生成四宫格后可选图';
            const runLabel = node.running ? '提交中...' : '生成四宫格';
            wrap.innerHTML = `
                <div class="prompt-list mb-3"></div>
                <div class="midjourney-input-head"><span>参考图片</span><span>最多 4 张</span></div>
                <div class="input-list mj-input-list"></div>
                <div class="gen-settings mj-settings">
                    <div class="gen-settings-row">
                        <select class="select-lite mj-mode"><option value="imagine" ${node.mode === 'imagine' ? 'selected' : ''}>生成</option><option value="blend" ${node.mode === 'blend' ? 'selected' : ''}>融合</option><option value="edit" ${node.mode === 'edit' ? 'selected' : ''}>编辑</option></select>
                        <select class="select-lite mj-provider">${midjourneyProviderOptions(node.apiProvider)}</select>
                        <select class="select-lite mj-version">
                            ${['8.2', '8.1', '7', '6.1', '5.2', '5.1'].map(version => `<option value="${version}" ${node.version === version ? 'selected' : ''}>v${version}</option>`).join('')}
                        </select>
                    </div>
                    <div class="gen-settings-row">
                        <select class="select-lite mj-size">
                            ${['1:1', '3:4', '4:3', '9:16', '16:9', '21:9'].map(size => `<option value="${size}" ${node.size === size ? 'selected' : ''}>${size}</option>`).join('')}
                        </select>
                        <select class="select-lite mj-speed">
                            <option value="relax" ${node.speed === 'relax' ? 'selected' : ''}>Relax</option>
                            <option value="fast" ${node.speed === 'fast' ? 'selected' : ''}>Fast</option>
                            <option value="turbo" ${node.speed === 'turbo' ? 'selected' : ''}>Turbo</option>
                        </select>
                    </div>
                </div>
                <div class="mj-task-line ${node.lastTaskId ? 'ready' : ''}"><i data-lucide="clock-3"></i><span>${taskText}</span></div>
                <div class="gen-run-row"><button class="gen-btn mj-run" ${node.running || !hasProvider ? 'disabled' : ''}><i data-lucide="wand-sparkles" class="w-4 h-4"></i>${runLabel}</button>${cascadeBtnHtml(node)}</div>
                ${midjourneyContinuationHtml(node)}
                ${midjourneyModalHtml(node, maskRef)}
                ${retryBarHtml(node)}
            `;
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            renderImageInputList(wrap.querySelector('.mj-input-list'), node, mediaInputs);
            ['mode', 'provider', 'version', 'size', 'speed'].forEach(field => {
                const input = wrap.querySelector(`.mj-${field}`);
                if (!input) return;
                input.onchange = event => {
                    event.stopPropagation();
                    node[field === 'provider' ? 'apiProvider' : field] = event.target.value;
                    scheduleSave();
                    if (field === 'provider' || field === 'mode') render();
                };
            });
            wrap.querySelector('.mj-run').onclick = event => { event.stopPropagation(); runCanvasGenerate(node.id); };
            wrap.querySelectorAll('[data-mj-action]').forEach(button => {
                button.onclick = event => {
                    event.stopPropagation();
                    runMidjourneyAction(node.id, button.dataset.mjAction, Number(button.dataset.index || 0), {
                        direction: button.dataset.direction || '',
                        zoomRatio: Number(button.dataset.zoomRatio || 0) || null
                    });
                };
            });
            const modalPrompt = wrap.querySelector('.mj-modal-prompt');
            if (modalPrompt) {
                modalPrompt.oninput = event => { node.mjModalPrompt = event.target.value; scheduleSave(); };
            }
            const modalSubmit = wrap.querySelector('.mj-modal-submit');
            if (modalSubmit) {
                modalSubmit.onclick = event => { event.stopPropagation(); runMidjourneyModal(node.id, maskRef); };
            }
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        function renderMsGenBody(node) {
            const wrap = document.createElement('div');
            wrap.className = 'generator-body';
            const modelKey = node.msgenModel || 'zimage';
            const msModel = MS_GEN_MODELS[modelKey] || MS_GEN_MODELS.zimage;
            const inputSources = generatorSources(node);
            const ordered = orderedSources(node, inputSources);
            const mediaInputs = ordered.filter(src => src.refs?.some(ref => ['image', 'video', 'audio'].includes(mediaKindForRef(ref))));
            const promptInputs = ordered.filter(src => src.prompt && !src.refs?.length);
            const referenceImages = ordered.flatMap(src => src.refs || []);
            const isCustomMs = modelKey === 'custom';
            const msUsesImages = Boolean(msModel.supportsImage || msModel.acceptsImage);
            node.msCustomModel = node.msCustomModel || modelscopeImageModels()[0] || 'Tongyi-MAI/Z-Image-Turbo';
            const msModelId = currentMsModelId(modelKey, node);
            const msLoras = modelscopeLorasForModel(msModelId);
            const selectedMsLora = msLoras.find(lora => String(lora.id || '').trim() === String(node.msLoraId || '').trim()) || msLoras[0];
            const loraEnabled = Boolean(node.msLoraEnabled);
            const loraStrength = node.msLoraStrength ?? Number(selectedMsLora?.strength ?? 0.8);
            const msCount = Math.max(1, Math.min(8, Number(node.count || 1)));
            wrap.innerHTML = `
                <div class="ms-model-tabs">
                    ${Object.entries(MS_GEN_MODELS).map(([k, m]) =>
                        `<button type="button" data-model="${k}" class="${modelKey === k ? 'active' : ''}">${escapeHtml(m.labelKey ? tr(m.labelKey) : m.label)}</button>`
                    ).join('')}
                </div>
                <div class="ms-content">
                    <div class="prompt-list mt-2 mb-2"></div>
                    ${msUsesImages ? `
                    <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">${tr('canvas.images')}</div>
                    <div class="input-list ms-img-list"></div>
                    ` : ''}
                </div>
                <div class="ms-controls">
                    <div class="gen-settings">
                        ${isCustomMs ? `
                        <div class="gen-settings-row">
                            <select class="select-lite ms-custom-model-select">${modelscopeImageModelOptions(node.msCustomModel)}</select>
                        </div>
                        ` : ''}
                        <div class="gen-settings-row">
                            <select class="select-lite resolution compact-select" data-field="msResolution">
                                <option value="1k">1K</option>
                                <option value="2k">2K</option>
                                <option value="4k">4K</option>
                                <option value="custom">${tr('canvas.custom')}</option>
                            </select>
                            <select class="select-lite ratio compact-select" data-field="msRatio">
                                <option value="square">1:1</option>
                                <option value="portrait">2:3</option>
                                <option value="landscape">3:2</option>
                                <option value="portrait43">3:4</option>
                                <option value="landscape43">4:3</option>
                                <option value="story">9:16</option>
                                <option value="wide">16:9</option>
                                <option value="ultrawide">21:9</option>
                                <option value="ultratall">9:21</option>
                                <option value="custom">${tr('canvas.custom')}</option>
                            </select>
                            <div class="gen-count-row">
                                <div class="gen-stepper">
                                    <button class="gen-step-btn" data-ms-step="-1" type="button" title="${tr('canvas.decrease')}" aria-label="${tr('canvas.decreaseCount')}"><i data-lucide="chevron-left" class="w-3.5 h-3.5"></i></button>
                                    <input class="gen-count-input ms-count-input" type="text" inputmode="numeric" pattern="[0-9]*" value="${msCount}">
                                    <button class="gen-step-btn" data-ms-step="1" type="button" title="${tr('canvas.increase')}" aria-label="${tr('canvas.increaseCount')}"><i data-lucide="chevron-right" class="w-3.5 h-3.5"></i></button>
                                </div>
                            </div>
                        </div>
                        <div class="gen-settings-row ms-custom-ratio-row" style="display:none">
                            <label class="field">
                                <div class="setting-title">${tr('canvas.ratioWidth')}</div>
                                <input class="setting-input ms-custom-ratio-w-input" type="number" min="1" step="1" value="${escapeHtml(node.msCustomRatioWidth || '')}" placeholder="4">
                            </label>
                            <label class="field">
                                <div class="setting-title">${tr('canvas.ratioHeight')}</div>
                                <input class="setting-input ms-custom-ratio-h-input" type="number" min="1" step="1" value="${escapeHtml(node.msCustomRatioHeight || '')}" placeholder="3">
                            </label>
                        </div>
                        <div class="gen-settings-row ms-custom-size-row" style="display:none">
                            <label class="field">
                                <div class="setting-title">${tr('canvas.width')}</div>
                                <input class="setting-input ms-custom-w-input" type="number" min="64" step="64" value="${escapeHtml(node.msCustomWidth || '')}" placeholder="Auto">
                            </label>
                            <label class="field">
                                <div class="setting-title">${tr('canvas.height')}</div>
                                <input class="setting-input ms-custom-h-input" type="number" min="64" step="64" value="${escapeHtml(node.msCustomHeight || '')}" placeholder="Auto">
                            </label>
                            <button class="secondary-btn ms-fit-size-btn" type="button" style="height:32px;align-self:flex-end;padding:0 10px;font-size:11px">${tr('canvas.fitImageSize')}</button>
                        </div>
                        ${msLoras.length ? `
                        <div class="gen-settings-row">
                            <label class="setting-check" style="cursor:pointer">
                                <input type="checkbox" class="ms-lora-check" ${node.msLoraEnabled ? 'checked' : ''}>
                                <span style="font-size:11px;font-weight:700">${tr('canvas.enableLora')}</span>
                            </label>
                        </div>
                        ${node.msLoraEnabled ? `
                        <div class="gen-settings-row">
                            <label class="field" style="flex:1">
                                <div class="setting-title">LoRA</div>
                                <select class="select-lite ms-lora-select">${modelscopeLoraOptions(msLoras, String(selectedMsLora?.id || '').trim())}</select>
                            </label>
                        </div>
                        <div class="gen-settings-row">
                            <label class="field" style="flex:1">
                                <div class="setting-title" style="display:flex;justify-content:space-between">
                                    <span>${tr('canvas.loraStrength')}</span><span class="ms-lora-strength-val">${loraStrength.toFixed(2)}</span>
                                </div>
                                <input type="range" class="canvas-range ms-lora-strength-slider" min="0.1" max="1.0" step="0.05" value="${loraStrength}">
                            </label>
                        </div>` : ''}` : ''}
                        ${!msLoras.length ? `<div class="gen-settings-row"><div style="color:var(--faint);font-size:11px;font-weight:700;line-height:1.45">${tr('canvas.noLoraForModel')}</div></div>` : ''}
                    </div>
                    <div class="gen-run-row">
                        <button class="gen-btn ${node.running ? 'running' : ''}" ${node.running ? 'disabled' : ''}>
                            <i data-lucide="zap" class="w-4 h-4"></i>${node.running ? tr('canvas.generating') : tr('canvas.msGenerate')}
                        </button>
                        ${cascadeBtnHtml(node)}
                    </div>
                    ${retryBarHtml(node)}
                </div>
            `;
            wrap.querySelectorAll('.ms-model-tabs button').forEach(btn => {
                btn.onclick = e => {
                    e.stopPropagation();
                    if (node.msgenModel !== btn.dataset.model) {
                        node.msLoraId = '';
                        delete node.msLoraStrength;
                        node.msLoraEnabled = false;
                    }
                    node.msgenModel = btn.dataset.model;
                    render();
                    scheduleSave();
                };
            });
            const msCustomModelSelect = wrap.querySelector('.ms-custom-model-select');
            if (msCustomModelSelect) {
                msCustomModelSelect.onmousedown = e => e.stopPropagation();
                msCustomModelSelect.onclick = e => e.stopPropagation();
                msCustomModelSelect.onchange = e => {
                    e.stopPropagation();
                    node.msCustomModel = e.target.value;
                    node.msLoraId = '';
                    delete node.msLoraStrength;
                    node.msLoraEnabled = false;
                    scheduleSave();
                    render();
                };
            }
            const msRatioSelect = wrap.querySelector('[data-field="msRatio"]');
            const msResolutionSelect = wrap.querySelector('[data-field="msResolution"]');
            if (msRatioSelect && msResolutionSelect) {
                const msCustomRatioRow = wrap.querySelector('.ms-custom-ratio-row');
                const msCustomSizeRow = wrap.querySelector('.ms-custom-size-row');
                const msCustomRatioWInput = wrap.querySelector('.ms-custom-ratio-w-input');
                const msCustomRatioHInput = wrap.querySelector('.ms-custom-ratio-h-input');
                const msCustomWInput = wrap.querySelector('.ms-custom-w-input');
                const msCustomHInput = wrap.querySelector('.ms-custom-h-input');
                const msFitSizeBtn = wrap.querySelector('.ms-fit-size-btn');
                if ((!node.msCustomRatioWidth || !node.msCustomRatioHeight) && node.msCustomRatio) {
                    const raw = String(node.msCustomRatio || '');
                    if (raw.includes(':')) {
                        const [w, h] = raw.split(':');
                        node.msCustomRatioWidth = node.msCustomRatioWidth || w;
                        node.msCustomRatioHeight = node.msCustomRatioHeight || h;
                    }
                }
                if ((!node.msCustomWidth || !node.msCustomHeight) && node.msCustomSize) {
                    const parsed = parseSizeValue(node.msCustomSize);
                    node.msCustomWidth = node.msCustomWidth || parsed?.width || '';
                    node.msCustomHeight = node.msCustomHeight || parsed?.height || '';
                }
                const syncMsCustomSizeControls = () => {
                    const ratioValue = node.msRatio && [...msRatioSelect.options].some(opt => opt.value === node.msRatio) ? node.msRatio : 'square';
                    msRatioSelect.value = ratioValue;
                    msResolutionSelect.value = node.msResolution || '1k';
                    msRatioSelect.disabled = node.msResolution === 'custom';
                    msCustomRatioRow.style.display = node.msRatio === 'custom' ? 'flex' : 'none';
                    msCustomSizeRow.style.display = node.msResolution === 'custom' ? 'flex' : 'none';
                    msCustomRatioWInput.value = node.msCustomRatioWidth || '';
                    msCustomRatioHInput.value = node.msCustomRatioHeight || '';
                    msCustomWInput.value = node.msCustomWidth || '';
                    msCustomHInput.value = node.msCustomHeight || '';
                    if (msFitSizeBtn) msFitSizeBtn.disabled = !referenceImages.some(ref => ref.url);
                };
                msRatioSelect.onmousedown = e => e.stopPropagation();
                msRatioSelect.onclick = e => e.stopPropagation();
                msRatioSelect.onchange = e => {
                    e.stopPropagation();
                    node.msRatio = e.target.value;
                    if (node.msRatio !== 'custom') {
                        node.msCustomRatio = '';
                        node.msCustomRatioWidth = '';
                        node.msCustomRatioHeight = '';
                    }
                    syncMsCustomSizeControls();
                    scheduleSave();
                };
                msResolutionSelect.onmousedown = e => e.stopPropagation();
                msResolutionSelect.onclick = e => e.stopPropagation();
                msResolutionSelect.onchange = e => {
                    e.stopPropagation();
                    node.msResolution = e.target.value;
                    if (node.msResolution === 'custom') {
                        node.msRatio = '';
                    } else if (!node.msRatio) {
                        node.msRatio = 'square';
                        node.msCustomSize = '';
                        node.msCustomWidth = '';
                        node.msCustomHeight = '';
                    } else {
                        node.msCustomSize = '';
                        node.msCustomWidth = '';
                        node.msCustomHeight = '';
                    }
                    syncMsCustomSizeControls();
                    scheduleSave();
                };
                [msCustomRatioWInput, msCustomRatioHInput].forEach(input => {
                    input.onmousedown = e => e.stopPropagation();
                    input.onclick = e => e.stopPropagation();
                    input.oninput = () => {
                        node.msCustomRatioWidth = msCustomRatioWInput.value;
                        node.msCustomRatioHeight = msCustomRatioHInput.value;
                        node.msCustomRatio = node.msCustomRatioWidth && node.msCustomRatioHeight ? `${node.msCustomRatioWidth}:${node.msCustomRatioHeight}` : '';
                        node.msRatio = 'custom';
                        syncMsCustomSizeControls();
                        scheduleSave();
                    };
                });
                [msCustomWInput, msCustomHInput].forEach(input => {
                    input.onmousedown = e => e.stopPropagation();
                    input.onclick = e => e.stopPropagation();
                    input.oninput = () => {
                        node.msCustomWidth = msCustomWInput.value;
                        node.msCustomHeight = msCustomHInput.value;
                        node.msCustomSize = node.msCustomWidth && node.msCustomHeight ? `${node.msCustomWidth}x${node.msCustomHeight}` : '';
                        node.msResolution = 'custom';
                        node.msRatio = '';
                        syncMsCustomSizeControls();
                        scheduleSave();
                    };
                });
                if (msFitSizeBtn) {
                    msFitSizeBtn.onmousedown = e => e.stopPropagation();
                    msFitSizeBtn.onclick = async e => {
                        e.stopPropagation();
                        const ref = referenceImages.find(item => item.url);
                        if (!ref) return;
                        try {
                            const dims = await getImageDimensions(ref.url);
                            node.msCustomWidth = dims.width;
                            node.msCustomHeight = dims.height;
                            node.msCustomSize = `${dims.width}x${dims.height}`;
                            node.msResolution = 'custom';
                            node.msRatio = '';
                            syncMsCustomSizeControls();
                            scheduleSave();
                        } catch (err) {
                            showErrorModal(tr('canvas.imageReadFailed'));
                        }
                    };
                }
                syncMsCustomSizeControls();
            }
            const msCountInput = wrap.querySelector('.ms-count-input');
            if (msCountInput) {
                msCountInput.onmousedown = e => e.stopPropagation();
                msCountInput.onclick = e => e.stopPropagation();
                msCountInput.oninput = e => {
                    node.count = Math.max(1, Math.min(8, Number(e.target.value) || 1));
                    scheduleSave();
                };
                msCountInput.onblur = e => { e.target.value = String(Math.max(1, Math.min(8, Number(node.count || 1)))); };
                wrap.querySelectorAll('[data-ms-step]').forEach(btn => {
                    btn.onclick = e => {
                        e.stopPropagation();
                        const next = Math.max(1, Math.min(8, Number(node.count || 1) + Number(btn.dataset.msStep || 0)));
                        node.count = next;
                        msCountInput.value = String(next);
                        scheduleSave();
                    };
                });
            }
            const msLoraCheck = wrap.querySelector('.ms-lora-check');
            if (msLoraCheck) {
                msLoraCheck.onchange = e => {
                    node.msLoraEnabled = e.target.checked;
                    if (node.msLoraEnabled && !node.msLoraId && msLoras[0]) {
                        node.msLoraId = String(msLoras[0].id || '').trim();
                        node.msLoraStrength = Number(msLoras[0].strength ?? 0.8);
                    }
                    scheduleSave();
                    render();
                };
            }
            const msLoraSelect = wrap.querySelector('.ms-lora-select');
            if (msLoraSelect) {
                msLoraSelect.onmousedown = e => e.stopPropagation();
                msLoraSelect.onclick = e => e.stopPropagation();
                msLoraSelect.onchange = e => {
                    node.msLoraId = e.target.value;
                    const picked = msLoras.find(lora => String(lora.id || '').trim() === node.msLoraId);
                    node.msLoraStrength = Number(picked?.strength ?? node.msLoraStrength ?? 0.8);
                    scheduleSave();
                    render();
                };
            }
            const msLoraSlider = wrap.querySelector('.ms-lora-strength-slider');
            if (msLoraSlider) {
                msLoraSlider.onmousedown = e => e.stopPropagation();
                msLoraSlider.onclick = e => e.stopPropagation();
                msLoraSlider.oninput = e => {
                    node.msLoraStrength = parseFloat(e.target.value);
                    const val = wrap.querySelector('.ms-lora-strength-val');
                    if (val) val.textContent = node.msLoraStrength.toFixed(2);
                    scheduleSave();
                };
            }
            wrap.querySelectorAll('.setting-check').forEach(pill => {
                pill.onmousedown = e => e.stopPropagation();
                const cb = pill.querySelector('input[type="checkbox"]');
                if (!cb) return;
                pill.onclick = e => {
                    e.stopPropagation();
                    e.preventDefault();
                    cb.checked = !cb.checked;
                    cb.dispatchEvent(new Event('change'));
                };
                cb.onclick = e => e.stopPropagation();
            });
            if (msUsesImages) {
                const list = wrap.querySelector('.ms-img-list');
                renderImageInputList(list, node, mediaInputs);
            }
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            wrap.querySelector('.gen-btn').onclick = e => { e.stopPropagation(); runCanvasGenerate(node.id); };
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        return Object.freeze({
            renderLLM: function (arg) { return renderLLMBody(arg.node); },
            renderGenerator: function (arg) { return renderGeneratorBody(arg.node); },
            renderMidjourney: function (arg) { return renderMidjourneyBody(arg.node); },
            renderMsGen: function (arg) { return renderMsGenBody(arg.node); },
        });
    }

    window.WorkbenchCanvasClassicCardBodyRenderer = Object.freeze({ create: create });
})();
