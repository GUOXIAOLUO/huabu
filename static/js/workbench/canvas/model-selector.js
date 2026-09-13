/* Generic Task ModelAvailability selector. It owns presentation-only selection
   state and never exposes credentials or executes a route. */
(function exposeWorkbenchModelSelector(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

    function normalize(value) { return text(value).toLowerCase().replace(/-/g, '_'); }

    function requirementsOf(values) {
        return [...new Set((Array.isArray(values) ? values : []).map(item => normalize(
            typeof item === 'string' ? item : item?.id,
        )).filter(Boolean))].sort();
    }

    function publicAvailability(value) {
        const item = value && typeof value === 'object' ? value : {};
        return {
            id: text(item.id), model_ref: text(item.model_ref), route_type: text(item.route_type),
            route_ref: text(item.route_ref), executor_type: text(item.executor_type),
            normalized_capabilities: Array.isArray(item.normalized_capabilities) ? item.normalized_capabilities.map(text).filter(Boolean) : [],
            enabled: item.enabled !== false, status: text(item.status, 'unknown'),
        };
    }

    function routeLabel(item) {
        const route = `${text(item.route_type, 'route')}:${text(item.route_ref, 'unknown')}`;
        return `${text(item.model_ref, 'model')} · ${route} · ${text(item.executor_type, 'executor')}`;
    }

    function create(options) {
        const settings = options || {};
        const task = settings.task || null;
        const requirements = requirementsOf(settings.requirements);
        const availabilities = Array.isArray(settings.availabilities) ? settings.availabilities.map(clone) : [];
        let selection = settings.selection && typeof settings.selection === 'object'
            ? {mode: settings.selection.mode === 'explicit' ? 'explicit' : 'auto', availabilityId: text(settings.selection.availabilityId)}
            : {mode: 'auto', availabilityId: ''};

        function candidateOf(availability) {
            availability = publicAvailability(availability);
            const available = new Set((availability.normalized_capabilities || []).map(normalize));
            const reasons = [];
            if (!availability.enabled) reasons.push('route_disabled');
            if (text(availability.status, 'unknown') !== 'available') reasons.push(`route_status:${text(availability.status, 'unknown')}`);
            requirements.filter(item => !available.has(item)).forEach(item => reasons.push(`missing_capability:${item}`));
            const compatible = reasons.length === 0;
            const score = compatible ? requirements.filter(item => available.has(item)).length : -reasons.length;
            return {availability: clone(availability), compatible, score, reasons};
        }

        function candidates() {
            return availabilities.map(candidateOf).sort((a, b) => b.score - a.score || text(a.availability.id).localeCompare(text(b.availability.id)));
        }

        function resolvedFor(items) {
            const compatible = items.filter(item => item.compatible);
            if (selection.mode === 'explicit') {
                return compatible.find(item => text(item.availability.id) === selection.availabilityId)?.availability || null;
            }
            return compatible[0]?.availability || null;
        }

        function snapshot() {
            const items = candidates();
            const resolved = resolvedFor(items);
            return Object.freeze({
                requirements: Object.freeze(requirements.slice()),
                selection: Object.freeze({...selection}),
                entries: Object.freeze(items.map(item => Object.freeze({...item, availability: clone(item.availability), reasons: Object.freeze(item.reasons.slice())}))),
                resolved: clone(resolved),
                resolvedLabel: resolved ? routeLabel(resolved) : '',
                reasons: Object.freeze(resolved ? [] : Object.freeze([...new Set(items.flatMap(item => item.reasons))].concat(items.length ? [] : ['no_availability_routes']))),
            });
        }

        function select(value) {
            const nextMode = value === 'auto' ? 'auto' : 'explicit';
            const nextId = nextMode === 'auto' ? '' : text(value);
            const view = candidates().find(item => text(item.availability.id) === nextId);
            if (nextMode === 'explicit' && (!view || !view.compatible)) throw new RangeError('cannot select an incompatible ModelAvailability');
            selection = {mode: nextMode, availabilityId: nextId};
            const state = snapshot();
            if (task && typeof task.update === 'function') task.update({modelSelection: clone({selection: state.selection, resolved: state.resolved})});
            if (typeof settings.onSelect === 'function') settings.onSelect(clone(state));
            return state;
        }

        function mount(host, mountOptions = {}) {
            if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('ModelSelector requires a host');
            const documentRef = mountOptions.document || host.ownerDocument || global.document;
            if (!documentRef || typeof documentRef.createElement !== 'function') throw new TypeError('ModelSelector requires a document');
            const root = documentRef.createElement('section'); root.className = 'workbench-model-selector';
            const label = documentRef.createElement('label'); label.textContent = mountOptions.label || 'Model route';
            const selectElement = documentRef.createElement('select'); selectElement.className = 'workbench-model-selector__select';
            const resolved = documentRef.createElement('p'); resolved.className = 'workbench-model-selector__resolved'; resolved.setAttribute('aria-live', 'polite');
            function render() {
                const view = snapshot(); selectElement.replaceChildren();
                const auto = documentRef.createElement('option'); auto.value = 'auto'; auto.textContent = view.resolvedLabel ? `Auto · ${view.resolvedLabel}` : 'Auto · unavailable';
                auto.selected = view.selection.mode === 'auto'; selectElement.append(auto);
                view.entries.forEach(item => {
                    const option = documentRef.createElement('option'); option.value = item.availability.id; option.textContent = item.compatible ? routeLabel(item.availability) : `${routeLabel(item.availability)} · ${item.reasons.join(', ')}`;
                    option.disabled = !item.compatible; option.title = item.reasons.join(', '); option.selected = view.selection.mode === 'explicit' && view.selection.availabilityId === item.availability.id; selectElement.append(option);
                });
                resolved.textContent = view.resolvedLabel ? `Resolved: ${view.resolvedLabel}` : `Unavailable: ${view.reasons.join(', ')}`;
            }
            selectElement.addEventListener('change', () => { select(selectElement.value); render(); });
            label.append(selectElement); root.append(label, resolved); host.replaceChildren(root); render();
            return Object.freeze({element: root, destroy: () => root.remove()});
        }
        return Object.freeze({snapshot, select, mount});
    }

    global.WorkbenchModelSelector = Object.freeze({create, requirementsOf});
}(window));
