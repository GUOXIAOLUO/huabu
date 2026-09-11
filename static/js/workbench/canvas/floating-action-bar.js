/* Generic contextual action bar. It owns visibility, action contribution,
   and intent emission; Canvas adapters own the resulting business commands. */
(function exposeWorkbenchFloatingActionBar(global) {
    'use strict';

    function normalizeAction(action) {
        if (!action || typeof action !== 'object') throw new TypeError('FloatingActionBar action is required');
        const id = String(action.id || '').trim();
        if (!id || typeof action.when !== 'function') throw new TypeError('FloatingActionBar action requires id and when');
        return Object.freeze({
            id, label: String(action.label || id), icon: String(action.icon || ''), order: Number(action.order) || 0,
            when: action.when,
        });
    }

    function create(options) {
        const settings = options || {};
        const documentRef = settings.document;
        const container = settings.container;
        if (!documentRef || !container) throw new TypeError('FloatingActionBar requires document and container');
        const onIntent = settings.onIntent;
        const actions = Object.freeze((settings.actions || []).map(normalizeAction).sort((a, b) => a.order - b.order || a.id.localeCompare(b.id)));
        let context = Object.freeze({nodeIds: Object.freeze([]), nodes: Object.freeze([]), count: 0, mode: 'empty'});

        container.classList.add('floating-action-bar');
        function update(nextContext) {
            const next = nextContext || {};
            const nodeIds = Object.freeze(Array.from(new Set((next.nodeIds || []).map(String))));
            const nodes = Object.freeze(Array.from(next.nodes || []));
            context = Object.freeze({nodeIds, nodes, count: nodeIds.length, mode: nodeIds.length === 1 ? 'single' : nodeIds.length > 1 ? 'multiple' : 'empty'});
            container.replaceChildren();
            const visible = actions.filter(action => action.when(context));
            visible.forEach(action => {
                const button = documentRef.createElement('button');
                button.type = 'button';
                button.className = 'hub-action';
                button.dataset.actionId = action.id;
                button.setAttribute('aria-label', action.label);
                button.title = action.label;
                if (action.icon) button.dataset.lucide = action.icon;
                button.textContent = action.label;
                button.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof onIntent === 'function') onIntent({type: 'floating_action', actionId: action.id, nodeIds: context.nodeIds, mode: context.mode});
                });
                container.appendChild(button);
            });
            container.classList.toggle('open', visible.length > 0 && context.count > 0);
            return Object.freeze({visible: visible.map(action => action.id), mode: context.mode});
        }
        function clear() { return update({nodeIds: [], nodes: []}); }
        return Object.freeze({update, clear, actions});
    }

    global.WorkbenchFloatingActionBar = Object.freeze({create});
}(window));
