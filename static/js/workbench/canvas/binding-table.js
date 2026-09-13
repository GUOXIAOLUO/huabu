/* Collection-backed Binding Table projection. This is pure data logic: it
   creates typed InputBinding payloads but owns no execution or graph edges. */
(function exposeWorkbenchBindingTable(global) {
    'use strict';

    const VALUE_TYPES = new Set(['asset_version', 'artifact_version', 'entity_ref', 'entity_version', 'collection', 'literal']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function cellSource(cell, column) {
        if (!cell || typeof cell !== 'object') return null;
        if (cell.type === 'reference' && column.value_type !== 'literal' && text(cell.reference_type) === text(column.value_type) && VALUE_TYPES.has(text(cell.reference_type))) {
            return {source_type:cell.reference_type, source_ref:text(cell.reference_id)};
        }
        if (cell.type === 'literal' && column.value_type === 'literal') {
            return {source_type:'literal', source_ref:JSON.stringify(cell.value)};
        }
        return null;
    }

    function columnRole(column, options) {
        const metadata = column?.metadata || {};
        const role = typeof options?.roleForColumn === 'function' ? options.roleForColumn(column) : metadata.input_role || metadata.inputRole || column?.key;
        return text(role);
    }

    function columnTarget(column, options) {
        const metadata = column?.metadata || {};
        const target = typeof options?.targetForColumn === 'function' ? options.targetForColumn(column) : metadata.input_target || metadata.inputTarget || column?.key;
        return text(target);
    }

    function projectRow(row, schema, options) {
        const item = row || {};
        const columns = Array.isArray(schema?.columns) ? schema.columns : [];
        const values = item.values || {};
        const missingRequired = columns.filter(column => column.required && !values[column.key]).map(column => column.key);
        const invalidCells = [];
        const bindings = [];
        columns.forEach((column, index) => {
            const cell = values[column.key];
            if (!cell) return;
            const source = cellSource(cell, column);
            if (!source || !source.source_ref) { invalidCells.push(column.key); return; }
            const role = columnRole(column, options);
            const target = columnTarget(column, options);
            if (!role || !target) { invalidCells.push(column.key); return; }
            bindings.push({
                id:`${text(item.id, 'row')}:${text(column.key, `column-${index}`)}`,
                target, source_type:source.source_type, source_ref:source.source_ref,
                role, order:index, enabled:true, metadata:{row_id:text(item.id), column_key:text(column.key)},
            });
        });
        return Object.freeze({rowId:text(item.id), valid:missingRequired.length === 0 && invalidCells.length === 0, missingRequired:Object.freeze(missingRequired), invalidCells:Object.freeze(invalidCells), bindings:Object.freeze(bindings)});
    }

    function projectCollection(collection, options) {
        const value = collection || {};
        const rows = [...(value.items || [])].sort((left, right) => Number(left.order || 0) - Number(right.order || 0));
        const projections = rows.map(row => projectRow(row, value.schema, options));
        return Object.freeze({valid:projections.every(row => row.valid), rows:Object.freeze(projections), bindings:Object.freeze(projections.flatMap(row => row.bindings))});
    }

    global.WorkbenchBindingTable = Object.freeze({projectRow, projectCollection});
}(window));
