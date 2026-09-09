/* Pure media-kind classification shared by temporary Canvas adapters. */
(function exposeCanvasMediaKind(global) {
    'use strict';

    const VIDEO = /\.(mp4|webm|mov|m4v|avi|mkv)(\?|#|$)/i;
    const VIDEO_WITH_FLV = /\.(mp4|webm|mov|m4v|avi|mkv|flv)(\?|#|$)/i;
    const AUDIO = /\.(mp3|wav|m4a|aac|ogg|flac)(\?|#|$)/i;
    const TEXT = /\.(txt|json|csv|srt|vtt|md)(\?|#|$)/i;
    const WORKFLOW = /\.(json|zip)(\?|#|$)/i;
    const IMAGE = /\.(png|jpe?g|webp|gif|bmp|avif|tiff?)(\?|#|$)/i;

    function explicitKind(value, options = {}) {
        const item = value && typeof value === 'object' ? value : {};
        const kind = String(item.kind || item.mediaKind || item.media_type || item.type || '').toLowerCase();
        const allowed = options.allowWorkflow
            ? ['image', 'video', 'audio', 'text', 'file', 'workflow']
            : ['image', 'video', 'audio', 'text', 'file'];
        return allowed.includes(kind) ? kind : '';
    }

    function kindForUrl(value, options = {}) {
        const fallback = options.fallback || 'image';
        const values = [value, options.name].map(item => String(item || '').toLowerCase());
        if (values.some(item => (options.includeFlv ? VIDEO_WITH_FLV : VIDEO).test(item))) return 'video';
        if (values.some(item => AUDIO.test(item))) return 'audio';
        if (options.allowText !== false && values.some(item => TEXT.test(item))) return 'text';
        if (options.allowWorkflow && values.some(item => WORKFLOW.test(item))) return 'workflow';
        return fallback;
    }

    function kindForItem(value, options = {}) {
        const explicit = explicitKind(value, options);
        if (explicit) return explicit;
        const item = value && typeof value === 'object' ? value : {url: value};
        const url = typeof options.originalUrl === 'function' ? options.originalUrl(item) : item.url || item.thumbnail || '';
        return kindForUrl(url, {...options, name: options.name || item.name || ''});
    }

    function kindForNode(node, options = {}) {
        if (!node) return options.fallback || 'image';
        return kindForItem({mediaKind: node.mediaKind, url: node.url, name: node.name}, options);
    }

    function kindForFile(file, options = {}) {
        const type = String(file?.type || '').toLowerCase();
        if (type.startsWith('video/')) return 'video';
        if (type.startsWith('audio/')) return 'audio';
        if (options.allowText !== false && type.startsWith('text/')) return 'text';
        return kindForUrl(file?.name || '', options);
    }

    function isKindForUrl(value, expected, options = {}) {
        return kindForUrl(value, options) === expected;
    }

    global.WorkbenchCanvasMediaKind = Object.freeze({
        kindForUrl,
        kindForItem,
        kindForNode,
        kindForFile,
        isKindForUrl,
        isImageUrl: value => IMAGE.test(String(value || '').toLowerCase()),
    });
}(window));
