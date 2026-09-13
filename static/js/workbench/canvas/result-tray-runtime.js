/* Generic result staging for execution outputs. The tray owns only session and
   item state plus generic card descriptors; it never creates a Canvas node,
   never mutates the graph, and never persists. Promotion of a staged result
   into a Canvas node or a Collection belongs to a later boundary. */
(function exposeWorkbenchCanvasResultTray(global) {
    'use strict';

    const KINDS = Object.freeze(['text', 'image', 'video', 'audio', 'file', 'json', 'resource', 'link', 'workflow']);
    const PREVIEWABLE = Object.freeze(['image', 'video', 'audio']);
    const DEFAULT_TITLE = 'Result';

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

    /* An output value is either a scalar (raw text) or a declared reference.
       A declared kind is preserved as given; only its absence is inferred. */
    function kindOf(value) {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            return text(value.kind || value.media_kind || value.type).toLowerCase() || 'json';
        }
        if (Array.isArray(value)) return 'json';
        return 'text';
    }

    function urlOf(value) {
        if (!value || typeof value !== 'object' || Array.isArray(value)) return '';
        return text(value.url || value.uri || value.file || value.href);
    }

    function sessionIdOf(settings) {
        const parts = [settings.projectId, settings.taskId, settings.runId].map(value => text(value)).filter(Boolean);
        return text(settings.sessionId) || parts.join(':') || 'result-tray';
    }

    function createSession(options) {
        const settings = options && typeof options === 'object' ? options : {};
        return {
            session_id: sessionIdOf(settings),
            project_id: text(settings.projectId),
            task_id: text(settings.taskId),
            run_id: text(settings.runId),
            attempt_id: text(settings.attemptId),
            items: [],
            materialized: false,
        };
    }

    /* Stage one attempt's outputs. An item is identified by
       attempt + output name + its occurrence in the batch, so re-ingesting the
       same attempt's outputs is a no-op instead of a duplicate. */
    function ingest(session, batch) {
        if (!session || typeof session !== 'object' || !Array.isArray(session.items)) {
            throw new TypeError('Result tray ingest requires a tray session');
        }
        const source = batch && typeof batch === 'object' ? batch : {};
        const runId = text(source.runId, session.run_id);
        const attemptId = text(source.attemptId, session.attempt_id);
        const outputs = Array.isArray(source.outputs) ? source.outputs : [];
        const seen = new Set(session.items.map(item => item.item_id));
        const ordinals = new Map();
        const added = [];
        outputs.forEach((raw, index) => {
            const output = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {name: '', value: raw};
            const name = text(output.name, `output.${index + 1}`);
            const ordinal = ordinals.get(name) || 0;
            ordinals.set(name, ordinal + 1);
            const itemId = `${attemptId}:${name}:${ordinal}`;
            if (seen.has(itemId)) return;
            seen.add(itemId);
            const value = clone(output.value);
            const item = {
                item_id: itemId,
                session_id: session.session_id,
                run_id: runId,
                attempt_id: attemptId,
                output_name: name,
                ordinal,
                kind: kindOf(value),
                value,
                materialized: false,
            };
            session.items.push(item);
            added.push(item);
        });
        return Object.freeze(added);
    }

    function cardFor(item) {
        const source = item && typeof item === 'object' ? item : {};
        const kind = text(source.kind, 'text');
        const previewUrl = urlOf(source.value);
        const attemptId = text(source.attempt_id);
        return Object.freeze({
            item_id: text(source.item_id),
            kind,
            title: text(source.output_name, DEFAULT_TITLE),
            subtitle: attemptId ? `${kind} · ${attemptId}` : kind,
            preview_url: previewUrl,
            previewable: PREVIEWABLE.includes(kind) && Boolean(previewUrl),
            materialized: Boolean(source.materialized),
            source: Object.freeze({
                run_id: text(source.run_id),
                attempt_id: attemptId,
                output_name: text(source.output_name),
                ordinal: Number.isInteger(source.ordinal) ? source.ordinal : 0,
            }),
        });
    }

    function cards(session) {
        const items = session && Array.isArray(session.items) ? session.items : [];
        return Object.freeze(items.map(cardFor));
    }

    function summaryOf(session) {
        const items = session && Array.isArray(session.items) ? session.items : [];
        return Object.freeze({
            session_id: text(session?.session_id),
            run_id: text(session?.run_id),
            attempt_id: text(session?.attempt_id),
            item_count: items.length,
            materialized: false,
        });
    }

    /* The preview body belongs to the result preview registry; the tray keeps
       the list structure and the staging state. Without a loaded registry a
       card renders exactly the bare reference marker it rendered before. */
    function previewBody(card, item) {
        const registry = global.WorkbenchCanvasResultPreview;
        if (!registry) {
            return card.previewable
                ? `<span class="result-card__preview" data-preview-url="${escapeHtml(card.preview_url)}"></span>`
                : '';
        }
        const preview = registry.previewFor({...card, value: item ? item.value : undefined});
        return `<span class="result-card__preview" data-preview-state="${escapeHtml(preview.state)}" data-preview-reason="${escapeHtml(preview.reason)}">${registry.renderPreview(preview)}</span>`;
    }

    function cardHtml(card, item) {
        return `<li class="workbench-result-tray__card" data-result-item="${escapeHtml(card.item_id)}" data-result-kind="${escapeHtml(card.kind)}"><span class="result-card__title">${escapeHtml(card.title)}</span><span class="result-card__subtitle">${escapeHtml(card.subtitle)}</span>${previewBody(card, item)}</li>`;
    }

    /* A tray controller. It stages results for a host to display; it exposes no
       materialization entry point on purpose. */
    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const session = createSession(settings);
        let host = null;

        function snapshot() { return clone(session); }

        function render() {
            if (!host) return;
            const items = session.items;
            host.setAttribute('data-result-tray', session.session_id);
            host.innerHTML = `<div class="workbench-result-tray__head"><strong>Results</strong><span>${items.length} staged</span></div><ol class="workbench-result-tray__items">${items.map(item => cardHtml(cardFor(item), item)).join('') || '<li class="is-empty">No results yet</li>'}</ol>`;
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function stage(batch) {
            const added = ingest(session, batch);
            render();
            return added;
        }

        function mount(target) {
            if (!target) throw new TypeError('Result tray requires a host');
            host = target;
            render();
            return Object.freeze({element: host, snapshot, ingest: stage, cards: () => cards(session), destroy: () => { host.innerHTML = ''; host.removeAttribute('data-result-tray'); host = null; }});
        }

        return Object.freeze({
            session_id: session.session_id,
            snapshot,
            ingest: stage,
            cards: () => cards(session),
            summary: () => summaryOf(session),
            mount,
        });
    }

    global.WorkbenchCanvasResultTray = Object.freeze({
        KINDS, PREVIEWABLE, kindOf, urlOf, createSession, ingest, cardFor, cards, summaryOf, create,
    });
}(window));
