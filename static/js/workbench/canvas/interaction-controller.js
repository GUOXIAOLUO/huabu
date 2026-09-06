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

    global.WorkbenchInteractionController = Object.freeze({create, createSelectionStore});
}(window));
