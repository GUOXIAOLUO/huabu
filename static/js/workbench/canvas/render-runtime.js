/* Unified RenderRuntime: owns the mounted-card lifecycle — mount bookkeeping
   keyed by node id, ordered destroy on unmount/remount, and batch mounting —
   which adapter render sweeps previously left implicit (cards died by omission
   from the next render and mounted handles were discarded). */
(function exposeWorkbenchRenderRuntime(global) {
    'use strict';

    function create(options) {
        const settings = options || {};
        if (typeof settings.mount !== 'function') throw new TypeError('RenderRuntime requires a mount callback');
        const mediaState = settings.mediaState || null;
        if (mediaState && (typeof mediaState.capture !== 'function' || typeof mediaState.restore !== 'function')) {
            throw new TypeError('RenderRuntime mediaState requires capture and restore callbacks');
        }
        const mounted = new Map();
        const pendingMediaStates = new Map();

        function mount(request) {
            const entry = request || {};
            const nodeId = String((entry.node && entry.node.id) || '');
            if (!nodeId) throw new TypeError('RenderRuntime mount requires node.id');
            unmount(nodeId);
            const handle = settings.mount(entry);
            mounted.set(nodeId, handle);
            // Media-state projection: state captured at unmount is restored into
            // the freshly mounted card, so remounts keep playback continuity
            // without page-owned bookkeeping.
            const stored = pendingMediaStates.get(nodeId);
            if (mediaState && stored && entry.card) {
                pendingMediaStates.delete(nodeId);
                mediaState.restore(entry.card, stored);
            }
            return handle;
        }

        function mountAll(requests) {
            if (!Array.isArray(requests)) throw new TypeError('RenderRuntime mountAll requires an array');
            return Object.freeze(requests.map(request => mount(request)));
        }

        function unmount(nodeId) {
            const key = String(nodeId || '');
            const handle = mounted.get(key);
            if (!handle) return false;
            if (mediaState && handle.element) {
                const states = mediaState.capture(handle.element);
                if (states && states.size) pendingMediaStates.set(key, states);
            }
            mounted.delete(key);
            if (typeof handle.destroy === 'function') handle.destroy();
            return true;
        }

        function unmountAll() {
            for (const handle of [...mounted.values()]) {
                if (typeof handle.destroy === 'function') handle.destroy();
            }
            mounted.clear();
            pendingMediaStates.clear();
        }

        function isMounted(nodeId) {
            return mounted.has(String(nodeId || ''));
        }

        function mountedNodeIds() {
            return Object.freeze([...mounted.keys()]);
        }

        // A sweep owns reconciliation, including removals received from a
        // remote record or undo. Page delete handlers must not have to know
        // which renderer resources a disappearing node owns.
        function retain(nodeIds) {
            const keep = new Set(nodeIds.map(id => String(id)));
            for (const id of [...mounted.keys()]) {
                if (!keep.has(id)) {
                    try { unmount(id); }
                    finally { pendingMediaStates.delete(id); }
                }
            }
            for (const id of pendingMediaStates.keys()) {
                if (!keep.has(id)) pendingMediaStates.delete(id);
            }
        }

        // Release the previous card BEFORE the builder initializes new
        // resources on the same payload (for example a timeline editor).
        // mount() alone is too late: legacy bodies are built before mounting.
        function rebuild(nodeId, build) {
            const key = String(nodeId || '');
            if (!key || typeof build !== 'function') throw new TypeError('RenderRuntime rebuild requires a node id and builder');
            unmount(key);
            try {
                return build();
            } catch (error) {
                unmount(key);
                throw error;
            } finally {
                // A rollback/failed builder may never mount a shared shell.
                // Its saved state must not leak into a later, unrelated card.
                pendingMediaStates.delete(key);
            }
        }

        // Group family mount: the runtime owns the group record assembly, the
        // media-vs-legacy-content decision, the mount execution and its
        // lifecycle entry; pages supply only member resolution, intent
        // callbacks, control selectors, card classes, and an optional empty
        // state hook. `cardClasses` may be a function receiving the mount
        // outcome so page CSS-state classes stay page-owned.
        function mountGroupCard(options) {
            const group = options || {};
            const node = group.node;
            if (!node || !node.id) throw new TypeError('RenderRuntime group mount requires node.id');
            const record = global.WorkbenchCanvas.legacyNodeView(node, group.context || {});
            const ownMedia = (node.images || []).map(item => ({url:item?.url, name:item?.name || node.title || 'Media', type:item?.type || item?.kind || ''}));
            const memberMedia = (group.memberImages || []).map(item => ({url:item?.url, name:item?.name || 'Media', type:item?.type || ''}));
            record.output_refs = [...ownMedia, ...memberMedia].filter(item => item.url);
            const mediaAllowed = group.mediaEnabled !== false;
            const hasRenderableMedia = mediaAllowed && Boolean(global.WorkbenchMediaRenderer?.canRender(record));
            const useLegacyContent = !hasRenderableMedia && (!global.WorkbenchLegacyRenderer || global.WorkbenchLegacyRenderer.canRender(record));
            const classList = typeof group.cardClasses === 'function'
                ? group.cardClasses({hasRenderableMedia, useLegacyContent})
                : (group.cardClasses || ['node-shell-mounted']);
            const shellView = global.WorkbenchUnifiedRenderHost.cardShellView({
                selected: group.selected,
                onIntent: group.onIntent,
                ...(group.ports ? {ports: group.ports} : {}),
            });
            const handle = mount({
                document: group.document, node: record, card: group.card, contentHost: group.contentHost,
                preserveLegacyContent: group.preserveLegacyContent !== undefined ? group.preserveLegacyContent : useLegacyContent,
                ...(group.legacyContentClassName ? {legacyContentClassName: group.legacyContentClassName} : {}),
                ...(group.controlSettings ? {controlSettings: group.controlSettings} : {}),
                removeControlsBeforeMount: group.removeControlsBeforeMount === true,
                cardClasses: classList.filter(Boolean),
                ...shellView,
            });
            const result = Object.freeze({
                ...handle, ...shellView,
                node: handle.node || record,
                hasRenderableMedia, useLegacyContent,
            });
            if (!hasRenderableMedia && !useLegacyContent && typeof group.mountEmptyState === 'function') {
                group.mountEmptyState(result);
            }
            return result;
        }

        return Object.freeze({mount, mountAll, mountGroupCard, unmount, unmountAll, isMounted, mountedNodeIds, retain, rebuild});
    }

    global.WorkbenchRenderRuntime = Object.freeze({create});
}(window));
