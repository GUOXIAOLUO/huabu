/* Neutral renderer for ordered media-input list entries. */
(function exposeMediaInputRenderer(global) {
    'use strict';
    function listState(media = {}) {
        const refs = Array.isArray(media.refs) ? media.refs.filter(Boolean) : [];
        return Object.freeze({refs, empty: refs.length === 0});
    }
    function itemMarkup(source, index, options = {}) {
        const escapeHtml = options.escapeHtml || (value => String(value ?? ''));
        const preview = options.preview || (() => '');
        const missing = options.missing || (() => '');
        const label = escapeHtml(source?.label || '');
        const previewHtml = source?.preview ? (options.isMissing?.(source.preview) ? missing(source.preview) : preview(source.preview)) : '<i data-lucide="image" class="w-6 h-6 text-slate-400"></i>';
        return `<span class="input-index">${index + 1}</span>${previewHtml}<span class="input-label">${label}</span>`;
    }
    function emptyMarkup(text, escapeHtml = value => String(value ?? '')) {
        return `<div class="text-[11px] text-gray-300 py-2">${escapeHtml(text || '')}</div>`;
    }
    global.WorkbenchCanvasMediaInputRenderer = Object.freeze({listState, itemMarkup, emptyMarkup});
}(window));
