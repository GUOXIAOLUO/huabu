/* Result preference persistence client. The seam decides what the user wants and
   this client is the only place that talks to the versioned API, so the seam
   itself stays transport-free. */
(function exposeWorkbenchResultSelectionApiClient(global) {
    'use strict';

    function settingsOf(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const actorId = String(settings.actorId || '').trim();
        if (!actorId) throw new Error('result selection persistence requires a local actor id');
        return {actorId, fetch: settings.fetch || global.fetch};
    }

    function basePath(runId) {
        const run = String(runId || '').trim();
        if (!run) throw new TypeError('result selection persistence requires a run id');
        return `/api/v1/execution-runs/${encodeURIComponent(run)}/selections`;
    }

    async function failure(response) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail;
        return new Error(typeof detail === 'string' ? detail : detail?.message || `Result selection API request failed (${response.status})`);
    }

    async function list(runId, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const response = await fetchImpl(basePath(runId), {method: 'GET', headers: {'X-User-ID': actorId}});
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    async function create(runId, record, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = record && typeof record === 'object' ? record : {};
        const response = await fetchImpl(basePath(runId), {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify({
                attempt_id: value.attempt_id,
                output_name: value.output_name,
                ordinal: value.ordinal,
                selected: Boolean(value.selected),
                favorite: Boolean(value.favorite),
                rating: value.rating ?? null,
                comment: value.comment ?? '',
                metadata: value.metadata ?? {},
            }),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    async function update(runId, selectionId, record, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = record && typeof record === 'object' ? record : {};
        const id = String(selectionId || '').trim();
        if (!id) throw new TypeError('result selection update requires a selection id');
        const revision = Number(value.revision);
        if (!Number.isInteger(revision) || revision < 1) throw new Error('result selection update requires a positive revision');
        const response = await fetchImpl(`${basePath(runId)}/${encodeURIComponent(id)}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify({
                expected_revision: revision,
                selected: Boolean(value.selected),
                favorite: Boolean(value.favorite),
                rating: value.rating ?? null,
                comment: value.comment ?? '',
                metadata: value.metadata ?? {},
            }),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    global.WorkbenchResultSelectionApiClient = Object.freeze({list, create, update});
}(window));
