/* Generic result preview rendering for the Result Tray. The registry owns only
   how a staged result is rendered and whether its reference is inspectable; it
   never creates a Canvas node, never mutates the graph, and never persists.

   Classification stays with the caller. The tray already derives each staged
   item's kind from the value the executor declared, so this module renders the
   kind it is given instead of re-deriving it from a value shape or a URL
   extension. Reference resolution is the caller's job too: the tray resolves
   the item's reference and passes it as `url`/`preview_url`, so this module
   never re-implements the tray's reference extraction.

   A preview is one of two explicit states. `ready` carries the renderer that
   owns the body; `unavailable` carries a reason instead of silently rendering
   nothing, so an unresolvable or failed reference stays visible to the user. */
(function exposeWorkbenchCanvasResultPreview(global) {
    'use strict';

    const PREVIEW_SCHEMA = 'workbench.result-preview/1';
    const KINDS = Object.freeze(['text', 'image', 'video', 'audio', 'file', 'json', 'resource', 'link', 'workflow']);
    const STATES = Object.freeze(['ready', 'unavailable']);
    const REASONS = Object.freeze(['empty_output', 'failed_output', 'missing_reference', 'unsafe_reference', 'unsupported_kind']);
    /* Kinds whose preview needs a resolved reference rather than a body value. */
    const REF_KINDS = Object.freeze(['image', 'video', 'audio', 'file', 'resource', 'link', 'workflow']);
    /* Kinds whose preview renders the value itself. */
    const VALUE_KINDS = Object.freeze(['text', 'json']);

    const REASON_MESSAGES = Object.freeze({
        empty_output: 'No value was produced for this result',
        failed_output: 'This result failed before it produced a usable value',
        missing_reference: 'This result has no resolvable reference',
        unsafe_reference: 'This result reference is not safe to render',
        unsupported_kind: 'No preview renderer is registered for this result kind',
    });

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[character]));
    }

    function isEmptyValue(value) {
        if (value == null) return true;
        if (typeof value === 'string') return value.trim() === '';
        if (Array.isArray(value)) return value.length === 0;
        if (typeof value === 'object') return Object.keys(value).length === 0;
        return false;
    }

    function bodyText(value) {
        if (typeof value === 'string') return value;
        if (value == null) return '';
        try {
            return JSON.stringify(value, null, 2);
        } catch (error) {
            return String(value);
        }
    }

    /* A reference is only rendered when it cannot smuggle an executable scheme
       into an href or a media src. Relative and known-inert absolute references
       pass; anything else (notably `javascript:` and `data:`, which can carry a
       script into a navigation) is reported as unavailable instead. */
    function isSafeRef(url) {
        const value = text(url);
        if (!value) return false;
        if (/^[/#?.]/.test(value)) return true;
        return /^(https?:|blob:|file:)/i.test(value);
    }

    function refName(url, fallback) {
        const value = text(url);
        const cleaned = value.split('#')[0].split('?')[0];
        const segment = cleaned.split('/').filter(Boolean).pop();
        return text(segment, text(fallback, 'result'));
    }

    function reasonMessage(reason) {
        return REASON_MESSAGES[text(reason)] || 'This result is not inspectable';
    }

    function normalizeInput(item) {
        const source = item && typeof item === 'object' ? item : {};
        const value = source.value;
        const declared = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
        const failure = text(source.error) || text(declared.error);
        return Object.freeze({
            item_id: text(source.item_id),
            kind: text(source.kind, 'text').toLowerCase(),
            title: text(source.title || source.output_name, 'Result'),
            url: text(source.preview_url || source.url),
            value,
            failed: Boolean(source.failed) || Boolean(declared.failed) || declared.status === 'failed' || Boolean(failure),
            missing: Boolean(source.missing) || Boolean(source.is_missing) || Boolean(declared.missing) || Boolean(declared.is_missing),
        });
    }

    function makePreview(input, state, rendererId, rendererVersion, reason) {
        return Object.freeze({
            schema_version: PREVIEW_SCHEMA,
            item_id: input.item_id,
            kind: input.kind,
            state,
            renderer_id: text(rendererId),
            renderer_version: text(rendererVersion),
            title: input.title,
            url: state === 'ready' ? input.url : '',
            reason: text(reason),
            message: state === 'unavailable' ? reasonMessage(reason) : '',
        });
    }

    function unavailable(input, reason, renderer) {
        return makePreview(input, 'unavailable', renderer ? renderer.id : '', renderer ? renderer.version : '', reason);
    }

    function ready(input, renderer) {
        return makePreview(input, 'ready', renderer.id, renderer.version, '');
    }

    function mediaBody(className, tag, preview, attributes) {
        return `<${tag} class="${className}" src="${escapeHtml(preview.url)}"${attributes}></${tag}>`;
    }

    function linkBody(className, preview, attributes) {
        return `<a class="${className}" href="${escapeHtml(preview.url)}"${attributes}>${escapeHtml(refName(preview.url, preview.title))}</a>`;
    }

    /* One built-in renderer per common result kind. A caller may register a
       higher-priority renderer for the same kind to override a built-in. */
    const BUILT_IN = Object.freeze([
        {
            id: 'result-preview/text', version: '1', kind: 'text', priority: 0,
            canRender: input => input.kind === 'text',
            render: preview => `<pre class="result-preview__text" data-preview-kind="text">${escapeHtml(bodyText(preview.value))}</pre>`,
        },
        {
            id: 'result-preview/json', version: '1', kind: 'json', priority: 0,
            canRender: input => input.kind === 'json',
            render: preview => `<pre class="result-preview__json" data-preview-kind="json">${escapeHtml(bodyText(preview.value))}</pre>`,
        },
        {
            id: 'result-preview/image', version: '1', kind: 'image', priority: 0,
            canRender: input => input.kind === 'image',
            render: preview => mediaBody('result-preview__image', 'img', preview, ` alt="${escapeHtml(preview.title)}" loading="lazy"`),
        },
        {
            id: 'result-preview/video', version: '1', kind: 'video', priority: 0,
            canRender: input => input.kind === 'video',
            render: preview => mediaBody('result-preview__video', 'video', preview, ' controls preload="metadata"'),
        },
        {
            id: 'result-preview/audio', version: '1', kind: 'audio', priority: 0,
            canRender: input => input.kind === 'audio',
            render: preview => mediaBody('result-preview__audio', 'audio', preview, ' controls preload="metadata"'),
        },
        {
            id: 'result-preview/file', version: '1', kind: 'file', priority: 0,
            canRender: input => input.kind === 'file',
            render: preview => linkBody('result-preview__file', preview, ' download'),
        },
        {
            id: 'result-preview/resource', version: '1', kind: 'resource', priority: 0,
            canRender: input => input.kind === 'resource',
            render: preview => linkBody('result-preview__resource', preview, ''),
        },
        {
            id: 'result-preview/link', version: '1', kind: 'link', priority: 0,
            canRender: input => input.kind === 'link',
            render: preview => linkBody('result-preview__link', preview, ' target="_blank" rel="noopener noreferrer"'),
        },
        {
            id: 'result-preview/workflow', version: '1', kind: 'workflow', priority: 0,
            canRender: input => input.kind === 'workflow',
            render: preview => linkBody('result-preview__workflow', preview, ' download'),
        },
    ]);

    function normalizeDescriptor(descriptor) {
        if (!descriptor || typeof descriptor !== 'object') throw new TypeError('Preview renderer descriptor is required');
        const id = text(descriptor.id);
        const version = text(descriptor.version);
        if (!id || !version) throw new TypeError('Preview renderer descriptor requires id and version');
        if (typeof descriptor.canRender !== 'function' || typeof descriptor.render !== 'function') {
            throw new TypeError('Preview renderer descriptor requires canRender and render functions');
        }
        return Object.freeze({
            id,
            version,
            kind: text(descriptor.kind).toLowerCase(),
            priority: Number.isFinite(Number(descriptor.priority)) ? Number(descriptor.priority) : 0,
            canRender: descriptor.canRender,
            render: descriptor.render,
        });
    }

    function create(initialDescriptors) {
        const descriptors = new Map();

        function register(descriptor) {
            const normalized = normalizeDescriptor(descriptor);
            const key = `${normalized.id}@${normalized.version}`;
            if (descriptors.has(key)) throw new RangeError(`preview renderer already registered: ${key}`);
            descriptors.set(key, normalized);
            return normalized;
        }

        /* Deterministic: highest priority wins, then lowest id. No fallback to a
           different kind, so an unregistered kind stays explicitly unavailable. */
        function resolve(input, options) {
            const preferred = text(options && options.renderer_id);
            if (preferred) {
                const exact = Array.from(descriptors.values()).find(descriptor => descriptor.id === preferred);
                if (exact && exact.canRender(input, options || {})) return exact;
            }
            return Array.from(descriptors.values())
                .filter(descriptor => descriptor.canRender(input, options || {}))
                .sort((left, right) => right.priority - left.priority || left.id.localeCompare(right.id))[0] || null;
        }

        function preview(item, options) {
            const input = normalizeInput(item);
            const renderer = resolve(input, options);
            if (!renderer) return unavailable(input, 'unsupported_kind', null);
            if (input.failed) return unavailable(input, 'failed_output', renderer);
            if (input.missing) return unavailable(input, 'missing_reference', renderer);
            if (REF_KINDS.includes(input.kind)) {
                if (!input.url) return unavailable(input, 'missing_reference', renderer);
                if (!isSafeRef(input.url)) return unavailable(input, 'unsafe_reference', renderer);
            } else if (VALUE_KINDS.includes(input.kind) && isEmptyValue(input.value)) {
                return unavailable(input, 'empty_output', renderer);
            }
            const rendered = ready(input, renderer);
            return Object.freeze({...rendered, value: input.value});
        }

        function previews(items, options) {
            const list = Array.isArray(items) ? items : [];
            return Object.freeze(list.map(item => preview(item, options)));
        }

        function render(previewDescriptor) {
            const descriptor = previewDescriptor && typeof previewDescriptor === 'object' ? previewDescriptor : {};
            if (descriptor.state !== 'ready') {
                return `<div class="result-preview__unavailable" data-preview-state="unavailable" data-preview-reason="${escapeHtml(descriptor.reason)}">${escapeHtml(descriptor.message || reasonMessage(descriptor.reason))}</div>`;
            }
            const owner = Array.from(descriptors.values()).find(candidate => candidate.id === text(descriptor.renderer_id));
            return owner ? owner.render(descriptor) : '';
        }

        Array.from(initialDescriptors === undefined ? BUILT_IN : initialDescriptors).forEach(register);
        return Object.freeze({all: () => Object.freeze(Array.from(descriptors.values())), register, resolve, preview, previews, render});
    }

    const DEFAULT = create(BUILT_IN);

    global.WorkbenchCanvasResultPreview = Object.freeze({
        PREVIEW_SCHEMA, KINDS, STATES, REASONS, REF_KINDS, VALUE_KINDS,
        DEFAULT_RENDERERS: BUILT_IN,
        create, reasonMessage, isSafeRef,
        previewFor: item => DEFAULT.preview(item),
        previewsFor: items => DEFAULT.previews(items),
        renderPreview: previewDescriptor => DEFAULT.render(previewDescriptor),
        previewHtml: item => DEFAULT.render(DEFAULT.preview(item)),
    });
}(window));
