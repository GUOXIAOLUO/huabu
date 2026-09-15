/*
 * static/js/workbench/canvas/classic-comfy-controls.js
 *
 * Wave 6 of R4-38 — bounded compat seam for the Classic Comfy workflow
 * / field controls. Five page-side functions move behind a shared seam:
 * `addComfyNode` (32-line factory), `comfyWorkflowOptions` (4-line
 * `<option>` builder), `renderComfyBody` (64-line body renderer),
 * `renderComfySettings` (80-line mode-specific settings panel),
 * `updateComfyField` (42-line field change handler).
 *
 * Page-side usage (canvas.js):
 *     const c = ensureClassicComfyControls();
 *     // createNodeByType:
 *     if(type === 'comfy') return c.addNode({point});
 *     // body dispatcher:
 *     if(node.type === 'comfy') body.appendChild(c.renderBody({node}));
 *
 * R8 owns the real executor-driven Comfy workflow rendering. R4-38
 * Wave 6 establishes the bounded compat boundary; the function bodies
 * stay page-side helpers (page-owned per COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reachable
 * only through this seam so the dispatcher and seam-call shape is
 * explicit.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM + i18n
        'document', 'escapeHtml', 'tr',
        // Factory host ops (mirrors Wave 2/3/4 addNode pattern)
        'addNode', 'uid', 'defaultPoint',
        'allImageModels', 'imageApiProviders',
        'getModels',           // closure: () => models (const lookup)
        'getComfyWorkflows',   // closure: () => comfyWorkflows (let lookup)
        // Shared source / media helpers
        'generatorSources', 'orderedSources', 'imageRefsOnly',
        // Comfy-specific helpers
        'comfyFields', 'validComfyWorkflowName',
        'hasComfyWorkflow', 'currentComfyWorkflow',
        'comfyFieldKind', 'ensureComfyWorkflow',
        // Page-side lifecycle
        'render', 'scheduleSave', 'runCanvasGenerate',
        // Render composition
        'renderPromptPreview', 'renderComfyImages',
        'renderComfyCustomField', 'toggleComfyRandom',
        'bindCascadeButtons', 'cascadeBtnHtml', 'retryBarHtml',
        // Optional versioned workflow projection (legacy controls remain usable without it).
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicComfyControls.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicComfyControls.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var escapeHtml = host.escapeHtml;
        var tr = host.tr;
        var addNode = host.addNode;
        var uid = host.uid;
        var defaultPoint = host.defaultPoint;
        var allImageModels = host.allImageModels;
        var imageApiProviders = host.imageApiProviders;
        var getModels = host.getModels;
        var getComfyWorkflows = host.getComfyWorkflows;
        var generatorSources = host.generatorSources;
        var orderedSources = host.orderedSources;
        var imageRefsOnly = host.imageRefsOnly;
        var comfyFields = host.comfyFields;
        var validComfyWorkflowName = host.validComfyWorkflowName;
        var hasComfyWorkflow = host.hasComfyWorkflow;
        var currentComfyWorkflow = host.currentComfyWorkflow;
        var comfyFieldKind = host.comfyFieldKind;
        var ensureComfyWorkflow = host.ensureComfyWorkflow;
        var render = host.render;
        var scheduleSave = host.scheduleSave;
        var runCanvasGenerate = host.runCanvasGenerate;
        var renderPromptPreview = host.renderPromptPreview;
        var renderComfyImages = host.renderComfyImages;
        var renderComfyCustomField = host.renderComfyCustomField;
        var toggleComfyRandom = host.toggleComfyRandom;
        var bindCascadeButtons = host.bindCascadeButtons;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var workflowPresentation = host.workflowPresentation;

        function versionedWorkflowDefinition(node) {
            var stored = node.comfyWorkflowDefinition || currentComfyWorkflow(node) || {};
            var reference = stored.workflow_ref || node.comfyWorkflowRef;
            var id = node.comfyWorkflowId || stored.id || stored.workflow_id;
            var version = node.comfyWorkflowVersion || stored.version;
            if ((!id || !version) && typeof reference === 'string') {
                var marker = reference.lastIndexOf('@');
                if (marker > 0) {
                    id = id || reference.slice(0, marker);
                    version = version || reference.slice(marker + 1);
                }
            }
            if (!id || !Number.isInteger(Number(version)) || Number(version) < 1) return null;
            return Object.assign({}, stored, {
                id: id,
                version: Number(version),
                title: node.comfyWorkflowTitle || stored.title || node.comfyWorkflow,
                input_bindings: node.comfyInputBindings || stored.input_bindings || [],
                output_mappings: node.comfyOutputMappings || stored.output_mappings || [],
            });
        }

        function addComfyNode(point) {
            var p = point || defaultPoint(160, 0);
            return addNode({
                id: uid('comfy'),
                type: 'comfy',
                x: p.x,
                y: p.y,
                w: 420,
                h: 460,
                mode: 'text',
                width: 1024,
                height: 1024,
                enhanceStrength: 0.5,
                enhanceUpscale: false,
                enhanceUpscaleRes: 2048,
                editUpscale: false,
                editUpscaleRes: 2048,
                editModel: allImageModels(imageApiProviders()[0]?.id || 'comfly')[0] || getModels().gpt,
                ratio: 'square',
                resolution: '1k',
                customRatio: '',
                customSize: '',
                customRatioWidth: '',
                customRatioHeight: '',
                customWidth: '',
                customHeight: '',
                comfyWorkflow: '',
                comfyWorkflowDefinition: null,
                comfyWorkflowRef: '',
                comfyWorkflowId: '',
                comfyWorkflowVersion: null,
                comfyInputBindings: [],
                comfyOutputMappings: [],
                comfyParams: {},
                count: 1,
                inputs: []
            });
        }

        function comfyWorkflowOptions(selected) {
            var workflows = getComfyWorkflows();
            var opts = workflows.map(function (w) {
                return '<option value="' + escapeHtml(w.name) + '" ' +
                    (w.name === selected ? 'selected' : '') + '>' +
                    escapeHtml(w.title || w.name.replace('.json', '')) + '</option>';
            }).join('');
            return opts || '<option value="">' + tr('canvas.comfyNoWorkflow') + '</option>';
        }

        function renderComfyBody(node) {
            var wrap = document.createElement('div');
            wrap.className = 'comfy-body';
            var inputSources = generatorSources(node);
            var ordered = orderedSources(node, inputSources);
            var mediaInputs = ordered.filter(function (src) { return src.refs?.length; });
            var imageInputs = mediaInputs
                .map(function (src) { return Object.assign({}, src, { refs: imageRefsOnly(src.refs || []) }); })
                .filter(function (src) { return src.refs?.length; });
            var promptInputs = ordered.filter(function (src) { return src.prompt && !src.refs?.length; });
            var mode = node.mode || 'text';
            var imageFieldCount = mode === 'custom' ? comfyFields(node, 'image').length : 0;
            var videoFieldCount = mode === 'custom' ? comfyFields(node, 'video').length : 0;
            var audioFieldCount = mode === 'custom' ? comfyFields(node, 'audio').length : 0;
            var mediaFieldCount = imageFieldCount + videoFieldCount + audioFieldCount;
            if (mode === 'custom') {
                var validWorkflow = validComfyWorkflowName(node.comfyWorkflow);
                if (node.comfyWorkflow && node.comfyWorkflow !== validWorkflow) node.comfyWorkflow = validWorkflow;
                if (!node.comfyWorkflow && validWorkflow) node.comfyWorkflow = validWorkflow;
            }
            wrap.innerHTML = '' +
                '<div class="mode-tabs">' +
                '<button type="button" data-mode="text" class="' + (mode === 'text' ? 'active' : '') + '">' + tr('canvas.comfyModeText') + '</button>' +
                '<button type="button" data-mode="enhance" class="' + (mode === 'enhance' ? 'active' : '') + '">' + tr('canvas.comfyModeEnhance') + '</button>' +
                '<button type="button" data-mode="edit" class="' + (mode === 'edit' ? 'active' : '') + '">' + tr('canvas.comfyModeEdit') + '</button>' +
                '<button type="button" data-mode="custom" class="' + (mode === 'custom' ? 'active' : '') + '">' + tr('canvas.comfyModeCustom') + '</button>' +
                '</div>' +
                '<div class="comfy-content">' +
                '<div class="prompt-list"></div>' +
                '<div class="comfy-images ' + ((mode === 'text' || (mode === 'custom' && !mediaFieldCount)) ? 'hidden' : '') + '">' +
                '<div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">' +
                (mode === 'custom' ? 'Media · Images ' + imageFieldCount + ' · Videos ' + videoFieldCount + ' · Audio ' + audioFieldCount : 'Images') +
                '</div>' +
                '<div class="input-list mt-2"></div>' +
                '</div>' +
                '</div>' +
                '<div class="comfy-controls">' +
                '<div class="gen-settings comfy-settings"></div>' +
                '<div class="gen-run-row">' +
                '<button class="comfy-run ' + (node.running ? 'running' : '') + '" ' + (node.running ? 'disabled' : '') + '><i data-lucide="zap" class="w-4 h-4"></i>' +
                (node.running ? tr('canvas.comfyRunning') : tr('canvas.comfyRun')) +
                '</button>' + cascadeBtnHtml(node) +
                '</div>' + retryBarHtml(node) +
                '</div>';
            wrap.querySelectorAll('[data-mode]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    node.mode = btn.dataset.mode;
                    var workflows = getComfyWorkflows();
                    if (node.mode === 'custom' && !hasComfyWorkflow(node.comfyWorkflow) && workflows[0]?.name) {
                        node.comfyWorkflow = workflows[0].name;
                        ensureComfyWorkflow(node.comfyWorkflow).then(function () { render(); });
                    }
                    render();
                    scheduleSave();
                };
            });
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            if (mode !== 'text' && !(mode === 'custom' && !mediaFieldCount)) {
                renderComfyImages(wrap.querySelector('.input-list'), node, mode === 'custom' ? mediaInputs : imageInputs);
            }
            renderComfySettings(wrap.querySelector('.comfy-settings'), node);
            var definition = workflowPresentation && versionedWorkflowDefinition(node);
            if (definition) workflowPresentation.create({
                document: document,
                container: wrap.querySelector('.comfy-content'),
                definition: definition,
                onRun: function (event) { event.stopPropagation(); runCanvasGenerate(node.id); },
            });
            wrap.querySelector('.comfy-run').onclick = function (e) { e.stopPropagation(); runCanvasGenerate(node.id); };
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        function renderComfySettings(container, node) {
            var mode = node.mode || 'text';
            if (mode === 'text') {
                container.innerHTML = '' +
                    '<div class="gen-settings-row">' +
                    '<label class="field"><div class="setting-title">' + tr('canvas.width') + '</div>' +
                    '<input class="setting-input" data-field="width" type="number" min="64" step="64" value="' + Number(node.width || 1024) + '"></label>' +
                    '<label class="field"><div class="setting-title">' + tr('canvas.height') + '</div>' +
                    '<input class="setting-input" data-field="height" type="number" min="64" step="64" value="' + Number(node.height || 1024) + '"></label>' +
                    '</div>';
            } else if (mode === 'enhance') {
                var strength = Number(node.enhanceStrength ?? 0.5);
                container.innerHTML = '' +
                    '<div class="gen-settings-row">' +
                    '<label class="field" style="flex:1">' +
                    '<div class="setting-title" style="display:flex;justify-content:space-between">' +
                    '<span>' + tr('studio.enhancementStrength') + '</span><span class="enhance-strength-val">' + strength.toFixed(2) + '</span>' +
                    '</div>' +
                    '<input type="range" class="canvas-range enhance-strength-slider" data-field="enhanceStrength" min="0.1" max="1.0" step="0.05" value="' + strength + '">' +
                    '</label>' +
                    '</div>' +
                    '<div class="gen-settings-row">' +
                    '<button type="button" class="setting-check ' + (node.enhanceUpscale ? 'active' : '') + '" data-toggle-field="enhanceUpscale"><span class="check-dot"></span>' + tr('studio.superResolution') + '</button>' +
                    '<select class="select-lite ' + (node.enhanceUpscale ? '' : 'opacity-40 cursor-not-allowed') + '" data-field="enhanceUpscaleRes" ' + (node.enhanceUpscale ? '' : 'disabled') + '>' +
                    '<option value="2048">2X (2048)</option><option value="4096">4X (4096)</option>' +
                    '</select>' +
                    '</div>';
                var enhanceRes = container.querySelector('[data-field="enhanceUpscaleRes"]');
                if (enhanceRes) enhanceRes.value = String(node.enhanceUpscaleRes || 2048);
            } else if (mode === 'edit') {
                container.innerHTML = '' +
                    '<div class="gen-settings-row">' +
                    '<button type="button" class="setting-check ' + (node.editUpscale ? 'active' : '') + '" data-toggle-field="editUpscale"><span class="check-dot"></span>' + tr('studio.superResolution') + '</button>' +
                    '<select class="select-lite ' + (node.editUpscale ? '' : 'opacity-40 cursor-not-allowed') + '" data-field="editUpscaleRes" ' + (node.editUpscale ? '' : 'disabled') + '>' +
                    '<option value="2048">2X (2048)</option><option value="4096">4X (4096)</option>' +
                    '</select>' +
                    '</div>';
                var editRes = container.querySelector('[data-field="editUpscaleRes"]');
                if (editRes) editRes.value = String(node.editUpscaleRes || 2048);
            } else if (mode === 'custom') {
                var workflows = getComfyWorkflows();
                var selected = validComfyWorkflowName(node.comfyWorkflow || workflows[0]?.name || '');
                if (node.comfyWorkflow && node.comfyWorkflow !== selected) node.comfyWorkflow = selected;
                var data = currentComfyWorkflow(node);
                var fields = data?.config?.fields || [];
                var settingFields = fields.filter(function (f) { return comfyFieldKind(f) === 'setting'; });
                container.innerHTML = '' +
                    '<div class="gen-settings-row">' +
                    '<select class="select-lite comfy-workflow-select" data-field="comfyWorkflow" style="width:100%">' +
                    comfyWorkflowOptions(selected) +
                    '</select>' +
                    '</div>' +
                    (!selected ? '<div class="text-[11px] text-slate-400">' + tr('canvas.comfyNoWorkflow') + '</div>' :
                        (!data ? '<div class="text-[11px] text-slate-400">' + tr('canvas.comfyLoadingWorkflow') + '</div>' : '')) +
                    (data ? settingFields.map(function (f) { return renderComfyCustomField(node, f); }).join('') ||
                        '<div class="text-[11px] text-slate-400">' + tr('canvas.comfyNoExtraParams') + '</div>' : '');
                if (selected && !data) ensureComfyWorkflow(selected).then(function () { render(); });
            } else {
                container.innerHTML = '';
            }
            container.querySelectorAll('[data-toggle-field]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = function (e) {
                    e.stopPropagation();
                    var field = btn.dataset.toggleField;
                    node[field] = !node[field];
                    render();
                    scheduleSave();
                };
            });
            container.querySelectorAll('button[data-comfy-param]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = function (e) { updateComfyField(node, btn, e); };
            });
            container.querySelectorAll('button[data-comfy-random]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = function (e) {
                    e.stopPropagation();
                    toggleComfyRandom(node.id, btn.dataset.comfyRandom);
                };
            });
            container.querySelectorAll('input, select, textarea').forEach(function (input) {
                input.onmousedown = function (e) { e.stopPropagation(); };
                input.onclick = function (e) { e.stopPropagation(); };
                if (input.classList.contains('model-select')) return;
                input.onchange = function (e) { updateComfyField(node, input, e); };
                input.oninput = function (e) { updateComfyField(node, input, e); };
            });
        }

        function updateComfyField(node, input, event) {
            if (event && event.stopPropagation) event.stopPropagation();
            var paramId = input.dataset.comfyParam;
            if (paramId) {
                node.comfyParams = node.comfyParams || {};
                var field = comfyFields(node).find(function (f) { return f.id === paramId; });
                var type = input.dataset.comfyType || field?.type || 'text';
                if (type === 'boolean') {
                    node.comfyParams[paramId] = !Boolean(node.comfyParams[paramId] ?? field?.default ?? false);
                } else if (type === 'number' || type === 'slider') {
                    node.comfyParams[paramId] = Number(input.value) || 0;
                } else {
                    node.comfyParams[paramId] = input.value;
                }
                var val = input.closest('.field')?.querySelector('.comfy-param-val');
                if (val) val.textContent = node.comfyParams[paramId];
                if (type === 'boolean') render();
                scheduleSave();
                return;
            }
            var fieldName = input.dataset.field;
            if (!fieldName) return;
            if (fieldName === 'comfyWorkflow') {
                node.comfyWorkflow = validComfyWorkflowName(input.value);
                node.comfyParams = {};
                ensureComfyWorkflow(node.comfyWorkflow).then(function () { render(); });
                scheduleSave();
                return;
            }
            if (input.type === 'checkbox') {
                node[fieldName] = input.checked;
                if (fieldName === 'enhanceUpscale') render();
            } else if (fieldName === 'enhanceStrength') {
                node[fieldName] = Number(input.value) || 0.5;
                var strengthVal = input.closest('.field')?.querySelector('.enhance-strength-val');
                if (strengthVal) strengthVal.textContent = node[fieldName].toFixed(2);
            } else if (['width', 'height', 'enhanceUpscaleRes', 'editUpscaleRes', 'count'].indexOf(fieldName) !== -1) {
                node[fieldName] = Number(input.value) || 1;
            } else {
                node[fieldName] = input.value;
            }
            scheduleSave();
        }

        return Object.freeze({
            addNode: function (arg) { return addComfyNode(arg.point); },
            renderBody: function (arg) { return renderComfyBody(arg.node); },
            renderSettings: function (arg) { renderComfySettings(arg.container, arg.node); },
            updateField: function (arg) { updateComfyField(arg.node, arg.input, arg.event); },
            getWorkflowOptions: function (arg) { return comfyWorkflowOptions(arg.selected); },
        });
    }

    window.WorkbenchCanvasClassicComfyControls = Object.freeze({ create: create });
})();
