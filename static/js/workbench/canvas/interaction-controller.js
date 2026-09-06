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

    global.WorkbenchInteractionController = Object.freeze({create});
}(window));
