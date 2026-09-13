/* Result to Collection persistence client. The seam decides how a collected
   result is described and this client is the only place that talks to the
   versioned API, so the seam itself stays transport-free. */
(function exposeWorkbenchResultCollectionApiClient(global) {
    'use strict';

    function settingsOf(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const actorId = String(settings.actorId || '').trim();
        if (!actorId) throw new Error('result collection persistence requires a local actor id');
        return {actorId, fetch: settings.fetch || global.fetch};
    }

    function basePath(collectionId) {
        const collection = String(collectionId || '').trim();
        if (!collection) throw new TypeError('result collection persistence requires a collection id');
        return `/api/v1/collections/${encodeURIComponent(collection)}/results`;
    }

    async function failure(response) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail;
        return new Error(typeof detail === 'string' ? detail : detail?.message || `Result collection API request failed (${response.status})`);
    }

    async function add(collectionId, request, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = request && typeof request === 'object' ? request : {};
        if (!String(value.run_id || '').trim()) throw new TypeError('result collection requires a run id');
        const revision = Number(value.expected_revision);
        if (!Number.isInteger(revision) || revision < 1) throw new TypeError('result collection requires a positive expected revision');
        const body = {
            run_id: String(value.run_id).trim(),
            expected_revision: revision,
            column_key: String(value.column_key || '').trim() || 'result',
        };
        const response = await fetchImpl(basePath(collectionId), {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify(body),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    global.WorkbenchResultCollectionApiClient = Object.freeze({add});
}(window));
