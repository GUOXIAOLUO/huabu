/* Explicit selected-result -> Asset transport. The selection runtime exposes
 * the user action; this adapter alone talks to the canonical R9-11 endpoint.
 * Content is a declared AssetVersionContent reference, never bytes invented in
 * the Canvas UI. */
(function exposeWorkbenchResultAssetMaterializationApiClient(global) {
    'use strict';

    function text(value) { return String(value ?? '').trim(); }

    function settingsOf(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const actorId = text(settings.actorId);
        if (!actorId) throw new Error('result asset materialization requires a local actor id');
        return {actorId, fetch: settings.fetch || global.fetch};
    }

    function path(runId) {
        const value = text(runId);
        if (!value) throw new TypeError('result asset materialization requires a run id');
        return `/api/v1/execution-runs/${encodeURIComponent(value)}/assets`;
    }

    function contentOf(value) {
        const content = value && typeof value === 'object' ? value : {};
        if (!text(content.location) || !text(content.checksum) || !text(content.mime_type)) {
            throw new TypeError('result asset materialization requires declared content');
        }
        const size = Number(content.size_bytes);
        if (!Number.isInteger(size) || size < 0) throw new TypeError('result asset materialization requires a valid content size');
        return {location: text(content.location), checksum: text(content.checksum), mime_type: text(content.mime_type), size_bytes: size};
    }

    async function failure(response) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail;
        return new Error(typeof detail === 'string' ? detail : detail?.message || `Result asset materialization API request failed (${response.status})`);
    }

    async function materialize(runId, result, options) {
        const {actorId, fetch: fetchImpl} = settingsOf(options);
        const value = result && typeof result === 'object' ? result : {};
        const attemptId = text(value.attempt_id);
        const outputName = text(value.output_name);
        if (!attemptId || !outputName) throw new TypeError('result asset materialization requires a result identity');
        const ordinal = Number(value.ordinal);
        if (!Number.isInteger(ordinal) || ordinal < 0) throw new TypeError('result asset materialization requires a non-negative ordinal');
        const projectId = text(value.project_id || options?.projectId);
        if (!projectId) throw new TypeError('result asset materialization requires a project id');
        const body = {
            project_id: projectId,
            attempt_id: attemptId,
            output_name: outputName,
            ordinal,
            title: text(value.title, `${outputName} #${ordinal}`),
            type: text(value.type, 'other'),
            content: contentOf(value.content),
            metadata: value.metadata && typeof value.metadata === 'object' ? value.metadata : {},
        };
        const response = await fetchImpl(path(runId), {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: JSON.stringify(body),
        });
        if (!response.ok) throw await failure(response);
        return response.json();
    }

    function createHandler(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const runId = text(settings.runId);
        const projectId = text(settings.projectId);
        if (!runId || !projectId || typeof settings.contentFor !== 'function') {
            throw new TypeError('result asset materialization handler requires run, project, and content resolver');
        }
        return record => materialize(runId, {
            ...record,
            project_id: projectId,
            title: text(record?.title, `${text(record?.output_name)} #${Number(record?.ordinal)}`),
            type: text(settings.type, 'other'),
            content: settings.contentFor(record),
            metadata: typeof settings.metadataFor === 'function' ? settings.metadataFor(record) : settings.metadata,
        }, settings).then(result => {
            if (typeof settings.onMaterialized === 'function') settings.onMaterialized(result, record);
            return result;
        });
    }

    global.WorkbenchResultAssetMaterializationApiClient = Object.freeze({materialize, createHandler});
}(window));
