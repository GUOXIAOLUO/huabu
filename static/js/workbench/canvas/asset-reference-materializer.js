/* Canvas-side seam for an AssetVersion drag. It carries identity only: the
 * canonical NodeCreationService persists the node and no file is copied. */
(function exposeAssetReferenceMaterializer(global) {
    'use strict';

    const DATA_TYPE = 'application/x-workbench-asset-version';

    function text(value) {
        return String(value ?? '').trim();
    }

    function reference(value) {
        if (!value || value.kind !== 'asset_version' || !text(value.asset_id) || !text(value.version_id)) return null;
        return Object.freeze({asset_id: text(value.asset_id), version_id: text(value.version_id)});
    }

    function payload(dataTransfer) {
        if (!dataTransfer || typeof dataTransfer.getData !== 'function') return null;
        let value;
        try { value = JSON.parse(dataTransfer.getData(DATA_TYPE) || '{}'); } catch (_) { return null; }
        const ref = reference(value);
        return ref ? Object.freeze({reference: ref, label: text(value.label, ref.version_id), type: text(value.type)}) : null;
    }

    function command(options) {
        const settings = options || {};
        const item = settings.payload && settings.payload.reference ? settings.payload : payload(settings.dataTransfer);
        if (!item) throw new TypeError('Asset reference payload is required');
        if (!text(settings.projectId) || !text(settings.canvasId)) throw new TypeError('Asset reference requires project and canvas ids');
        if (!settings.position || !Number.isFinite(Number(settings.position.x)) || !Number.isFinite(Number(settings.position.y))) throw new TypeError('Asset reference requires a finite position');
        return Object.freeze({
            projectId: text(settings.projectId), canvasId: text(settings.canvasId), source: 'asset_reference_drag',
            definitionRef: {type: 'legacy', id: 'image', version: '0'}, position: {x: Number(settings.position.x), y: Number(settings.position.y)},
            expectedRevision: settings.expectedRevision == null ? null : Number(settings.expectedRevision),
            title: item.label,
            initialConfig: {asset_version_ref: item.reference, mediaKind: item.type || 'file', name: item.label},
        });
    }

    function create(options) {
        const settings = options || {};
        if (typeof settings.createNode !== 'function') throw new TypeError('Asset reference materializer requires canonical createNode');
        return settings.createNode(command(settings));
    }

    global.WorkbenchAssetReferenceMaterializer = Object.freeze({DATA_TYPE, reference, payload, command, create});
}(window));
