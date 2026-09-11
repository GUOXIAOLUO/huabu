/* Generic Collection Rich Node. Collection data stays a resource projection;
   this module owns only gallery presentation, selection, and open intents. */
(function exposeWorkbenchCollectionRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);
    const REFERENCE_TYPES = new Set(['asset_version', 'artifact_version']);
    const VISUAL_TYPES = new Set(['image', 'video']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function collectionOf(node) {
        const source = node && typeof node === 'object' ? node : {};
        return source.collection || source.config?.collection || source.extensions?.collection?.payload
            || source.extensions?.legacy?.payload?.collection || null;
    }

    function isCompatible(node) {
        const collection = collectionOf(node);
        return Boolean(node && typeof node === 'object' && (node.kind === 'collection' || node.type === 'collection')
            && collection && typeof collection === 'object');
    }

    function visualItems(node, resolveReference) {
        const collection = collectionOf(node);
        if (!collection || !Array.isArray(collection.items)) return Object.freeze([]);
        const columns = new Map((collection.schema?.columns || []).map(column => [column.key, column]));
        const resolve = typeof resolveReference === 'function' ? resolveReference : () => null;
        const result = [];
        [...collection.items].sort((left, right) => Number(left.order || 0) - Number(right.order || 0)).forEach(item => {
            Object.keys(item.values || {}).sort((left, right) => (columns.get(left)?.key || left).localeCompare(columns.get(right)?.key || right)).forEach(columnKey => {
                const cell = item.values[columnKey];
                if (cell?.type !== 'reference' || !REFERENCE_TYPES.has(text(cell.reference_type))) return;
                const resolved = resolve(cell.reference_type, cell.reference_id, item, columnKey);
                const media = typeof resolved === 'string' ? {url: resolved} : resolved;
                const url = text(media?.url || media?.src || media?.preview_url);
                if (!url) return;
                const kind = text(media?.kind || media?.mediaKind || media?.media_type || media?.type, 'image').toLowerCase();
                if (!VISUAL_TYPES.has(kind)) return;
                result.push(Object.freeze({
                    itemId: text(item.id), columnKey, referenceType: cell.reference_type,
                    referenceId: text(cell.reference_id), url, kind,
                    label: text(media?.name || media?.title || columns.get(columnKey)?.label, 'Media'),
                }));
            });
        });
        return Object.freeze(result);
    }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!isCompatible(node)) throw new TypeError('CollectionRichNode requires a collection NodeRecord');
        const presentation = settings.presentation || global.WorkbenchPresentationState?.create({
            initial: settings.presentationState,
            storage: settings.storage,
            storageKey: settings.storageKey || `workbench.collection.presentation:${text(node.id, 'unknown')}`,
            onChange: settings.onChange,
        });
        if (!presentation || typeof presentation.state !== 'function' || typeof presentation.transition !== 'function') {
            throw new Error('CollectionRichNode requires WorkbenchPresentationState');
        }
        let selectedItemId = text(settings.selectedItemId);
        const items = () => visualItems(node, settings.resolveReference);
        const selectable = itemId => items().some(item => item.itemId === text(itemId));
        function select(itemId) {
            const id = text(itemId);
            if (!selectable(id)) return snapshot();
            selectedItemId = id;
            settings.onSelect?.(items().find(item => item.itemId === id));
            return snapshot();
        }
        function open(itemId) {
            const id = text(itemId);
            const item = items().find(candidate => candidate.itemId === id);
            if (item) settings.onOpen?.(item);
            return item || null;
        }
        function snapshot() {
            return Object.freeze({nodeId: text(node.id), title: text(node.title, 'Collection'), presentation: presentation.state(), items: items(), selectedItemId});
        }
        return Object.freeze({
            presentations: PRESENTATIONS, snapshot, state: presentation.state,
            canTransition: presentation.canTransition,
            transition: next => { presentation.transition(next); return snapshot(); },
            select, open,
        });
    }

    function mount(shell, node, options) {
        if (!shell?.contentHost) throw new TypeError('CollectionRichNode requires a shell content host');
        const settings = options || {};
        const rich = settings.richNode || create({node, ...settings, presentation: settings.presentation || shell.collectionRichNode?.presentation});
        const documentRef = settings.document || shell.contentHost.ownerDocument || global.document;
        const root = documentRef.createElement('div');
        root.className = 'workbench-collection-gallery';
        const render = () => {
            root.replaceChildren();
            rich.snapshot().items.forEach(item => {
                const tile = documentRef.createElement('button');
                tile.type = 'button';
                tile.className = `workbench-collection-gallery__item${item.itemId === rich.snapshot().selectedItemId ? ' is-selected' : ''}`;
                tile.dataset.itemId = item.itemId;
                tile.setAttribute('aria-label', item.label);
                const media = documentRef.createElement(item.kind === 'video' ? 'video' : 'img');
                media.className = 'workbench-collection-gallery__media';
                media.src = item.url;
                media.alt = item.label;
                if (item.kind === 'video') { media.controls = true; media.preload = 'metadata'; media.playsInline = true; }
                tile.append(media);
                tile.addEventListener('click', event => { event.stopPropagation(); rich.select(item.itemId); render(); });
                tile.addEventListener('dblclick', event => { event.stopPropagation(); rich.open(item.itemId); });
                tile.addEventListener('keydown', event => { if (event.key === 'Enter') rich.open(item.itemId); });
                root.append(tile);
            });
        };
        render();
        shell.contentHost.replaceChildren(root);
        return Object.freeze({element: root, richNode: rich, destroy: () => root.remove()});
    }

    const descriptor = {
        id: 'collection-gallery', version: '1', priority: 120,
        canRender: isCompatible,
        mount,
    };
    global.WorkbenchCollectionRichNode = Object.freeze({PRESENTATIONS, collectionOf, isCompatible, visualItems, create, mount});
    if (global.WorkbenchNodeCardHost?.registry) global.WorkbenchNodeCardHost.registry.register(descriptor);
}(window));
