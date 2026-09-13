/* Definition-driven Task presentation. Skill metadata is declarative; all
   executable workspace/action behavior must come from injected registries. */
(function exposeWorkbenchSkillDrivenPresentation(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

    function properties(definition) {
        const schema = definition?.parameter_schema;
        return schema && typeof schema === 'object' && schema.properties && typeof schema.properties === 'object'
            ? Object.entries(schema.properties).map(([id, schemaValue]) => ({id, schema: schemaValue || {}})) : [];
    }

    function inputRoles(definition) {
        return (definition?.ports?.inputs || []).map(port => ({id: text(port.id), required: Boolean(port.required), accepts: [...(port.accepts || [])]}));
    }

    function outputSummary(definition) {
        const ports = (definition?.ports?.outputs || []).map(port => ({id: text(port.id), produces: [...(port.produces || [])]}));
        const schema = definition?.output_schema;
        return {ports, fields: schema?.properties && typeof schema.properties === 'object' ? Object.keys(schema.properties) : []};
    }

    function declaredActions(definition, registry) {
        const ids = Array.isArray(definition?.presentation?.metadata?.actions)
            ? definition.presentation.metadata.actions.map(item => typeof item === 'string' ? item : item?.id).filter(Boolean) : [];
        if (!registry) return [];
        return ids.map(id => typeof registry.resolve === 'function' ? registry.resolve(id) : registry[id]).filter(action => action && typeof action === 'object');
    }

    function declaredWorkspace(definition, registry) {
        const workspace = definition?.workspace;
        if (!workspace || !registry) return null;
        return typeof registry.resolve === 'function' ? registry.resolve(workspace.workspace_type, workspace.entrypoint) : registry[workspace.workspace_type] || null;
    }

    function create(options) {
        const settings = options || {};
        const definition = settings.definition;
        if (!definition || !text(definition.id) || !text(definition.version)) throw new TypeError('SkillDrivenPresentation requires a SkillDefinition');
        const task = settings.task || null;
        let parameters = clone(settings.binding?.parameters || {});
        function snapshot() {
            return Object.freeze({
                skill: Object.freeze({id: text(definition.id), version: text(definition.version), title: text(definition.title, definition.id)}),
                parameters: Object.freeze(clone(parameters)), controls: Object.freeze(properties(definition)),
                inputs: Object.freeze(inputRoles(definition)), output: Object.freeze(outputSummary(definition)),
                workspace: declaredWorkspace(definition, settings.workspaceRegistry),
                actions: Object.freeze(declaredActions(definition, settings.actionRegistry)),
            });
        }
        function setParameter(id, value) {
            const name = text(id);
            if (!properties(definition).some(item => item.id === name)) throw new RangeError(`unknown Skill parameter: ${name}`);
            parameters = {...parameters, [name]: value};
            if (task && typeof task.update === 'function') task.update({skillBinding: {...(settings.binding || {}), skill_id: definition.id, version: definition.version, parameters: clone(parameters)}});
            settings.onChange?.(snapshot());
            return snapshot();
        }
        function mount(host, mountOptions = {}) {
            if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('SkillDrivenPresentation requires a host');
            const documentRef = mountOptions.document || host.ownerDocument || global.document;
            if (!documentRef?.createElement) throw new TypeError('SkillDrivenPresentation requires a document');
            const root = documentRef.createElement('section'); root.className = 'workbench-skill-driven-presentation';
            const title = documentRef.createElement('h3'); title.textContent = text(definition.title, definition.id); root.append(title);
            const controls = documentRef.createElement('div'); controls.className = 'workbench-skill-driven-presentation__parameters';
            properties(definition).forEach(({id, schema}) => {
                const label = documentRef.createElement('label'); label.dataset.parameter = id; label.textContent = text(schema.title, id);
                const control = schema.enum ? documentRef.createElement('select') : documentRef.createElement(schema.type === 'boolean' ? 'input' : 'input');
                control.name = id; control.type = schema.enum ? undefined : (schema.type === 'boolean' ? 'checkbox' : 'text');
                if (schema.enum) schema.enum.forEach(value => { const option = documentRef.createElement('option'); option.value = value; option.textContent = value; control.append(option); });
                if (schema.type === 'boolean') control.checked = Boolean(parameters[id]); else control.value = parameters[id] ?? schema.default ?? '';
                control.addEventListener('change', () => setParameter(id, schema.type === 'boolean' ? control.checked : control.value));
                label.append(control); controls.append(label);
            });
            root.append(controls);
            const summary = documentRef.createElement('div'); summary.className = 'workbench-skill-driven-presentation__summary';
            inputRoles(definition).forEach(port => { const item = documentRef.createElement('div'); item.dataset.inputRole = port.id; item.textContent = `Input: ${port.id}${port.required ? ' *' : ''}`; summary.append(item); });
            outputSummary(definition).ports.forEach(port => { const item = documentRef.createElement('div'); item.dataset.outputRole = port.id; item.textContent = `Output: ${port.id}`; summary.append(item); });
            root.append(summary);
            const actions = declaredActions(definition, settings.actionRegistry);
            actions.forEach(action => { const button = documentRef.createElement('button'); button.type = 'button'; button.dataset.action = text(action.id); button.textContent = text(action.title, action.id); button.addEventListener('click', () => action.invoke?.({task, definition, binding: snapshot()})); root.append(button); });
            const workspace = declaredWorkspace(definition, settings.workspaceRegistry);
            if (workspace) { const item = documentRef.createElement('div'); item.className = 'workbench-skill-driven-presentation__workspace'; item.textContent = text(workspace.title, text(definition.workspace?.workspace_type)); root.append(item); }
            host.replaceChildren(root);
            return Object.freeze({element: root, destroy: () => root.remove()});
        }
        return Object.freeze({snapshot, setParameter, mount});
    }

    global.WorkbenchSkillDrivenPresentation = Object.freeze({create, properties, inputRoles, outputSummary});
}(window));
