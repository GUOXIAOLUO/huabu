/* Shared browser-side compatibility helpers.  This file intentionally has no DOM or storage side effects. */
(function exposeWorkbenchCanvas(global) {
    'use strict';

    const STATES = Object.freeze([
        'draft', 'ready', 'missing_input', 'queued', 'running', 'waiting_user',
        'waiting_approval', 'completed', 'failed', 'outdated', 'frozen',
    ]);

    function asNumber(value, fallback) {
        const number = Number(value);
        return Number.isFinite(number) ? number : fallback;
    }

    function asRevision(value, fallback) {
        const number = Math.floor(asNumber(value, fallback));
        return number >= 1 ? number : fallback;
    }

    function legacyNodeView(node, context) {
        const source = node && typeof node === 'object' ? node : {};
        const nodeType = String(source.type || 'unknown');
        const assetType = nodeType === 'image' || nodeType === 'smart-image';
        const collectionType = nodeType === 'collection';
        const collection = source.collection || source.config?.collection || source.extensions?.collection?.payload || source.extensions?.legacy?.payload?.collection;
        const stateChangedAt = source.state_changed_at || source.stateChangedAt || source.status_updated_at || source.statusUpdatedAt || null;
        const inputBindings = Array.isArray(source.input_bindings)
            ? source.input_bindings.filter(binding => binding && typeof binding === 'object').map(binding => ({...binding}))
            : Array.isArray(source.inputNodeIds)
                ? source.inputNodeIds.filter(Boolean).map(nodeId => ({node_id: String(nodeId)}))
                : [];
        const outputRefs = Array.isArray(source.output_refs)
            ? source.output_refs.filter(reference => reference && typeof reference === 'object').map(reference => ({...reference}))
            : [];
        return {
            schema_version: 'workbench.node/1',
            id: String(source.id || ''),
            project_id: String((context && context.projectId) || ''),
            canvas_id: String((context && context.canvasId) || ''),
            kind: assetType ? 'asset' : collectionType ? 'collection' : 'legacy',
            definition_ref: {type: 'legacy', id: nodeType, version: '0'},
            renderer: {id: 'legacy', version: '1'},
            state: STATES.includes(source.state) ? source.state : 'ready',
            title: String(source.name || source.title || nodeType),
            revision: asRevision(source.revision, 1),
            provenance_ref: source.provenance_ref ? String(source.provenance_ref) : null,
            created_by: source.created_by ? String(source.created_by) : '',
            position: {x: asNumber(source.x, 0), y: asNumber(source.y, 0)},
            size: {width: asNumber(source.w, 280), height: asNumber(source.h, 180)},
            input_bindings: inputBindings,
            output_refs: outputRefs,
            metadata: {inspector_origin_label: '兼容画布', state_changed_at: stateChangedAt},
            extensions: {legacy: {payload: source}},
            ...(collection ? {collection} : {}),
        };
    }

    global.WorkbenchCanvas = Object.freeze({
        NODE_SCHEMA_VERSION: 'workbench.node/1',
        STATES,
        isNodeState: value => STATES.includes(value),
        legacyNodeView,
    });
}(window));
