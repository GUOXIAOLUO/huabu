/* Generic pre-run view for a frozen ExecutionInputProjection. It owns only
   preview state and policy validation; execution and resource mutation stay
   with the caller. */
(function exposeWorkbenchExecutionInputPreview(global) {
    'use strict';

    const MODES = Object.freeze(['single', 'batch', 'map']);

    function clone(value) {
        if (value == null || typeof value !== 'object') return value;
        if (typeof structuredClone === 'function') return structuredClone(value);
        return JSON.parse(JSON.stringify(value));
    }

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function normalizePolicy(source) {
        const input = source && typeof source === 'object' ? source : {};
        const policy = {
            mode: MODES.includes(input.mode) ? input.mode : 'single',
            concurrency: Number.isInteger(input.concurrency) ? input.concurrency : 1,
            start_index: Number.isInteger(input.start_index) ? input.start_index : 0,
            limit: input.limit == null || input.limit === '' ? null : Number(input.limit),
            retry: Number.isInteger(input.retry) ? input.retry : 0,
            timeout: Number(input.timeout ?? 300),
            order: input.order === 'completion' ? 'completion' : 'input',
            continue_on_error: Boolean(input.continue_on_error),
        };
        if (policy.mode === 'single') policy.concurrency = 1;
        return policy;
    }

    function policyErrors(policy, itemCount) {
        const errors = [];
        if (!Number.isInteger(policy.concurrency) || policy.concurrency < 1) errors.push('concurrency must be at least 1');
        if (policy.mode === 'single' && policy.concurrency !== 1) errors.push('single mode requires concurrency=1');
        if (!Number.isInteger(policy.start_index) || policy.start_index < 0) errors.push('start index must be non-negative');
        if (policy.start_index >= itemCount && itemCount > 0) errors.push('start index is outside the input items');
        if (policy.limit != null && (!Number.isInteger(policy.limit) || policy.limit < 1)) errors.push('limit must be at least 1');
        if (!Number.isInteger(policy.retry) || policy.retry < 0) errors.push('retry must be non-negative');
        if (!Number.isFinite(policy.timeout) || policy.timeout <= 0) errors.push('timeout must be greater than 0');
        return errors;
    }

    function normalize(projection, policy) {
        const source = projection && typeof projection === 'object' ? projection : {};
        const inputs = Array.isArray(source.inputs) ? source.inputs : [];
        const errors = Array.isArray(source.errors) ? source.errors : [];
        const missing = errors.map((error, index) => ({
            input_id: text(error?.binding_id, `missing-${index + 1}`),
            binding_id: text(error?.binding_id, ''), role: 'missing', target: '',
            source_type: 'missing', source_ref: '', missing: true,
            message: text(error?.message, 'input is unavailable'),
        }));
        const items = inputs.map((input, index) => ({
            input_id: text(input?.input_id, `input-${index + 1}`),
            binding_id: text(input?.binding_id, ''), role: text(input?.role, 'input'),
            target: text(input?.target, ''), source_type: text(input?.source_type, 'literal'),
            source_ref: text(input?.source_ref, ''), missing: false,
            order: Number.isInteger(input?.order) ? input.order : index, value: clone(input?.value),
        }));
        const normalizedPolicy = normalizePolicy(policy);
        const schedulingErrors = policyErrors(normalizedPolicy, items.length);
        return {
            schema_version: text(source.schema_version, 'workbench.execution-input-projection/1'),
            items: [...items, ...missing], missing, policy: normalizedPolicy,
            policyErrors: schedulingErrors,
            valid: source.valid !== false && errors.length === 0,
            executable: source.valid !== false && errors.length === 0 && items.length > 0 && schedulingErrors.length === 0,
        };
    }

    function escapeHtml(value) {
        return text(value).replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
    }

    function create(options) {
        const settings = options || {};
        let state = normalize(settings.projection, settings.policy);
        let host = null;
        function snapshot() { return clone(state); }
        function emitChange() { if (typeof settings.onChange === 'function') settings.onChange(snapshot()); }
        function render() {
            if (!host) return;
            const rows = state.items.map((item, index) => `<li class="workbench-execution-preview__item ${item.missing ? 'is-missing' : ''}"><span class="item-index">${index + 1}</span><span class="item-role">${escapeHtml(item.role)}</span><span class="item-target">${escapeHtml(item.target || item.source_type)}</span><span class="item-state">${escapeHtml(item.missing ? item.message : item.source_ref || 'ready')}</span></li>`).join('');
            const policyErrors = state.policyErrors.map(error => `<li>${escapeHtml(error)}</li>`).join('');
            host.innerHTML = `<div class="workbench-execution-preview__head"><strong>Execution preview</strong><span>${state.items.length} item(s)</span></div><div class="workbench-execution-preview__summary"><span>Ready: ${state.items.filter(item => !item.missing).length}</span><span>Missing: ${state.missing.length}</span></div><ol class="workbench-execution-preview__items">${rows || '<li class="is-empty">No concrete inputs</li>'}</ol><div class="workbench-execution-preview__policy"><label>Mode <select data-policy="mode"><option value="single" ${state.policy.mode === 'single' ? 'selected' : ''}>single</option><option value="batch" ${state.policy.mode === 'batch' ? 'selected' : ''}>batch</option><option value="map" ${state.policy.mode === 'map' ? 'selected' : ''}>map</option></select></label><label>Concurrency <input data-policy="concurrency" type="number" min="1" value="${state.policy.concurrency}"></label><label>Start index <input data-policy="start_index" type="number" min="0" value="${state.policy.start_index}"></label></div>${state.policyErrors.length ? `<ul class="workbench-execution-preview__errors">${policyErrors}</ul>` : ''}<button type="button" data-execution-preview-start ${state.executable ? '' : 'disabled'}>Start run</button>`;
            host.querySelectorAll('[data-policy]').forEach(control => control.addEventListener('change', () => updatePolicy({[control.dataset.policy]: control.dataset.policy === 'mode' ? control.value : Number(control.value)})));
            host.querySelector('[data-execution-preview-start]')?.addEventListener('click', () => { if (state.executable && typeof settings.onStart === 'function') settings.onStart(snapshot()); });
        }
        function updatePolicy(patch) {
            if (!patch || typeof patch !== 'object') throw new TypeError('Execution preview policy patch is required');
            state = normalize(settings.projection, {...state.policy, ...patch});
            render(); emitChange(); return snapshot();
        }
        function mount(target) {
            if (!target) throw new TypeError('Execution preview requires a host');
            host = target; host.setAttribute('data-execution-input-preview', ''); render();
            return Object.freeze({element: host, snapshot, updatePolicy, destroy: () => { host.innerHTML = ''; host = null; }});
        }
        return Object.freeze({snapshot, updatePolicy, mount});
    }

    global.WorkbenchExecutionInputPreview = Object.freeze({MODES, normalize, create});
}(window));
