/* Canonical Collection persistence client. Canvas passes editable projections
   here; the versioned API remains the application save boundary. */
(function exposeWorkbenchCollectionApiClient(global) {
    'use strict';

    async function update(collection, options) {
        const value = collection && typeof collection === 'object' ? collection : null;
        const settings = options || {};
        const actorId = String(settings.actorId || '').trim();
        if (!value || !String(value.id || '').trim()) throw new TypeError('collection id is required');
        if (!actorId) throw new Error('collection persistence requires a local actor id');
        const revision = Number(value.revision);
        if (!Number.isInteger(revision) || revision < 1) throw new Error('collection persistence requires a positive revision');
        const response = await (settings.fetch || global.fetch)(`/api/v1/collections/${encodeURIComponent(value.id)}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify({
                expected_revision: revision,
                name: value.name,
                schema: value.schema,
                items: value.items,
                default_view: value.default_view,
                metadata: value.metadata,
            }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = payload?.detail;
            throw new Error(typeof detail === 'string' ? detail : detail?.message || `Collection API request failed (${response.status})`);
        }
        return payload;
    }

    async function create(collection, options) {
        const value = collection && typeof collection === 'object' ? collection : null;
        const settings = options || {};
        const actorId = String(settings.actorId || '').trim();
        if (!value || !String(value.project_id || '').trim()) throw new TypeError('collection project id is required');
        if (!actorId) throw new Error('collection persistence requires a local actor id');
        const response = await (settings.fetch || global.fetch)('/api/v1/collections', {
            method:'POST', headers:{'Content-Type':'application/json', 'X-User-ID':actorId}, body:JSON.stringify(value),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload?.detail?.message || payload?.detail || `Collection API request failed (${response.status})`);
        return payload;
    }

    global.WorkbenchCollectionApiClient = Object.freeze({create, update});
}(window));
