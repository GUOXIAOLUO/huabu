/* Generic Collection Rich Node. Collection data stays a resource projection;
   this module owns only gallery presentation, selection, and open intents. */
(function exposeWorkbenchCollectionRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);
    const VIEW_MODES = Object.freeze(['grid', 'list']);
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

    function normalizeViewMode(value) { return VIEW_MODES.includes(value) ? value : 'grid'; }

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
                const resolved = resolve(cell.reference_type, cell.reference_id, item, columnKey) || cell.metadata;
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
        const viewStorage = settings.storage && typeof settings.storage.getItem === 'function' && typeof settings.storage.setItem === 'function' ? settings.storage : null;
        const viewStorageKey = settings.viewStorageKey || `workbench.collection.view:${text(node.id, 'unknown')}`;
        let viewMode = normalizeViewMode(viewStorage?.getItem(viewStorageKey) || settings.viewMode);
        const items = visualItems(node, settings.resolveReference);
        const tableWorkspace = global.WorkbenchCollectionTableWorkspace?.isCompatible(node)
            ? global.WorkbenchCollectionTableWorkspace.create({
                node, session: settings.workspaceSession, persist: settings.persistCollection,
                onChange: settings.onWorkspaceChange,
            }) : null;
        if (!items.some(item => item.itemId === selectedItemId)) selectedItemId = '';
        function select(itemId) {
            const id = text(itemId);
            const item = items.find(candidate => candidate.itemId === id);
            if (!item) return snapshot();
            selectedItemId = id;
            settings.onSelect?.(item);
            return snapshot();
        }
        function open(itemId) {
            const id = text(itemId);
            const item = items.find(candidate => candidate.itemId === id);
            if (item) settings.onOpen?.(item);
            return item || null;
        }
        function setViewMode(next) {
            const mode = normalizeViewMode(next);
            if (!VIEW_MODES.includes(next)) throw new RangeError(`unknown collection view mode: ${next}`);
            viewMode = mode;
            if (viewStorage) viewStorage.setItem(viewStorageKey, viewMode);
            settings.onViewChange?.(viewMode);
            return snapshot();
        }
        function snapshot() {
            return Object.freeze({nodeId: text(node.id), title: text(node.title, 'Collection'), presentation: presentation.state(), viewMode, items, selectedItemId});
        }
        return Object.freeze({
            presentations: PRESENTATIONS, viewModes: VIEW_MODES, snapshot, state: presentation.state,
            canTransition: presentation.canTransition,
            transition: next => { presentation.transition(next); return snapshot(); },
            select, open, setViewMode, tableWorkspace,
        });
    }

    function mount(shell, node, options) {
        if (!shell?.contentHost) throw new TypeError('CollectionRichNode requires a shell content host');
        const settings = options || {};
        const rich = settings.richNode || create({node, ...settings, presentation: settings.presentation || shell.collectionRichNode?.presentation});
        if (rich.tableWorkspace && rich.snapshot().presentation === 'workspace') {
            return global.WorkbenchCollectionTableWorkspace.mount(shell.contentHost, rich.tableWorkspace, settings);
        }
        const documentRef = settings.document || shell.contentHost.ownerDocument || global.document;
        const root = documentRef.createElement('div');
        root.className = 'workbench-collection-gallery';
        const render = () => {
            root.replaceChildren();
            const snapshot = rich.snapshot();
            root.dataset.viewMode = snapshot.viewMode;
            root.className = `workbench-collection-gallery workbench-collection-gallery--${snapshot.viewMode}`;
            snapshot.items.forEach(item => {
                const tile = documentRef.createElement('button');
                tile.type = 'button';
                tile.className = `workbench-collection-gallery__item${item.itemId === snapshot.selectedItemId ? ' is-selected' : ''}`;
                tile.dataset.itemId = item.itemId;
                tile.setAttribute('aria-label', item.label);
                const media = documentRef.createElement(item.kind === 'video' ? 'video' : 'img');
                media.className = 'workbench-collection-gallery__media';
                media.src = item.url;
                media.alt = item.label;
                if (item.kind === 'video') { media.controls = true; media.preload = 'metadata'; media.playsInline = true; }
                else media.loading = 'lazy';
                tile.append(media);
                tile.addEventListener('click', event => { event.stopPropagation(); rich.select(item.itemId); render(); });
                tile.addEventListener('dblclick', event => { event.stopPropagation(); rich.open(item.itemId); });
                tile.addEventListener('keydown', event => {
                    if (event.key !== 'Enter') return;
                    event.preventDefault();
                    event.stopPropagation();
                    rich.open(item.itemId);
                });
                root.append(tile);
            });
            const controls = documentRef.createElement('div');
            controls.className = 'workbench-collection-gallery__view-controls';
            controls.setAttribute('role', 'group');
            controls.setAttribute('aria-label', 'Collection view');
            rich.viewModes.forEach(mode => {
                const control = documentRef.createElement('button');
                control.type = 'button';
                control.dataset.viewMode = mode;
                control.textContent = mode === 'grid' ? 'Grid' : 'List';
                control.setAttribute('aria-pressed', String(snapshot.viewMode === mode));
                control.addEventListener('click', event => { event.stopPropagation(); rich.setViewMode(mode); render(); });
                controls.append(control);
            });
            const openWorkspace = () => {
                settings.workspaceSession?.openFromSelection?.(node.id);
                rich.transition('workspace');
                mount(shell, node, {...settings, richNode:rich});
                return true;
            };
            settings.registerWorkspaceOpen?.(openWorkspace);
            const workspaceControl = documentRef.createElement('button');
            workspaceControl.type = 'button';
            workspaceControl.dataset.presentation = 'workspace';
            workspaceControl.textContent = 'Table workspace';
            workspaceControl.addEventListener('click', event => {
                event.stopPropagation();
                openWorkspace();
            });
            controls.append(workspaceControl);
            root.append(controls);
        };
        render();
        shell.contentHost.replaceChildren(root);
        return Object.freeze({element: root, richNode: rich, destroy: () => root.remove()});
    }

    global.WorkbenchCollectionRichNode = Object.freeze({PRESENTATIONS, VIEW_MODES, collectionOf, isCompatible, visualItems, create, mount});
}(window));
