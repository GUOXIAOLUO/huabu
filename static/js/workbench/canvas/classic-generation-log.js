/*
 * static/js/workbench/canvas/classic-generation-log.js
 *
 * Wave 13 of R4-38 — bounded compat seam for the Classic generation
 * log panel. Two page-side functions move behind a shared seam:
 * `addGenerationLog` (~19-line log entry writer that prepends a new
 * `canvas.logs` entry capped at 500, plays the completion sound when
 * outputs are present, captures platform/nodeType/model/request/prompt/
 * outputs/refs/runMs/error metadata), and `renderCanvasLog` (~70-line
 * log list HTML renderer that emits `<div class="log-item">` rows
 * with status/platform/taskLabel/duration chips, subline (date +
 * outputs count + ID + backend), optional error line, prompt preview
 * with copy-on-click binding, and per-thumb lightbox click binding,
 * plus a refreshIcons() call). Both functions stay page-side helpers
 * (page-owned per COMPAT/R8 semantics in
 * docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but are reachable
 * only through this seam so the dispatcher and seam-call shape is
 * explicit.
 *
 * Page-side usage (canvas.js):
 *     const genLog = ensureClassicGenerationLog();
 *     // thin page-side wrapper preserves the 22 caller sites
 *     // (run*Node success/failure handlers, miniMax run, comfy run,
 *     // pending-output recovery, group run, etc.) — they continue
 *     // to call addGenerationLog({run, outputs, runMs, error}):
 *     function addGenerationLog(arg) {
 *         genLog.addGenerationLog(arg);
 *     }
 *     // openCanvasLog's render call:
 *     genLog.renderCanvasLog();
 *
 * R8 owns the real executor-driven generation-log rendering.
 * R4-38 Wave 13 establishes the bounded compat boundary; the
 * function bodies stay page-side helpers but are reachable only
 * through this seam.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM + i18n
        'document', 'tr',
        // Page-state (canvas.logs is mutated by addGenerationLog)
        'getCanvas',
        // Utility
        'escapeHtml', 'escapeAttr',
        'isMissingAssetUrl', 'mediaKindForOutputItem',
        'canvasVideoPreviewHtml', 'canvasPreviewImgHtml',
        // Log composition
        'runPlatformLabel', 'runTaskLabel', 'logTaskLabel',
        'formatRunDuration', 'langIsEn',
        // i18n window helper (used for date locale)
        'windowObj',
        // Output helpers (used by both addGenerationLog and renderCanvasLog)
        'outputUrlValue',
        // Audio + clipboard + icons
        'playGenerationCompleteSound', 'copyTextToClipboard', 'refreshIcons',
        // Lifecycle / log binding
        'bindCanvasPreviewImageFallbacks', 'openOutputLightbox',
        // UID factory
        'uid'
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicGenerationLog.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicGenerationLog.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var tr = host.tr;
        var getCanvas = host.getCanvas;
        var escapeHtml = host.escapeHtml;
        var escapeAttr = host.escapeAttr;
        var isMissingAssetUrl = host.isMissingAssetUrl;
        var mediaKindForOutputItem = host.mediaKindForOutputItem;
        var canvasVideoPreviewHtml = host.canvasVideoPreviewHtml;
        var canvasPreviewImgHtml = host.canvasPreviewImgHtml;
        var runPlatformLabel = host.runPlatformLabel;
        var runTaskLabel = host.runTaskLabel;
        var logTaskLabel = host.logTaskLabel;
        var formatRunDuration = host.formatRunDuration;
        var langIsEn = host.langIsEn;
        var windowObj = host.windowObj;
        var outputUrlValue = host.outputUrlValue;
        var playGenerationCompleteSound = host.playGenerationCompleteSound;
        var copyTextToClipboard = host.copyTextToClipboard;
        var refreshIcons = host.refreshIcons;
        var bindCanvasPreviewImageFallbacks = host.bindCanvasPreviewImageFallbacks;
        var openOutputLightbox = host.openOutputLightbox;
        var uid = host.uid;

        function addGenerationLog(arg) {
            var run = (arg && arg.run) || {};
            var outputs = (arg && arg.outputs) || [];
            var runMs = (arg && arg.runMs) || 0;
            var error = (arg && arg.error) || '';
            var canvas = getCanvas();
            if (!canvas) return;
            canvas.logs = canvas.logs || [];
            if (!error && (outputs || []).some(function (item) { return outputUrlValue(item); })) {
                playGenerationCompleteSound();
            }
            var entry = {
                id: uid('log'),
                createdAt: Date.now(),
                status: error ? 'failed' : 'success',
                platform: runPlatformLabel(run),
                nodeType: run.nodeType || '',
                model: run.taskLabel || runTaskLabel(run),
                request: run.request || {},
                prompt: run.prompt || '',
                outputs: (outputs || []).filter(Boolean),
                refs: run.refs || [],
                runMs: Number(runMs || 0),
                error: error ? String(error) : ''
            };
            canvas.logs = [entry].concat(canvas.logs).slice(0, 500);
        }

        function renderCanvasLog() {
            var list = document.getElementById('logList') || (typeof windowObj.logList !== 'undefined' ? windowObj.logList : null);
            var canvas = getCanvas();
            var logs = (canvas && Array.isArray(canvas.logs)) ? canvas.logs : [];
            if (!list) return;
            list.innerHTML = logs.length ? logs.map(function (log) {
                var thumbs = (log.outputs || []).slice(0, 8).map(function (item) {
                    var url = outputUrlValue(item);
                    if (!url) return '';
                    var safe = escapeAttr(url);
                    if (isMissingAssetUrl(url)) return '<div class="missing-asset compact" data-url="' + safe + '"><i data-lucide="image-off" class="w-4 h-4"></i></div>';
                    var kind = mediaKindForOutputItem(item);
                    return kind === 'video'
                        ? canvasVideoPreviewHtml(url, 256, 'alt="output"')
                        : canvasPreviewImgHtml(url, 256, 'alt="output"');
                }).join('');
                var date = new Date(log.createdAt || Date.now()).toLocaleString(
                    (windowObj.StudioI18n && windowObj.StudioI18n.lang && windowObj.StudioI18n.lang()) === 'en' ? 'en-US' : 'zh-CN'
                );
                var req = log.request || {};
                var taskId = req.task_id || req.taskId || req.prompt_id || req.promptId || '';
                var requestId = req.request_id || req.requestId || req.id || '';
                var backend = req.backend || req.provider_id || req.providerId || '';
                var workflow = req.workflow_json || req.workflow || '';
                var taskLabel = logTaskLabel(log);
                var idText = taskId || requestId || '';
                var backendText = workflow || backend || '';
                var subParts = [
                    date,
                    (langIsEn() ? 'outputs' : '输出') + ' ' + ((log.outputs || []).length),
                    idText ? 'ID ' + idText : '',
                    backendText
                ].filter(Boolean);
                var statusChip = log.status === 'failed' ? 'status-failed' : 'status-ok';
                var statusText = log.status === 'failed' ? tr('canvas.failed') : tr('canvas.success');
                return '<div class="log-item ' + (log.status === 'failed' ? 'failed' : '') + '">' +
                    '<div class="log-main">' +
                        '<div class="log-meta">' +
                            '<span class="log-chip ' + statusChip + '">' + escapeHtml(statusText) + '</span>' +
                            '<span class="log-chip">' + escapeHtml(log.platform || '-') + '</span>' +
                            (taskLabel ? '<span class="log-chip">' + escapeHtml(taskLabel) + '</span>' : '') +
                            '<span class="log-chip">' + escapeHtml(formatRunDuration(log.runMs || 0)) + '</span>' +
                        '</div>' +
                        '<div class="log-subline">' + subParts.map(function (part) {
                            return '<span title="' + escapeAttr(part) + '">' + escapeHtml(part) + '</span>';
                        }).join('') + '</div>' +
                        (log.error ? '<div class="log-error" title="' + escapeAttr(log.error) + '" data-error="' + escapeAttr(log.error) + '">' + escapeHtml(log.error) + '</div>' : '') +
                        '<div class="log-prompt" title="' + escapeAttr(log.prompt || tr('canvas.noPromptMeta')) + '" data-prompt="' + escapeAttr(log.prompt || '') + '">' + escapeHtml(log.prompt || tr('canvas.noPromptMeta')) + '</div>' +
                    '</div>' +
                    '<div class="log-thumbs">' + thumbs + '</div>' +
                '</div>';
            }).join('') : '<div class="log-empty">' + tr('canvas.noLogs') + '</div>';
            bindCanvasPreviewImageFallbacks(list);
            list.querySelectorAll('[data-url]').forEach(function (el) {
                el.onclick = function (e) {
                    e.stopPropagation();
                    openOutputLightbox(el.dataset.url, null);
                };
            });
            var bindCanvasLogCopy = function (selector, key) {
                list.querySelectorAll(selector).forEach(function (el) {
                    el.onclick = async function (e) {
                        e.stopPropagation();
                        var text = el.dataset[key] || '';
                        var copied = await copyTextToClipboard(text);
                        var oldText = el.textContent;
                        el.textContent = copied ? tr('canvas.copied') : tr('canvas.copyFailed');
                        if (copied) el.classList.add('copied');
                        setTimeout(function () {
                            el.textContent = oldText;
                            el.classList.remove('copied');
                        }, 900);
                    };
                });
            };
            bindCanvasLogCopy('[data-prompt]', 'prompt');
            bindCanvasLogCopy('[data-error]', 'error');
            refreshIcons();
        }

        return Object.freeze({
            addGenerationLog: function (arg) { return addGenerationLog(arg); },
            renderCanvasLog: function () { return renderCanvasLog(); }
        });
    }

    if (typeof window !== 'undefined') {
        window.WorkbenchCanvasClassicGenerationLog = Object.freeze({ create: create });
    }
})();