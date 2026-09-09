/* Neutral markup renderer for Comfy dynamic parameter fields. */
(function exposeComfyFieldRenderer(global) {
    'use strict';
    function kind(field) {
        if (['image', 'video', 'audio'].includes(field?.type)) return field.type;
        const key = `${field?.input || ''} ${field?.name || ''}`.toLowerCase();
        if (field?.type === 'textarea' || /prompt|text|提示词|正向|负向/.test(key)) return 'prompt';
        return 'setting';
    }
    function workflowName(name, workflows = []) {
        const values = Array.isArray(workflows) ? workflows : [];
        const requested = String(name || '');
        return values.some(workflow => workflow?.name === requested) ? requested : String(values[0]?.name || '');
    }
    function hasWorkflow(name, workflows = []) {
        const requested = String(name || '');
        return Array.isArray(workflows) && workflows.some(workflow => workflow?.name === requested);
    }
    async function loadWorkflow(name, workflows, cache, fetcher) {
        const selected = workflowName(name, workflows);
        if (!selected) return null;
        if (cache && cache[selected]) return cache[selected];
        const response = await fetcher(selected);
        if (!response || !response.ok) {
            if (cache) delete cache[selected];
            return null;
        }
        const data = await response.json();
        if (cache) cache[selected] = data;
        return data;
    }
    function create(options = {}) {
        const currentWorkflow = typeof options.currentWorkflow === 'function'
            ? options.currentWorkflow : (() => null);
        function fields(node, fieldKind = 'all') {
            const data = currentWorkflow(node);
            const values = data?.config?.fields || [];
            return fieldKind === 'all' ? values : values.filter(field => kind(field) === fieldKind);
        }
        function paramValue(node, field) {
            node.comfyParams = node.comfyParams || {};
            if (node.comfyParams[field.id] !== undefined) return node.comfyParams[field.id];
            return field.default ?? (field.type === 'boolean' ? false : (field.type === 'number' || field.type === 'slider' ? 0 : ''));
        }
        function randomEnabled(field) { return field?.type === 'number' && field.random_enabled === true; }
        function randomActive(node, fieldId) {
            node.comfyRandomActive = node.comfyRandomActive || {};
            return node.comfyRandomActive[fieldId] !== false;
        }
        function toggleRandomActive(state, fieldId) {
            const next = {...(state || {})};
            next[fieldId] = next[fieldId] === false;
            return Object.freeze(next);
        }
        function randomValue(field) {
            const isFloat = Number(field.step) > 0 && Number(field.step) < 1;
            let min = Number.isFinite(Number(field.min)) ? Number(field.min) : null;
            let max = Number.isFinite(Number(field.max)) ? Number(field.max) : null;
            const name = `${field.input || ''} ${field.name || ''}`.toLowerCase();
            const looksSeed = name.includes('seed') || name.includes('noise') || name.includes('随机') || name.includes('噪');
            if (min === null) min = looksSeed ? 1 : 0;
            if (max === null || max <= min) max = looksSeed ? 4294967295 : 999999;
            if (looksSeed) max = Math.min(max, 4294967295);
            const value = min + Math.random() * (max - min);
            if (isFloat) {
                const precision = Math.min(8, Math.max(1, String(field.step).split('.')[1]?.length || 2));
                return Number(value.toFixed(precision));
            }
            return Math.floor(value);
        }
        return Object.freeze({fields, paramValue, randomEnabled, randomActive, toggleRandomActive, randomValue});
    }
    function render(options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const id = e(options.id || '');
        const label = e(options.label || '');
        const type = options.type || 'text';
        if (type === 'boolean') return `<div class="gen-settings-row"><button type="button" class="setting-check ${options.active ? 'active' : ''}" data-comfy-param="${id}" data-comfy-type="boolean"><span class="check-dot"></span>${label}</button></div>`;
        if (type === 'slider') return `<div class="gen-settings-row"><label class="field" style="flex:1"><div class="setting-title" style="display:flex;justify-content:space-between"><span>${label}</span><span class="comfy-param-val">${e(options.value)}</span></div><input type="range" class="canvas-range" data-comfy-param="${id}" data-comfy-type="slider" min="${e(options.min)}" max="${e(options.max)}" step="${e(options.step)}" value="${e(options.value)}"></label></div>`;
        if (type === 'dropdown') return `<div class="gen-settings-row"><label class="field" style="flex:1"><div class="setting-title">${label}</div><select class="select-lite" data-comfy-param="${id}" data-comfy-type="dropdown" style="width:100%">${(options.options || []).map(option => `<option value="${e(option)}" ${String(options.value) === String(option) ? 'selected' : ''}>${e(option)}</option>`).join('') || '<option value="">(无选项)</option>'}</select></label></div>`;
        if (type === 'textarea') return `<div class="gen-settings-row"><label class="field" style="flex:1"><div class="setting-title">${label}</div><textarea class="setting-input" data-comfy-param="${id}" data-comfy-type="textarea" style="height:66px;padding-top:8px;resize:vertical">${e(options.value)}</textarea></label></div>`;
        if (options.random) return `<div class="gen-settings-row"><div class="comfy-random-field"><label class="field"><div class="setting-title">${label}</div><input class="setting-input" type="number" data-comfy-param="${id}" data-comfy-type="number" value="${e(options.value)}"></label><button class="tool-btn comfy-random-btn ${options.active ? 'active' : ''}" type="button" data-comfy-random="${id}" title="${options.active ? '随机已开启，点击关闭' : '随机已关闭，点击开启'}" aria-label="${options.active ? '随机已开启，点击关闭' : '随机已关闭，点击开启'}"><i data-lucide="dice-5" class="w-4 h-4"></i></button></div></div>`;
        return `<div class="gen-settings-row"><label class="field" style="flex:1"><div class="setting-title">${label}</div><input class="setting-input" type="${type === 'number' ? 'number' : 'text'}" data-comfy-param="${id}" data-comfy-type="${e(type)}" value="${e(options.value)}"></label></div>`;
    }
    global.WorkbenchCanvasComfyFieldRenderer = Object.freeze({create, kind, workflowName, hasWorkflow, loadWorkflow, render});
}(window));
