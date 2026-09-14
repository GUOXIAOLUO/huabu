/* User preference metadata for staged run results. This seam owns what the user
   decided about a result — selected, favorite, rating, comment — and the
   boundary that turns that decision into records to persist and back.

   Three boundaries are deliberate. A result is identified by the attempt that
   produced it plus the output name and that output's occurrence in the batch,
   which is the identity the Result Tray stages and the Result Compare workspace
   compares; nothing here invents a second identity for a result. The rating is
   what the user assigned and is never computed or derived, so this seam cannot
   become a machine judgement about which candidate is better. And no state of
   record is modelled — settling a design belongs to a later, separate concept —
   so nothing here authorizes anything.

   The seam owns no transport: it reports what should be persisted and accepts
   what was persisted, while the client that performs the request stays outside. */
(function exposeWorkbenchCanvasResultSelection(global) {
    'use strict';

    const SELECTION_SCHEMA = 'workbench.result-selection/1';
    const RATING_MIN = 1;
    const RATING_MAX = 5;
    const MAX_COMMENT_LENGTH = 2000;
    const REASONS = Object.freeze(['applied', 'cleared', 'unchanged', 'unknown_result', 'rating_out_of_range', 'comment_too_long']);
    const PREFERENCE_FIELDS = Object.freeze(['selected', 'favorite', 'rating', 'comment']);

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    function clone(value) {
        if (value == null || typeof value !== 'object') return value;
        if (typeof structuredClone === 'function') return structuredClone(value);
        return JSON.parse(JSON.stringify(value));
    }

    /* The canonical identity of one run result. An item that cannot supply all
       three parts has no identity, and is reported as unknown rather than being
       silently keyed on a partial match. */
    function identityOf(source) {
        const item = source && typeof source === 'object' ? source : {};
        const attemptId = text(item.attempt_id ?? item.attemptId);
        const outputName = text(item.output_name ?? item.outputName);
        const ordinal = Number(item.ordinal);
        if (!attemptId || !outputName || !Number.isInteger(ordinal) || ordinal < 0) return null;
        return Object.freeze({attempt_id: attemptId, output_name: outputName, ordinal});
    }

    function sameResult(left, right) {
        const a = identityOf(left);
        const b = identityOf(right);
        if (!a || !b) return false;
        return a.attempt_id === b.attempt_id && a.output_name === b.output_name && a.ordinal === b.ordinal;
    }

    /* Internal index key only. This is deliberately not a public result id: the
       persisted identity is the three parts above, and the Tray keeps owning the
       display id it stages. */
    function indexKey(identity) {
        return JSON.stringify([identity.attempt_id, identity.output_name, identity.ordinal]);
    }

    function blankPreference() {
        return Object.freeze({selected: false, favorite: false, rating: null, comment: ''});
    }

    function hasPreference(preference) {
        const value = preference && typeof preference === 'object' ? preference : {};
        return Boolean(value.selected) || Boolean(value.favorite) || value.rating != null || text(value.comment) !== '';
    }

    /* Validate rather than coerce: a rating outside the allowed band or a
       comment beyond the allowed length is refused with a reason, so a caller
       never gets a silently clamped preference back. */
    function preferenceFrom(input, current, limit) {
        const source = input && typeof input === 'object' ? input : {};
        const base = current || blankPreference();
        const preference = {
            selected: Object.prototype.hasOwnProperty.call(source, 'selected') ? Boolean(source.selected) : base.selected,
            favorite: Object.prototype.hasOwnProperty.call(source, 'favorite') ? Boolean(source.favorite) : base.favorite,
            rating: Object.prototype.hasOwnProperty.call(source, 'rating') ? source.rating : base.rating,
            comment: Object.prototype.hasOwnProperty.call(source, 'comment') ? text(source.comment) : base.comment,
        };
        if (preference.rating != null) {
            const rating = preference.rating;
            if (!Number.isInteger(rating) || rating < RATING_MIN || rating > RATING_MAX) {
                return {error: 'rating_out_of_range'};
            }
        }
        if (preference.comment.length > limit) return {error: 'comment_too_long'};
        return {preference: Object.freeze(preference)};
    }

    /* One persisted record, flattened to the shape this seam compares. */
    function recordFrom(input) {
        const source = input && typeof input === 'object' ? input : {};
        const identity = identityOf(source);
        if (!identity) return null;
        const preference = preferenceFrom(source, null, MAX_COMMENT_LENGTH);
        if (preference.error) return null;
        return Object.freeze({
            ...identity,
            ...preference.preference,
            selection_id: text(source.id || source.selection_id),
            revision: Number.isInteger(Number(source.revision)) ? Number(source.revision) : 1,
        });
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const limit = Number.isInteger(settings.maxCommentLength) && settings.maxCommentLength > 0
            ? settings.maxCommentLength
            : MAX_COMMENT_LENGTH;
        let persisted = new Map();
        let current = new Map();
        let host = null;

        function emitChange() {
            if (typeof settings.onChange === 'function') settings.onChange(snapshot());
        }

        function keyFor(item) {
            const identity = identityOf(item);
            return identity ? indexKey(identity) : null;
        }

        /* The identity parts that address one result, recovered from the internal
           index key so every record and every change can be handed straight to
           persistence without a caller having to re-derive them. */
        function identityFromKey(key) {
            const parts = JSON.parse(key);
            return {attempt_id: parts[0], output_name: parts[1], ordinal: parts[2]};
        }

        /* What is currently marked. A record that has been cleared is still
           persisted until the clear is saved, but it no longer carries a
           preference, so it is reported through `pending` rather than counted
           here. */
        function snapshot() {
            const records = [];
            current.forEach((value, key) => {
                if (!hasPreference(value)) return;
                records.push(Object.freeze({...identityFromKey(key), ...value, key}));
            });
            return Object.freeze({
                schema_version: SELECTION_SCHEMA,
                rating_min: RATING_MIN,
                rating_max: RATING_MAX,
                records: Object.freeze(records),
                count: records.length,
                pending: pending(),
            });
        }

        function preferenceFor(item) {
            const key = keyFor(item);
            if (key === null) return blankPreference();
            return current.get(key) || blankPreference();
        }

        function setPreference(item, patch) {
            const identity = identityOf(item);
            if (!identity) return Object.freeze({result: null, preference: blankPreference(), reason: 'unknown_result'});
            const key = indexKey(identity);
            const existing = current.get(key) || blankPreference();
            const outcome = preferenceFrom(patch, existing, limit);
            if (outcome.error) return Object.freeze({result: identity, preference: existing, reason: outcome.error});
            const preference = outcome.preference;
            const base = persisted.get(key);
            if (!hasPreference(preference) && !base) {
                current.delete(key);
                return Object.freeze({result: identity, preference: blankPreference(), reason: 'unchanged'});
            }
            current.set(key, preference);
            render();
            return Object.freeze({result: identity, preference, reason: hasPreference(preference) ? 'applied' : 'cleared'});
        }

        function clearPreference(item) {
            const key = keyFor(item);
            if (key === null) return Object.freeze({result: null, preference: blankPreference(), reason: 'unknown_result'});
            if (persisted.has(key)) {
                current.set(key, blankPreference());
            } else {
                current.delete(key);
            }
            render();
            return Object.freeze({result: identityOf(item), preference: blankPreference(), reason: 'cleared'});
        }

        /* Everything that differs from the last known persisted state, in a
           deterministic order, ready to be sent to persistence. */
        function pending() {
            const keys = Array.from(new Set([...persisted.keys(), ...current.keys()])).sort();
            const changes = [];
            keys.forEach(key => {
                const base = persisted.get(key);
                const value = current.get(key) || blankPreference();
                const identity = identityFromKey(key);
                if (base && !hasPreference(value)) {
                    changes.push(Object.freeze({key, ...identity, action: 'clear', selection_id: base.selection_id, revision: base.revision}));
                    return;
                }
                if (base && PREFERENCE_FIELDS.every(field => base[field] === value[field])) return;
                if (!base && !hasPreference(value)) return;
                changes.push(Object.freeze({
                    key,
                    ...identity,
                    action: base ? 'update' : 'create',
                    selection_id: base ? base.selection_id : '',
                    revision: base ? base.revision : 0,
                    selected: value.selected,
                    favorite: value.favorite,
                    rating: value.rating,
                    comment: value.comment,
                }));
            });
            return Object.freeze(changes);
        }

        /* Accept what persistence now holds. Records that are absent from the
           supplied set are no longer persisted, so they drop back to unset. */
        function hydrate(records) {
            persisted = new Map();
            Array.from(Array.isArray(records) ? records : []).forEach(entry => {
                const record = recordFrom(entry);
                if (!record) return;
                persisted.set(indexKey(record), record);
            });
            current = new Map();
            persisted.forEach((value, key) => current.set(key, Object.freeze({
                selected: value.selected, favorite: value.favorite, rating: value.rating, comment: value.comment,
            })));
            render();
            return snapshot();
        }

        function markSaved(records) {
            return hydrate(records);
        }

        function rowHtml(record) {
            const rating = record.rating == null ? '' : String(record.rating);
            const saveAction = record.selected
                ? `<button type="button" class="result-selection__save-asset" data-result-save-asset="${escapeHtml(indexKey(record))}">Save as asset</button>`
                : '';
            return `<li class="result-selection__row" data-selection-attempt="${escapeHtml(record.attempt_id)}" data-selection-output="${escapeHtml(record.output_name)}" data-selection-ordinal="${escapeHtml(record.ordinal)}" data-selection-selected="${record.selected}" data-selection-favorite="${record.favorite}" data-selection-rating="${escapeHtml(rating)}"><span class="result-selection__output">${escapeHtml(record.output_name)}</span><span class="result-selection__comment">${escapeHtml(record.comment)}</span>${saveAction}</li>`;
        }

        function handleClick(event) {
            const button = event?.target?.closest?.('[data-result-save-asset]');
            if (!button || typeof settings.onSaveAsAsset !== 'function') return;
            const key = button.getAttribute('data-result-save-asset');
            const record = snapshot().records.find(entry => indexKey(entry) === key);
            if (!record || !record.selected) return;
            settings.onSaveAsAsset(clone(record));
        }

        function render() {
            if (!host) return;
            const records = snapshot().records;
            host.setAttribute('data-result-selection', SELECTION_SCHEMA);
            host.innerHTML = `<div class="workbench-result-selection__head"><strong>Result preferences</strong><span>${records.length} marked</span></div>${records.length ? `<ul class="workbench-result-selection__rows">${records.map(rowHtml).join('')}</ul>` : '<p class="is-empty">No result preferences yet</p>'}`;
            emitChange();
        }

        function mount(target) {
            if (!target) throw new TypeError('Result selection requires a host');
            host = target;
            host.addEventListener?.('click', handleClick);
            render();
            return Object.freeze({element: host, snapshot, preferenceFor, setPreference, clearPreference, pending, hydrate, markSaved, destroy: () => { host.removeEventListener?.('click', handleClick); host.innerHTML = ''; host.removeAttribute('data-result-selection'); host = null; }});
        }

        if (Array.isArray(settings.records)) hydrate(settings.records);

        return Object.freeze({
            snapshot, preferenceFor, setPreference, clearPreference, pending, hydrate, markSaved, mount,
            has: item => hasPreference(preferenceFor(item)),
        });
    }

    global.WorkbenchCanvasResultSelection = Object.freeze({
        SELECTION_SCHEMA, RATING_MIN, RATING_MAX, MAX_COMMENT_LENGTH, REASONS, PREFERENCE_FIELDS,
        identityOf, sameResult, hasPreference, recordFrom, create,
    });
}(window));
