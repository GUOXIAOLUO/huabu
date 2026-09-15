/* Shared presentation for generation nodes.
   It projects model availability, execution profile, and capabilities without
   owning provider settings, credentials, persistence, or execution. */
(function exposeWorkbenchGenerationPresentation(global) {
    'use strict';

    function text(value, fallback = '—') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function list(value) {
        return Array.isArray(value) ? value : [];
    }

    function projection(node, options = {}) {
        const source = node && typeof node === 'object' ? node : {};
        const projected = typeof options.project === 'function' ? options.project(source) : {};
        const registries = global.WorkbenchRuntimeRegistries || global.WorkbenchRegistries || {};
        const availabilityRegistry = registries.modelAvailability || registries.modelAvailabilities || global.WorkbenchModelAvailabilityRegistry;
        const model = projected.model || source.model || source.model_ref || source.msCustomModel || source.msgenModel;
        const candidates = availabilityRegistry && typeof availabilityRegistry.listForModel === 'function'
            ? availabilityRegistry.listForModel(source.model_ref || source.model || '')
            : (availabilityRegistry && typeof availabilityRegistry.list === 'function'
                ? availabilityRegistry.list({model_ref: source.model_ref || source.model || ''}) : []);
        const selectedAvailability = candidates.find(item => String(item.id || '') === String(source.modelAvailabilityId || source.model_availability_id || ''))
            || candidates.find(item => item.status === 'available' && item.enabled !== false)
            || candidates[0];
        const availability = projected.availability || source.modelAvailability || source.model_availability || selectedAvailability || {};
        const route = projected.route || availability.route_ref || availability.routeRef || availability.route_type
            || source.apiProvider || source.provider_id;
        const execution = projected.execution || source.executionProfile || source.execution_profile || availability.executor_type;
        const capabilities = list(projected.capabilities || availability.normalized_capabilities || source.capabilities || source.normalized_capabilities);
        return Object.freeze({
            model: text(model), route: text(route), execution: text(execution),
            capabilities: Object.freeze(capabilities.map(item => text(item)).filter(item => item !== '—')),
        });
    }

    function create(options = {}) {
        const documentRef = options.document || global.document;
        const container = options.container;
        const node = options.node;
        if (!documentRef || !container || !node) throw new TypeError('Generation presentation requires document, container, and node');
        const root = documentRef.createElement('section');
        root.className = 'workbench-generation-presentation';
        root.setAttribute('data-generation-presentation', '');
        const heading = documentRef.createElement('div');
        heading.className = 'workbench-generation-presentation__heading';
        const title = documentRef.createElement('strong');
        title.className = 'workbench-generation-presentation__title';
        title.textContent = text(options.title, '生成');
        const status = documentRef.createElement('span');
        status.className = 'workbench-generation-presentation__status';
        status.textContent = text(options.status || node.state, 'ready');
        heading.append(title, status);
        const route = documentRef.createElement('div');
        route.className = 'workbench-generation-presentation__route';
        const capabilities = documentRef.createElement('div');
        capabilities.className = 'workbench-generation-presentation__capabilities';
        root.append(heading, route, capabilities);
        container.prepend(root);

        function refresh() {
            const current = projection(node, options);
            route.textContent = `模型 · ${current.model}  ·  路由 · ${current.route}  ·  执行 · ${current.execution}`;
            capabilities.replaceChildren();
            const values = current.capabilities.length ? current.capabilities : ['能力由模型定义提供'];
            values.forEach(value => {
                const chip = documentRef.createElement('span');
                chip.className = 'workbench-generation-presentation__capability';
                chip.textContent = value;
                capabilities.append(chip);
            });
            status.textContent = text(options.status || node.state, 'ready');
            return current;
        }
        refresh();
        return Object.freeze({root, refresh, projection: () => projection(node, options)});
    }

    global.WorkbenchGenerationPresentation = Object.freeze({create, projection});
}(window));
