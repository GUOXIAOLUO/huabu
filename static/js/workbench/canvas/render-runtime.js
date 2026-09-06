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

        return Object.freeze({mount, mountAll, unmount, unmountAll, isMounted, mountedNodeIds});
    }

    global.WorkbenchRenderRuntime = Object.freeze({create});
}(window));
