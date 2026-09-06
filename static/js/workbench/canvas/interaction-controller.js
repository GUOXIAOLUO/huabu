/* Unified InteractionController: single owner for pointer-session lifecycle on
   the window handler slot — begin wires move/up dispatch to the active
   session, mouseup ends the session and invokes onEnd (the handlers stay
   assigned as guarded no-ops, matching the page runtimes' existing
   supersede-on-begin semantics), and end() unwires explicitly. Pure
   interaction math stays in WorkbenchCanvasRuntime sessions. */
(function exposeWorkbenchInteractionController(global) {
    'use strict';

    function create(options) {
        const settings = options || {};
        const windowRef = settings.windowRef || global;
        if (!windowRef) throw new TypeError('InteractionController requires a window reference');
        let active = null;

        function begin(session) {
            const entry = session || {};
            if (typeof entry.onMove !== 'function' || typeof entry.onEnd !== 'function') {
                throw new TypeError('InteractionController session requires onMove and onEnd callbacks');
            }
            active = {
                kind: String(entry.kind || 'pointer'),
                onMove: entry.onMove,
                onEnd: entry.onEnd,
            };
            windowRef.onmousemove = event => {
                const current = active;
                if (current) current.onMove(event);
            };
            windowRef.onmouseup = event => {
                const current = active;
                if (!current) return;
                active = null;
                current.onEnd(event);
            };
            return active.kind;
        }

        function end() {
            if (!active) return false;
            active = null;
            windowRef.onmousemove = null;
            windowRef.onmouseup = null;
            return true;
        }

        function activeKind() {
            return active ? active.kind : null;
        }

        return Object.freeze({begin, end, activeKind});
    }

    // Selection authority: a Set-compatible store that owns selection state for
    // a page. All mutations flow through it (single click, multi-select, box
    // selection results), so the page keeps no second selection source of
    // truth. Ids are coerced to strings; normalization against live nodes
    // stays the caller's concern, exactly like the previous page-local Sets.
    function createSelectionStore(options) {
        const settings = options || {};
        const onChange = typeof settings.onChange === 'function' ? settings.onChange : null;
        const ids = new Set();
        const store = {};

        function changed() {
            if (onChange) onChange([...ids]);
        }

        store.has = id => ids.has(String(id));
        store.add = id => {
            const key = String(id);
            if (!ids.has(key)) {
                ids.add(key);
                changed();
            }
            return store;
        };
        store.delete = id => {
            const had = ids.delete(String(id));
            if (had) changed();
            return had;
        };
        store.clear = () => {
            if (!ids.size) return;
            ids.clear();
            changed();
        };
        store.replace = next => {
            ids.clear();
            for (const id of next || []) ids.add(String(id));
            changed();
        };
        Object.defineProperty(store, 'size', {get: () => ids.size});
        store.forEach = (callback, thisArg) => {
            ids.forEach(value => callback.call(thisArg, value, value, store));
        };
        store[Symbol.iterator] = function* () { yield* ids; };
        store.ids = () => Object.freeze([...ids]);

        return Object.freeze(store);
    }

    // Viewport controller: one owner for viewport mutations over the
    // runtime-state kernel. Commands dispatch through the kernel and the
    // resolved viewport is returned; applyViewport-style DOM persistence stays
    // with the page via callbacks, so the kernel remains the single state
    // owner while the page keeps only its render shell.
    function createViewportController(options) {
        const settings = options || {};
        if (typeof settings.getKernel !== 'function') throw new TypeError('ViewportController requires getKernel');
        if (typeof settings.applyViewport !== 'function') throw new TypeError('ViewportController requires applyViewport');
        const kernel = () => settings.getKernel();

        function apply() {
            const runtime = kernel();
            if (!runtime) return null;
            settings.applyViewport(runtime.snapshot().viewport);
            return runtime.snapshot().viewport;
        }

        function dispatch(command) {
            const runtime = kernel();
            if (!runtime) return null;
            runtime.dispatch(command);
            return apply();
        }

        return Object.freeze({
            set: viewport => dispatch({type:'canvas.viewport.set', viewport}),
            panBy: (dx, dy) => dispatch({type:'canvas.viewport.pan', dx, dy}),
            zoomAt: (anchor, scale) => dispatch({type:'canvas.viewport.zoom-at', anchor, scale}),
            centerOn: (worldPoint, size) => {
                const runtime = kernel();
                if (!runtime || typeof runtime.viewportCenteredOnWorldPoint !== 'function') return null;
                const viewport = runtime.viewportCenteredOnWorldPoint(runtime.snapshot().viewport, worldPoint, size);
                return dispatch({type:'canvas.viewport.set', viewport});
            },
            current: () => {
                const runtime = kernel();
                return runtime ? runtime.snapshot().viewport : null;
            },
            apply,
        });
    }

    global.WorkbenchInteractionController = Object.freeze({create, createSelectionStore, createViewportController});
}(window));
