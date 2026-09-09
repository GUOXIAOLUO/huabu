/* Neutral output-media card renderer; page supplies preview/effect callbacks. */
(function exposeMediaOutputRenderer(global) {
    'use strict';
    function render(item, options = {}) {
        const presentation = options.presentation(item), url = presentation.url, safe = options.escapeAttr(url);
        const placement = presentation.placement, meta = item && typeof item === 'object' ? item : {};
        const gridStyle = placement ? ` style="grid-row:${placement.row + 1};grid-column:${placement.col + 1};aspect-ratio:${placement.w}/${placement.h}"` : '';
        const timePill = presentation.runMs && !meta.viewed ? `<span class="output-time-pill">${options.formatDuration(presentation.runMs)}</span>` : '';
        if (options.isMissing(url)) return `<div class="output-img-wrap" data-output-url="${safe}" data-missing-url="${safe}"${gridStyle}>${options.missingHtml(url, true)}${timePill}<button class="output-del" title="${options.tr('common.delete')}">×</button></div>`;
        if (presentation.kind === 'video') return `<div class="output-img-wrap" data-output-url="${safe}"${gridStyle}>${options.videoPreview(url, options.useGrid ? 512 : 768, 'alt="video output" data-video-fallback-attrs="controls data-output-video-fallback=&quot;1&quot;"')}${timePill}<button class="canvas-video-play output-video-play" type="button" title="播放"><i data-lucide="play"></i></button><div class="output-video-badge"><i data-lucide="play" class="w-3 h-3"></i>VIDEO</div><button class="output-del" title="${options.tr('common.delete')}">×</button></div>`;
        if (presentation.kind === 'audio') return `<div class="output-img-wrap output-audio-wrap" data-output-url="${safe}"${gridStyle}><div class="output-audio-card"><i data-lucide="file-audio" class="w-7 h-7"></i><span>${options.escapeHtml(presentation.name)}</span><audio src="${safe}" data-url="${safe}" controls preload="metadata"></audio></div>${timePill}<button class="output-del" title="${options.tr('common.delete')}">×</button></div>`;
        if (presentation.kind === 'text' || presentation.kind === 'file') { const icon = presentation.kind === 'text' ? 'file-text' : 'file', label = presentation.kind === 'text' ? 'TEXT' : 'FILE'; return `<div class="output-img-wrap output-file-wrap" data-output-url="${safe}"${gridStyle}><div class="output-file-card"><i data-lucide="${icon}" class="w-7 h-7"></i><span>${options.escapeHtml(presentation.name)}</span><small>${label}</small></div>${timePill}<button class="output-del" title="${options.tr('common.delete')}">×</button></div>`; }
        return `<div class="output-img-wrap" data-output-url="${safe}"${gridStyle}>${options.imagePreview(url, options.useGrid ? 512 : 768, 'alt="generated output"')}${timePill}<button class="output-del" title="${options.tr('common.delete')}">×</button></div>`;
    }
    function renderLite(item, options = {}) {
        const url = options.urlValue(item), kind = options.kind(item), label = options.escapeHtml(item?.name || options.label || 'Media');
        if (kind === 'image' && url) return options.imagePreview(url, 512, 'draggable="false"');
        if (kind === 'video' && url) return `<div class="minimax-lite-media is-video">${options.videoPreview(url, 512, 'draggable="false"')}<span>${label}</span></div>`;
        const icon = kind === 'audio' ? 'file-audio' : kind === 'video' ? 'film' : 'sparkles';
        return `<div class="minimax-lite-media is-${options.escapeAttr(kind || 'file')}"><i data-lucide="${icon}"></i><span>${label}</span></div>`;
    }
    global.WorkbenchCanvasMediaOutputRenderer = Object.freeze({render, renderLite});
}(window));
