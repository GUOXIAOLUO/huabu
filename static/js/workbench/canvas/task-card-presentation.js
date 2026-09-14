/* Shared, definition-driven Task/LLM card presentation. It owns only the
   compact card hierarchy; TaskRichNode owns state and the page supplies the
   persistence/execution callbacks. */
(function exposeWorkbenchTaskCardPresentation(global) {
    'use strict';

    const OUTPUT_MODES = Object.freeze(['text', 'list', 'structured']);
    function text(value, fallback = '') { const normalized = String(value ?? '').trim(); return normalized || fallback; }
    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }
    function outputMode(value) { return OUTPUT_MODES.includes(value) ? value : 'text'; }
    function inputLabel(input, index) {
        if (!input || typeof input !== 'object') return `输入 ${index + 1}`;
        return text(input.name, text(input.label, text(input.title, text(input.role, `输入 ${index + 1}`))));
    }
    function create(options) {
        const settings = options || {}, task = settings.task;
        if (!task || typeof task.state !== 'function' || typeof task.update !== 'function') throw new TypeError('TaskCardPresentation requires a TaskRichNode');
        let host = null, mounted = [];
        function state() { return task.state(); }
        function binding() { const value = state().skillBinding; return value && typeof value === 'object' ? value : {}; }
        function skillTitle() { const current = state(); return text(current.definition?.title, text(current.skill, text(binding().skill_id, '选择 Skill'))); }
        function modelTitle() { const resolved = state().modelSelection?.resolved; return text(resolved?.model_ref, text(resolved?.model, text(settings.modelLabel, '自动选择模型'))); }
        function element(tag, className, label) {
            const item = (host.ownerDocument || settings.document).createElement(tag);
            if (className) item.className = className;
            if (label !== undefined) item.textContent = label;
            return item;
        }
        function button(className, label, onClick) {
            const item = element('button', className, label); item.type = 'button';
            item.addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); onClick(event); });
            return item;
        }
        function section(className, title) { const item = element('section', className); item.append(element('h4', 'workbench-task-card__section-title', title)); return item; }
        function render() {
            if (!host) return null;
            mounted.forEach(item => item?.destroy?.()); mounted = [];
            const current = state(), root = element('article', 'workbench-task-card'); root.dataset.taskNodeId = text(current.nodeId);
            const header = element('header', 'workbench-task-card__header'), identity = element('div', 'workbench-task-card__identity');
            identity.append(element('div', 'workbench-task-card__title', text(current.title, 'Task')), element('div', 'workbench-task-card__subtitle', skillTitle()));
            header.append(identity, element('span', 'workbench-task-card__status', text(current.status, 'draft'))); root.append(header);
            root.append(element('div', 'workbench-task-card__route', `${text(settings.routeLabel, '平台 / 路由')} · ${modelTitle()}`));
            const inputs = section('workbench-task-card__inputs', '输入资源'), inputList = element('div', 'workbench-task-card__input-list');
            const values = Array.isArray(current.inputs) ? current.inputs : [];
            if (!values.length) inputList.append(element('span', 'workbench-task-card__empty', '连接资源或添加输入'));
            values.forEach((input, index) => { const chip = element('span', 'workbench-task-card__input-chip', inputLabel(input, index)); chip.dataset.inputIndex = String(index); inputList.append(chip); });
            inputs.append(inputList); root.append(inputs);
            const prompt = section('workbench-task-card__prompt-section', 'Prompt'), promptInput = element('textarea', 'workbench-task-card__prompt');
            promptInput.value = text(current.prompt); promptInput.placeholder = text(settings.promptPlaceholder, '输入任务提示词…'); promptInput.setAttribute('aria-label', 'Prompt');
            promptInput.addEventListener('input', () => task.update({prompt: promptInput.value})); prompt.append(promptInput); root.append(prompt);
            const controls = element('div', 'workbench-task-card__controls'), skill = element('label', 'workbench-task-card__skill-label', `Skill · ${skillTitle()}`), toggle = element('input');
            toggle.type = 'checkbox'; toggle.checked = binding().enabled !== false; toggle.addEventListener('change', () => task.update({skillBinding: {...clone(binding()), enabled: toggle.checked}})); skill.prepend(toggle); controls.append(skill);
            const modes = element('div', 'workbench-task-card__output-mode');
            OUTPUT_MODES.forEach(name => { const active = outputMode(current.outputMode) === name; const item = button(`workbench-task-card__mode ${active ? 'is-active' : ''}`, name === 'text' ? '文本' : name === 'list' ? '列表' : '结构化', () => { task.update({outputMode: name}); render(); }); item.dataset.outputMode = name; item.setAttribute('aria-pressed', String(active)); modes.append(item); });
            controls.append(modes); root.append(controls);
            if (settings.skillSelectorOptions && task.mountSkillSelector) {
                const selectorHost = element('div', 'workbench-task-card__skill-selector');
                root.append(selectorHost); mounted.push(task.mountSkillSelector(selectorHost, settings.skillSelectorOptions));
            } else {
                // Keep the reference hierarchy visible without inventing a
                // Skill candidate when the application has not injected its
                // canonical registry yet.
                const selectorHost = element('div', 'workbench-task-card__skill-selector');
                const label = element('label', 'workbench-task-card__skill-selector-label', 'Skill');
                const select = element('select', 'workbench-task-card__skill-selector-select');
                select.setAttribute('aria-label', 'Skill'); select.disabled = true;
                const option = element('option', '', `${skillTitle()} · 等待 Skill Registry`); option.selected = true;
                select.append(option); label.append(select); selectorHost.append(label); root.append(selectorHost);
            }
            if (settings.skillPresentationOptions && task.mountSkillPresentation && current.definition) { const presentationHost = element('div', 'workbench-task-card__skill-presentation'); root.append(presentationHost); mounted.push(task.mountSkillPresentation(presentationHost, {...settings.skillPresentationOptions, definition: current.definition, binding: binding()})); }
            if (settings.modelSelectorOptions && task.mountModelSelector) { const modelHost = element('div', 'workbench-task-card__model-selector'); root.append(modelHost); mounted.push(task.mountModelSelector(modelHost, settings.modelSelectorOptions)); }
            const footer = element('footer', 'workbench-task-card__footer'), run = button('workbench-task-card__run', text(settings.runLabel, '生成'), () => settings.onRun?.({task, state: state()}));
            run.disabled = typeof settings.onRun !== 'function'; footer.append(run); root.append(footer); host.replaceChildren(root); return root;
        }
        function mount(target) { if (!target || typeof target.replaceChildren !== 'function') throw new TypeError('TaskCardPresentation requires a host'); host = target; return render(); }
        return Object.freeze({mount, render, outputModes: OUTPUT_MODES});
    }
    global.WorkbenchTaskCardPresentation = Object.freeze({create, outputModes: OUTPUT_MODES, outputMode});
}(window));
