/* Result to Canvas materialization persistence client. The seam decides how a
   materialized node is described and this client is the only place that talks to
   the versioned API, so the seam itself stays transport-free. */
(function exposeWorkbenchResultMaterializationApiClient(global) {
    'use strict';

    function settingsOf(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const actorId = String(settings.actorId || '').trim();
        if (!actorId) throw new Error('result materialization persistence requires a local actor id');
        return {actorId, fetch: settings.fetch || global.fetch};
    }

    function basePath(canvasId) {
        const canvas = String(canvasId || '').trim();
        if (!canvas) throw new TypeError('result materialization persistence requires a canvas id');
        return `/api/v1/canvases/${encodeURIComponent(canvas)}/result-nodes`;
    }

    async function failure(response) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail;
        return new Error(typeof detail === 'string' ? detail : detail?.message || `Result materialization API request failed (${response.status})`);
    }

    async function materialize(canvasId, request, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = request && typeof request === 'object' ? request : {};
        if (!String(value.request_id || '').trim()) throw new TypeError('result materialization requires a request id');
        if (!String(value.run_id || '').trim()) throw new TypeError('result materialization requires a run id');
        if (!String(value.attempt_id || '').trim()) throw new TypeError('result materialization requires an attempt id');
        if (!String(value.output_name || '').trim()) throw new TypeError('result materialization requires an output name');
        const ordinal = Number(value.ordinal);
        if (!Number.isInteger(ordinal) || ordinal < 0) throw new TypeError('result materialization requires a non-negative ordinal');
        const body = {
            request_id: String(value.request_id).trim(),
            project_id: String(value.project_id || '').trim(),
            run_id: String(value.run_id).trim(),
            attempt_id: String(value.attempt_id).trim(),
            output_name: String(value.output_name).trim(),
            ordinal,
            position: {x: Number(value.position?.x) || 0, y: Number(value.position?.y) || 0},
        };
        if (value.expected_revision !== undefined && value.expected_revision !== null && value.expected_revision !== '') {
            body.expected_revision = Number(value.expected_revision);
        }
        if (String(value.title || '').trim()) body.title = String(value.title).trim();
        const response = await fetchImpl(basePath(canvasId), {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify(body),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    global.WorkbenchResultMaterializationApiClient = Object.freeze({materialize});
}(window));
