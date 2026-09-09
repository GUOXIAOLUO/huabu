/* Neutral loop-prompt projection. Input collection remains page-owned. */
(function exposeLoopPromptRenderer(global) {
    'use strict';
    function render(options = {}) {
        if (!options.showPrompt) return '';
        const index = Math.max(1, Number(options.index) || 1);
        const total = Math.max(1, Number(options.total) || 1);
        const tokens = options.tokens || {};
        const replace = text => String(text || '')
            .replaceAll('《计数》', String(index)).replaceAll('《总数》', String(total)).replaceAll('《进度》', `${index}/${total}`)
            .replaceAll(`[${tokens.counter || '计数'}]`, String(index)).replaceAll(`[${tokens.total || '总数'}]`, String(total)).replaceAll(`[${tokens.progress || '进度'}]`, `${index}/${total}`);
        return replace(options.selected || options.variable || '');
    }
    function tokenChip(token, options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const a = options.escapeAttr || e;
        return `<span class="loop-token-chip" contenteditable="false" data-token="${a(token)}"><span>${e(options.label || token)}</span><button type="button" aria-label="${e(options.deleteLabel || '删除')}" title="${e(options.deleteLabel || '删除')}">×</button></span>`;
    }
    function variableMarkup(text, options = {}) {
        const token = options.token || '《计数》';
        const e = options.escapeHtml || (value => String(value ?? ''));
        const chip = options.tokenChip || (value => tokenChip(value, options));
        return String(text || '').split(token).map((part, index) => `${index ? chip(token) : ''}${e(part)}`).join('');
    }
    function tokenLabel(token, labels = {}) {
        return labels[token] || token;
    }
    function count(value) { return Math.max(1, Math.min(100, Number(value || 1) || 1)); }
    function contextProjection(node = {}, ctx = {}, countValue) {
        const rounds = typeof countValue === 'function' ? countValue(node.count) : count(node.count);
        return Object.freeze({variable:String(node.variablePrompt || '').trim(), count:rounds, index:Math.max(1, Number(ctx.index || 1) || 1), total:Math.max(1, Number(ctx.total || rounds) || rounds)});
    }
    function editorText(editor) {
        const walk = node => {
            if (!node) return '';
            if (node.nodeType === 3) return node.nodeValue || '';
            if (node.nodeType !== 1) return '';
            if (node.classList?.contains('loop-token-chip')) return node.dataset?.token || '';
            if (node.tagName === 'BR') return '\n';
            return [...(node.childNodes || [])].map(walk).join('');
        };
        return [...(editor?.childNodes || [])].map(walk).join('').replace(/\u00a0/g, ' ');
    }
    function splitItems(text) {
        const trimmed = String(text || '').trim();
        if (!trimmed) return [];
        const numbered = trimmed.split(/\s*(?:^|\s)\d+\s*[.、)）．]\s+/).map(s => s.trim()).filter(Boolean);
        if (numbered.length >= 2) return numbered;
        const lines = trimmed.split(/\r?\n+/).map(s => s.trim()).filter(Boolean);
        return lines.length >= 2 ? lines : [trimmed];
    }
    function textLength(text) { return Array.from(String(text || '')).length; }
    function counterMarkup(text, maxLength, locale = undefined) {
        const countValue = textLength(text);
        const over = countValue > maxLength;
        const format = value => Number(value).toLocaleString(locale);
        return {count:countValue, over, markup:`<div class="prompt-counter ${over ? 'over' : ''}"><span>${format(countValue)}</span><span>/ ${format(maxLength)}</span></div>`};
    }
    function insertToken(editor, token, options = {}) {
        if (!editor) return false;
        const documentRef = options.document || global.document;
        if (!documentRef) return false;
        editor.focus?.();
        const chipWrap = documentRef.createElement('span');
        chipWrap.innerHTML = options.chipMarkup || tokenChip(token, options);
        const chip = chipWrap.firstElementChild;
        const spacer = documentRef.createTextNode(' ');
        const selection = options.selection || global.getSelection?.();
        if (selection && selection.rangeCount && editor.contains?.(selection.anchorNode)) {
            const range = selection.getRangeAt(0);
            range.deleteContents();
            range.insertNode(spacer);
            range.insertNode(chip);
            range.setStartAfter(spacer);
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
        } else {
            editor.appendChild(chip);
            editor.appendChild(spacer);
        }
        return true;
    }
    global.WorkbenchCanvasLoopPromptRenderer = Object.freeze({render, contextProjection, editorText, tokenChip, variableMarkup, tokenLabel, count, splitItems, textLength, counterMarkup, insertToken});
}(window));
