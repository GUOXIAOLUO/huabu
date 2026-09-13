/* Execution branch lineage for the Canvas. This seam owns how a run's ancestry
   is described and turned into rows, and how a regeneration request is shaped
   before it is sent; it owns no transport, and it never executes anything, so a
   branch is always a decision recorded rather than work started.

   Two boundaries are deliberate. A run descends from at most one source, so the
   lineage is a chain and not a graph: nothing here merges branches. And naming
   the result a regeneration came from means naming all three parts of that
   result — the attempt, the output name and that output's occurrence — which is
   the identity the Result Tray stages and Result Selection rates, so a partial
   name is refused rather than silently completed. */
(function exposeWorkbenchCanvasExecutionBranch(global) {
    'use strict';

    const BRANCH_SCHEMA = 'workbench.execution-branch/1';
    const REASONS = Object.freeze(['accepted', 'partial_result', 'unknown_run']);

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    /* The source result a regeneration came from, or null when the whole run was
       reused. Naming any part without the others is refused: a half-named result
       would point at the wrong candidate. */
    function resultIdentityOf(source) {
        const item = source && typeof source === 'object' ? source : {};
        const attemptId = text(item.source_attempt_id ?? item.attempt_id);
        const outputName = text(item.source_output_name ?? item.output_name);
        const raw = item.source_ordinal ?? item.ordinal;
        const named = [attemptId, outputName, raw];
        const blank = raw === undefined || raw === null || raw === '';
        if (!attemptId && !outputName && blank) return {identity: null};
        const ordinal = Number(raw);
        if (!attemptId || !outputName || !Number.isInteger(ordinal) || ordinal < 0) return {error: 'partial_result'};
        return {identity: {attempt_id: attemptId, output_name: outputName, ordinal}};
    }

    function hasResultLineage(entry) {
        return Boolean(text(entry.source_attempt_id ?? entry.attempt_id));
    }

    /* One persisted branch record, flattened to the shape this seam renders. */
    function recordFrom(input) {
        const source = input && typeof input === 'object' ? input : {};
        const runId = text(source.run_id);
        const sourceRunId = text(source.source_run_id);
        if (!runId || !sourceRunId) return null;
        return Object.freeze({
            id: text(source.id),
            run_id: runId,
            source_run_id: sourceRunId,
            kind: text(source.kind, 'regenerate'),
            result: hasResultLineage(source) ? resultIdentityOf(source).identity || null : null,
            created_at: text(source.created_at),
        });
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        let current = '';
        let ancestors = [];
        let children = [];
        let host = null;

        function emitChange() {
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function snapshot() {
            return Object.freeze({
                schema_version: BRANCH_SCHEMA,
                run_id: current,
                ancestors: Object.freeze(ancestors.slice()),
                children: Object.freeze(children.slice()),
                depth: ancestors.length,
                count: children.length,
            });
        }

        /* Accept what persistence holds: the chain this run descends from and the
           branches taken from it. Records that cannot name both ends are ignored
           rather than half-keyed. */
        function hydrate(payload) {
            const body = payload && typeof payload === 'object' ? payload : {};
            current = text(body.run_id ?? body.current);
            const read = key => Array.from(Array.isArray(body[key]) ? body[key] : [])
                .map(recordFrom)
                .filter(Boolean);
            ancestors = read('lineage');
            children = read('branches');
            render();
            return snapshot();
        }

        function setRun(runId) {
            current = text(runId);
            render();
            return snapshot();
        }

        /* Validate a regeneration request before it leaves: a partial result name
           would silently point at the wrong candidate. */
        function requestFrom(input) {
            const source = input && typeof input === 'object' ? input : {};
            if (!text(source.run_id)) return Object.freeze({request: null, reason: 'unknown_run'});
            const outcome = resultIdentityOf(source);
            if (outcome.error) return Object.freeze({request: null, reason: outcome.error});
            const request = {run_id: text(source.run_id)};
            if (outcome.identity) Object.assign(request, {
                source_attempt_id: outcome.identity.attempt_id,
                source_output_name: outcome.identity.output_name,
                source_ordinal: outcome.identity.ordinal,
            });
            if (source.policy_override && typeof source.policy_override === 'object') {
                request.policy_override = source.policy_override;
            }
            return Object.freeze({request: Object.freeze(request), reason: 'accepted'});
        }

        function rowHtml(record, kind) {
            const result = record.result
                ? `${escapeHtml(record.result.output_name)} #${escapeHtml(record.result.ordinal)}`
                : '';
            return `<li class="execution-branch__row" data-branch-kind="${kind}" data-branch-id="${escapeHtml(record.id)}" data-branch-run="${escapeHtml(record.run_id)}" data-branch-source="${escapeHtml(record.source_run_id)}" data-branch-result="${escapeHtml(result)}"><span class="execution-branch__link">${escapeHtml(record.source_run_id)} &rarr; ${escapeHtml(record.run_id)}</span></li>`;
        }

        function render() {
            if (!host) return;
            const rows = ancestors.map(entry => rowHtml(entry, 'ancestor'))
                .concat(children.map(entry => rowHtml(entry, 'child')));
            host.setAttribute('data-execution-branch', BRANCH_SCHEMA);
            host.innerHTML = `<div class="workbench-execution-branch__head"><strong>Lineage</strong><span>${ancestors.length} up, ${children.length} down</span></div>${rows.length ? `<ul class="workbench-execution-branch__rows">${rows.join('')}</ul>` : '<p class="is-empty">This run has no branches yet</p>'}`;
            emitChange();
        }

        function mount(target) {
            if (!target) throw new TypeError('Execution branch requires a host');
            host = target;
            render();
            return Object.freeze({element: host, snapshot, hydrate, setRun, requestFrom, destroy: () => { host.innerHTML = ''; host.removeAttribute('data-execution-branch'); host = null; }});
        }

        return Object.freeze({snapshot, hydrate, setRun, requestFrom, mount});
    }

    global.WorkbenchCanvasExecutionBranch = Object.freeze({
        BRANCH_SCHEMA, REASONS, create, recordFrom, resultIdentityOf, hasResultLineage,
    });
}(window));
