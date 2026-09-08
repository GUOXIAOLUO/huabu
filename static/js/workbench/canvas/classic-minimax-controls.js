/*
 * static/js/workbench/canvas/classic-minimax-controls.js
 *
 * Wave 8 of R4-38 — bounded compat seam for the Classic MiniMax
 * timeline / player / generation controls. Six page-side functions
 * move behind a shared seam:
 * `addMiniMaxNode` (~23-line factory), `renderMiniMaxBody`
 * (~102-line body renderer), `bindMiniMaxWorkbench` (~226-line
 * workbench binder that wires up segment / ref / drop / scrub /
 * run / download interactions), `miniMaxEngine` (3-line engine
 * resolver), `miniMaxPlayerHtml` (8-line player HTML builder),
 * `miniMaxSyncPlayerDom` (~18-line player sync).
 *
 * Page-side usage (canvas.js):
 *     const mmx = ensureClassicMiniMaxControls();
 *     // createNodeByType:
 *     if(type === 'minimax') return mmx.addNode({point});
 *     // body dispatcher:
 *     if(node.type === 'minimax') body.appendChild(mmx.renderBody({node}));
 *     // external callers (run, refresh):
 *     mmx.bindWorkbench({wrap, node}); // or via the body dispatcher
 *     mmx.syncPlayerDom({wrap, seg, time, play});
 *     mmx.buildPlayerHtml({seg});
 *
 * R8 owns the real executor-driven MiniMax workflow rendering.
 * R4-38 Wave 8 establishes the bounded compat boundary; the
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
        'document', 'escapeHtml', 'escapeAttr',
        // Factory host ops (mirrors Wave 2/3/4 addNode pattern)
        'addNode', 'uid', 'defaultPoint',
        // MiniMax helper functions (page-side, stay page-owned per COMPAT)
        'miniMaxSelectedSegment', 'miniMaxTimelineTotal',
        'miniMaxActiveSegmentAt', 'miniMaxCompactSegments',
        'miniMaxExplicitRefsForSegment', 'miniMaxRefsForNode',
        'miniMaxUniqueRefs', 'miniMaxMediaHtml',
        'miniMaxSegmentRefsByKind', 'miniMaxStartPaneResize',
        'miniMaxApplyTimelineTime', 'miniMaxDownloadItem',
        'miniMaxSetSegmentResult',
        // Source / media / display helpers
        'mediaKindForRef', 'mediaKindForOutputItem',
        'canvasDisplayMediaUrl', 'canvasPreviewImgHtml',
        'canvasVideoPlayerHtml', 'canvasFileNameFromUrl',
        // Lifecycle / composition
        'pushUndo', 'refreshNodes', 'scheduleSave',
        'bindScrollableText', 'bindCascadeButtons',
        'cascadeBtnHtml', 'retryBarHtml', 'refreshIcons',
        // Cross-card host ops (reused from Wave 5/6/7 seams)
        'rhPaymentOptions',
        // Generation entry point (page-owned; calls into runMiniMaxNode)
        'runMiniMaxNode',
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicMiniMaxControls.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicMiniMaxControls.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var escapeHtml = host.escapeHtml;
        var escapeAttr = host.escapeAttr;
        var addNode = host.addNode;
        var uid = host.uid;
        var defaultPoint = host.defaultPoint;
        var miniMaxSelectedSegment = host.miniMaxSelectedSegment;
        var miniMaxTimelineTotal = host.miniMaxTimelineTotal;
        var miniMaxActiveSegmentAt = host.miniMaxActiveSegmentAt;
        var miniMaxCompactSegments = host.miniMaxCompactSegments;
        var miniMaxExplicitRefsForSegment = host.miniMaxExplicitRefsForSegment;
        var miniMaxRefsForNode = host.miniMaxRefsForNode;
        var miniMaxUniqueRefs = host.miniMaxUniqueRefs;
        var miniMaxMediaHtml = host.miniMaxMediaHtml;
        var miniMaxSegmentRefsByKind = host.miniMaxSegmentRefsByKind;
        var miniMaxStartPaneResize = host.miniMaxStartPaneResize;
        var miniMaxApplyTimelineTime = host.miniMaxApplyTimelineTime;
        var miniMaxDownloadItem = host.miniMaxDownloadItem;
        var miniMaxSetSegmentResult = host.miniMaxSetSegmentResult;
        var mediaKindForRef = host.mediaKindForRef;
        var mediaKindForOutputItem = host.mediaKindForOutputItem;
        var canvasDisplayMediaUrl = host.canvasDisplayMediaUrl;
        var canvasPreviewImgHtml = host.canvasPreviewImgHtml;
        var canvasVideoPlayerHtml = host.canvasVideoPlayerHtml;
        var canvasFileNameFromUrl = host.canvasFileNameFromUrl;
        var pushUndo = host.pushUndo;
        var refreshNodes = host.refreshNodes;
        var scheduleSave = host.scheduleSave;
        var bindScrollableText = host.bindScrollableText;
        var bindCascadeButtons = host.bindCascadeButtons;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var refreshIcons = host.refreshIcons;
        var rhPaymentOptions = host.rhPaymentOptions;
        var runMiniMaxNode = host.runMiniMaxNode;

        // MiniMax constants — injected as host ops so the seam module
        // never touches page-locals directly. Defaults match the
        // canvas.js module-level `const`s (R4 card_id defaults).
        var CANVAS_MINIMAX_REF_IMAGE_MAX = host.CANVAS_MINIMAX_REF_IMAGE_MAX !== undefined
            ? host.CANVAS_MINIMAX_REF_IMAGE_MAX : 9;
        var CANVAS_MINIMAX_REF_VIDEO_MAX = host.CANVAS_MINIMAX_REF_VIDEO_MAX !== undefined
            ? host.CANVAS_MINIMAX_REF_VIDEO_MAX : 3;
        var CANVAS_MINIMAX_REF_AUDIO_MAX = host.CANVAS_MINIMAX_REF_AUDIO_MAX !== undefined
            ? host.CANVAS_MINIMAX_REF_AUDIO_MAX : 3;
        var CANVAS_MINIMAX_DEFAULT_ENGINE = host.CANVAS_MINIMAX_DEFAULT_ENGINE !== undefined
            ? host.CANVAS_MINIMAX_DEFAULT_ENGINE : 'comfyui';
        var CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID = host.CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID !== undefined
            ? host.CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID : '';

        function addMiniMaxNode(point) {
            var p = point || defaultPoint(170, 0);
            return addNode({
                id: uid('mmx'),
                type: 'minimax',
                x: p.x,
                y: p.y,
                w: 980,
                h: 720,
                minimaxEngine: CANVAS_MINIMAX_DEFAULT_ENGINE,
                workflow: 'MiniMax_H3.json',
                minimaxRunningHubWorkflowId: CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID,
                rhPayment: 'free',
                duration: 8,
                aspectRatio: '16:9',
                megapixels: 0.4,
                selectedSegmentId: '',
                playhead: 0,
                segments: [],
                materials: [],
                inputs: [],
                running: false
            });
        }

        function miniMaxEngine(node) {
            return node && node.minimaxEngine === 'runninghub' ? 'runninghub' : CANVAS_MINIMAX_DEFAULT_ENGINE;
        }

        function miniMaxPlayerHtml(seg) {
            var item = seg && seg.result && seg.result.url ? seg.result : null;
            if (!item) return '<div class="minimax-player-empty"><i data-lucide="clapperboard"></i><span>Current segment</span></div>';
            var kind = mediaKindForOutputItem(item);
            if (kind === 'audio') return '<div class="minimax-player-empty"><i data-lucide="file-audio"></i><span>' + escapeHtml(item.name || 'Audio') + '</span><audio src="' + escapeAttr(canvasDisplayMediaUrl(item.url, item.name || 'audio')) + '" controls preload="metadata"></audio></div>';
            if (kind === 'image') return '<div class="minimax-player-image">' + canvasPreviewImgHtml(item.url, 1024, 'draggable="false"') + '</div>';
            return canvasVideoPlayerHtml(item.url, 'data-minimax-player="1"');
        }

        function miniMaxSyncPlayerDom(wrap, seg, time, play) {
            if (play === undefined) play = false;
            var stage = wrap.querySelector('[data-minimax-player-stage]');
            if (!stage || !seg) return;
            var nextUrl = (seg.result && seg.result.url) || '';
            if (stage.dataset.minimaxPlayerSegment !== seg.id || stage.dataset.minimaxPlayerUrl !== nextUrl) {
                stage.dataset.minimaxPlayerSegment = seg.id || '';
                stage.dataset.minimaxPlayerUrl = nextUrl;
                var content = stage.querySelector('[data-minimax-player-content]');
                if (content) content.innerHTML = miniMaxPlayerHtml(seg);
                refreshIcons();
            }
            var media = stage.querySelector('[data-minimax-player]');
            if (media) {
                var rel = Math.max(0, Number(time || 0) - Number(seg.start || 0));
                try { media.currentTime = Math.min(Math.max(0, rel), Number(seg.duration || rel) || rel); } catch (e) { /* ignore */ }
                if (play) media.play && media.play().catch(function () {});
                else media.pause && media.pause();
            }
        }

        function renderMiniMaxBody(node) {
            var wrap = document.createElement('div');
            wrap.className = 'minimax-canvas-workbench';
            var selected = miniMaxSelectedSegment(node);
            var total = miniMaxTimelineTotal(node);
            var playhead = Math.max(0, Math.min(total, Number(node.playhead || 0)));
            var playheadPct = total > 0 ? (playhead / total) * 100 : 0;
            var fmt = function (value) {
                var v = Number(value || 0);
                return v.toFixed(v % 1 ? 1 : 0) + 's';
            };
            var previewH = Math.max(130, Math.min(760, Number(node.minimaxPreviewH || 220)));
            var videoTrackH = Math.max(48, Math.min(180, Number(node.minimaxVideoTrackH || 74)));
            var refLaneH = Math.max(30, Math.min(130, Number(node.minimaxRefLaneH || 36)));
            var libraryW = Math.max(170, Math.min(520, Number(node.minimaxLibraryW || 190)));
            var ticks = Array.from({ length: Math.min(13, Math.max(3, Math.ceil(total) + 1)) }).map(function (_, i, arr) {
                var ratio = arr.length <= 1 ? 0 : i / (arr.length - 1);
                return '<span class="minimax-tick" style="left:' + (ratio * 100) + '%"><b>' + fmt(total * ratio) + '</b></span>';
            }).join('');
            var segmentsHtml = node.segments.map(function (seg, index) {
                var left = total ? (Number(seg.start || 0) / total) * 100 : 0;
                var width = total ? Math.max(5, (Number(seg.duration || 1) / total) * 100) : 100;
                var active = seg.id === (selected && selected.id);
                var result = seg.result && seg.result.url ? seg.result : null;
                var refCount = miniMaxExplicitRefsForSegment(seg).length;
                return '<div class="minimax-tl-clip ' + (active ? 'active ' : '') + (result ? 'has-result' : '') + '" data-minimax-segment="' + escapeAttr(seg.id) + '" data-minimax-drop-segment="' + escapeAttr(seg.id) + '" style="left:' + left + '%;width:' + Math.min(width, 100 - left) + '%" title="Clip ' + (index + 1) + '">' +
                    '<div class="minimax-clip-media">' + (result ? miniMaxMediaHtml(result, 'Clip ' + (index + 1)) : '<div class="minimax-clip-empty"><i data-lucide="sparkles"></i></div>') + '</div>' +
                    '<div class="minimax-clip-meta"><b>Clip ' + (index + 1) + '</b><span>' + fmt(seg.start) + ' - ' + fmt(Number(seg.start || 0) + Number(seg.duration || 0)) + '</span></div>' +
                    (refCount ? '<span class="minimax-clip-ref-count"><i data-lucide="paperclip"></i>' + refCount + '</span>' : '') +
                    (node.segments.length > 1 ? '<button type="button" class="minimax-clip-delete" data-minimax-delete-segment="' + escapeAttr(seg.id) + '" title="删除片段"><i data-lucide="trash-2"></i></button>' : '') +
                    '</div>';
            }).join('');
            var selectedRefs = miniMaxExplicitRefsForSegment(selected);
            var refLanes = Math.max(1, selectedRefs.length, ...node.segments.map(function (seg) { return miniMaxExplicitRefsForSegment(seg).length; }));
            var refsHtml = Array.from({ length: refLanes }).map(function (_, laneIndex) {
                var clips = node.segments.map(function (seg) {
                    var left = total ? (Number(seg.start || 0) / total) * 100 : 0;
                    var width = total ? Math.max(5, (Number(seg.duration || 1) / total) * 100) : 100;
                    var ref = miniMaxExplicitRefsForSegment(seg)[laneIndex] || null;
                    var active = seg.id === (selected && selected.id);
                    return '<div class="minimax-ref-clip ' + (active ? 'active ' : '') + (ref ? 'has-ref' : 'is-empty') + '" data-minimax-ref-segment="' + escapeAttr(seg.id) + '" data-minimax-segment="' + escapeAttr(seg.id) + '" data-minimax-drop-segment="' + escapeAttr(seg.id) + '" style="left:' + left + '%;width:' + Math.min(width, 100 - left) + '%">' +
                        '<div class="minimax-ref-media">' + (ref ? miniMaxMediaHtml(ref, 'Ref ' + (laneIndex + 1)) : '<div class="minimax-clip-empty"><i data-lucide="paperclip"></i></div>') + '</div>' +
                        (ref ? '<button type="button" data-minimax-delete-ref="' + escapeAttr(seg.id + ':' + laneIndex) + '" title="移除参考"><i data-lucide="x"></i></button>' : '') +
                        '<span class="minimax-ref-counts">' + (ref ? escapeHtml(ref.name || ('Ref ' + (laneIndex + 1))) : ('Ref ' + (laneIndex + 1))) + '</span>' +
                        '</div>';
                }).join('');
                return '<div class="minimax-ref-lane">' + clips + '</div>';
            }).join('');
            var upstream = miniMaxRefsForNode(node);
            var assets = miniMaxUniqueRefs([...node.segments.flatMap(function (seg) { return seg.refs || []; }), ...upstream.refs]).slice(0, 36);
            var assetsHtml = assets.length ? assets.map(function (item, index) {
                return '<div class="minimax-material-card minimax-asset-item" draggable="true" data-minimax-asset-index="' + index + '" title="' + escapeAttr(item.name || mediaKindForRef(item)) + '">' +
                    miniMaxMediaHtml(item, item.name || mediaKindForRef(item)) +
                    '<span>' + escapeHtml(mediaKindForRef(item)) + '</span>' +
                    '</div>';
            }).join('') : '<div class="minimax-library-empty"><i data-lucide="database"></i><span>Assets</span></div>';
            var materialsHtml = (node.materials || []).slice(0, 24).map(function (item, index) {
                return '<div class="minimax-material-card minimax-output-item" draggable="true" data-minimax-material-index="' + index + '" title="' + escapeAttr(item.name || 'Output') + '">' +
                    miniMaxMediaHtml(item, 'Output') +
                    '<button type="button" data-minimax-download-material="' + index + '" title="下载"><i data-lucide="download"></i></button>' +
                    '<button type="button" data-minimax-use-material="' + index + '" title="设为当前片段"><i data-lucide="replace"></i></button>' +
                    '</div>';
            }).join('') || '<div class="minimax-library-empty"><i data-lucide="inbox"></i><span>Output</span></div>';
            var segDuration = Math.max(0.5, Number((selected && selected.duration) || 8) || 8);
            var imageCount = miniMaxSegmentRefsByKind(selectedRefs, 'image').length;
            var videoCount = miniMaxSegmentRefsByKind(selectedRefs, 'video').length;
            var audioCount = miniMaxSegmentRefsByKind(selectedRefs, 'audio').length;
            var overLimit = imageCount > CANVAS_MINIMAX_REF_IMAGE_MAX || videoCount > CANVAS_MINIMAX_REF_VIDEO_MAX || audioCount > CANVAS_MINIMAX_REF_AUDIO_MAX;
            wrap.innerHTML =
                '<div class="minimax-wb-toolbar">' +
                '<div class="minimax-brand"><i data-lucide="clapperboard"></i><span>MiniMax H3</span><b data-minimax-time-label>' + fmt(playhead) + ' / ' + fmt(total) + '</b></div>' +
                '<div class="minimax-transport"><button type="button" data-minimax-play title="播放"><i data-lucide="play"></i></button><button type="button" data-minimax-add-segment title="新增片段"><i data-lucide="plus"></i></button></div>' +
                '<div class="minimax-top-actions"><button type="button" data-minimax-download-current ' + ((selected && selected.result && selected.result.url) ? '' : 'disabled') + ' title="下载当前片段"><i data-lucide="download"></i></button></div>' +
                '</div>' +
                '<div class="minimax-wb-body" style="--minimax-library-w:' + libraryW + 'px">' +
                '<div class="minimax-library minimax-asset-bin"><span class="minimax-pane-resize minimax-library-resize" data-minimax-pane-resize="library"></span><div class="minimax-library-head"><i data-lucide="database"></i><span>Assets</span></div><div class="minimax-library-list">' + assetsHtml + '</div><div class="minimax-library-head minimax-output-head"><i data-lucide="folder-output"></i><span>Output</span></div><div class="minimax-library-list minimax-output-list">' + materialsHtml + '</div></div>' +
                '<div class="minimax-wb-main" style="--minimax-preview-h:' + previewH + 'px;--minimax-video-h:' + videoTrackH + 'px;--minimax-ref-lane-h:' + refLaneH + 'px;--minimax-ref-h:' + Math.max(78, refLanes * refLaneH) + 'px">' +
                '<div class="minimax-player-stage" data-minimax-player-stage="1" data-minimax-player-segment="' + escapeAttr((selected && selected.id) || '') + '" data-minimax-player-url="' + escapeAttr((selected && selected.result && selected.result.url) || '') + '"><div class="minimax-player-content" data-minimax-player-content="1">' + miniMaxPlayerHtml(selected) + '</div><span class="minimax-pane-resize minimax-preview-resize" data-minimax-pane-resize="preview"></span></div>' +
                '<div class="minimax-edit-timeline" data-minimax-scrub-track="1">' +
                '<span class="minimax-pane-resize minimax-video-resize" data-minimax-pane-resize="video"></span>' +
                '<span class="minimax-pane-resize minimax-ref-resize" data-minimax-pane-resize="refs"></span>' +
                '<div class="minimax-timeline-controls"><button type="button" data-minimax-play title="播放"><i data-lucide="play"></i></button></div>' +
                '<div class="minimax-ruler"><div class="minimax-track-content">' + ticks + '<span class="minimax-playhead" data-minimax-playhead="1" style="left:' + playheadPct + '%"></span></div></div>' +
                '<div class="minimax-add-gutter minimax-ruler-gutter"></div>' +
                '<div class="minimax-track-label minimax-video-label">Video</div>' +
                '<div class="minimax-track minimax-video-track"><div class="minimax-track-content">' + segmentsHtml + '</div></div>' +
                '<button type="button" class="minimax-video-add" data-minimax-add-segment title="新增片段"><i data-lucide="plus"></i></button>' +
                '<div class="minimax-track-label minimax-ref-label">Refs</div>' +
                '<div class="minimax-ref-track"><div class="minimax-ref-content">' + refsHtml + '</div></div>' +
                '<div class="minimax-add-gutter minimax-ref-gutter"></div>' +
                '</div>' +
                '<div class="minimax-current-panel">' +
                '<div class="minimax-current-head"><div class="minimax-current-title"><span class="minimax-current-dot"></span><b>Clip ' + Math.max(1, node.segments.findIndex(function (seg) { return seg.id === (selected && selected.id); }) + 1) + '</b><span>' + fmt(selected && selected.start) + ' - ' + fmt(Number((selected && selected.start) || 0) + segDuration) + '</span></div><div class="minimax-current-refs"><span><i data-lucide="image"></i>' + imageCount + '</span><span><i data-lucide="film"></i>' + videoCount + '</span><span><i data-lucide="file-audio"></i>' + audioCount + '</span></div></div>' +
                '<label class="minimax-prompt-field"><span><i data-lucide="text-cursor-input"></i>Prompt</span><textarea data-minimax-prompt placeholder="Prompt for selected clip">' + escapeHtml((selected && selected.prompt) || '') + '</textarea></label>' +
                '<div class="minimax-clip-parameters"><div class="minimax-section-label"><i data-lucide="sliders-horizontal"></i><span>Clip settings</span></div><div class="minimax-settings minimax-segment-fields">' +
                '<label class="minimax-wide-setting minimax-engine-setting"><span>Engine</span><select class="minimax-engine-select" data-minimax-engine><option value="comfyui" ' + (node.minimaxEngine === 'comfyui' ? 'selected' : '') + '>ComfyUI</option><option value="runninghub" ' + (node.minimaxEngine === 'runninghub' ? 'selected' : '') + '>RunningHub</option></select></label>' +
                '<label><span>Duration</span><input type="number" min="0.5" max="60" step="0.1" data-minimax-seg-number="duration" value="' + escapeAttr(segDuration) + '"><b>s</b></label>' +
                '<label><span>Megapixels</span><input type="number" min="0.1" max="2" step="0.1" data-minimax-seg-number="megapixels" value="' + escapeAttr((selected && selected.megapixels) || node.megapixels || 0.4) + '"><b>MP</b></label>' +
                '<label class="minimax-wide-setting"><span>Aspect ratio</span><select data-minimax-select="aspectRatio">' + ['16:9', '9:16', '1:1', '4:3', '3:4', '21:9', '9:21'].map(function (value) { return '<option value="' + value + '" ' + (value === ((selected && selected.aspectRatio) || node.aspectRatio) ? 'selected' : '') + '>' + value + '</option>'; }).join('') + '</select></label>' +
                '<label class="minimax-wide-setting"><span>Payment</span><select data-minimax-payment>' + rhPaymentOptions(node) + '</select></label>' +
                '<button class="minimax-run ' + (node.running ? 'running' : '') + '" type="button" data-minimax-run ' + (node.running || overLimit ? 'disabled' : '') + '><i data-lucide="' + (node.running ? 'loader-2' : 'sparkles') + '"></i><span>' + (node.running ? 'Running' : 'Generate clip') + '</span></button>' +
                '</div></div>' +
                '</div>' +
                '</div>' +
                retryBarHtml(node);
            bindMiniMaxWorkbench(wrap, node);
            bindCascadeButtons(wrap, node.id);
            return wrap;
        }

        function bindMiniMaxWorkbench(wrap, node) {
            wrap.querySelectorAll('button,select,input,textarea,.minimax-tl-clip,.minimax-ref-clip,.minimax-material-card').forEach(function (el) {
                el.onmousedown = function (e) { e.stopPropagation(); };
                el.onclick = el.onclick || function (e) { e.stopPropagation(); };
            });
            wrap.querySelectorAll('[data-minimax-pane-resize]').forEach(function (handle) {
                handle.onmousedown = e => miniMaxStartPaneResize(e, node, handle.dataset.minimaxPaneResize);
            });
            var addRefToSegment = function (seg, item) {
                if (!seg || !item || !item.url) return false;
                var kind = mediaKindForRef(item);
                var limits = { image: CANVAS_MINIMAX_REF_IMAGE_MAX, video: CANVAS_MINIMAX_REF_VIDEO_MAX, audio: CANVAS_MINIMAX_REF_AUDIO_MAX };
                if (!limits[kind]) return false;
                var current = miniMaxUniqueRefs(seg.refs || []);
                if (current.some(function (ref) { return ref.url === item.url; })) return false;
                if (current.filter(function (ref) { return mediaKindForRef(ref) === kind; }).length >= limits[kind]) return false;
                seg.refs = miniMaxUniqueRefs([...current, Object.assign({}, item, { kind: kind })]);
                return true;
            };
            var assetsForNode = function () { return miniMaxUniqueRefs([...node.segments.flatMap(function (seg) { return seg.refs || []; }), ...miniMaxRefsForNode(node).refs]).slice(0, 36); };
            var resolveDroppedMiniMaxItem = function (dataTransfer) {
                var assetIndex = Number(dataTransfer && dataTransfer.getData('application/x-canvas-minimax-asset-index'));
                if (Number.isFinite(assetIndex)) return { item: assetsForNode()[assetIndex], mode: 'ref' };
                var materialIndex = Number(dataTransfer && dataTransfer.getData('application/x-canvas-minimax-material-index'));
                if (Number.isFinite(materialIndex)) return { item: node.materials && node.materials[materialIndex], mode: 'result' };
                var canvasUrl = (dataTransfer && (dataTransfer.getData('application/x-canvas-output-image') || dataTransfer.getData('text/uri-list') || dataTransfer.getData('text/plain'))) || '';
                var url = String(canvasUrl || '').split(/\r?\n/).find(Boolean) || '';
                return url ? { item: { url: url, name: canvasFileNameFromUrl(url) || 'asset', kind: mediaKindForRef({ url: url }) }, mode: 'ref' } : null;
            };
            wrap.querySelectorAll('[data-minimax-scrub-track], .minimax-ruler, .minimax-video-track').forEach(function (track) {
                track.onmousedown = function (e) {
                    if (e.button !== 0 || e.target.closest('button,.minimax-tl-clip,.minimax-ref-clip,.minimax-pane-resize')) return;
                    e.preventDefault();
                    e.stopPropagation();
                    var content = wrap.querySelector('.minimax-ruler .minimax-track-content') || track;
                    var rect = content.getBoundingClientRect();
                    var setFromEvent = function (ev) {
                        if (ev.preventDefault) ev.preventDefault();
                        var ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / Math.max(1, rect.width)));
                        miniMaxApplyTimelineTime(wrap, node, ratio * miniMaxTimelineTotal(node));
                    };
                    var onMove = function (move) { setFromEvent(move); };
                    var onUp = function () {
                        window.removeEventListener('mousemove', onMove, true);
                        window.removeEventListener('mouseup', onUp, true);
                        window.removeEventListener('blur', onUp, true);
                        scheduleSave();
                    };
                    setFromEvent(e);
                    window.addEventListener('mousemove', onMove, true);
                    window.addEventListener('mouseup', onUp, true);
                    window.addEventListener('blur', onUp, true);
                };
            });
            wrap.querySelectorAll('[data-minimax-drop-segment], .minimax-ref-track, .minimax-video-track').forEach(function (zone) {
                zone.ondragover = function (e) { e.preventDefault(); e.stopPropagation(); zone.classList.add('drag-over'); };
                zone.ondragleave = function (e) { e.stopPropagation(); zone.classList.remove('drag-over'); };
                zone.ondrop = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    zone.classList.remove('drag-over');
                    var segId = zone.dataset.minimaxDropSegment || ((zone.closest && zone.closest('[data-minimax-drop-segment]')) && zone.closest('[data-minimax-drop-segment]').dataset.minimaxDropSegment) || '';
                    if (!segId) {
                        var content = wrap.querySelector('.minimax-ruler .minimax-track-content') || wrap.querySelector('.minimax-video-track');
                        var rect = content && content.getBoundingClientRect && content.getBoundingClientRect();
                        if (rect) {
                            var ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / Math.max(1, rect.width)));
                            segId = (miniMaxActiveSegmentAt(node, ratio * miniMaxTimelineTotal(node)) && miniMaxActiveSegmentAt(node, ratio * miniMaxTimelineTotal(node)).id) || '';
                        }
                    }
                    segId = segId || node.selectedSegmentId;
                    var seg = node.segments.find(function (item) { return item.id === segId; }) || miniMaxSelectedSegment(node);
                    var dropped = resolveDroppedMiniMaxItem(e.dataTransfer);
                    if (!dropped || !dropped.item || !dropped.item.url || !seg) return;
                    pushUndo();
                    node.selectedSegmentId = seg.id;
                    var intoVideoTrack = Boolean((zone.closest && (zone.closest('.minimax-video-track,.minimax-tl-clip'))) || (zone.classList && (zone.classList.contains('minimax-video-track') || zone.classList.contains('minimax-tl-clip'))));
                    var intoRefTrack = Boolean((zone.closest && (zone.closest('.minimax-ref-track,.minimax-ref-clip'))) || (zone.classList && (zone.classList.contains('minimax-ref-track') || zone.classList.contains('minimax-ref-clip'))));
                    if (dropped.mode === 'result' && intoVideoTrack && !intoRefTrack) miniMaxSetSegmentResult(node, seg, dropped.item);
                    else addRefToSegment(seg, dropped.item);
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-segment], [data-minimax-ref-segment]').forEach(function (el) {
                el.onclick = function (e) {
                    if (e.target.closest('button')) return;
                    e.stopPropagation();
                    node.selectedSegmentId = el.dataset.minimaxSegment || el.dataset.minimaxRefSegment || node.selectedSegmentId;
                    var seg = miniMaxSelectedSegment(node);
                    node.playhead = Number((seg && seg.start) || 0);
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-add-segment]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    pushUndo();
                    miniMaxCompactSegments(node);
                    var start = miniMaxTimelineTotal(node);
                    var duration = Math.max(0.5, Number((node.segments.at && node.segments.at(-1).duration) || node.duration || 8) || 8);
                    var seg = { id: uid('seg'), start: start, duration: duration, prompt: '', refs: [], result: null, results: [], aspectRatio: node.aspectRatio || '16:9', megapixels: Number(node.megapixels || 0.4), trimIn: 0, trimOut: duration };
                    node.segments.push(seg);
                    node.selectedSegmentId = seg.id;
                    node.playhead = start;
                    miniMaxCompactSegments(node);
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-delete-segment]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    if (node.segments.length <= 1) return;
                    pushUndo();
                    var id = btn.dataset.minimaxDeleteSegment;
                    node.segments = node.segments.filter(function (seg) { return seg.id !== id; });
                    node.selectedSegmentId = (node.segments[0] && node.segments[0].id) || '';
                    miniMaxCompactSegments(node);
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-delete-ref]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    var parts = String(btn.dataset.minimaxDeleteRef || '').split(':');
                    var segId = parts[0];
                    var rawIndex = parts[1];
                    var seg = node.segments.find(function (item) { return item.id === segId; });
                    var index = Number(rawIndex);
                    if (!seg || !Number.isFinite(index)) return;
                    pushUndo();
                    var refs = miniMaxExplicitRefsForSegment(seg);
                    refs.splice(index, 1);
                    seg.refs = refs;
                    node.selectedSegmentId = seg.id;
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            var prompt = wrap.querySelector('[data-minimax-prompt]');
            if (prompt) {
                bindScrollableText(prompt);
                prompt.oninput = function (e) {
                    e.stopPropagation();
                    var seg = miniMaxSelectedSegment(node);
                    if (seg) seg.prompt = prompt.value;
                    scheduleSave();
                };
            }
            wrap.querySelectorAll('[data-minimax-engine]').forEach(function (select) {
                select.onchange = function (e) { e.stopPropagation(); node.minimaxEngine = e.target.value === 'runninghub' ? 'runninghub' : 'comfyui'; refreshNodes([node.id]); scheduleSave(); };
            });
            wrap.querySelectorAll('[data-minimax-payment]').forEach(function (select) {
                select.onchange = function (e) { e.stopPropagation(); node.rhPayment = e.target.value === 'wallet' ? 'wallet' : 'free'; scheduleSave(); };
            });
            wrap.querySelectorAll('[data-minimax-select]').forEach(function (select) {
                select.onchange = function (e) {
                    e.stopPropagation();
                    var seg = miniMaxSelectedSegment(node);
                    if (seg) seg[select.dataset.minimaxSelect] = select.value;
                    node[select.dataset.minimaxSelect] = select.value;
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-seg-number]').forEach(function (input) {
                input.oninput = input.onchange = function (e) {
                    e.stopPropagation();
                    var seg = miniMaxSelectedSegment(node);
                    if (!seg) return;
                    var value = Number(input.value);
                    if (input.dataset.minimaxSegNumber === 'duration') {
                        seg.duration = Math.max(0.5, value || 0.5);
                        seg.trimOut = Math.min(seg.duration, Math.max(Number(seg.trimOut || seg.duration), Number(seg.trimIn || 0) + 0.1));
                        miniMaxCompactSegments(node);
                        if (e.type === 'change') refreshNodes([node.id]);
                    }
                    if (input.dataset.minimaxSegNumber === 'megapixels') {
                        seg.megapixels = Math.max(0.1, Math.min(2, value || 0.4));
                        node.megapixels = seg.megapixels;
                    }
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-run]').forEach(function (btn) {
                btn.onclick = function (e) { e.stopPropagation(); runMiniMaxNode(node.id); };
            });
            wrap.querySelectorAll('[data-minimax-download-current]').forEach(function (btn) {
                btn.onclick = function (e) { e.stopPropagation(); miniMaxDownloadItem(miniMaxSelectedSegment(node) && miniMaxSelectedSegment(node).result); };
            });
            wrap.querySelectorAll('[data-minimax-download-material]').forEach(function (btn) {
                btn.onclick = function (e) { e.stopPropagation(); miniMaxDownloadItem(node.materials && node.materials[Number(btn.dataset.minimaxDownloadMaterial)]); };
            });
            wrap.querySelectorAll('[data-minimax-use-material]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    var item = node.materials && node.materials[Number(btn.dataset.minimaxUseMaterial)];
                    var seg = miniMaxSelectedSegment(node);
                    if (!item || !seg) return;
                    pushUndo();
                    miniMaxSetSegmentResult(node, seg, item);
                    refreshNodes([node.id]);
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-minimax-asset-index]').forEach(function (card) {
                card.ondragstart = function (e) {
                    e.stopPropagation();
                    e.dataTransfer.effectAllowed = 'copy';
                    e.dataTransfer.setData('application/x-canvas-minimax-asset-index', card.dataset.minimaxAssetIndex || '');
                };
            });
            wrap.querySelectorAll('[data-minimax-material-index]').forEach(function (card) {
                card.ondragstart = function (e) {
                    e.stopPropagation();
                    e.dataTransfer.effectAllowed = 'copy';
                    e.dataTransfer.setData('application/x-canvas-minimax-material-index', card.dataset.minimaxMaterialIndex || '');
                };
            });
            wrap.querySelectorAll('[data-minimax-play]').forEach(function (btn) {
                btn.onclick = function (e) {
                    e.stopPropagation();
                    var video = wrap.querySelector('[data-minimax-player]');
                    if (video) { video.paused ? (video.play && video.play().catch(function () {})) : (video.pause && video.pause()); }
                };
            });
        }

        return Object.freeze({
            addNode: function (arg) { return addMiniMaxNode(arg.point); },
            renderBody: function (arg) { return renderMiniMaxBody(arg.node); },
            bindWorkbench: function (arg) { return bindMiniMaxWorkbench(arg.wrap, arg.node); },
            getEngine: function (arg) { return miniMaxEngine(arg.node); },
            buildPlayerHtml: function (arg) { return miniMaxPlayerHtml(arg.seg); },
            syncPlayerDom: function (arg) { return miniMaxSyncPlayerDom(arg.wrap, arg.seg, arg.time, arg.play); },
        });
    }

    window.WorkbenchCanvasClassicMiniMaxControls = Object.freeze({ create: create });
})();