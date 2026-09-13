/* Side-by-side comparison of staged run results. The workspace owns only a
   bounded selection over candidates that are still run results, the metadata
   shown for each one, and the layout that puts them next to each other. It
   never promotes a result into a Canvas node, never mutates the graph, and
   never persists.

   Comparison is deliberately unscored: candidates are ordered by the order the
   user selected them, and no candidate is ranked, weighted, or preferred. The
   preview body is not re-implemented here either — it is asked of the result
   preview registry, which owns result rendering. */
(function exposeWorkbenchCanvasResultCompare(global) {
    'use strict';

    const COMPARE_SCHEMA = 'workbench.result-compare/1';
    const STATES = Object.freeze(['empty', 'incomplete', 'ready']);
    const TOGGLE_REASONS = Object.freeze(['selected', 'deselected', 'at_capacity', 'unknown_candidate']);
    const MIN_CANDIDATES = 2;
    const MAX_CANDIDATES = 4;

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function clone(value) {
        if (value == null || typeof value !== 'object') return value;
        if (typeof structuredClone === 'function') return structuredClone(value);
        return JSON.parse(JSON.stringify(value));
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    /* Flatten one staged tray card plus its staged item into the shape this
       workspace compares. Cards and items are joined on item_id so the caller
       never has to keep two lists index-aligned.

       The join is keyed by id, never by position: a card whose item is absent
       still yields a candidate, because the card's own metadata and reference
       are real, but it never borrows a neighbouring item's value. `null` is
       reserved for a card with no identity at all, and callers filter it out. */
    function candidateFrom(card, item) {
        const source = card && typeof card === 'object' ? card : {};
        const staged = item && typeof item === 'object' ? item : {};
        const linkage = source.source && typeof source.source === 'object' ? source.source : {};
        const itemId = text(source.item_id || staged.item_id);
        if (!itemId) return null;
        return Object.freeze({
            item_id: itemId,
            kind: text(source.kind || staged.kind, 'text').toLowerCase(),
            title: text(source.title || staged.output_name, 'Result'),
            subtitle: text(source.subtitle, ''),
            preview_url: text(source.preview_url),
            run_id: text(linkage.run_id || staged.run_id),
            attempt_id: text(linkage.attempt_id || staged.attempt_id),
            output_name: text(linkage.output_name || staged.output_name),
            ordinal: Number.isInteger(linkage.ordinal) ? linkage.ordinal : (Number.isInteger(staged.ordinal) ? staged.ordinal : 0),
            value: clone(staged.value),
        });
    }

    function candidatesFrom(cards, items) {
        const staged = Array.isArray(items) ? items : [];
        const byId = new Map(staged.map(item => [text(item && item.item_id), item]));
        return Object.freeze((Array.isArray(cards) ? cards : [])
            .map(card => candidateFrom(card, byId.get(text(card && card.item_id))))
            .filter(Boolean));
    }

    function stateOf(count) {
        if (count === 0) return 'empty';
        return count < MIN_CANDIDATES ? 'incomplete' : 'ready';
    }

    /* The preview body belongs to the preview registry. Without one loaded the
       column still shows its metadata, and says so instead of pretending. */
    function previewOf(candidate) {
        const registry = global.WorkbenchCanvasResultPreview;
        if (!registry) return Object.freeze({source: 'none', state: '', reason: '', html: ''});
        const preview = registry.previewFor(candidate);
        return Object.freeze({
            source: 'registry',
            state: preview.state,
            reason: preview.reason,
            html: registry.renderPreview(preview),
        });
    }

    function columnFor(candidate, position) {
        const preview = previewOf(candidate);
        return Object.freeze({
            position,
            item_id: candidate.item_id,
            kind: candidate.kind,
            title: candidate.title,
            subtitle: candidate.subtitle,
            preview_url: candidate.preview_url,
            run_id: candidate.run_id,
            attempt_id: candidate.attempt_id,
            output_name: candidate.output_name,
            ordinal: candidate.ordinal,
            preview_source: preview.source,
            preview_state: preview.state,
            preview_reason: preview.reason,
            preview_html: preview.html,
        });
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const limit = Number.isInteger(settings.maxCandidates) && settings.maxCandidates >= MIN_CANDIDATES
            ? settings.maxCandidates
            : MAX_CANDIDATES;
        let candidates = Object.freeze((Array.isArray(settings.candidates) ? settings.candidates : []).filter(Boolean));
        /* Selection is an ordered list, not a set: the user's order is the only
           order the comparison has, because comparison is unscored. */
        let selected = [];
        let omitted = [];
        let host = null;

        function knownIds() {
            return new Set(candidates.map(candidate => candidate.item_id));
        }

        function snapshot() {
            return Object.freeze({
                selected: Object.freeze(selected.slice()),
                omitted: Object.freeze(omitted.slice()),
                state: stateOf(selected.length),
                candidate_count: candidates.length,
                max_candidates: limit,
            });
        }

        function emitChange() {
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function columnHtml(column) {
            const meta = [
                ['run', column.run_id], ['attempt', column.attempt_id],
                ['output', column.output_name], ['ordinal', String(column.ordinal)],
            ].map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`).join('');
            const body = column.preview_source === 'registry'
                ? column.preview_html
                : `<span class="result-compare__reference">${escapeHtml(column.preview_url || '')}</span>`;
            return `<article class="result-compare__column" data-compare-item="${escapeHtml(column.item_id)}" data-compare-position="${column.position}" data-compare-kind="${escapeHtml(column.kind)}" data-compare-preview="${escapeHtml(column.preview_source)}" data-compare-state="${escapeHtml(column.preview_state)}"><header><span class="result-compare__title">${escapeHtml(column.title)}</span><span class="result-compare__subtitle">${escapeHtml(column.subtitle)}</span></header><dl class="result-compare__meta">${meta}</dl><div class="result-compare__preview">${body}</div></article>`;
        }

        function render() {
            if (!host) return;
            const current = comparison();
            host.setAttribute('data-result-compare', current.state);
            host.innerHTML = `<div class="workbench-result-compare__head"><strong>Compare results</strong><span>${selected.length} of ${limit} selected</span></div>${current.candidates.length ? `<div class="workbench-result-compare__columns">${current.candidates.map(columnHtml).join('')}</div>` : '<p class="is-empty">Select at least two results to compare</p>'}`;
            emitChange();
        }

        function toggle(itemId) {
            const id = text(itemId);
            if (!knownIds().has(id)) return Object.freeze({item_id: id, selected: false, reason: 'unknown_candidate'});
            const index = selected.indexOf(id);
            if (index >= 0) {
                selected = selected.filter(entry => entry !== id);
                render();
                return Object.freeze({item_id: id, selected: false, reason: 'deselected'});
            }
            if (selected.length >= limit) return Object.freeze({item_id: id, selected: false, reason: 'at_capacity'});
            selected = [...selected, id];
            render();
            return Object.freeze({item_id: id, selected: true, reason: 'selected'});
        }

        function select(itemIds) {
            const available = knownIds();
            const next = [];
            Array.from(Array.isArray(itemIds) ? itemIds : []).forEach(entry => {
                const id = text(entry);
                if (available.has(id) && !next.includes(id) && next.length < limit) next.push(id);
            });
            selected = next;
            render();
            return snapshot();
        }

        function clear() {
            selected = [];
            render();
            return snapshot();
        }

        /* Replacing the candidate list must not lose the user's selection: ids
           that are still present keep their position, and ids that vanished are
           reported through `omitted` rather than silently dropped. */
        function setCandidates(nextCandidates) {
            candidates = Object.freeze((Array.isArray(nextCandidates) ? nextCandidates : []).filter(Boolean));
            const available = knownIds();
            omitted = selected.filter(id => !available.has(id));
            selected = selected.filter(id => available.has(id));
            render();
            return snapshot();
        }

        function comparison() {
            const byId = new Map(candidates.map(candidate => [candidate.item_id, candidate]));
            const columns = selected.map((id, position) => columnFor(byId.get(id), position));
            return Object.freeze({
                schema_version: COMPARE_SCHEMA,
                state: stateOf(columns.length),
                min_candidates: MIN_CANDIDATES,
                max_candidates: limit,
                candidate_count: candidates.length,
                selected_count: columns.length,
                omitted: Object.freeze(omitted.slice()),
                candidates: Object.freeze(columns),
            });
        }

        function mount(target) {
            if (!target) throw new TypeError('Result compare requires a host');
            host = target;
            render();
            return Object.freeze({element: host, snapshot, comparison, toggle, select, clear, setCandidates, destroy: () => { host.innerHTML = ''; host.removeAttribute('data-result-compare'); host = null; }});
        }

        return Object.freeze({snapshot, comparison, selection: () => Object.freeze(selected.slice()), has: id => selected.includes(text(id)), toggle, select, clear, setCandidates, mount});
    }

    global.WorkbenchCanvasResultCompare = Object.freeze({
        COMPARE_SCHEMA, STATES, TOGGLE_REASONS, MIN_CANDIDATES, MAX_CANDIDATES,
        candidateFrom, candidatesFrom, create,
    });
}(window));
