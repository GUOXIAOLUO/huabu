/* Unified RenderRuntime: owns the mounted-card lifecycle — mount bookkeeping
   keyed by node id, ordered destroy on unmount/remount, and batch mounting —
   which adapter render sweeps previously left implicit (cards died by omission
   from the next render and mounted handles were discarded). */
(function exposeWorkbenchRenderRuntime(global) {
    'use strict';

    function create(options) {
        const settings = options || {};
        if (typeof settings.mount !== 'function') throw new TypeError('RenderRuntime requires a mount callback');
        const mounted = new Map();

        function mount(request) {
            const entry = request || {};
            const nodeId = String((entry.node && entry.node.id) || '');
            if (!nodeId) throw new TypeError('RenderRuntime mount requires node.id');
            unmount(nodeId);
            const handle = settings.mount(entry);
            mounted.set(nodeId, handle);
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
            mounted.delete(key);
            if (typeof handle.destroy === 'function') handle.destroy();
            return true;
        }

        function unmountAll() {
            for (const handle of [...mounted.values()]) {
                if (typeof handle.destroy === 'function') handle.destroy();
            }
            mounted.clear();
        }

        function isMounted(nodeId) {
            return mounted.has(String(nodeId || ''));
        }

        function mountedNodeIds() {
            return Object.freeze([...mounted.keys()]);
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

        return Object.freeze({mount, mountAll, mountGroupCard, unmount, unmountAll, isMounted, mountedNodeIds});
    }

    global.WorkbenchRenderRuntime = Object.freeze({create});
}(window));
