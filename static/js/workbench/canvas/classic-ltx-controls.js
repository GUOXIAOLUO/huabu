/*
 * static/js/workbench/canvas/classic-ltx-controls.js
 *
 * Wave 9 of R4-38 — bounded compat seam for the Classic LTX director
 * timeline / relay controls. Six page-side functions move behind a
 * shared seam:
 * `addLTXDirectorNode` (~30-line factory), `renderLTXDirectorBody`
 * (~78-line body renderer that mounts the `CanvasLTXTimelineEditor`
 * instance), `destroyLTXEditor` (4-line editor cleanup),
 * `ltxParseTimeline` (~10-line JSON timeline parser),
 * `ltxFlushTimelineToNode` (4-line editor commit), and
 * `ltxBuildContiguousRelay` (~50-line contiguous-relay builder
 * that produces the `local_prompts` / `segment_lengths` /
 * `guide_strength` payloads).
 *
 * Page-side usage (canvas.js):
 *     const ltx = ensureClassicLtxControls();
 *     // createNodeByType:
 *     if(type === 'ltxDirector') return ltx.addNode({point});
 *     // body dispatcher:
 *     if(node.type === 'ltxDirector') body.appendChild(ltx.renderBody({node}));
 *     // onCardDestroy:
 *     onCardDestroy: payloadNode => ltx.destroyEditor({node: payloadNode}),
 *     // ltxSyncConnectedImagesToTimeline / runLTXDirectorNode:
 *     const timeline = ltx.parseTimeline({node});
 *     ltx.flushTimelineToNode({node});
 *     const relay = ltx.buildContiguousRelay({node, globalPromptFallback});
 *
 * R8 owns the real executor-driven LTX workflow rendering.
 * R4-38 Wave 9 establishes the bounded compat boundary; the
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
        'document', 'escapeHtml', 'tr',
        // Factory host ops (mirrors Wave 2/3/4 addNode pattern)
        'addNode', 'uid', 'defaultPoint',
        // LTX helper functions (page-side, stay page-owned per COMPAT)
        'ltxMigrateLegacySegments', 'ltxDirectorSyncSeconds',
        'bindLTXParamsRow', 'ltxSyncConnectedImagesToTimeline',
        'defaultLTXSegment',
        // Source / media / display helpers
        'orderedSources', 'generatorSources', 'imageRefsOnly',
        'renderPromptPreview', 'renderComfyImages',
        // Lifecycle / composition
        'scheduleSave', 'runCanvasGenerate',
        'bindCascadeButtons', 'cascadeBtnHtml', 'retryBarHtml',
        // Node geometry / layout
        'updateLTXNodeElementSize', 'refreshGeometryAfterLayout',
        // Global LTX migration helper (window.ltxMigrateLegacySegments
        // is the production path; page-side fallback also injected)
        'windowObj',
        ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicLtxControls.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicLtxControls.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var escapeHtml = host.escapeHtml;
        var tr = host.tr;
        var addNode = host.addNode;
        var uid = host.uid;
        var defaultPoint = host.defaultPoint;
        var ltxMigrateLegacySegments = host.ltxMigrateLegacySegments;
        var ltxDirectorSyncSeconds = host.ltxDirectorSyncSeconds;
        var bindLTXParamsRow = host.bindLTXParamsRow;
        var ltxSyncConnectedImagesToTimeline = host.ltxSyncConnectedImagesToTimeline;
        var defaultLTXSegment = host.defaultLTXSegment;
        var orderedSources = host.orderedSources;
        var generatorSources = host.generatorSources;
        var imageRefsOnly = host.imageRefsOnly;
        var renderPromptPreview = host.renderPromptPreview;
        var renderComfyImages = host.renderComfyImages;
        var scheduleSave = host.scheduleSave;
        var runCanvasGenerate = host.runCanvasGenerate;
        var bindCascadeButtons = host.bindCascadeButtons;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var updateLTXNodeElementSize = host.updateLTXNodeElementSize;
        var refreshGeometryAfterLayout = host.refreshGeometryAfterLayout;
        var windowObj = host.windowObj;

        function addLTXDirectorNode(point) {
            var p = point || defaultPoint(200, 0);
            return addNode({
                id: uid('ltxdir'),
                type: 'ltxDirector',
                x: p.x,
                y: p.y,
                w: 1000,
                h: 800,
                globalPrompt: '',
                durationFrames: 120,
                durationSeconds: 5,
                frameRate: 24,
                customWidth: 0,
                customHeight: 0,
                displayMode: 'seconds',
                useCustomAudio: false,
                imgCompression: 18,
                epsilon: 0.001,
                divisibleBy: 32,
                noiseSeed: 12,
                ltxTimelineData: '',
                ltxLocalPrompts: '',
                ltxSegmentLengths: '',
                ltxGuideStrength: '',
                ltxSegments: [],
                ltxSelectedSegId: '',
                inputs: [],
                running: false
            });
        }

        function destroyLTXEditor(node) {
            if (!node || !node._ltxEditor) return;
            try { if (node._ltxEditor.destroy) node._ltxEditor.destroy(); } catch (e) { /* ignore */ }
            node._ltxEditor = null;
        }

        function ltxParseTimeline(node) {
            try {
                var t = JSON.parse((node && node.ltxTimelineData) || '{}');
                return {
                    segments: Array.isArray(t.segments) ? t.segments : [],
                    audioSegments: Array.isArray(t.audioSegments) ? t.audioSegments : []
                };
            } catch (e) {
                return { segments: [], audioSegments: [] };
            }
        }

        function ltxFlushTimelineToNode(node) {
            if (!node || node.type !== 'ltxDirector') return;
            if (node._ltxEditor && typeof node._ltxEditor.commitChanges === 'function') {
                node._ltxEditor.commitChanges(true);
            }
        }

        function ltxBuildContiguousRelay(node, globalPromptFallback) {
            if (globalPromptFallback === undefined) globalPromptFallback = '';
            ltxFlushTimelineToNode(node);
            var durationFrames = Math.max(1, Number(node.durationFrames) || 120);
            var fallback = (globalPromptFallback || node.globalPrompt || '').trim() || '.';
            var sortedSegments = [];
            try {
                var t = JSON.parse(node.ltxTimelineData || '{}');
                sortedSegments = (t.segments || []).slice().sort(function (a, b) {
                    return (Number(a.start) || 0) - (Number(b.start) || 0);
                });
            } catch (e) { /* empty fallback below */ }
            var consecutiveLengths = [];
            var consecutivePrompts = [];
            var currentCursor = 0;
            var pendingGap = 0;
            for (var i = 0; i < sortedSegments.length; i++) {
                var seg = sortedSegments[i];
                var start = Number(seg.start) || 0;
                var length = Math.max(1, Number(seg.length) || 1);
                if (start >= durationFrames) break;
                if (start > currentCursor) {
                    var gapLength = Math.min(start, durationFrames) - currentCursor;
                    if (consecutiveLengths.length > 0) consecutiveLengths[consecutiveLengths.length - 1] += gapLength;
                    else pendingGap += gapLength;
                }
                var clippedEnd = Math.min(start + length, durationFrames);
                var clippedLength = clippedEnd - start;
                consecutiveLengths.push(clippedLength + pendingGap);
                var prompt = (seg.prompt || '').trim();
                consecutivePrompts.push(prompt || fallback);
                if (!prompt) seg.prompt = fallback;
                pendingGap = 0;
                currentCursor = start + length;
            }
            var clampedCursor = Math.min(currentCursor, durationFrames);
            if (consecutiveLengths.length > 0 && clampedCursor < durationFrames) {
                consecutiveLengths[consecutiveLengths.length - 1] += durationFrames - clampedCursor;
            }
            if (!consecutiveLengths.length) {
                consecutiveLengths.push(durationFrames);
                consecutivePrompts.push(fallback);
            }
            var guideStrength = sortedSegments
                .filter(function (s) { return s.type !== 'text'; })
                .map(function (s) { return (s.guideStrength !== undefined ? s.guideStrength : 1.0).toFixed(2); })
                .join(',');
            return {
                local_prompts: consecutivePrompts.join(' | '),
                segment_lengths: consecutiveLengths.join(','),
                guide_strength: guideStrength,
                sortedSegments: sortedSegments
            };
        }

        function renderLTXDirectorBody(node) {
            if (typeof windowObj.ltxMigrateLegacySegments === 'function') windowObj.ltxMigrateLegacySegments(node);
            else if (typeof ltxMigrateLegacySegments === 'function') ltxMigrateLegacySegments(node);
            ltxDirectorSyncSeconds(node);
            if (!node.ltxTimelineData) {
                var len = Math.max(1, Number(node.durationFrames) || 120);
                node.ltxTimelineData = JSON.stringify({
                    segments: [Object.assign({}, defaultLTXSegment(0, len), { prompt: '', type: 'text' })],
                    audioSegments: []
                });
            }
            var wrap = document.createElement('div');
            wrap.className = 'ltx-director-body';
            var sources = orderedSources(node, generatorSources(node));
            var promptInputs = sources.filter(function (src) { return src.prompt && !(src.refs && src.refs.length); });
            var imageInputs = sources
                .map(function (src) { return Object.assign({}, src, { refs: imageRefsOnly(src.refs || []) }); })
                .filter(function (src) { return src.refs && src.refs.length; });
            wrap.innerHTML =
                '<div class="prompt-list"></div>' +
                '<div class="ltx-params-row" data-ltx-params>' +
                '<label class="field"><span class="setting-title">' + tr('canvas.ltxDurationSec') + '</span><input class="setting-input" data-ltx-duration-seconds type="number" min="0.1" max="1000" step="0.01"></label>' +
                '<label class="field"><span class="setting-title">' + tr('canvas.ltxDurationFrames') + '</span><input class="setting-input" data-ltx-duration-frames type="number" min="1" max="10000" step="1"></label>' +
                '<label class="field"><span class="setting-title">' + tr('canvas.ltxFps') + '</span><input class="setting-input" data-ltx-frame-rate type="number" min="1" max="240" step="1"></label>' +
                '<label class="field"><span class="setting-title">' + tr('canvas.width') + '</span><input class="setting-input" data-ltx-width type="number" min="0" max="8192" step="32" title="0 = auto"></label>' +
                '<label class="field"><span class="setting-title">' + tr('canvas.height') + '</span><input class="setting-input" data-ltx-height type="number" min="0" max="8192" step="32" title="0 = auto"></label>' +
                '</div>' +
                '<div class="ltx-director-timeline-host" data-ltx-timeline-host></div>' +
                '<div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">' + tr('canvas.ltxLinkedImages') + ' · ' + imageInputs.length + '</div>' +
                '<div class="input-list mt-1"></div>' +
                '<div class="gen-run-row">' +
                '<button class="comfy-run ltx-run ' + (node.running ? 'running' : '') + '" ' + (node.running ? 'disabled' : '') + '><i data-lucide="film" class="w-4 h-4"></i>' + (node.running ? tr('canvas.ltxRunning') : tr('canvas.ltxRun')) + '</button>' +
                cascadeBtnHtml(node) +
                '</div>' +
                retryBarHtml(node);
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            bindLTXParamsRow(wrap, node);
            ltxSyncConnectedImagesToTimeline(node);
            renderComfyImages(wrap.querySelector('.input-list'), node, imageInputs);
            var host = wrap.querySelector('[data-ltx-timeline-host]');
            if (host && windowObj.CanvasLTXTimelineEditor) {
                if (node._ltxEditor && node._ltxEditor.wrapper) {
                    host.appendChild(node._ltxEditor.wrapper);
                    node._ltxEditor.container = host;
                    node._ltxEditor._onCanvasCommit = function () { scheduleSave(); };
                    node._ltxEditor._onCanvasResize = function () { updateLTXNodeElementSize(node); scheduleSave(); };
                } else {
                    destroyLTXEditor(node);
                    try {
                        var editor = new windowObj.CanvasLTXTimelineEditor(node, host, null);
                        editor._onCanvasCommit = function () { scheduleSave(); };
                        editor._onCanvasResize = function () { updateLTXNodeElementSize(node); scheduleSave(); };
                        node._ltxEditor = editor;
                    } catch (err) {
                        if (windowObj.console && windowObj.console.error) windowObj.console.error('LTX timeline editor init failed', err);
                        host.innerHTML = '<div class="text-[11px] text-red-500 p-2">' + escapeHtml(tr('canvas.ltxTimelineLoadFailed')) + '</div>';
                    }
                }
            } else if (host) {
                host.innerHTML = '<div class="text-[11px] text-red-500 p-2">' + escapeHtml(tr('canvas.ltxTimelineScriptMissing')) + '</div>';
            }
            var runBtn = wrap.querySelector('.ltx-run');
            if (runBtn) {
                runBtn.onmousedown = function (e) { e.stopPropagation(); };
                runBtn.onclick = function (e) {
                    e.stopPropagation();
                    e.preventDefault();
                    runCanvasGenerate(node.id);
                };
            }
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        return Object.freeze({
            addNode: function (arg) { return addLTXDirectorNode(arg.point); },
            renderBody: function (arg) { return renderLTXDirectorBody(arg.node); },
            destroyEditor: function (arg) { return destroyLTXEditor(arg.node); },
            parseTimeline: function (arg) { return ltxParseTimeline(arg.node); },
            flushTimelineToNode: function (arg) { return ltxFlushTimelineToNode(arg.node); },
            buildContiguousRelay: function (arg) { return ltxBuildContiguousRelay(arg.node, arg.globalPromptFallback); },
        });
    }

    window.WorkbenchCanvasClassicLtxControls = Object.freeze({ create: create });
})();