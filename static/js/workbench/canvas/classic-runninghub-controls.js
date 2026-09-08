/*
 * static/js/workbench/canvas/classic-runninghub-controls.js
 *
 * Wave 7 of R4-38 — bounded compat seam for the Classic RunningHub
 * workflow / params controls. Six page-side functions move behind a
 * shared seam:
 * `addRhNode` (20-line factory), `renderRhBody` (~80-line body
 * renderer), `renderRhParams` (~22-line params renderer),
 * `runningHubProvider` (4-line resolver), `currentRunningHubWorkflow`
 * (4-line resolver), `currentRunningHubWorkflowConfig` (~18-line
 * config builder).
 *
 * Page-side usage (canvas.js):
 *     const rh = ensureClassicRunningHubControls();
 *     // createNodeByType:
 *     if(type === 'rh') return rh.addNode({point});
 *     // body dispatcher:
 *     if(node.type === 'rh') body.appendChild(rh.renderBody({node}));
 *     // refreshGeneratorInputViews:
 *     rh.renderParams({container, node, fields, media});
 *     // resolveWorkflow (etc.):
 *     const provider = rh.getProvider();
 *     const wf = rh.getCurrentWorkflow({node});
 *     const config = rh.getCurrentWorkflowConfig({node});
 *
 * R8 owns the real executor-driven RunningHub workflow rendering.
 * R4-38 Wave 7 establishes the bounded compat boundary; the
 * function bodies stay page-side helpers (page-owned per
 * COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reachable
 * only through this seam so the dispatcher and seam-call shape is
 * explicit.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM + i18n
        'document', 'escapeHtml', 'escapeAttr', 'tr',
        // Factory host ops (mirrors Wave 2/3/4 addNode pattern)
        'addNode', 'uid', 'defaultPoint',
        // RunningHub resolver / entry helpers (page-side)
        'validRunningHubWorkflowId', 'parseRunningHubEntryKey',
        'runningHubEntryKey', 'runningHubAllEntries', 'runningHubEntries',
        'runningHubEntryId', 'ensureRhNodeSelection', 'applyRhEntrySelection',
        'rhSelectedEntryRef', 'rhCurrentKind', 'rhEntryOptions',
        'rhPaymentOptions', 'rhModelSettingsHtml', 'bindRhModelControls',
        'renderRhPromptFields', 'renderRhInputs', 'rhMediaSources',
        'rhActiveFields', 'rhFieldRole', 'rhParamKey', 'rhExtractFieldOptions',
        'rhFieldValue', 'rhDefaultValue', 'rhRandomEnabled', 'rhRandomActive',
        'toggleRhRandom', 'currentRunningHubWorkflowEntry', 'rhEntryFields',
        'rhWorkflowJsonFromSources', 'bindRhParamControls',
        'renderRhSettingField',
        // Source / media helpers (page-side)
        'generatorSources', 'orderedSources', 'imageRefsOnly', 'videoRefsOnly',
        'audioRefsOnly', 'mediaKindForRef', 'nodeTitleForMedia',
        'rhMediaPreviewHtml',
        // API / model helpers (page-side)
        'normalizeApiNodeSizeChoice', 'defaultApiImageResolution',
        'parseSizeValue', 'renderImageInputList',
        // Page-side lifecycle
        'render', 'scheduleSave', 'runCanvasGenerate', 'refreshIcons',
        // Render composition
        'renderPromptPreview', 'bindCascadeButtons',
        'cascadeBtnHtml', 'retryBarHtml',
        // Closure values (so the seam sees the live module-level state)
        'getApiProviders',                // closure: () => apiProviders
        'getRunningHubWorkflowCache',     // closure: () => runningHubWorkflowCache
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicRunningHubControls.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicRunningHubControls.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var escapeHtml = host.escapeHtml;
        var escapeAttr = host.escapeAttr;
        var tr = host.tr;
        var addNode = host.addNode;
        var uid = host.uid;
        var defaultPoint = host.defaultPoint;
        var validRunningHubWorkflowId = host.validRunningHubWorkflowId;
        var parseRunningHubEntryKey = host.parseRunningHubEntryKey;
        var runningHubEntryKey = host.runningHubEntryKey;
        var runningHubAllEntries = host.runningHubAllEntries;
        var runningHubEntries = host.runningHubEntries;
        var runningHubEntryId = host.runningHubEntryId;
        var ensureRhNodeSelection = host.ensureRhNodeSelection;
        var applyRhEntrySelection = host.applyRhEntrySelection;
        var rhSelectedEntryRef = host.rhSelectedEntryRef;
        var rhCurrentKind = host.rhCurrentKind;
        var rhEntryOptions = host.rhEntryOptions;
        var rhPaymentOptions = host.rhPaymentOptions;
        var rhModelSettingsHtml = host.rhModelSettingsHtml;
        var bindRhModelControls = host.bindRhModelControls;
        var renderRhPromptFields = host.renderRhPromptFields;
        var renderRhInputs = host.renderRhInputs;
        var rhMediaSources = host.rhMediaSources;
        var rhActiveFields = host.rhActiveFields;
        var rhFieldRole = host.rhFieldRole;
        var rhParamKey = host.rhParamKey;
        var rhExtractFieldOptions = host.rhExtractFieldOptions;
        var rhFieldValue = host.rhFieldValue;
        var rhDefaultValue = host.rhDefaultValue;
        var rhRandomEnabled = host.rhRandomEnabled;
        var rhRandomActive = host.rhRandomActive;
        var toggleRhRandom = host.toggleRhRandom;
        var currentRunningHubWorkflowEntry = host.currentRunningHubWorkflowEntry;
        var rhEntryFields = host.rhEntryFields;
        var rhWorkflowJsonFromSources = host.rhWorkflowJsonFromSources;
        var bindRhParamControls = host.bindRhParamControls;
        var renderRhSettingField = host.renderRhSettingField;
        var generatorSources = host.generatorSources;
        var orderedSources = host.orderedSources;
        var imageRefsOnly = host.imageRefsOnly;
        var videoRefsOnly = host.videoRefsOnly;
        var audioRefsOnly = host.audioRefsOnly;
        var mediaKindForRef = host.mediaKindForRef;
        var nodeTitleForMedia = host.nodeTitleForMedia;
        var rhMediaPreviewHtml = host.rhMediaPreviewHtml;
        var normalizeApiNodeSizeChoice = host.normalizeApiNodeSizeChoice;
        var defaultApiImageResolution = host.defaultApiImageResolution;
        var parseSizeValue = host.parseSizeValue;
        var renderImageInputList = host.renderImageInputList;
        var render = host.render;
        var scheduleSave = host.scheduleSave;
        var runCanvasGenerate = host.runCanvasGenerate;
        var refreshIcons = host.refreshIcons;
        var renderPromptPreview = host.renderPromptPreview;
        var bindCascadeButtons = host.bindCascadeButtons;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var getApiProviders = host.getApiProviders;
        var getRunningHubWorkflowCache = host.getRunningHubWorkflowCache;

        function addRhNode(point) {
            var p = point || defaultPoint(180, 0);
            return addNode({
                id: uid('rh'),
                type: 'rh',
                x: p.x,
                y: p.y,
                w: 430,
                h: 0,
                rhMode: 'app',
                rhPayment: 'free',
                webappId: '',
                workflowId: '',
                instanceType: '',
                rhAppInfo: null,
                rhWorkflowInfo: null,
                rhParams: {},
                inputs: [],
                running: false
            });
        }

        function renderRhBody(node) {
            var wrap = document.createElement('div');
            wrap.className = 'rh-body';
            node.rhParams = node.rhParams || {};
            var entry = ensureRhNodeSelection(node);
            var selectedRef = rhSelectedEntryRef(node);
            var media = rhMediaSources(node);
            var fields = rhActiveFields(node);
            var mode = selectedRef?.kind || rhCurrentKind(node);
            var selectedId = selectedRef?.id || (mode === 'workflow' ? (node.workflowId || '') : (node.webappId || ''));
            var selectedKey = selectedRef ? runningHubEntryKey(selectedRef.kind, selectedRef.id) : '';
            var entryNote = entry?.note || entry?.description || '';
            if (mode === 'model') {
                node.model = selectedRef?.id || node.rhModel || node.model || '';
                normalizeApiNodeSizeChoice(node);
            }
            wrap.innerHTML =
                '<div class="rh-top">' +
                '<label class="field rh-webapp-field">' +
                '<div class="setting-title">RunningHub 配置</div>' +
                '<select class="select-lite rh-entry-select">' + rhEntryOptions(selectedKey) + '</select>' +
                '</label>' +
                '<label class="field rh-payment-field" style="' + (mode === 'model' ? 'display:none' : '') + '">' +
                '<div class="setting-title">Key</div>' +
                '<select class="select-lite rh-payment-select">' + rhPaymentOptions(node) + '</select>' +
                '</label>' +
                '<label class="field rh-machine-field" style="' + (mode === 'model' ? 'display:none' : '') + '">' +
                '<div class="setting-title">显存</div>' +
                '<select class="select-lite rh-machine-select">' +
                '<option value="" ' + (!node.instanceType ? 'selected' : '') + '>24G</option>' +
                '<option value="plus" ' + (node.instanceType === 'plus' ? 'selected' : '') + '>48G</option>' +
                '</select>' +
                '</label>' +
                '</div>' +
                '<div class="rh-prompt-list"></div>' +
                '<div class="rh-media-section">' +
                '<div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">' + tr('canvas.rhInputs') + '</div>' +
                '<div class="input-list rh-input-list"></div>' +
                '</div>' +
                (mode === 'model' ? rhModelSettingsHtml(node) : '') +
                '<div class="rh-param-head">' +
                '<span>' + (mode === 'model' ? '模型 API 参数' : mode === 'workflow' ? tr('canvas.rhWorkflowParams') : tr('canvas.rhParams')) + '</span>' +
                '<span>' + fields.length + '</span>' +
                '</div>' +
                '<div class="rh-param-list"></div>' +
                '<div class="gen-run-row">' +
                '<button class="gen-btn rh-run ' + (node.running ? 'running' : '') + '" ' + (node.running ? 'disabled' : '') + '><i data-lucide="workflow" class="w-4 h-4"></i>' + (node.running ? tr('canvas.rhRunning') : tr('canvas.rhRun')) + '</button>' +
                cascadeBtnHtml(node) +
                '</div>' +
                retryBarHtml(node);
            var entrySelect = wrap.querySelector('.rh-entry-select');
            if (entrySelect) entrySelect.onchange = function (e) {
                var parsed = parseRunningHubEntryKey(e.target.value);
                var ref = parsed ? runningHubAllEntries().find(function (item) { return item.kind === parsed.kind && item.id === parsed.id; }) : null;
                if (ref) applyRhEntrySelection(node, ref);
                node.rhParams = {};
                node.rhRandomValues = {};
                render();
                scheduleSave();
            };
            var paymentSelect = wrap.querySelector('.rh-payment-select');
            if (paymentSelect) paymentSelect.onchange = function (e) {
                node.rhPayment = e.target.value === 'wallet' ? 'wallet' : 'free';
                scheduleSave();
            };
            var machineSelect = wrap.querySelector('.rh-machine-select');
            if (machineSelect) machineSelect.onchange = function (e) {
                node.instanceType = e.target.value === 'plus' ? 'plus' : '';
                scheduleSave();
            };
            if (mode === 'model') renderPromptPreview(wrap.querySelector('.rh-prompt-list'), media.sources.filter(function (src) { return src.prompt && !src.refs?.length; }));
            else renderRhPromptFields(wrap.querySelector('.rh-prompt-list'), node, fields);
            renderRhInputs(wrap.querySelector('.rh-input-list'), node, media);
            renderRhParams({ container: wrap.querySelector('.rh-param-list'), node: node, fields: fields, media: media });
            if (mode === 'model') bindRhModelControls(wrap, node, media);
            wrap.querySelector('.rh-run').onclick = function (e) { e.stopPropagation(); runCanvasGenerate(node.id); };
            bindCascadeButtons(wrap, node.id);
            refreshIcons();
            return wrap;
        }

        function renderRhParams(arg) {
            var container = arg.container;
            var node = arg.node;
            var fields = arg.fields;
            var media = arg.media;
            if (!container) return;
            var params = (fields || []).filter(function (field) {
                var role = rhFieldRole(field);
                return ['image', 'video', 'audio', 'prompt'].indexOf(role) === -1;
            });
            if (!params.length) {
                container.innerHTML = '<div class="rh-empty">' + tr('canvas.rhNoParams') + '</div>';
                return;
            }
            container.innerHTML = params.map(function (field, i) {
                var key = rhParamKey(field.nodeId, field.fieldName);
                var kind = rhFieldRole(field);
                var options = rhExtractFieldOptions(field);
                var value = rhFieldValue(node, field, media);
                var label = field.label || field.fieldName || ('Field ' + (i + 1));
                var valueText = String(value ?? '');
                var wide = kind === 'text' && (String(label).length > 18 || valueText.length > 28);
                return renderRhSettingField(node, field, key, kind, label, value, options, wide);
            }).join('');
            bindRhParamControls(container, node);
        }

        function runningHubProvider() {
            var providers = getApiProviders();
            var provider = (providers || []).find(function (p) { return p.id === 'runninghub'; });
            return provider || null;
        }

        function currentRunningHubWorkflow(node) {
            var workflowId = validRunningHubWorkflowId(node.workflowId || '');
            return getRunningHubWorkflowCache()[workflowId] || null;
        }

        function currentRunningHubWorkflowConfig(node) {
            if (rhCurrentKind(node) !== 'workflow') return null;
            var workflowId = validRunningHubWorkflowId(node.workflowId || '');
            var entry = currentRunningHubWorkflowEntry(node);
            if (entry) {
                var cached = workflowId ? getRunningHubWorkflowCache()[workflowId] : null;
                return {
                    ...entry,
                    ...(cached || {}),
                    workflowId: runningHubEntryId(entry, 'workflow') || workflowId,
                    title: entry.title || cached?.title || workflowId,
                    fields: rhEntryFields(entry).length ? rhEntryFields(entry) : (cached?.fields || []),
                    optionalImageMode: entry.optionalImageMode || cached?.optionalImageMode || 'prune-workflow',
                    workflowJson: rhWorkflowJsonFromSources(cached?.workflowJson, entry.workflowJson, entry.raw?.workflowJson, entry.raw?.prompt)
                };
            }
            return workflowId ? getRunningHubWorkflowCache()[workflowId] : null;
        }

        return Object.freeze({
            addNode: function (arg) { return addRhNode(arg.point); },
            renderBody: function (arg) { return renderRhBody(arg.node); },
            renderParams: function (arg) { return renderRhParams(arg); },
            getProvider: function () { return runningHubProvider(); },
            getCurrentWorkflow: function (arg) { return currentRunningHubWorkflow(arg.node); },
            getCurrentWorkflowConfig: function (arg) { return currentRunningHubWorkflowConfig(arg.node); },
        });
    }

    window.WorkbenchCanvasClassicRunningHubControls = Object.freeze({ create: create });
})();