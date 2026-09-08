/*
 * static/js/workbench/canvas/classic-output-grid.js
 *
 * Wave 12 of R4-38 — bounded compat seam for the Classic output-node
 * grid renderer. Three page-side functions move behind a shared seam:
 * `bindOutputWrap` (~95-line per-item interaction binder that wires
 * up drag/drop previews, lightbox open, video play, download click,
 * delete click, recover-query click for the output-node grid item
 * wraps — `output-img-wrap`), `refreshOutputNodeContent` (~53-line
 * incremental grid refresh that diffs `node.images` + `node._pending`
 * against the existing DOM grid and adds/removes/replaces children,
 * then re-binds `output-img-wrap` items), and `renderOutputGrid` (5-line
 * full grid HTML builder that emits `<div class="output-grid">` with
 * the grid-layout style when `outputGridLayout(node)` returns a
 * layout). All three stay page-side helpers (page-owned per
 * COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reachable
 * only through this seam so the dispatcher and seam-call shape is
 * explicit.
 *
 * Page-side usage (canvas.js):
 *     const outputGrid = ensureClassicOutputGrid();
 *     // refreshNodes output-node fast path:
 *     if(node.type === 'output' && outputGrid.refreshOutputNodeContent({node})) continue;
 *     // body dispatcher's 'output' branch:
 *     body.innerHTML = outputGrid.renderOutputGrid({node, pendingHtml});
 *     body.querySelectorAll('.output-img-wrap').forEach(wrap =>
 *         outputGrid.bindOutputWrap({wrap, node}));
 *
 * R8 owns the real executor-driven output-node grid rendering.
 * R4-38 Wave 12 establishes the bounded compat boundary; the
 * function bodies stay page-side helpers but are reachable only
 * through this seam.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM
        'document', 'nodesEl',
        // Per-item helpers
        'setOutputDragPreview', 'openOutputLightbox',
        'downloadUrl', 'outputDownloadName',
        'canvasActivateVideoPreview', 'queryRecoverPendingOutput',
        'outputUrlValue',
        // Grid-level helpers
        'outputGridLayout', 'outputDomKeyForItem',
        'outputDomKeyForPending',
        'renderOutputMedia', 'renderPendingOutput',
        'bindCanvasPreviewImageFallbacks',
        'syncCanvasSelectedImageResolution', 'refreshOutputTimer',
        // Lifecycle
        'scheduleSave', 'refreshNodes'
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicOutputGrid.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicOutputGrid.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var nodesEl = host.nodesEl;
        var setOutputDragPreview = host.setOutputDragPreview;
        var openOutputLightbox = host.openOutputLightbox;
        var downloadUrl = host.downloadUrl;
        var outputDownloadName = host.outputDownloadName;
        var canvasActivateVideoPreview = host.canvasActivateVideoPreview;
        var queryRecoverPendingOutput = host.queryRecoverPendingOutput;
        var outputUrlValue = host.outputUrlValue;
        var outputGridLayout = host.outputGridLayout;
        var outputDomKeyForItem = host.outputDomKeyForItem;
        var outputDomKeyForPending = host.outputDomKeyForPending;
        var renderOutputMedia = host.renderOutputMedia;
        var renderPendingOutput = host.renderPendingOutput;
        var bindCanvasPreviewImageFallbacks = host.bindCanvasPreviewImageFallbacks;
        var syncCanvasSelectedImageResolution = host.syncCanvasSelectedImageResolution;
        var refreshOutputTimer = host.refreshOutputTimer;
        var scheduleSave = host.scheduleSave;
        var refreshNodes = host.refreshNodes;

        function bindOutputWrap(wrap, node) {
            var img = wrap.querySelector('img');
            var video = wrap.querySelector('video');
            var audio = wrap.querySelector('audio');
            var fileCard = wrap.querySelector('.output-file-card');
            var playBtn = wrap.querySelector('.canvas-video-play');
            var del = wrap.querySelector('.output-del');
            var recoverQuery = wrap.querySelector('.output-recover-query');
            var outputDragUrl = function () {
                return (img && img.dataset.url) ||
                    (video && video.dataset.url) ||
                    (audio && audio.dataset.url) ||
                    wrap.dataset.outputUrl ||
                    '';
            };
            wrap.draggable = Boolean(outputDragUrl());
            wrap.ondragstart = function (e) {
                var url = outputDragUrl();
                if (!url || e.target.closest('button,audio,video')) return;
                e.stopPropagation();
                wrap.dataset.dragging = '1';
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('application/x-canvas-output-image', url);
                e.dataTransfer.setData('text/uri-list', url);
                e.dataTransfer.setData('text/plain', url);
                if (img) setOutputDragPreview(e, img);
            };
            wrap.ondragend = function () {
                setTimeout(function () { delete wrap.dataset.dragging; }, 0);
            };
            if (img) {
                img.draggable = true;
                img.ondragstart = function (e) {
                    e.stopPropagation();
                    img.dataset.dragging = '1';
                    setOutputDragPreview(e, img);
                    e.dataTransfer.effectAllowed = 'copy';
                    e.dataTransfer.setData('application/x-canvas-output-image', img.dataset.url);
                    e.dataTransfer.setData('text/uri-list', img.dataset.url);
                };
                img.ondragend = function () {
                    setTimeout(function () { delete img.dataset.dragging; }, 0);
                };
                img.onclick = function (e) {
                    e.stopPropagation();
                    if (img.dataset.dragging || wrap.dataset.dragging) return;
                    openOutputLightbox(img.dataset.url, node);
                };
            }
            wrap.addEventListener('click', function (e) {
                var fallbackVideo = e.target.closest && e.target.closest('video[data-output-video-fallback]');
                if (!fallbackVideo || !wrap.contains(fallbackVideo)) return;
                e.stopPropagation();
                openOutputLightbox(fallbackVideo.dataset.url, node);
            });
            if (video) {
                video.onclick = function (e) {
                    e.stopPropagation();
                    openOutputLightbox(video.dataset.url, node);
                };
            }
            if (fileCard) {
                fileCard.onclick = function (e) {
                    e.stopPropagation();
                    var url = wrap.dataset.outputUrl;
                    if (url) downloadUrl(url, outputDownloadName(url)).catch(function (err) { alert(err.message || '下载失败'); });
                };
            }
            if (del) {
                del.onmousedown = function (e) { e.stopPropagation(); };
                del.onclick = function (e) {
                    e.stopPropagation();
                    var pid = wrap.dataset.pendingId;
                    if (pid) {
                        node._pending = (node._pending || []).filter(function (p) { return p.id !== pid; });
                    } else {
                        var url = (img && img.dataset.url) ||
                            (video && video.dataset.url) ||
                            (audio && audio.dataset.url) ||
                            wrap.dataset.outputUrl ||
                            wrap.dataset.missingUrl ||
                            '';
                        node.images = (node.images || []).filter(function (item) { return outputUrlValue(item) !== url; });
                        if (node.imageComparisons) delete node.imageComparisons[url];
                        scheduleSave();
                    }
                    refreshNodes([node.id]);
                };
            }
            if (playBtn && img) {
                playBtn.onmousedown = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                };
                playBtn.onclick = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    canvasActivateVideoPreview(wrap);
                };
            }
            if (recoverQuery) {
                recoverQuery.onmousedown = function (e) { e.stopPropagation(); };
                recoverQuery.onclick = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var pid = wrap.dataset.pendingId;
                    if (pid) queryRecoverPendingOutput(pid);
                };
            }
        }

        function renderOutputGrid(node, pendingHtml) {
            if (pendingHtml === undefined || pendingHtml === null) pendingHtml = '';
            var layout = outputGridLayout(node);
            var gridClass = layout ? 'output-grid grid-layout' : 'output-grid';
            var style = layout ? ' style="--grid-cols:' + Math.max(1, Number(layout.cols || 1)) + '"' : '';
            return '<div class="' + gridClass + '"' + style + '>' +
                (node.images || []).map(function (item) { return renderOutputMedia(item, !!layout); }).join('') +
                pendingHtml +
                '</div>';
        }

        function refreshOutputNodeContent(node) {
            var el = nodesEl.querySelector('.output-node[data-id="' + (typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(node.id) : node.id) + '"]');
            var body = el && el.querySelector('.node-body');
            var grid = body && body.querySelector('.output-grid');
            if (!body || !grid) return false;
            body.onwheel = function (e) { e.stopPropagation(); };
            var layout = outputGridLayout(node);
            grid.classList.toggle('grid-layout', !!layout);
            if (layout) grid.style.setProperty('--grid-cols', String(Math.max(1, Number(layout.cols || 1))));
            else grid.style.removeProperty('--grid-cols');
            var items = []
                .concat((node.images || []).map(function (item) {
                    return { key: outputDomKeyForItem(item), html: renderOutputMedia(item, !!layout) };
                }))
                .concat((node._pending || []).map(function (p) {
                    return { key: outputDomKeyForPending(p), html: renderPendingOutput(p) };
                }));
            var wanted = new Set(items.map(function (item) { return item.key; }));
            var existing = Array.prototype.slice.call(grid.children);
            existing.forEach(function (child) {
                var key = child.dataset.pendingId
                    ? outputDomKeyForPending({ id: child.dataset.pendingId })
                    : 'url:' + (child.dataset.outputUrl || child.dataset.missingUrl ||
                        (child.querySelector('img,video,audio') && child.querySelector('img,video,audio').dataset.url) || '');
                if (!wanted.has(key)) child.remove();
                else child.dataset.outputKey = key;
            });
            items.forEach(function (item) {
                var child = Array.prototype.slice.call(grid.children).find(function (el) { return el.dataset.outputKey === item.key; });
                if (!child) {
                    grid.insertAdjacentHTML('beforeend', item.html);
                    child = grid.lastElementChild;
                    child.dataset.outputKey = item.key;
                    child.dataset.outputHtml = item.html;
                    bindOutputWrap(child, node);
                } else if (item.key.indexOf('pending:') === 0 && child.dataset.outputHtml !== item.html) {
                    var tpl = document.createElement('template');
                    tpl.innerHTML = item.html.trim();
                    var fresh = tpl.content.firstElementChild;
                    if (fresh) {
                        fresh.dataset.outputKey = item.key;
                        fresh.dataset.outputHtml = item.html;
                        child.replaceWith(fresh);
                        child = fresh;
                        bindOutputWrap(child, node);
                    }
                }
                grid.appendChild(child);
            });
            bindCanvasPreviewImageFallbacks(grid);
            syncCanvasSelectedImageResolution(el);
            refreshOutputTimer();
            return true;
        }

        return Object.freeze({
            renderOutputGrid: function (arg) { return renderOutputGrid(arg.node, arg.pendingHtml); },
            bindOutputWrap: function (arg) { return bindOutputWrap(arg.wrap, arg.node); },
            refreshOutputNodeContent: function (arg) { return refreshOutputNodeContent(arg.node); }
        });
    }

    if (typeof window !== 'undefined') {
        window.WorkbenchCanvasClassicOutputGrid = Object.freeze({ create: create });
    }
})();