/* Execution branch persistence client. The seam decides how lineage is described
   and this client is the only place that talks to the versioned API, so the seam
   itself stays transport-free. */
(function exposeWorkbenchExecutionBranchApiClient(global) {
    'use strict';

    function settingsOf(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const actorId = String(settings.actorId || '').trim();
        if (!actorId) throw new Error('execution branch persistence requires a local actor id');
        return {actorId, fetch: settings.fetch || global.fetch};
    }

    function basePath(runId) {
        const run = String(runId || '').trim();
        if (!run) throw new TypeError('execution branch persistence requires a run id');
        return `/api/v1/execution-runs/${encodeURIComponent(run)}/branches`;
    }

    async function failure(response) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail;
        return new Error(typeof detail === 'string' ? detail : detail?.message || `Execution branch API request failed (${response.status})`);
    }

    async function list(runId, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const response = await fetchImpl(basePath(runId), {method: 'GET', headers: {'X-User-ID': actorId}});
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    async function lineage(runId, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const run = String(runId || '').trim();
        if (!run) throw new TypeError('execution branch persistence requires a run id');
        const response = await fetchImpl(`/api/v1/execution-runs/${encodeURIComponent(run)}/lineage`, {method: 'GET', headers: {'X-User-ID': actorId}});
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    async function create(runId, request, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = request && typeof request === 'object' ? request : {};
        if (!String(value.run_id || '').trim()) throw new TypeError('execution branch create requires a run id');
        const body = {metadata: value.metadata ?? {}};
        if (value.policy_override && typeof value.policy_override === 'object') body.policy_override = value.policy_override;
        if (value.source_attempt_id) {
            body.source_attempt_id = value.source_attempt_id;
            body.source_output_name = value.source_output_name;
            body.source_ordinal = value.source_ordinal;
        }
        const response = await fetchImpl(basePath(runId), {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify(body),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    global.WorkbenchExecutionBranchApiClient = Object.freeze({list, lineage, create});
}(window));
