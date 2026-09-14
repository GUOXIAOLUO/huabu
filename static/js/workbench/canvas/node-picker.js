/* Shared searchable Node Picker projection. It filters CreationCatalog entries
   and emits a definition-backed selection; the host owns the creation command. */
(function exposeWorkbenchNodePicker(global) {
    'use strict';

    function text(value, fallback = '') {
        return typeof value === 'string' && value.trim() ? value.trim() : fallback;
    }

    function list(value) {
        return Object.freeze(Array.from(new Set((Array.isArray(value) ? value : []).map(item => text(item)).filter(Boolean))));
    }

    function normalize(entry) {
        if (!entry || typeof entry !== 'object') throw new TypeError('Node Picker entry must be an object');
        const definition = entry.definition_ref;
        if (!definition || typeof definition !== 'object') throw new TypeError('Node Picker entry requires definition_ref');
        const metadata = entry.metadata && typeof entry.metadata === 'object' ? entry.metadata : {};
        const normalized = {
            id: text(entry.id),
            definition_ref: Object.freeze({id:text(definition.id), type:text(definition.type), version:text(definition.version)}),
            order: Number.isFinite(entry.order) ? entry.order : 0,
            metadata: Object.freeze({
                ...metadata,
                title:text(metadata.title, text(definition.id, text(entry.id))),
                description:text(metadata.description),
                category:text(metadata.category, '其他'),
                keywords:list(metadata.keywords),
                capabilities:list(metadata.capabilities),
                package:metadata.package && typeof metadata.package === 'object' ? Object.freeze({...metadata.package}) : Object.freeze({id:'core', version:'builtin'}),
                canvasKinds:list(metadata.canvasKinds),
            }),
        };
        if (!normalized.id || !normalized.definition_ref.id || !normalized.definition_ref.type || !normalized.definition_ref.version) throw new TypeError('Node Picker entry identity is incomplete');
        return Object.freeze(normalized);
    }

    function searchText(entry) {
        const metadata = entry.metadata || {};
        const packageRef = metadata.package || {};
        return [entry.id, entry.definition_ref.id, metadata.title, metadata.description, metadata.category,
            ...(metadata.keywords || []), ...(metadata.capabilities || []), packageRef.id, packageRef.version].join(' ').toLocaleLowerCase();
    }

    function filterEntries(entries, {query = '', category = 'all'} = {}) {
        const needle = text(query).toLocaleLowerCase();
        return Object.freeze(entries.filter(entry => {
            const metadata = entry.metadata || {};
            return (category === 'all' || metadata.category === category) && (!needle || searchText(entry).includes(needle));
        }));
    }

    function create(options) {
        const settings = options || {};
        const documentRef = settings.document;
        const container = settings.container;
        if (!documentRef || !container) throw new TypeError('Node Picker requires document and container');
        let entries = Object.freeze((settings.entries || []).map(normalize).sort((left, right) => left.order - right.order || left.id.localeCompare(right.id)));
        let state = {query:'', category:'all', open:false};

        function label(key, fallback) { return text(settings.labels?.[key], fallback); }
        function element(tag, className, content) {
            const node = documentRef.createElement(tag);
            if (className) node.className = className;
            if (content !== undefined) node.textContent = content;
            return node;
        }
        function render() {
            container.replaceChildren();
            if (!state.open) { container.classList.remove('open'); return Object.freeze({visible:[], category:state.category, query:state.query}); }
            const panel = element('div', 'node-picker-panel');
            const search = element('input', 'node-picker-search');
            search.type = 'search'; search.placeholder = label('searchPlaceholder', '搜索节点…'); search.value = state.query;
            search.setAttribute('aria-label', label('searchLabel', '搜索节点'));
            search.addEventListener('input', event => {
                state = {...state, query:event.target.value};
                render();
                const refreshedSearch = container.querySelector?.('.node-picker-search');
                refreshedSearch?.focus?.();
                refreshedSearch?.setSelectionRange?.(state.query.length, state.query.length);
            });
            panel.appendChild(search);
            const categories = Object.freeze(['all', ...Array.from(new Set(entries.map(entry => entry.metadata.category)))]);
            const categoryBar = element('div', 'node-picker-categories');
            categories.forEach(category => {
                const button = element('button', 'node-picker-category', category === 'all' ? label('allCategory', '全部') : category);
                button.type = 'button'; button.dataset.category = category; button.setAttribute('aria-pressed', String(state.category === category));
                button.addEventListener('click', event => { event.preventDefault(); state = {...state, category}; render(); });
                categoryBar.appendChild(button);
            });
            panel.appendChild(categoryBar);
            const listEl = element('div', 'node-picker-list');
            const visible = filterEntries(entries, state);
            visible.forEach(entry => {
                const metadata = entry.metadata;
                const button = element('button', 'node-picker-item');
                button.type = 'button'; button.dataset.nodePickerEntry = entry.id;
                button.setAttribute('aria-label', metadata.title);
                const icon = element('i', 'node-picker-item-icon');
                icon.dataset.lucide = metadata.icon || 'box';
                const body = element('span', 'node-picker-item-body');
                body.appendChild(element('strong', 'node-picker-item-title', metadata.title));
                body.appendChild(element('span', 'node-picker-item-description', metadata.description));
                const meta = element('span', 'node-picker-item-meta', `${metadata.category} · ${metadata.package?.id || 'core'}`);
                body.appendChild(meta); button.appendChild(icon); button.appendChild(body);
                button.addEventListener('click', event => { event.preventDefault(); if (typeof settings.onSelect === 'function') settings.onSelect(entry); });
                listEl.appendChild(button);
            });
            if (!visible.length) listEl.appendChild(element('div', 'node-picker-empty', label('empty', '没有匹配的节点')));
            panel.appendChild(listEl); container.appendChild(panel); container.classList.add('open');
            if (typeof settings.refreshIcons === 'function') settings.refreshIcons();
            return Object.freeze({visible:visible.map(entry => entry.id), category:state.category, query:state.query});
        }
        function open(next = {}) { state = {...state, open:true, query:text(next.query, state.query), category:text(next.category, state.category)}; container.style.left = `${Number(next.x) || 0}px`; container.style.top = `${Number(next.y) || 0}px`; return render(); }
        function close() { state = {...state, open:false}; return render(); }
        function setEntries(next) { entries = Object.freeze((next || []).map(normalize).sort((left, right) => left.order - right.order || left.id.localeCompare(right.id))); return render(); }
        return Object.freeze({open, close, render, setEntries, filter:query => filterEntries(entries, query)});
    }

    global.WorkbenchNodePicker = Object.freeze({create, filterEntries, normalize});
}(window));
