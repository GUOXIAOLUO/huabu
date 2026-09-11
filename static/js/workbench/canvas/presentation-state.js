/* Generic Node presentation state machine. Canvas selection and business data
   remain outside this module; persistence is supplied by an adapter. */
(function exposeWorkbenchPresentationState(global) {
    'use strict';

    const STATES = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);
    const TRANSITIONS = Object.freeze({
        card: Object.freeze(['expanded', 'workspace', 'inspector']),
        expanded: Object.freeze(['card', 'workspace', 'inspector']),
        workspace: Object.freeze(['card', 'expanded', 'inspector']),
        inspector: Object.freeze(['card', 'expanded', 'workspace']),
    });

    function normalize(value) { return STATES.includes(value) ? value : 'card'; }
    function canTransition(from, to) {
        return STATES.includes(from) && STATES.includes(to) && (from === to || TRANSITIONS[from].includes(to));
    }
    function create(options) {
        const settings = options || {};
        let current = normalize(settings.initial);
        const storage = settings.storage && typeof settings.storage.getItem === 'function' && typeof settings.storage.setItem === 'function' ? settings.storage : null;
        const key = String(settings.storageKey || 'workbench.presentation.state');
        if (storage) current = normalize(storage.getItem(key));
        function persist() { if (storage) storage.setItem(key, current); }
        function transition(next) {
            if (!STATES.includes(next)) throw new RangeError(`unknown presentation state: ${next}`);
            const target = next;
            if (!canTransition(current, target)) throw new RangeError(`invalid presentation transition: ${current} -> ${target}`);
            current = target;
            persist();
            if (typeof settings.onChange === 'function') settings.onChange(current);
            return current;
        }
        return Object.freeze({
            states: STATES,
            state: () => current,
            canTransition: next => canTransition(current, next),
            transition,
            snapshot: () => Object.freeze({state: current}),
            restore: snapshot => transition(snapshot && snapshot.state),
        });
    }

    global.WorkbenchPresentationState = Object.freeze({STATES, TRANSITIONS, normalize, canTransition, create});
}(window));
