/* Generic Task Rich Node skeleton. It describes product-facing task UX only;
   future capability and runtime ownership are deliberately deferred. */
(function exposeWorkbenchTaskRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);
    const DEFAULT_STATE = Object.freeze({
        status: 'draft', inputs: [], definition: null, skill: null, presentation: 'card',
        workspace: null, inspector: null,
    });
    const PERSISTED_KEYS = Object.freeze(['status', 'inputs', 'definition', 'skill', 'presentation', 'workspace', 'inspector']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function compatible(node) {
        return Boolean(node && typeof node === 'object' && (node.kind === 'task' || node.type === 'task'));
    }

    function readStored(storage, key) {
        if (!storage || typeof storage.getItem !== 'function') return {};
        try {
            const value = JSON.parse(storage.getItem(key) || '{}');
            return value && typeof value === 'object' ? value : {};
        } catch(error) { return {}; }
    }

    function stateFrom(source) {
        const value = source && typeof source === 'object' ? source : {};
        return {
            status: text(value.status, DEFAULT_STATE.status),
            inputs: Array.isArray(value.inputs) ? value.inputs.map(input => input && typeof input === 'object' ? Object.freeze({...input}) : input) : [],
            definition: value.definition && typeof value.definition === 'object' ? Object.freeze({...value.definition}) : null,
            skill: value.skill == null ? null : text(value.skill),
            presentation: PRESENTATIONS.includes(value.presentation) ? value.presentation : 'card',
            workspace: value.workspace == null ? null : text(value.workspace),
            inspector: value.inspector == null ? null : text(value.inspector),
        };
    }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!compatible(node)) throw new TypeError('TaskRichNode requires a generic task NodeRecord');
        const storage = settings.storage
            && typeof settings.storage.getItem === 'function'
            && typeof settings.storage.setItem === 'function'
            ? settings.storage : null;
        const key = String(settings.storageKey || `workbench.task.state:${text(node.id, 'unknown')}`);
        const presentationController = settings.presentationController || null;
        let state = stateFrom({...DEFAULT_STATE, ...node, ...readStored(storage, key)});
        if (presentationController?.state) state.presentation = presentationController.state();
        function persist() {
            if (!storage) return;
            const persisted = {};
            PERSISTED_KEYS.forEach(name => { persisted[name] = state[name]; });
            storage.setItem(key, JSON.stringify(persisted));
        }
        function snapshot() {
            return Object.freeze({
                nodeId: text(node.id), title: text(node.title, 'Task'), kind: 'task',
                presentation: text(state.presentation, 'card'),
                fields: Object.freeze({status: state.status, inputs: Object.freeze(state.inputs.slice()), definition: state.definition, skill: state.skill, workspace: state.workspace, inspector: state.inspector}),
                legacyCompatible: node.type === 'task',
            });
        }
        function update(patch) {
            if (!patch || typeof patch !== 'object') throw new TypeError('TaskRichNode update requires fields');
            const next = {...state, ...patch};
            if (presentationController && Object.prototype.hasOwnProperty.call(patch, 'presentation')) {
                if (!presentationController.canTransition(patch.presentation)) throw new RangeError(`invalid task presentation: ${patch.presentation}`);
                if (presentationController.state() !== patch.presentation) presentationController.transition(patch.presentation);
                next.presentation = presentationController.state();
            }
            state = stateFrom(next);
            if (presentationController?.state) state.presentation = presentationController.state();
            persist();
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
            return snapshot();
        }
        return Object.freeze({
            presentations: PRESENTATIONS, snapshot, update,
            state: () => Object.freeze({...state, presentation: presentationController?.state() || state.presentation, inputs: Object.freeze(state.inputs.slice())}),
        });
    }

    global.WorkbenchTaskRichNode = Object.freeze({PRESENTATIONS, compatible, create});
}(window));
