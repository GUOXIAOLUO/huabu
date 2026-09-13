/* Canvas-side projection for Collection gallery references.
 * Resource resolution stays injected or comes from a persisted reference
 * snapshot; this adapter does not own Collection persistence. */
(function exposeWorkbenchCollectionGalleryCanvasAdapter(global) {
    'use strict';

    const VISUAL_TYPES = new Set(['image', 'video']);

    function text(value) {
        return String(value ?? '').trim();
    }

    function collectionOf(node) {
        return node?.collection || node?.config?.collection || node?.extensions?.collection?.payload
            || node?.extensions?.legacy?.payload?.collection || null;
    }

    function referenceKey(type, id) {
        return `${text(type)}:${text(id)}`;
    }

    function sourceFor(nodes, referenceId) {
        const id = text(referenceId);
        return nodes.find(node => node?.id === id
            || (Array.isArray(node?.output_refs) && node.output_refs.some(reference => text(reference?.id) === id))) || null;
    }

    function resolveFromSnapshot(node, type, id) {
        const metadata = collectionOf(node)?.metadata;
        const snapshot = metadata?.resolved_references;
        if (!snapshot || typeof snapshot !== 'object') return null;
        return snapshot[referenceKey(type, id)] || snapshot[text(id)] || null;
    }

    function create(options) {
        const settings = options || {};
        const viewStorage = settings.storage || (() => {
            try { return global.localStorage || null; } catch (error) { return null; }
        })();
        const getNodes = typeof settings.getNodes === 'function' ? settings.getNodes : () => [];
        const externalResolve = typeof settings.resolveReference === 'function' ? settings.resolveReference : null;
        const outputUrlValue = typeof settings.outputUrlValue === 'function' ? settings.outputUrlValue : value => typeof value === 'string' ? value : value?.url || value?.src || '';
        const mediaKindForNode = typeof settings.mediaKindForNode === 'function' ? settings.mediaKindForNode : () => 'image';
        const mediaKindForOutputItem = typeof settings.mediaKindForOutputItem === 'function' ? settings.mediaKindForOutputItem : item => item?.kind || item?.type || 'image';
        const outputImageName = typeof settings.outputImageName === 'function' ? settings.outputImageName : url => text(url).split('/').pop();
        const openOutputLightbox = typeof settings.openOutputLightbox === 'function' ? settings.openOutputLightbox : () => {};
        const onSelect = typeof settings.onSelect === 'function' ? settings.onSelect : () => {};
        const onOpen = typeof settings.onOpen === 'function' ? settings.onOpen : () => {};
        const workspaceSession = settings.workspaceSession || null;
        const persistCollection = typeof settings.persistCollection === 'function' ? settings.persistCollection : null;
        const onWorkspaceChange = typeof settings.onWorkspaceChange === 'function' ? settings.onWorkspaceChange : null;
        const selectedItems = new Map();
        const workspaceOpeners = new Map();

        function resolve(node, referenceType, referenceId) {
            const id = text(referenceId);
            if (!id) return null;
            let media = externalResolve?.(referenceType, id, node) || resolveFromSnapshot(node, referenceType, id);
            const nodes = Array.isArray(getNodes()) ? getNodes() : [];
            const source = sourceFor(nodes, id);
            if (!media && source) {
                const direct = (source.output_refs || []).find(reference => text(reference?.id) === id
                    && (!reference?.type || reference.type === referenceType));
                const candidates = [direct, ...(source.generatedOutputs || []), ...(source.images || []), ...(source.outputs || [])].filter(Boolean);
                media = candidates.find(candidate => typeof candidate === 'string' ? candidate === id : [candidate.id, candidate.asset_id, candidate.artifact_id, candidate.version_id].some(value => text(value) === id));
                if ((!media || !outputUrlValue(media)) && source.url) media = {url:source.url, kind:mediaKindForNode(source), name:source.name || source.title};
                if (!media && candidates.length === 1) media = candidates[0];
            }
            const url = text(outputUrlValue(media));
            const kind = text(media?.kind || media?.mediaKind || media?.media_type || media?.type || (media ? mediaKindForOutputItem(media) : '')) || 'image';
            if (!url || !VISUAL_TYPES.has(kind.toLowerCase())) return null;
            return {url, kind:kind.toLowerCase(), name:text(media?.name || media?.title || outputImageName(url))};
        }

        function optionsFor(node) {
            const nodeId = text(node?.id);
            return {
                selectedItemId:selectedItems.get(node?.id) || '',
                storage:viewStorage,
                viewStorageKey:`workbench.collection.view:${text(node?.id) || 'unknown'}`,
                resolveReference:(type, id) => resolve(node, type, id),
                onSelect:item => { selectedItems.set(node?.id, item.itemId); onSelect(item); },
                onOpen:item => { openOutputLightbox(item.url, sourceFor(Array.isArray(getNodes()) ? getNodes() : [], item.referenceId)); onOpen(item); },
                workspaceSession,
                persistCollection,
                onWorkspaceChange,
                registerWorkspaceOpen:opener => {
                    if (nodeId && typeof opener === 'function') workspaceOpeners.set(nodeId, opener);
                },
            };
        }

        function openWorkspace(nodeId) {
            const opener = workspaceOpeners.get(text(nodeId));
            return typeof opener === 'function' ? Boolean(opener()) : false;
        }

        return Object.freeze({resolve, optionsFor, openWorkspace});
    }

    global.WorkbenchCollectionGalleryCanvasAdapter = Object.freeze({create});
}(window));
