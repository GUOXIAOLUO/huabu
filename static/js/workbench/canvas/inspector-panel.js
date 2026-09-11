/* The single right-side Inspector owner. Renderers contribute view-model
   sections through NodeInspector; this panel owns selection binding and DOM. */
(function exposeWorkbenchInspectorPanel(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function placeholder(id, title, label, value) {
        return {id, title, fields: [{id: `${id}-placeholder`, label, value}]};
    }

    function sectionsFor(model, single) {
        const sections = Array.isArray(model?.sections) ? [...model.sections] : [];
        if (single) sections.unshift(placeholder('metadata', '元数据', '节点 ID', model.nodeId || '未记录'));
        if (!sections.some(section => section?.id === 'history')) sections.push(placeholder('history', '历史', '记录', '暂无历史记录'));
        if (!sections.some(section => section?.id === 'version')) sections.push(placeholder('version', '版本', '版本', '未记录'));
        if (!sections.some(section => section?.id === 'execution')) sections.push(placeholder('execution', '执行', '记录', '暂无执行记录'));
        return sections;
    }

    function create(options) {
        const settings = options || {};
        const documentRef = settings.document || global.document;
        const root = settings.element;
        const inspector = settings.inspector || global.WorkbenchNodeInspector;
        if (!documentRef || !root || !inspector) throw new TypeError('InspectorPanel requires document, element, and NodeInspector');
        root.setAttribute('aria-label', '节点检查器');

        function clear() {
            root.replaceChildren();
            root.hidden = true;
            return null;
        }
        function render(nodes, context) {
            const records = Array.isArray(nodes) ? nodes.filter(Boolean) : [];
            if (!records.length) return clear();
            const single = records.length === 1;
            const model = single ? inspector.viewModel(records[0], context) : inspector.selectionViewModel(records);
            root.replaceChildren();
            root.hidden = false;
            const header = documentRef.createElement('header');
            header.className = 'workbench-inspector__header';
            const title = documentRef.createElement('strong');
            title.textContent = text(model.title, single ? '节点检查器' : '选择检查器');
            header.append(title);
            root.append(header);
            sectionsFor(model, single).forEach(section => {
                const sectionElement = documentRef.createElement('section');
                sectionElement.className = 'workbench-inspector__section';
                sectionElement.dataset.inspectorSection = text(section.id, 'section');
                const heading = documentRef.createElement('h3');
                heading.textContent = text(section.title, '信息');
                sectionElement.append(heading);
                (Array.isArray(section.fields) ? section.fields : []).forEach(item => {
                    const row = documentRef.createElement('div');
                    row.className = 'workbench-inspector__field';
                    const label = documentRef.createElement('span');
                    label.textContent = text(item.label, '字段');
                    const value = documentRef.createElement('span');
                    value.textContent = text(item.value, '—');
                    row.append(label, value);
                    sectionElement.append(row);
                });
                root.append(sectionElement);
            });
            return model;
        }
        return Object.freeze({element: root, render, clear});
    }

    global.WorkbenchInspectorPanel = Object.freeze({create});
}(window));
