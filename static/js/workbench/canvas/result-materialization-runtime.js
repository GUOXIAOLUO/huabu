/* Result to Canvas materialization. This seam owns how a materialized result
   node is described — which run, attempt, output and occurrence it stands for —
   and how a request to materialize is shaped before it is sent. It owns no
   transport, and it never materializes anything by itself: a node appears only
   because a caller named one result and asked, which is the whole point of the
   card.

   Two boundaries are deliberate. Every part of the result's address is
   required, because naming an attempt without an output, or an output without
   its occurrence, would put a node on the Canvas that points at a different
   result than the caller meant. And the request carries its own idempotency key
   rather than being given one here: only the caller knows whether it is asking
   for the first time or asking again. */
(function exposeWorkbenchCanvasResultMaterialization(global) {
    'use strict';

    const NODE_SCHEMA = 'workbench.node/1';
    const REASONS = Object.freeze([
        'accepted', 'unknown_canvas', 'unknown_request', 'unknown_run', 'unknown_result', 'bad_ordinal', 'bad_position',
    ]);

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    /* One materialized node, flattened to the shape this seam renders. A node
       that carries no result lineage is ignored rather than rendered as an empty
       row: the node is not a result node if it does not know which result it
       stands for. */
    function recordFrom(input) {
        const node = input && typeof input === 'object' ? input : {};
        const source = node.node && typeof node.node === 'object' ? node.node : node;
        const result = source.config && typeof source.config === 'object' ? source.config.result : null;
        if (!result || typeof result !== 'object') return null;
        const runId = text(result.run_id);
        const attemptId = text(result.attempt_id);
        const outputName = text(result.output_name);
        const raw = result.ordinal;
        if (!runId || !attemptId || !outputName || raw === undefined || raw === null || raw === '') return null;
        const ordinal = Number(raw);
        if (!Number.isInteger(ordinal) || ordinal < 0) return null;
        return Object.freeze({
            id: text(source.id),
            title: text(source.title, `${outputName} #${ordinal}`),
            run_id: runId,
            attempt_id: attemptId,
            output_name: outputName,
            ordinal,
            canvas_id: text(source.canvas_id),
            provenance_ref: text(source.provenance_ref),
        });
    }

    /* Validate a materialization request before it leaves. The position is
       required to be real geometry rather than defaulted: a node that silently
       lands at the origin is a node nobody can find. */
    function requestFrom(input) {
        const source = input && typeof input === 'object' ? input : {};
        if (!text(source.canvas_id)) return Object.freeze({request: null, reason: 'unknown_canvas'});
        if (!text(source.request_id)) return Object.freeze({request: null, reason: 'unknown_request'});
        if (!text(source.run_id)) return Object.freeze({request: null, reason: 'unknown_run'});
        if (!text(source.attempt_id) || !text(source.output_name)) return Object.freeze({request: null, reason: 'unknown_result'});
        const ordinal = Number(source.ordinal);
        if (!Number.isInteger(ordinal) || ordinal < 0) return Object.freeze({request: null, reason: 'bad_ordinal'});
        const position = source.position && typeof source.position === 'object' ? source.position : {};
        const x = Number(position.x);
        const y = Number(position.y);
        if (!Number.isFinite(x) || !Number.isFinite(y)) return Object.freeze({request: null, reason: 'bad_position'});
        const request = {
            request_id: text(source.request_id),
            project_id: text(source.project_id),
            run_id: text(source.run_id),
            attempt_id: text(source.attempt_id),
            output_name: text(source.output_name),
            ordinal,
            position: {x, y},
        };
        if (source.expected_revision !== undefined && source.expected_revision !== null && source.expected_revision !== '') {
            request.expected_revision = Number(source.expected_revision);
        }
        if (text(source.title)) request.title = text(source.title);
        return Object.freeze({request: Object.freeze(request), reason: 'accepted'});
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        let canvasId = '';
        let revision = 0;
        let nodes = [];
        let host = null;

        function emitChange() {
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function snapshot() {
            return Object.freeze({
                schema_version: NODE_SCHEMA,
                canvas_id: canvasId,
                revision,
                nodes: Object.freeze(nodes.slice()),
                count: nodes.length,
            });
        }

        function hydrate(payload) {
            const body = payload && typeof payload === 'object' ? payload : {};
            const created = body.node && typeof body.node === 'object' ? body.node : null;
            canvasId = text(created?.canvas_id, text(body.canvas_id, canvasId));
            revision = Number(body.canvas_revision) || revision;
            const record = created ? recordFrom(created) : null;
            if (record) nodes = nodes.filter(entry => entry.id !== record.id).concat([record]);
            render();
            return snapshot();
        }

        function rowHtml(record) {
            return `<li class="result-materialization__row" data-result-node="${escapeHtml(record.id)}" data-result-run="${escapeHtml(record.run_id)}" data-result-attempt="${escapeHtml(record.attempt_id)}" data-result-output="${escapeHtml(record.output_name)}" data-result-ordinal="${escapeHtml(record.ordinal)}"><span class="result-materialization__link">${escapeHtml(record.title)}</span><span class="result-materialization__from">${escapeHtml(record.attempt_id)}</span></li>`;
        }

        function render() {
            if (!host) return;
            const rows = nodes.map(rowHtml);
            host.setAttribute('data-result-materialization', NODE_SCHEMA);
            host.innerHTML = `<div class="workbench-result-materialization__head"><strong>On canvas</strong><span>${nodes.length} result${nodes.length === 1 ? '' : 's'}</span></div>${rows.length ? `<ul class="workbench-result-materialization__rows">${rows.join('')}</ul>` : '<p class="is-empty">Nothing materialized yet</p>'}`;
            emitChange();
        }

        function mount(target) {
            if (!target) throw new TypeError('Result materialization requires a host');
            host = target;
            render();
            return Object.freeze({
                element: host, snapshot, hydrate, requestFrom,
                destroy: () => { host.innerHTML = ''; host.removeAttribute('data-result-materialization'); host = null; },
            });
        }

        return Object.freeze({snapshot, hydrate, requestFrom, mount});
    }

    global.WorkbenchCanvasResultMaterialization = Object.freeze({
        NODE_SCHEMA, REASONS, create, recordFrom, requestFrom,
    });
}(window));
