/* Shared Canvas-record persistence boundary for temporary editor adapters.

   Canonical-first transport: while SQLite authority is active, full-canvas
   saves use the logical-revision CAS API and this client owns the revision
   cursor (fed by load/save responses and by adoptRevision after versioned
   writes). The legacy updated_at transport remains the explicit fallback for
   a revision-less state or when the canonical API reports 503; updated_at is
   display/compat metadata only and never the normal CAS cursor. */
(function exposeCanvasPersistenceClient(global) {
    'use strict';

    const revisionCursors = new Map();

    function legacyPath(canvasId) {
        if (!canvasId) throw new Error('A Canvas id is required.');
        return `/api/canvases/${encodeURIComponent(canvasId)}`;
    }

    // Kept as the routed-compat path name; the canonical CAS API lives under /api/v1.
    const canvasPath = legacyPath;

    function canonicalPath(canvasId) {
        if (!canvasId) throw new Error('A Canvas id is required.');
        return `/api/v1/canvases/${encodeURIComponent(canvasId)}`;
    }

    function rememberRevision(canvasId, revision) {
        const value = Number(revision) || 0;
        if (canvasId && value > 0) revisionCursors.set(String(canvasId), value);
    }

    function canonicalPayload(record) {
        const payload = {...(record || {})};
        delete payload.base_updated_at;   // timestamp cursor: display/compat only
        delete payload.client_id;         // transport metadata, not canvas payload
        delete payload.expected_revision;
        return payload;
    }

    async function requestPath(path, options) {
        const response = await fetch(path, options);
        const payload = await response.json().catch(() => ({}));
        const detail = payload && payload.detail && typeof payload.detail === 'object' ? payload.detail : {};
        return {
            ok: response.ok,
            status: response.status,
            canvas: detail.canvas || payload.canvas || null,
            updatedAt: Number(detail.updated_at || payload.updated_at || detail.canvas?.updated_at || payload.canvas?.updated_at || 0) || 0,
            revision: Number(detail.current_revision || payload.revision || 0) || 0,
            payload,
        };
    }

    // One owner for adopting a server-provided Canvas revision after a versioned
    // write: a positive server revision wins, the current revision is kept when
    // the write returned none, and missingFallback covers a revision-less canvas.
    // A positive revision also feeds the canonical save cursor so the next
    // full-canvas save participates in the same logical-revision CAS.
    function adoptRevision(canvas, revision, missingFallback) {
        const value = Number(revision) || 0;
        const current = Number(canvas && canvas.updated_at) || 0;
        const adopted = value > 0 ? value : (current > 0 ? current : Number(missingFallback) || 0);
        if (canvas) canvas.updated_at = adopted;
        if (value > 0) rememberRevision(canvas && canvas.id, value);
        return adopted;
    }

    async function load(canvasId) {
        const canonical = await requestPath(canonicalPath(canvasId), {method: 'GET'});
        if (canonical.status === 503) return requestPath(canvasPath(canvasId), {method: 'GET'});
        rememberRevision(canvasId, canonical.revision);
        return canonical;
    }

    async function save(canvasId, record) {
        const expected = Number(revisionCursors.get(String(canvasId)) || (record && record.expected_revision) || 0);
        if (expected > 0) {
            const canonical = await requestPath(canonicalPath(canvasId), {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({payload: canonicalPayload(record), expected_revision: expected, client_id: String(record?.client_id || '')}),
            });
            if (canonical.status !== 503) {
                rememberRevision(canvasId, canonical.revision);
                return canonical;
            }
        }
        return requestPath(canvasPath(canvasId), {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(record),
        });
    }

    global.WorkbenchCanvasPersistence = Object.freeze({
        load,
        metadata: canvasId => requestPath(`${canonicalPath(canvasId)}/meta`, {method: 'GET'})
            .then(canonical => canonical.status === 503
                ? requestPath(`${canvasPath(canvasId)}/meta`, {method: 'GET'})
                : canonical),
        save,
        adoptRevision,
        revisionOf: canvasId => Number(revisionCursors.get(String(canvasId)) || 0),
    });
}(window));
