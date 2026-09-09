/* Neutral node display projections used by the Canvas compatibility renderer. */
(function exposeNodePresentation(global) {
    'use strict';
    function title(node, translate = key => key) {
        const type = node?.type;
        if (type === 'image') return node.title || 'Image';
        const labels = {
            prompt: 'Prompt', loop: 'canvas.loopNode', promptGroup: 'Prompts', group: 'Group', output: 'Output',
            llm: 'LLM', comfy: 'ComfyUI', ltxDirector: 'canvas.ltxDirector', rh: 'RunningHub', minimax: 'MiniMax H3',
            midjourney: 'Midjourney', msgen: 'canvas.modelscopeGenerate', video: 'canvas.videoGenerateNode',
        };
        return labels[type] ? (labels[type].startsWith('canvas.') ? translate(labels[type]) : labels[type]) : translate('canvas.apiGenerate');
    }
    function statusLabel(status, labels = {}) {
        return labels[status] || ({queued: '排队中', running: '运行中', done: '完成', failed: '失败'}[status] || '');
    }
    function shouldShowStatus(node) {
        const types = ['generator', 'midjourney', 'msgen', 'comfy', 'ltxDirector', 'llm', 'video', 'rh', 'minimax'];
        return Boolean(node?.runStatus && types.includes(node.type) && (node.runStatus !== 'failed' || node._cascadeFailed));
    }
    function statusMarkup(node, escapeHtml = value => value) {
        if (!shouldShowStatus(node)) return '';
        const label = statusLabel(node.runStatus);
        const suffix = node._cascadeIdx ? ` ${node._cascadeIdx}` : '';
        return `<span class="node-run-status ${node.runStatus}"><span class="dot"></span>${escapeHtml(label)}${suffix}</span>`;
    }
    function displayTitle(node, baseTitle, mediaTitle = '') {
        return node?.type === 'image' && node?.url ? (mediaTitle || baseTitle) : baseTitle;
    }
    function mediaTitle(kind) {
        if (kind === 'video') return 'Video';
        if (kind === 'audio') return 'Audio';
        return 'Image';
    }
    function defaultSize(type) {
        const sizes = {
            image: [260, 336], prompt: [310, 0], loop: [336, 0], llm: [420, 590], generator: [380, 0],
            midjourney: [380, 0], msgen: [380, 0], video: [400, 0], minimax: [980, 720], rh: [430, 0],
            comfy: [420, 460], ltxDirector: [1000, 800], output: [460, 0],
        };
        const [w, h] = sizes[type] || [260, 0];
        return {w, h};
    }
    function isFixedSize(node, size) {
        return Boolean(node?.h || size?.h);
    }
    function dimensions(node, size) {
        return {width: Number(node?.w || size?.w || 0), height: Number(node?.h || size?.h || 0)};
    }
    function position(node) {
        return {left: Number(node?.x) || 0, top: Number(node?.y) || 0};
    }
    function className(node, selected = false, sized = false) {
        return `node ${node?.type || ''}-node ${node?.url ? 'has-image' : ''} ${sized ? 'sized' : ''} ${selected ? 'selected' : ''}`;
    }
    global.WorkbenchCanvasNodePresentation = Object.freeze({title, statusLabel, shouldShowStatus, statusMarkup, displayTitle, mediaTitle, defaultSize, isFixedSize, dimensions, position, className});
}(window));
