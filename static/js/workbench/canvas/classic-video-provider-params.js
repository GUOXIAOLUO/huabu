/*
 * static/js/workbench/canvas/classic-video-provider-params.js
 *
 * Wave 11 of R4-38 — bounded compat seam for the Classic video-node
 * provider/params helpers. Four page-side functions move behind a
 * shared seam:
 * `videoApiProviders` (5-line provider list filter that strips
 * `modelscope` and providers without video_models, falling back to
 * `defaultApiProviders()` when empty), `resolveVideoProviderId(id)`
 * (3-line provider id resolver that prefers the requested id, else
 * the first provider, else 'comfly'), `providerVideoModels(providerId)`
 * (4-line model resolver that uses `apiProviders.find(p => p.id === id)`
 * for exact-match only, then dedupes via `uniqueModels`), and
 * `renderVideoImageInputs(list, node, imageInputs)` (~30-line DOM
 * renderer for the `video`-type generator card's media input list —
 * first/last frame role labels, preview rendering, drag/drop reorder
 * via `reorderInput`, audio/video/image preview shapes). All four
 * functions stay page-side helpers (page-owned per COMPAT/R8
 * semantics in docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but
 * are reachable only through this seam so the dispatcher and
 * seam-call shape is explicit.
 *
 * Page-side usage (canvas.js):
 *     const videoPP = ensureClassicVideoProviderParams();
 *     // videoProviderOptions / sanitizeVideoNodeProviderModel /
 *     // videoModelOptions / runVideoNode pre-flight:
 *     videoPP.videoApiProviders()
 *     videoPP.resolveVideoProviderId({id: 'comfly'})
 *     videoPP.providerVideoModels({providerId: 'comfly'})
 *     // syncGeneratorInputs video branch:
 *     videoPP.renderVideoImageInputs({list, node, imageInputs})
 *
 * R8 owns the real executor-driven video-node provider/params
 * rendering. R4-38 Wave 11 establishes the bounded compat boundary;
 * the function bodies stay page-side helpers (page-owned per
 * COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reachable
 * only through this seam so the dispatcher and seam-call shape is
 * explicit.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM
        'document',
        // i18n
        'tr',
        // Utility helpers
        'escapeHtml', 'mediaKindForRef',
        'canvasVideoPreviewHtml', 'canvasPreviewImgHtml',
        'isMissingAssetUrl', 'missingAssetHtml',
        // Page-state getters (apiProviders + videoModels + chatModels
        // + imageModels + DEFAULT_VIDEO_MODELS are page-locals; the
        // seam sees them only through host-injected getters)
        'getApiProviders', 'getInternalDrag', 'setInternalDrag',
        // Composition / pure helpers
        'uniqueModels', 'defaultApiProviders',
        // Lifecycle / drop handler
        'reorderInput', 'refreshIcons'
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicVideoProviderParams.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicVideoProviderParams.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var tr = host.tr;
        var escapeHtml = host.escapeHtml;
        var mediaKindForRef = host.mediaKindForRef;
        var canvasVideoPreviewHtml = host.canvasVideoPreviewHtml;
        var canvasPreviewImgHtml = host.canvasPreviewImgHtml;
        var isMissingAssetUrl = host.isMissingAssetUrl;
        var missingAssetHtml = host.missingAssetHtml;
        var getApiProviders = host.getApiProviders;
        var getInternalDrag = host.getInternalDrag;
        var setInternalDrag = host.setInternalDrag;
        var uniqueModels = host.uniqueModels;
        var defaultApiProviders = host.defaultApiProviders;
        var reorderInput = host.reorderInput;
        var refreshIcons = host.refreshIcons;

        function videoApiProviders() {
            var apiList = getApiProviders();
            var providers = (apiList && apiList.length ? apiList : defaultApiProviders())
                .filter(function (p) {
                    return p.id !== 'modelscope' && p.enabled !== false && (p.video_models || []).length;
                });
            return providers.length ? providers : defaultApiProviders();
        }

        function resolveVideoProviderId(id) {
            var providers = videoApiProviders();
            var found = providers.find(function (p) { return p.id === id; });
            return (found && found.id) || (providers[0] && providers[0].id) || 'comfly';
        }

        function providerVideoModels(providerId) {
            // 不走 providerById（会 fallback 到第一个 provider，造成串台），直接查精确匹配
            var provider = getApiProviders().find(function (p) { return p.id === providerId; });
            return uniqueModels((provider && provider.video_models) || []);
        }

        function renderVideoImageInputs(list, node, imageInputs) {
            if (!list) return;
            list.innerHTML = imageInputs.length ? '' : '<div class="text-[11px] text-gray-300 py-2">' + tr('canvas.groupEmpty') + '</div>';
            imageInputs.forEach(function (src, i) {
                var item = document.createElement('div');
                item.className = 'input-item video-input-item';
                item.draggable = true;
                item.dataset.sourceId = src.id;
                var kind = mediaKindForRef((src.refs && src.refs[0]) || { url: src.preview || '' });
                var frameLabel = kind === 'image' && node.useFrameRoles && i === 0
                    ? tr('canvas.videoRoleFirstFrame')
                    : kind === 'image' && node.useFrameRoles && i === 1
                        ? tr('canvas.videoRoleLastFrame')
                        : '';
                var previewHtml;
                if (kind === 'video') {
                    previewHtml = canvasVideoPreviewHtml(src.preview || (src.refs && src.refs[0] && src.refs[0].url) || '', 256);
                } else if (kind === 'audio') {
                    previewHtml = '<div class="video-input-audio"><i data-lucide="file-audio" class="w-6 h-6"></i><span>' + escapeHtml(src.label || 'Audio') + '</span></div>';
                } else if (src.preview && !isMissingAssetUrl(src.preview)) {
                    previewHtml = canvasPreviewImgHtml(src.preview, 256);
                } else if (src.preview) {
                    previewHtml = missingAssetHtml(src.preview, true);
                } else {
                    previewHtml = '<i data-lucide="image" class="w-6 h-6 text-slate-400"></i>';
                }
                var typeLabel = kind === 'audio'
                    ? ('音频' + (i + 1))
                    : kind === 'video'
                        ? ('视频' + (i + 1))
                        : ('图' + (i + 1));
                item.innerHTML = ''
                    + '<div class="video-input-thumb">'
                    +   '<span class="input-index">' + (i + 1) + '</span>'
                    +   previewHtml
                    +   '<span class="input-label">' + escapeHtml(typeLabel) + '</span>'
                    + '</div>'
                    + (frameLabel ? '<div class="video-frame-label">' + frameLabel + '</div>' : '');
                item.ondragstart = function (e) {
                    e.stopPropagation();
                    setInternalDrag(true);
                    if (e.dataTransfer) {
                        e.dataTransfer.effectAllowed = 'move';
                        e.dataTransfer.setData('application/x-canvas-input', src.id);
                    }
                };
                item.ondragend = function () { setInternalDrag(false); };
                item.ondragover = function (e) { e.preventDefault(); e.stopPropagation(); };
                item.ondrop = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var movedId = e.dataTransfer ? e.dataTransfer.getData('application/x-canvas-input') : '';
                    reorderInput(node, movedId, src.id);
                    setInternalDrag(false);
                };
                list.appendChild(item);
            });
            if (refreshIcons) refreshIcons();
        }

        return Object.freeze({
            videoApiProviders: function () { return videoApiProviders(); },
            resolveVideoProviderId: function (arg) { return resolveVideoProviderId(arg.id); },
            providerVideoModels: function (arg) { return providerVideoModels(arg.providerId); },
            renderVideoImageInputs: function (arg) {
                return renderVideoImageInputs(arg.list, arg.node, arg.imageInputs);
            }
        });
    }

    if (typeof window !== 'undefined') {
        window.WorkbenchCanvasClassicVideoProviderParams = Object.freeze({ create: create });
    }
})();