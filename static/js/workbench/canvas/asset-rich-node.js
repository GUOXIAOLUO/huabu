/* Generic rich presentation for an existing asset-compatible NodeRecord.
   AssetVersion and Resource Library concerns intentionally stay out of R5. */
(function exposeWorkbenchAssetRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function mediaItems(node) {
        const source = node && typeof node === 'object' ? node : {};
        const legacy = source.extensions?.legacy?.payload;
        const candidates = [legacy?.url, legacy?.media, legacy?.images, legacy?.outputs, source.output_refs];
        const seen = new Set();
        return Object.freeze(candidates.flatMap(value => Array.isArray(value) ? value : value == null ? [] : [value]).map(item => {
            const value = typeof item === 'string' ? {url: item} : item || {};
            const url = text(value.url || value.src || value.preview_url);
            if (!url || seen.has(url)) return null;
            seen.add(url);
            return Object.freeze({url, name: text(value.name || value.title, 'Media'), kind: text(value.media_type || value.kind || value.type, 'image')});
        }).filter(Boolean));
    }

    function isCompatible(node) {
        return Boolean(node && typeof node === 'object' && (node.kind === 'asset' || mediaItems(node).length));
    }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!isCompatible(node)) throw new TypeError('AssetRichNode requires an asset-compatible NodeRecord');
        const presentation = settings.presentation || global.WorkbenchPresentationState?.create({
            initial: settings.presentationState,
            storage: settings.storage,
            storageKey: settings.storageKey || `workbench.asset.presentation:${text(node.id, 'unknown')}`,
            onChange: settings.onChange,
        });
        if (!presentation || typeof presentation.state !== 'function' || typeof presentation.transition !== 'function') {
            throw new Error('AssetRichNode requires WorkbenchPresentationState');
        }
        function snapshot() {
            return Object.freeze({
                nodeId: text(node.id), title: text(node.title, 'Asset'),
                presentation: presentation.state(), media: mediaItems(node),
                legacyCompatible: true,
            });
        }
        return Object.freeze({
            presentations: PRESENTATIONS,
            snapshot,
            state: presentation.state,
            canTransition: presentation.canTransition,
            transition: next => { presentation.transition(next); return snapshot(); },
        });
    }

    global.WorkbenchAssetRichNode = Object.freeze({PRESENTATIONS, isCompatible, mediaItems, create});
}(window));
