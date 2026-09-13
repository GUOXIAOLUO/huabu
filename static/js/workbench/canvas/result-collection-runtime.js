/* Result to Collection for the Canvas. This seam owns how a produced result is
   described once it has been collected — the run and result identity an item
   carries — and how a request to collect is shaped before it is sent. It owns no
   transport, and it never creates a Canvas node: a result reaches a Collection
   directly, which is the whole point of the card.

   One boundary is deliberate. A result is named by four parts — the run, the
   attempt, the output name and that output's occurrence — because it is finer
   than the attempt that produced it and coarser than nothing. A request that
   names a Collection without a run, or a run without a Collection, is refused
   with a reason rather than sent, because a half-named request would silently
   populate the wrong Collection. */
(function exposeWorkbenchCanvasResultCollection(global) {
    'use strict';

    const COLLECTION_SCHEMA = 'workbench.collection/1';
    const REASONS = Object.freeze(['accepted', 'unknown_collection', 'unknown_run', 'bad_revision']);

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    /* One collected result, flattened to the shape this seam renders. Items that
       hold no result cell are ignored rather than rendered as empty rows. The
       column key is honoured because the API lets a caller choose it: a seam
       that only ever read `result` would silently render nothing for a
       Collection that collected under another key. */
    function recordFrom(input, columnKey) {
        const key = text(columnKey, 'result');
        const item = input && typeof input === 'object' ? input : {};
        const cell = item.values && typeof item.values === 'object'
            ? (item.values[key] ?? item[key] ?? null)
            : (item[key] ?? null);
        if (!cell || typeof cell !== 'object') return null;
        const runId = text(cell.run_id);
        const attemptId = text(cell.attempt_id);
        const outputName = text(cell.output_name);
        const raw = cell.ordinal;
        if (!runId || !attemptId || !outputName || raw === undefined || raw === null || raw === '') return null;
        const ordinal = Number(raw);
        if (!Number.isInteger(ordinal) || ordinal < 0) return null;
        return Object.freeze({
            id: text(item.id),
            order: Number.isInteger(Number(item.order)) ? Number(item.order) : 0,
            run_id: runId,
            attempt_id: attemptId,
            output_name: outputName,
            ordinal,
        });
    }

    /* Validate a collect request before it leaves. The expected revision must be
       a positive integer: appending is a write to a shared aggregate, so a
       caller that does not know the current revision has to go and look. */
    function requestFrom(input, columnKey) {
        const source = input && typeof input === 'object' ? input : {};
        if (!text(source.collection_id)) return Object.freeze({request: null, reason: 'unknown_collection'});
        if (!text(source.run_id)) return Object.freeze({request: null, reason: 'unknown_run'});
        const revision = Number(source.expected_revision);
        if (!Number.isInteger(revision) || revision < 1) return Object.freeze({request: null, reason: 'bad_revision'});
        const request = {
            collection_id: text(source.collection_id),
            run_id: text(source.run_id),
            expected_revision: revision,
            column_key: text(source.column_key, text(columnKey, 'result')),
        };
        return Object.freeze({request: Object.freeze(request), reason: 'accepted'});
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const columnKey = text(settings.columnKey, 'result');
        let current = '';
        let revision = 0;
        let items = [];
        let host = null;

        function emitChange() {
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function snapshot() {
            return Object.freeze({
                schema_version: COLLECTION_SCHEMA,
                collection_id: current,
                revision,
                items: Object.freeze(items.slice()),
                count: items.length,
            });
        }

        function hydrate(payload) {
            const body = payload && typeof payload === 'object' ? payload : {};
            current = text(body.collection_id ?? body.id);
            revision = Number(body.revision) || 0;
            items = Array.from(Array.isArray(body.items) ? body.items : [])
                .map(entry => recordFrom(entry, columnKey))
                .filter(Boolean)
                .sort((left, right) => left.order - right.order);
            render();
            return snapshot();
        }

        function rowHtml(record) {
            return `<li class="result-collection__row" data-result-id="${escapeHtml(record.id)}" data-result-run="${escapeHtml(record.run_id)}" data-result-attempt="${escapeHtml(record.attempt_id)}" data-result-output="${escapeHtml(record.output_name)}" data-result-ordinal="${escapeHtml(record.ordinal)}"><span class="result-collection__link">${escapeHtml(record.output_name)} #${escapeHtml(record.ordinal)}</span><span class="result-collection__from">${escapeHtml(record.run_id)}</span></li>`;
        }

        function render() {
            if (!host) return;
            const rows = items.map(rowHtml);
            host.setAttribute('data-result-collection', COLLECTION_SCHEMA);
            host.innerHTML = `<div class="workbench-result-collection__head"><strong>Collected</strong><span>${items.length} result${items.length === 1 ? '' : 's'}</span></div>${rows.length ? `<ul class="workbench-result-collection__rows">${rows.join('')}</ul>` : '<p class="is-empty">Nothing collected yet</p>'}`;
            emitChange();
        }

        function mount(target) {
            if (!target) throw new TypeError('Result collection requires a host');
            host = target;
            render();
            return Object.freeze({
                element: host, snapshot, hydrate,
                requestFrom: input => requestFrom(input, columnKey),
                destroy: () => { host.innerHTML = ''; host.removeAttribute('data-result-collection'); host = null; },
            });
        }

        return Object.freeze({
            snapshot, hydrate,
            requestFrom: input => requestFrom(input, columnKey),
            mount,
        });
    }

    global.WorkbenchCanvasResultCollection = Object.freeze({
        COLLECTION_SCHEMA, REASONS, create, recordFrom, requestFrom,
    });
}(window));
