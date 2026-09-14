/* Shared compact parameter presentation for generation/task cards.
   The host owns node mutation and persistence; this module only owns the
   summary/popover DOM and delegates every edit through onChange. */
(function exposeWorkbenchParameterPresentation(global) {
    'use strict';

    const DEFAULT_FIELDS = Object.freeze([
        {id: 'ratio', label: '比例', values: Object.freeze([
            ['square', '1:1'], ['portrait', '2:3'], ['landscape', '3:2'],
            ['portrait43', '3:4'], ['landscape43', '4:3'], ['story', '9:16'],
            ['wide', '16:9'], ['ultrawide', '21:9'], ['ultratall', '9:21'],
            ['source', '原图'], ['custom', '自定义'],
        ])},
        {id: 'resolution', label: '分辨率', values: Object.freeze([
            ['auto', '自动'], ['1k', '1K'], ['2k', '2K'], ['4k', '4K'], ['custom', '自定义'],
        ])},
        {id: 'count', label: '数量', value: node => Math.max(1, Math.min(8, Number(node?.count || 1))), values: Object.freeze(Array.from({length: 8}, (_, index) => [String(index + 1), `×${index + 1}`]))},
    ]);

    function text(value, fallback = '—') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function valueOf(node, field) {
        const result = typeof field.value === 'function' ? field.value(node) : node?.[field.id];
        return text(result);
    }

    function labelOf(field, value) {
        const match = (field.values || []).find(item => String(item[0]) === String(value));
        return match ? text(match[1]) : text(value);
    }

    function summary(node, fields = DEFAULT_FIELDS) {
        const source = node && typeof node === 'object' ? node : {};
        const items = fields.map(field => Object.freeze({
            id: field.id, label: text(field.label, field.id), value: valueOf(source, field),
            display: labelOf(field, valueOf(source, field)),
        }));
        return Object.freeze({items: Object.freeze(items), text: items.map(item => item.display).join(' · ')});
    }

    function create(options = {}) {
        const documentRef = options.document || global.document;
        const container = options.container;
        const node = options.node;
        const fields = Array.isArray(options.fields) && options.fields.length ? options.fields : DEFAULT_FIELDS;
        if (!documentRef || !container || !node) throw new TypeError('Parameter presentation requires document, container, and node');
        if (typeof options.onChange !== 'function') throw new TypeError('Parameter presentation requires onChange');
        const root = documentRef.createElement('section');
        root.className = 'workbench-parameter-presentation';
        root.setAttribute('data-parameter-presentation', '');
        const summaryButton = documentRef.createElement('button');
        summaryButton.type = 'button';
        summaryButton.className = 'workbench-parameter-summary';
        summaryButton.setAttribute('aria-haspopup', 'dialog');
        summaryButton.setAttribute('aria-expanded', 'false');
        const summaryLabel = documentRef.createElement('span');
        summaryLabel.className = 'workbench-parameter-summary__label';
        const summaryValue = documentRef.createElement('span');
        summaryValue.className = 'workbench-parameter-summary__value';
        summaryButton.append(summaryLabel, summaryValue);
        const popover = documentRef.createElement('div');
        popover.className = 'workbench-parameter-popover';
        popover.hidden = true;
        popover.setAttribute('role', 'dialog');
        popover.setAttribute('aria-label', '常用参数');
        const popoverTitle = documentRef.createElement('strong');
        popoverTitle.textContent = '常用参数';
        popover.append(popoverTitle);
        const fieldsHost = documentRef.createElement('div');
        fieldsHost.className = 'workbench-parameter-popover__fields';
        popover.append(fieldsHost);
        const advancedButton = documentRef.createElement('button');
        advancedButton.type = 'button';
        advancedButton.className = 'workbench-parameter-advanced';
        advancedButton.textContent = '高级参数';
        advancedButton.setAttribute('aria-expanded', 'false');
        root.append(summaryButton, popover, advancedButton);
        container.prepend(root);
        const advanced = typeof container.querySelector === 'function'
            ? container.querySelector(options.advancedSelector || '.gen-settings') : null;
        if (advanced) advanced.hidden = true;
        const controls = new Map();
        function refresh() {
            const model = summary(node, fields);
            summaryLabel.textContent = '参数';
            summaryValue.textContent = model.text;
            model.items.forEach(item => {
                const control = controls.get(item.id);
                if (control) control.value = item.value === '—' ? '' : item.value;
            });
            return model;
        }
        fields.forEach(field => {
            const label = documentRef.createElement('label');
            label.className = 'workbench-parameter-popover__field';
            const name = documentRef.createElement('span');
            name.textContent = text(field.label, field.id);
            const select = documentRef.createElement('select');
            select.dataset.parameterField = field.id;
            (field.values || []).forEach(option => {
                const optionRef = documentRef.createElement('option');
                optionRef.value = String(option[0]);
                optionRef.textContent = String(option[1]);
                select.append(optionRef);
            });
            select.addEventListener('mousedown', event => event.stopPropagation());
            select.addEventListener('click', event => event.stopPropagation());
            select.addEventListener('change', event => {
                event.stopPropagation(); options.onChange(field.id, event.target.value); refresh();
            });
            label.append(name, select); fieldsHost.append(label); controls.set(field.id, select);
        });
        summaryButton.addEventListener('mousedown', event => event.stopPropagation());
        summaryButton.addEventListener('click', event => {
            event.stopPropagation(); popover.hidden = !popover.hidden;
            summaryButton.setAttribute('aria-expanded', String(!popover.hidden));
        });
        advancedButton.addEventListener('mousedown', event => event.stopPropagation());
        advancedButton.addEventListener('click', event => {
            event.stopPropagation(); if (!advanced) return;
            advanced.hidden = !advanced.hidden;
            advancedButton.setAttribute('aria-expanded', String(!advanced.hidden));
            popover.hidden = true; summaryButton.setAttribute('aria-expanded', 'false');
        });
        refresh();
        return Object.freeze({root, popover, advanced, summary: () => summary(node, fields), refresh});
    }

    global.WorkbenchParameterPresentation = Object.freeze({DEFAULT_FIELDS, summary, create});
}(window));
