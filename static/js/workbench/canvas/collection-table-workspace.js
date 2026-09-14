/* Generic Collection table workspace. It owns an editable presentation copy;
   canonical Collection persistence stays behind the injected save callback. */
(function exposeWorkbenchCollectionTableWorkspace(global) {
    'use strict';

    const VALUE_TYPES = new Set(['asset_version', 'artifact_version', 'entity_ref', 'entity_version', 'collection', 'literal']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) { return JSON.parse(JSON.stringify(value)); }

    function collectionOf(node) {
        return node?.collection || node?.config?.collection || node?.extensions?.collection?.payload
            || node?.extensions?.legacy?.payload?.collection || null;
    }

    function isCompatible(node) {
        const collection = collectionOf(node);
        return Boolean(collection && typeof collection === 'object' && Array.isArray(collection.items)
            && collection.schema && Array.isArray(collection.schema.columns));
    }

    function ordered(items) { return [...items].sort((left, right) => Number(left.order || 0) - Number(right.order || 0)); }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!isCompatible(node)) throw new TypeError('CollectionTableWorkspace requires a Collection NodeRecord');
        let working = clone(collectionOf(node));
        let original = clone(working);
        let filterText = '';
        let sortKey = '';
        let sortDirection = 'asc';
        let dirty = false;
        let selectedRowId = text(settings.selectedRowId);

        function markDirty() {
            dirty = true;
            settings.session?.markDirty?.(true);
            settings.onChange?.(snapshot());
        }

        function visibleRows() {
            let rows = ordered(working.items);
            if (filterText) {
                const needle = filterText.toLowerCase();
                rows = rows.filter(row => Object.values(row.values || {}).some(cell => JSON.stringify(cell).toLowerCase().includes(needle)));
            }
            if (sortKey) {
                const direction = sortDirection === 'desc' ? -1 : 1;
                rows = [...rows].sort((left, right) => String(left.values?.[sortKey]?.value ?? left.values?.[sortKey]?.reference_id ?? '')
                    .localeCompare(String(right.values?.[sortKey]?.value ?? right.values?.[sortKey]?.reference_id ?? ''), undefined, {numeric: true}) * direction);
            }
            return rows;
        }

        function snapshot() {
            return Object.freeze({
                nodeId: text(node.id), collection: Object.freeze(clone(working)),
                columns: Object.freeze(clone(working.schema.columns)), rows: Object.freeze(clone(visibleRows())),
                filterText, sortKey, sortDirection, dirty, selectedRowId,
            });
        }

        function columnFor(key) {
            const column = working.schema.columns.find(candidate => candidate.key === text(key));
            if (!column) throw new RangeError(`unknown collection column: ${key}`);
            return column;
        }

        function rowFor(id) {
            const row = working.items.find(candidate => candidate.id === text(id));
            if (!row) throw new RangeError(`unknown collection row: ${id}`);
            return row;
        }

        function cellFor(column, value) {
            if (column.value_type === 'literal') return {type: 'literal', value};
            if (!value || typeof value !== 'object' || text(value.type, 'reference') !== 'reference' || !text(value.reference_id)) {
                throw new TypeError(`column ${column.key} requires a ${column.value_type} reference`);
            }
            if (text(value.reference_type) !== column.value_type) {
                throw new TypeError(`column ${column.key} requires a ${column.value_type} reference`);
            }
            return {type: 'reference', reference_type: column.value_type, reference_id: text(value.reference_id), metadata: clone(value.metadata || {})};
        }

        function setCell(rowId, columnKey, value) {
            const row = rowFor(rowId);
            const column = columnFor(columnKey);
            row.values[column.key] = cellFor(column, value);
            markDirty();
            return snapshot();
        }

        function addRow(row) {
            const next = row || {};
            const id = text(next.id);
            if (!id || working.items.some(item => item.id === id)) throw new TypeError('collection row id must be unique');
            const maxOrder = working.items.reduce((max, item) => Math.max(max, Number(item.order) || 0), 0);
            const values = {};
            Object.entries(next.values || {}).forEach(([key, value]) => { values[columnFor(key).key] = cellFor(columnFor(key), value); });
            working.items.push({id, order: Number.isInteger(next.order) ? next.order : maxOrder + 1, values, metadata: clone(next.metadata || {})});
            markDirty();
            return snapshot();
        }

        function addColumn(column) {
            const next = column || {};
            const key = text(next.key);
            const valueType = text(next.value_type);
            if (!key || !text(next.id) || !text(next.label) || !VALUE_TYPES.has(valueType) || working.schema.columns.some(item => item.key === key)) {
                throw new TypeError('collection column requires unique id/key, label, and supported value_type');
            }
            working.schema.columns.push({id:text(next.id), key, label:text(next.label), value_type:valueType, required:Boolean(next.required), metadata:clone(next.metadata || {})});
            markDirty();
            return snapshot();
        }

        function setFilter(value) { filterText = text(value); return snapshot(); }
        function sortBy(columnKey, direction = 'asc') { if (columnKey) columnFor(columnKey); sortKey = text(columnKey); sortDirection = direction === 'desc' ? 'desc' : 'asc'; return snapshot(); }
        function selectRow(rowId) {
            const id = text(rowId);
            rowFor(id);
            selectedRowId = id;
            settings.onSelectRow?.(rowId, snapshot());
            return snapshot();
        }
        function save() {
            if (!dirty) return snapshot();
            if (typeof settings.persist !== 'function') throw new Error('collection workspace persistence is unavailable');
            const result = settings.persist(clone(working));
            const finish = saved => {
                if (saved && typeof saved === 'object' && isCompatible({collection:saved})) {
                    working = clone(saved);
                    original = clone(saved);
                }
                dirty = false; settings.session?.save?.(); settings.onChange?.(snapshot()); return snapshot();
            };
            return result && typeof result.then === 'function' ? result.then(finish) : finish(result);
        }
        function discard() {
            working = clone(original); dirty = false; settings.session?.discard?.(); settings.onChange?.(snapshot()); return snapshot();
        }

        function bindingProjection(options) {
            if (!global.WorkbenchBindingTable) throw new Error('binding table projection is unavailable');
            return global.WorkbenchBindingTable.projectCollection(working, options);
        }
        function rowBindings(rowId, options) {
            const row = rowFor(rowId);
            if (!global.WorkbenchBindingTable) throw new Error('binding table projection is unavailable');
            return global.WorkbenchBindingTable.projectRow(row, working.schema, options);
        }

        return Object.freeze({snapshot, setCell, addRow, addColumn, setFilter, sortBy, selectRow, save, discard, bindingProjection, rowBindings});
    }

    function mount(host, workspace, options) {
        if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('CollectionTableWorkspace requires a host');
        const settings = options || {};
        const documentRef = settings.document || host.ownerDocument || global.document;
        const root = documentRef.createElement('section');
        root.className = 'workbench-collection-table-workspace';
        let feedback = '';
        function actionButton(action, label, handler) {
            const button = documentRef.createElement('button');
            button.type = 'button'; button.dataset.action = action; button.textContent = label;
            button.addEventListener('click', event => { event.preventDefault(); handler(); });
            return button;
        }
        function nextId(prefix, values) {
            let index = values.length + 1;
            let candidate = `${prefix}-${index}`;
            while (values.some(value => value === candidate)) { index += 1; candidate = `${prefix}-${index}`; }
            return candidate;
        }
        const render = () => {
            const state = workspace.snapshot();
            root.replaceChildren();
            const toolbar = documentRef.createElement('div');
            toolbar.className = 'workbench-collection-table-workspace__toolbar';
            const filter = documentRef.createElement('input');
            filter.type = 'search'; filter.value = state.filterText; filter.placeholder = 'Filter rows';
            filter.addEventListener('input', () => { workspace.setFilter(filter.value); render(); });
            toolbar.append(filter);
            toolbar.append(
                actionButton('add-row', 'Add row', () => {
                    const collection = workspace.snapshot().collection;
                    workspace.addRow({id:nextId('row', collection.items.map(item => item.id))});
                    feedback = ''; render();
                }),
                actionButton('add-column', 'Add column', () => {
                    const collection = workspace.snapshot().collection;
                    const id = nextId('column', collection.schema.columns.map(column => column.id));
                    const key = nextId('column', collection.schema.columns.map(column => column.key));
                    workspace.addColumn({id, key, label:`Column ${collection.schema.columns.length + 1}`, value_type:'literal'});
                    feedback = ''; render();
                }),
                actionButton('discard', 'Discard', () => {
                    workspace.discard(); feedback = 'Changes discarded'; render();
                }),
                actionButton('save', 'Save', () => {
                    Promise.resolve(workspace.save()).then(() => { feedback = 'Saved'; render(); }).catch(error => { feedback = String(error?.message || error); render(); });
                }),
            );
            const status = documentRef.createElement('output');
            status.className = 'workbench-collection-table-workspace__status';
            status.setAttribute('aria-live', 'polite'); status.textContent = feedback || (state.dirty ? 'Unsaved changes' : '');
            toolbar.append(status);
            const table = documentRef.createElement('table');
            table.className = 'workbench-collection-table';
            const head = documentRef.createElement('thead');
            const headRow = documentRef.createElement('tr');
            state.columns.forEach(column => { const cell = documentRef.createElement('th'); cell.textContent = column.label; cell.dataset.columnKey = column.key; cell.addEventListener('click', () => { workspace.sortBy(column.key, state.sortKey === column.key && state.sortDirection === 'asc' ? 'desc' : 'asc'); render(); }); headRow.append(cell); });
            head.append(headRow); table.append(head);
            const body = documentRef.createElement('tbody');
            state.rows.forEach(row => { const rowElement = documentRef.createElement('tr'); rowElement.dataset.rowId = row.id; rowElement.setAttribute('aria-selected', String(row.id === state.selectedRowId)); if (row.id === state.selectedRowId) rowElement.className = 'is-selected'; rowElement.addEventListener('click', () => { workspace.selectRow(row.id); render(); }); state.columns.forEach(column => { const cell = documentRef.createElement('td'); const input = documentRef.createElement('input'); const value = row.values?.[column.key]; input.value = value?.type === 'literal' ? String(value.value ?? '') : String(value?.reference_id ?? ''); input.dataset.rowId = row.id; input.dataset.columnKey = column.key; input.addEventListener('click', event => event.stopPropagation()); input.addEventListener('change', () => { workspace.setCell(row.id, column.key, column.value_type === 'literal' ? input.value : {type:'reference', reference_type:column.value_type, reference_id:input.value}); render(); }); cell.append(input); rowElement.append(cell); }); body.append(rowElement); });
            table.append(body); root.append(toolbar, table); host.replaceChildren(root);
        };
        render();
        return Object.freeze({element:root, workspace, destroy:() => root.remove()});
    }

    global.WorkbenchCollectionTableWorkspace = Object.freeze({collectionOf, isCompatible, create, mount});
}(window));
