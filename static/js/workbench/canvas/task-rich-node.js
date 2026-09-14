/* Generic Task Rich Node skeleton. It describes product-facing task UX only;
   future capability and runtime ownership are deliberately deferred. */
(function exposeWorkbenchTaskRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);
    const DEFAULT_STATE = Object.freeze({
        status: 'draft', inputs: [], definition: null, skill: null, skillBinding: null, modelSelection: null, prompt: '', outputMode: 'text', presentation: 'card',
        workspace: null, inspector: null,
    });
    const PERSISTED_KEYS = Object.freeze(['status', 'inputs', 'definition', 'skill', 'skillBinding', 'modelSelection', 'prompt', 'outputMode', 'presentation', 'workspace', 'inspector']);

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
            skillBinding: value.skillBinding && typeof value.skillBinding === 'object' ? Object.freeze({...value.skillBinding, parameters: value.skillBinding.parameters && typeof value.skillBinding.parameters === 'object' ? Object.freeze({...value.skillBinding.parameters}) : {}}) : null,
            modelSelection: value.modelSelection && typeof value.modelSelection === 'object' ? Object.freeze({selection: value.modelSelection.selection && typeof value.modelSelection.selection === 'object' ? Object.freeze({...value.modelSelection.selection}) : null, resolved: value.modelSelection.resolved && typeof value.modelSelection.resolved === 'object' ? Object.freeze({...value.modelSelection.resolved}) : null}) : null,
            prompt: value.prompt == null ? '' : text(value.prompt),
            outputMode: ['text', 'list', 'structured'].includes(value.outputMode) ? value.outputMode : 'text',
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
                fields: Object.freeze({status: state.status, inputs: Object.freeze(state.inputs.slice()), definition: state.definition, skill: state.skill, skillBinding: state.skillBinding, modelSelection: state.modelSelection, prompt: state.prompt, outputMode: state.outputMode, workspace: state.workspace, inspector: state.inspector}),
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
        function currentState() {
            return Object.freeze({...state, presentation: presentationController?.state() || state.presentation, inputs: Object.freeze(state.inputs.slice())});
        }
        function mountSkillSelector(host, options) {
            if (!global.WorkbenchSkillSelector) throw new Error('Task Skill selector is unavailable');
            const settings = options || {};
            const selector = global.WorkbenchSkillSelector.create({...settings, task: {update}});
            return selector.mount(host, settings);
        }
        function mountTaskPresentation(host, options) {
            if (!global.WorkbenchTaskCardPresentation) throw new Error('Task card presentation is unavailable');
            const settings = options || {};
            return global.WorkbenchTaskCardPresentation.create({...settings, task: {
                state: currentState,
                update,
                mountSkillSelector,
                mountModelSelector,
            }}).mount(host);
        }
        function mountSkillPresentation(host, options) {
            if (!global.WorkbenchSkillDrivenPresentation) throw new Error('Task Skill presentation is unavailable');
            const settings = options || {};
            return global.WorkbenchSkillDrivenPresentation.create({...settings, task: {update}}).mount(host, settings);
        }
        function mountSkillInspector(host, options) {
            if (!global.WorkbenchSkillInspector) throw new Error('Task Skill inspector is unavailable');
            const settings = options || {};
            return global.WorkbenchSkillInspector.create({...settings, definition: settings.definition || state.definition, binding: settings.binding || state.skillBinding}).mount(host, settings);
        }
        function mountModelSelector(host, options) {
            if (!global.WorkbenchModelSelector) throw new Error('Task Model selector is unavailable');
            const settings = options || {};
            return global.WorkbenchModelSelector.create({...settings, task: {update}, selection: settings.selection || state.modelSelection?.selection}).mount(host, settings);
        }
        function mountExecutionInputPreview(host, options) {
            if (!global.WorkbenchExecutionInputPreview) throw new Error('Task execution input preview is unavailable');
            return global.WorkbenchExecutionInputPreview.create(options || {}).mount(host);
        }
        function mountResultTray(host, options) {
            if (!global.WorkbenchCanvasResultTray) throw new Error('Task result tray is unavailable');
            return global.WorkbenchCanvasResultTray.create(options || {}).mount(host);
        }
        function mountResultCompare(host, options) {
            if (!global.WorkbenchCanvasResultCompare) throw new Error('Task result compare is unavailable');
            return global.WorkbenchCanvasResultCompare.create(options || {}).mount(host);
        }
        function mountResultSelection(host, options) {
            if (!global.WorkbenchCanvasResultSelection) throw new Error('Task result selection is unavailable');
            return global.WorkbenchCanvasResultSelection.create(options || {}).mount(host);
        }
        function mountExecutionBranch(host, options) {
            if (!global.WorkbenchCanvasExecutionBranch) throw new Error('Task execution branch is unavailable');
            return global.WorkbenchCanvasExecutionBranch.create(options || {}).mount(host);
        }
        function mountResultCollection(host, options) {
            if (!global.WorkbenchCanvasResultCollection) throw new Error('Task result collection is unavailable');
            return global.WorkbenchCanvasResultCollection.create(options || {}).mount(host);
        }
        function mountResultMaterialization(host, options) {
            if (!global.WorkbenchCanvasResultMaterialization) throw new Error('Task result materialization is unavailable');
            return global.WorkbenchCanvasResultMaterialization.create(options || {}).mount(host);
        }
        function mountResultWorkspace(host, options) {
            if (!global.WorkbenchCanvasResultWorkspace) throw new Error('Task result workspace is unavailable');
            return global.WorkbenchCanvasResultWorkspace.create(options || {}).mount(host);
        }
        return Object.freeze({
            presentations: PRESENTATIONS, snapshot, update, mountTaskPresentation, mountSkillSelector, mountSkillPresentation, mountSkillInspector, mountModelSelector, mountExecutionInputPreview, mountResultTray, mountResultCompare, mountResultSelection, mountExecutionBranch, mountResultCollection, mountResultMaterialization, mountResultWorkspace,
            state: currentState,
        });
    }

    global.WorkbenchTaskRichNode = Object.freeze({PRESENTATIONS, compatible, create});
}(window));
