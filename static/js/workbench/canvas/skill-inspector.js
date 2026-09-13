/* Definition-driven Skill details. Safe resource actions are injected by the
   host; this module never resolves or executes a Skill or an executor. */
(function exposeWorkbenchSkillInspector(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

    function list(value) { return Array.isArray(value) ? value : []; }

    function definitionInputs(definition) {
        const ports = list(definition?.ports?.inputs);
        if (ports.length) return ports.map(port => ({
            id: text(port.id, 'input'), label: text(port.title, text(port.label, text(port.id, 'Input'))),
            required: Boolean(port.required), accepts: list(port.accepts).map(item => text(item)).filter(Boolean),
        }));
        const properties = definition?.input_schema?.properties;
        return properties && typeof properties === 'object'
            ? Object.entries(properties).map(([id, schema]) => ({
                id, label: text(schema?.title, id), required: list(definition.input_schema.required).includes(id), accepts: schema?.type ? [schema.type] : [],
            })) : [];
    }

    function definitionOutputs(definition) {
        const ports = list(definition?.ports?.outputs);
        if (ports.length) return ports.map(port => ({
            id: text(port.id, 'output'), label: text(port.title, text(port.label, text(port.id, 'Output'))),
            produces: list(port.produces).map(item => text(item)).filter(Boolean),
        }));
        const properties = definition?.output_schema?.properties;
        return properties && typeof properties === 'object'
            ? Object.entries(properties).map(([id, schema]) => ({id, label: text(schema?.title, id), produces: schema?.type ? [schema.type] : []})) : [];
    }

    function parameterEntries(definition, binding) {
        const properties = definition?.parameter_schema?.properties;
        if (!properties || typeof properties !== 'object') return [];
        const parameters = binding?.parameters && typeof binding.parameters === 'object' ? binding.parameters : {};
        return Object.entries(properties).map(([id, schema]) => ({
            id, label: text(schema?.title, id), type: text(schema?.type, 'unknown'),
            value: parameters[id] ?? schema?.default ?? '未设置',
        }));
    }

    function packageInfo(definition) {
        const source = definition?.package && typeof definition.package === 'object' ? definition.package : {};
        return {
            id: text(source.package_id, text(source.id, text(definition?.package_id, text(definition?.packageId, '未声明')))),
            version: text(source.version, text(definition?.package_version, text(definition?.packageVersion, '未声明'))),
        };
    }

    function promptRefs(definition, binding) {
        const declared = definition?.prompt ? [definition.prompt] : (definition?.prompt_refs || definition?.promptRefs || definition?.prompts);
        const refs = list(declared).map(ref => {
            if (typeof ref === 'string') return {id: ref, version: ''};
            return {id: text(ref?.prompt_id, text(ref?.id, '')), version: text(ref?.version, '')};
        }).filter(ref => ref.id);
        const override = binding?.prompt_override;
        if (override && typeof override === 'object' && text(override.prompt_id)) {
            refs.push({id: text(override.prompt_id), version: text(override.version, ''), source: 'override'});
        }
        return refs;
    }

    function capabilities(definition) {
        return list(definition?.capability_requirements || definition?.capabilities || definition?.metadata?.capabilities)
            .map(item => typeof item === 'string' ? item : item?.id || item?.name).map(item => text(item)).filter(Boolean);
    }

    function create(options) {
        const settings = options || {};
        const definition = settings.definition;
        if (!definition || !text(definition.id) || !text(definition.version)) throw new TypeError('SkillInspector requires a versioned SkillDefinition');
        const binding = settings.binding && typeof settings.binding === 'object' ? settings.binding : {};
        const callbacks = {
            change: settings.onChangeSkill,
            open_resource: settings.onOpenResource,
        };

        function snapshot() {
            const packageRef = packageInfo(definition);
            return Object.freeze({
                skill: Object.freeze({id: text(definition.id), version: text(definition.version), title: text(definition.title, definition.id)}),
                binding: Object.freeze({skill_id: text(binding.skill_id, definition.id), version: text(binding.version, definition.version), enabled: binding.enabled !== false}),
                package: Object.freeze(packageRef),
                inputs: Object.freeze(definitionInputs(definition)),
                outputs: Object.freeze(definitionOutputs(definition)),
                parameters: Object.freeze(parameterEntries(definition, binding)),
                capabilities: Object.freeze(capabilities(definition)),
                promptRefs: Object.freeze(promptRefs(definition, binding)),
                actions: Object.freeze(Object.keys(callbacks).filter(id => typeof callbacks[id] === 'function').map(id => ({id, title: id === 'change' ? '更换 Skill' : '打开资源'}))),
            });
        }

        function invoke(actionId) {
            const action = callbacks[text(actionId)];
            if (typeof action !== 'function') throw new RangeError(`Unsupported Skill inspector action: ${actionId}`);
            return action({definition: clone(definition), binding: clone(binding)});
        }

        function mount(host, mountOptions = {}) {
            if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('SkillInspector requires a host');
            const documentRef = mountOptions.document || host.ownerDocument || global.document;
            if (!documentRef?.createElement) throw new TypeError('SkillInspector requires a document');
            const view = snapshot();
            const root = documentRef.createElement('section'); root.className = 'workbench-skill-inspector';
            root.dataset.skillId = view.skill.id; root.dataset.skillVersion = view.skill.version;
            const heading = documentRef.createElement('h3'); heading.textContent = view.skill.title; root.append(heading);
            function section(id, title, rows) {
                if (!rows.length) return;
                const element = documentRef.createElement('section'); element.className = 'workbench-skill-inspector__section'; element.dataset.inspectorSection = id;
                const label = documentRef.createElement('h4'); label.textContent = title; element.append(label);
                rows.forEach(row => { const item = documentRef.createElement('div'); item.className = 'workbench-skill-inspector__field'; item.dataset.field = row.id; item.textContent = `${row.label}: ${row.value}`; element.append(item); });
                root.append(element);
            }
            section('identity', 'Skill', [{id: 'version', label: '版本', value: view.skill.version}, {id: 'package', label: '包', value: `${view.package.id} · ${view.package.version}`}]);
            section('inputs', '输入', view.inputs.map(item => ({id: item.id, label: item.label, value: `${item.required ? '必填' : '可选'}${item.accepts.length ? ` · ${item.accepts.join(', ')}` : ''}`})));
            section('outputs', '输出', view.outputs.map(item => ({id: item.id, label: item.label, value: item.produces.join(', ') || '未声明'})));
            section('parameters', '参数', view.parameters.map(item => ({id: item.id, label: item.label, value: String(item.value)})));
            section('capabilities', '能力', view.capabilities.map((item, index) => ({id: `capability-${index}`, label: '能力', value: item})));
            section('prompts', 'Prompt 引用', view.promptRefs.map((item, index) => ({id: `prompt-${index}`, label: item.source === 'override' ? '覆盖' : 'Prompt', value: `${item.id}${item.version ? ` · ${item.version}` : ''}`})));
            const actions = documentRef.createElement('div'); actions.className = 'workbench-skill-inspector__actions';
            view.actions.forEach(action => { const button = documentRef.createElement('button'); button.type = 'button'; button.dataset.action = action.id; button.textContent = action.title; button.addEventListener('click', () => invoke(action.id)); actions.append(button); });
            if (view.actions.length) root.append(actions);
            host.replaceChildren(root);
            return Object.freeze({element: root, snapshot, invoke, destroy: () => root.remove()});
        }
        return Object.freeze({snapshot, invoke, mount});
    }

    global.WorkbenchSkillInspector = Object.freeze({create, definitionInputs, definitionOutputs});
}(window));
