/* Generic immersive workspace lifecycle. Sessions are transient UI state;
   Canvas records and business data remain owned by their application services. */
(function exposeWorkbenchWorkspaceSession(global) {
    'use strict';

    const STATES = Object.freeze(['closed', 'open']);

    function freezeContext(value) {
        const context = {...value};
        if (Array.isArray(context.selection)) {
            context.selection = Object.freeze(context.selection.slice());
        }
        return Object.freeze(context);
    }

    function snapshot(state, context, dirty) {
        return Object.freeze({state, context: context || null, dirty: Boolean(dirty)});
    }

    function notify(callback, state, context, dirty) {
        const value = snapshot(state, context, dirty);
        if (typeof callback === 'function') callback(value);
        return value;
    }

    function createRegistry() {
        const definitions = new Map();
        return Object.freeze({
            register(definition) {
                if (!definition || !String(definition.id || '').trim() || typeof definition.open !== 'function') {
                    throw new TypeError('WorkspaceRegistry entries require id and open');
                }
                const id = String(definition.id);
                if (definitions.has(id)) throw new Error(`workspace already registered: ${id}`);
                definitions.set(id, Object.freeze({...definition, id}));
                return definitions.get(id);
            },
            resolve(id) { return definitions.get(String(id)) || null; },
            list() { return Object.freeze(Array.from(definitions.values())); },
            unregister(id) { return definitions.delete(String(id)); },
        });
    }

    function create(options) {
        const settings = options || {};
        let state = 'closed';
        let context = null;
        let dirty = false;

        function current() { return snapshot(state, context, dirty); }
        function emit() { return notify(settings.onChange, state, context, dirty); }
        function requireOpen() {
            if (state !== 'open') throw new Error('workspace session is closed');
        }
        function finishDiscard() {
            dirty = false;
            state = 'closed';
            context = null;
            return emit();
        }
        function discard() {
            requireOpen();
            const handler = settings.onDiscard;
            if (typeof handler !== 'function') return finishDiscard();
            const result = handler(context);
            if (result && typeof result.then === 'function') return result.then(finishDiscard);
            return finishDiscard();
        }
        function open(nextContext) {
            if (!nextContext || typeof nextContext !== 'object') throw new TypeError('workspace context is required');
            if (state === 'open') {
                if (context && context.nodeId === nextContext.nodeId) return current();
                if (dirty) throw new Error('cannot replace a dirty workspace session');
            }
            state = 'open';
            context = freezeContext(nextContext);
            dirty = false;
            return emit();
        }
        function close(optionsArg) {
            requireOpen();
            const closeOptions = optionsArg || {};
            if (dirty && closeOptions.discard !== true) throw new Error('workspace has unsaved changes');
            return dirty ? discard() : finishDiscard();
        }
        function save() {
            requireOpen();
            if (!dirty) return current();
            if (typeof settings.onSave !== 'function') throw new Error('workspace save handler is required');
            const result = settings.onSave(context);
            const finishSave = () => { dirty = false; return emit(); };
            if (result && typeof result.then === 'function') return result.then(finishSave);
            return finishSave();
        }
        function markDirty(value = true) {
            requireOpen();
            dirty = Boolean(value);
            return emit();
        }
        return Object.freeze({
            states: STATES,
            state: () => state,
            context: () => context,
            isDirty: () => dirty,
            snapshot: current,
            open,
            close,
            save,
            discard,
            markDirty,
        });
    }

    global.WorkbenchWorkspaceSession = Object.freeze({STATES, create, createRegistry});
}(window));
