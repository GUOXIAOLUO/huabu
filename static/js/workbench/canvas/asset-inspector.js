/* Canonical Asset Inspector: what one canonical Asset *is* — its preview, its
 * metadata, its version history, where each version came from, and who
 * references it.
 *
 * Ownership boundary: this module owns the presentation of a canonical Asset's
 * facts and the request shape of the version-history read. It never persists an
 * asset, never reads or writes Canvas JSON, never reimplements the legacy
 * per-category detail panels, and never talks to SQLite. The host page owns the
 * DOM, the events, the actor and the fetch implementation; `AssetService.history`
 * and `GET /api/v1/assets/{asset_id}/versions` own what a history means.
 *
 * It is deliberately pure where it can be: `render()` returns an HTML string and
 * the host owns the DOM, so the host keeps its single focus and IME path instead
 * of this module growing a second one.
 *
 * Three things it refuses to guess, because guessing them would be a second
 * owner for a fact someone else already owns:
 *
 *   - **Which version is current.** The service resolves it from the sequence
 *     and the reply names it. Re-deriving "the highest ordinal" here would be a
 *     second owner of that rule, free to disagree with the history it came from.
 *     A reply that names a current version which is not in its own list renders
 *     no version rather than inventing one.
 *
 *   - **Whether anything references the asset.** "Nothing references it" and
 *     "no reference source is wired yet" are different answers. Rendering the
 *     second as the first would tell a user their asset is unused when the truth
 *     is that nobody looked, so the host supplies the usage verdict explicitly
 *     and the two states render differently.
 *
 *   - **Whether a location can be fetched.** Only an absolute http(s) URL or a
 *     site-absolute path is put into a `src`; a `file://` or `asset://` location
 *     is shown as text, never requested. */
(function exposeWorkbenchAssetInspector(global) {
    'use strict';

    /* The label maps are the mirror of the domain's closed sets, and the key
     * lists are derived from them rather than kept beside them: a list and a map
     * that can disagree is exactly how a UI loses the ability to render a
     * canonical member. Written in the domain's own order so an equality check
     * against `get_args(...)` is meaningful. */
    const TYPE_LABELS = Object.freeze({
        image: '图片', video: '视频', audio: '音频', document: '文档',
        model: '模型', workflow: '工作流', other: '其他',
    });
    const SOURCE_LABELS = Object.freeze({
        upload: '上传', url: '链接', local_path: '本地路径', provider: '供应商', import: '导入', execution: '执行结果',
    });
    const STATUS_LABELS = Object.freeze({draft: '草稿', ready: '就绪', archived: '归档'});
    const TYPES = Object.freeze(Object.keys(TYPE_LABELS));
    const SOURCES = Object.freeze(Object.keys(SOURCE_LABELS));
    const STATUSES = Object.freeze(Object.keys(STATUS_LABELS));

    /* How a version's bytes can be shown inline. Derived from the version's own
     * mime type — a version is what has bytes, the asset's `type` is a label on
     * the identity — and never from the file extension. */
    const PREVIEW_KINDS = Object.freeze(['image', 'video', 'audio', 'file']);
    const PREVIEW_LABELS = Object.freeze({image: '图片预览', video: '视频预览', audio: '音频预览', file: '文件'});

    const BASE_PATH = '/api/v1/assets';
    const DEFAULT_USAGE_REASON = '引用索引尚未接入：目前没有任何规范记录会引用资产版本。';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function memberOf(value, allowed, label) {
        const normalized = text(value);
        if (!allowed.includes(normalized)) throw new TypeError(`Unsupported ${label}: ${normalized}`);
        return normalized;
    }

    function objectOrEmpty(value) {
        return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    }

    /* The mime type decides how a version can be shown. `image/svg+xml` is an
     * image; `application/pdf` is not, and is offered as a file rather than
     * guessed at from its name. */
    function previewKind(version) {
        const mime = text(version && version.content && version.content.mime_type).toLowerCase();
        const family = mime.split('/')[0];
        return PREVIEW_KINDS.includes(family) ? family : 'file';
    }

    /* A location may only reach a `src` when the browser could actually fetch it
     * from this page. An absolute http(s) URL or a site-absolute path qualifies;
     * a `file://`, `asset://` or bare relative location is shown as text, so a
     * stored address can never be turned into a request by rendering it. */
    function isServableLocation(location) {
        const value = text(location);
        if (!value) return false;
        if (value.startsWith('//')) return false;
        if (value.startsWith('/')) return !value.startsWith('//');
        return /^https?:\/\//i.test(value);
    }

    function formatSize(bytes) {
        const size = Number(bytes);
        if (!Number.isFinite(size) || size < 0) return '';
        if (size < 1024) return `${size} B`;
        const units = ['KB', 'MB', 'GB', 'TB'];
        let value = size / 1024;
        let unit = 0;
        while (value >= 1024 && unit < units.length - 1) { value /= 1024; unit += 1; }
        return `${value >= 10 ? value.toFixed(0) : value.toFixed(1)} ${units[unit]}`;
    }

    /* A short, timezone-free rendering of the stored timestamp. The value is
     * sliced, never parsed into a Date: a `Date` would re-render the same stored
     * instant differently on another machine, and "traceable" means the reader
     * sees what was stored. Anything not in the stored shape is passed through. */
    function shortTimestamp(value) {
        const raw = text(value);
        return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(raw) ? raw.slice(0, 16).replace('T', ' ') : raw;
    }

    function previewLabel(value) {
        return Object.assign({}, PREVIEW_LABELS, value || {});
    }

    /* The one version this inspector is looking at: the host's explicit
     * selection when it resolves, otherwise the version the reply names as
     * current. If neither resolves, nothing is shown — the alternative is
     * guessing, which is the rule this module declines to own. */
    function activeVersion(history, selectedVersionId) {
        const versions = history && Array.isArray(history.versions) ? history.versions : [];
        const selected = text(selectedVersionId);
        if (selected) {
            const match = versions.find(version => version.id === selected);
            if (match) return match;
        }
        const current = text(history && history.currentVersionId);
        if (!current) return null;
        return versions.find(version => version.id === current) || null;
    }

    /* The drag payload for one version: identity plus the labels a drop target
     * needs to describe what it is about to receive. It carries no bytes and no
     * location — a drop target addresses the version, it does not copy the file,
     * which is what keeps dragging an asset from duplicating its content. */
    function dragPayload(asset, version) {
        if (!asset || !version) throw new TypeError('dragPayload requires an asset and a version');
        return Object.freeze({
            kind: 'asset_version',
            asset_id: text(asset.id),
            version_id: text(version.id),
            ordinal: Number(version.ordinal || 0),
            type: text(asset.type),
            mime_type: text(version.content && version.content.mime_type),
            label: text(asset.metadata && asset.metadata.name, text(asset.id)),
        });
    }

    /* The canonical history transport. It builds one request and normalizes the
     * reply; what the server means by a history is not re-decided here. */
    function createClient(options) {
        const settings = options || {};
        const fetchImpl = settings.fetch || global.fetch;
        if (typeof fetchImpl !== 'function') throw new TypeError('AssetInspectorClient requires fetch');
        const actorId = text(settings.actorId);
        if (!actorId) throw new TypeError('AssetInspectorClient requires an actor id');
        const basePath = text(settings.basePath, BASE_PATH);
        const versionPath = typeof settings.versionPath === 'function'
            ? settings.versionPath
            : assetId => `${basePath}/${encodeURIComponent(assetId)}/versions`;

        async function history(assetId) {
            const id = text(assetId);
            if (!id) throw new TypeError('AssetInspectorClient.history requires an asset id');
            const response = await fetchImpl(versionPath(id), {
                method: 'GET',
                headers: {'X-User-ID': actorId},
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                const detail = payload && payload.detail;
                throw new Error(typeof detail === 'string' ? detail : `读取资产版本失败（${response.status}）`);
            }
            return {
                assetId: text(payload.asset_id, id),
                currentVersionId: payload.current_version_id == null ? null : text(payload.current_version_id),
                versions: Array.isArray(payload.versions) ? payload.versions : [],
            };
        }

        return Object.freeze({history, basePath: () => basePath});
    }

    /* Pure presentation of one asset. The host owns the DOM, the events and the
     * focus, so this never touches a live element. */
    function createInspector(options) {
        const settings = options || {};
        const escapeHtml = settings.escapeHtml;
        if (typeof escapeHtml !== 'function') throw new TypeError('AssetInspector requires escapeHtml');
        const escapeAttr = typeof settings.escapeAttr === 'function' ? settings.escapeAttr : escapeHtml;
        const typeLabels = Object.assign({}, TYPE_LABELS, settings.typeLabels || {});
        const sourceLabels = Object.assign({}, SOURCE_LABELS, settings.sourceLabels || {});
        const statusLabels = Object.assign({}, STATUS_LABELS, settings.statusLabels || {});
        const kindLabels = previewLabel(settings.previewLabels);
        const usageReason = text(settings.usageReason, DEFAULT_USAGE_REASON);
        const emptyLabel = text(settings.emptyLabel, '未选择资产');

        function badge(value, labels) {
            const key = text(value);
            return `<span class="asset-inspector-badge">${escapeHtml(labels[key] || key)}</span>`;
        }

        function renderPreview(asset, version) {
            const kind = previewKind(version);
            const location = text(version.content && version.content.location);
            const mime = text(version.content && version.content.mime_type);
            const title = text(asset.metadata && asset.metadata.name, text(asset.id));
            const draggable = ' draggable="true" data-asset-inspector-drag="1"';
            if (isServableLocation(location) && kind !== 'file') {
                const media = kind === 'image'
                    ? `<img class="asset-inspector-media" src="${escapeAttr(location)}" alt="${escapeAttr(title)}" loading="lazy">`
                    : `<${kind} class="asset-inspector-media" src="${escapeAttr(location)}" controls preload="metadata"></${kind}>`;
                return `<div class="asset-inspector-preview"${draggable}>${media}`
                    + `<span class="asset-inspector-preview-kind">${escapeHtml(kindLabels[kind] || kind)}</span></div>`;
            }
            /* Not servable, or not a media kind: show the address instead of
             * requesting it. A `file://` path rendered into a `src` would be a
             * request the page cannot make and a leak of a local path. */
            return `<div class="asset-inspector-preview file"${draggable}>`
                + '<i data-lucide="file"></i>'
                + `<span class="asset-inspector-location">${escapeHtml(location)}</span>`
                + `<span class="asset-inspector-preview-kind">${escapeHtml(mime || kindLabels[kind] || kind)}</span></div>`;
        }

        function renderMetadata(asset) {
            const entries = Object.entries(objectOrEmpty(asset.metadata)).sort(([a], [b]) => a.localeCompare(b));
            if (!entries.length) return '<p class="asset-inspector-note">没有元数据。</p>';
            return '<dl class="asset-inspector-meta">' + entries.map(([key, value]) => {
                const shown = typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
                    ? String(value)
                    : JSON.stringify(value);
                return `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(shown)}</dd></div>`;
            }).join('') + '</dl>';
        }

        function renderVersionRow(version, history, shownVersionId) {
            const isCurrent = version.id === text(history.currentVersionId);
            const isSelected = version.id === text(shownVersionId);
            const provenance = objectOrEmpty(version.provenance);
            const content = objectOrEmpty(version.content);
            const size = formatSize(content.size_bytes);
            const source = text(provenance.source);
            const origin = [sourceLabels[source] || source, text(provenance.source_ref), text(provenance.actor_id)]
                .filter(Boolean).join(' · ');
            return `<li class="asset-inspector-version${isSelected ? ' active' : ''}">`
                + '<button class="asset-inspector-version-btn" type="button"'
                + ` data-asset-inspector-version="${escapeAttr(version.id)}"`
                + ` aria-pressed="${isSelected ? 'true' : 'false'}">`
                + `<span class="asset-inspector-version-head">`
                + `<strong>v${escapeHtml(text(version.ordinal))}</strong>`
                + `${isCurrent ? '<span class="asset-inspector-current">当前</span>' : ''}`
                + `<span class="asset-inspector-version-time">${escapeHtml(shortTimestamp(version.created_at))}</span>`
                + '</span>'
                + '<span class="asset-inspector-version-facts">'
                + `<span>${escapeHtml(text(content.mime_type))}</span>`
                + `${size ? `<span>${escapeHtml(size)}</span>` : ''}`
                + `${origin ? `<span>${escapeHtml(origin)}</span>` : ''}`
                + '</span>'
                + `<span class="asset-inspector-checksum" title="${escapeAttr(text(content.checksum))}">`
                + `${escapeHtml(text(content.checksum))}</span>`
                + '</button></li>';
        }

        /* The row marked active is the version this inspector is *showing* — the
         * host's selection when it resolves, otherwise the one the reply names as
         * current. Highlighting the raw selection instead would leave the preview
         * showing a version no row claims, which is the confusing state a second
         * rule for "which one is active" produces. */
        function renderVersions(asset, history, shownVersionId) {
            const versions = history && Array.isArray(history.versions) ? history.versions : [];
            if (!versions.length) {
                return '<p class="asset-inspector-note">该资产还没有版本，因此没有历史可追溯。</p>';
            }
            /* Newest first: the version a reader is most often looking for is the
             * one at the end of the sequence, and the current badge is already
             * rendered, so the order is a reading convenience, not a claim. */
            const ordered = versions.slice().sort((a, b) => Number(b.ordinal || 0) - Number(a.ordinal || 0));
            return '<ol class="asset-inspector-versions">'
                + ordered.map(version => renderVersionRow(version, history, shownVersionId)).join('')
                + '</ol>';
        }

        /* The usage verdict is the host's, and its shape carries the distinction
         * this module will not flatten: `available: false` is "we did not look",
         * `available: true` with an empty list is "we looked and found nothing". */
        function renderUsage(usage) {
            const supplied = objectOrEmpty(usage);
            if (supplied.available !== true) {
                return `<p class="asset-inspector-note muted">${escapeHtml(text(supplied.reason, usageReason))}</p>`;
            }
            const references = Array.isArray(supplied.references) ? supplied.references : [];
            if (!references.length) return '<p class="asset-inspector-note">尚未被任何记录引用。</p>';
            return '<ul class="asset-inspector-usage">' + references.map(reference => {
                const item = objectOrEmpty(reference);
                const label = text(item.label, text(item.id));
                const kind = text(item.kind);
                return '<li class="asset-inspector-usage-item">'
                    + `<span class="asset-inspector-badge soft">${escapeHtml(kind || '记录')}</span>`
                    + `<span class="asset-inspector-usage-label">${escapeHtml(label)}</span>`
                    + `<span class="asset-inspector-usage-id">${escapeHtml(text(item.id))}</span>`
                    + '</li>';
            }).join('') + '</ul>';
        }

        function renderActions(asset, version) {
            const location = text(version && version.content && version.content.location);
            const openable = Boolean(version) && isServableLocation(location);
            const draggable = Boolean(version);
            return '<div class="asset-inspector-actions">'
                + `<button class="asset-btn" type="button" data-asset-inspector-open="${escapeAttr(location)}"`
                + `${openable ? '' : ' disabled'} title="${escapeAttr(openable ? location : '该版本没有可直接打开的位置')}">`
                + '<i data-lucide="external-link"></i><span>打开</span></button>'
                + `<button class="asset-btn" type="button" data-asset-inspector-drag-hint`
                + `${draggable ? '' : ' disabled'}>`
                + '<i data-lucide="move"></i><span>拖拽到画布</span></button>'
                + '</div>';
        }

        function render(asset, history, state) {
            if (!asset) return `<section class="asset-inspector empty" aria-label="资产详情"><p class="asset-inspector-note">${escapeHtml(emptyLabel)}</p></section>`;
            const status = state || {};
            const version = activeVersion(history, status.selectedVersionId);
            const versionCount = history && Array.isArray(history.versions) ? history.versions.length : 0;
            const name = text(asset.metadata && asset.metadata.name, text(asset.id));
            /* "No versions" and "versions but none resolved" are different
             * answers and read differently: the second happens when a reply
             * names a current version its own list does not contain, and saying
             * "no versions" there would be a false statement about the asset. */
            const preview = version
                ? renderPreview(asset, version)
                : `<div class="asset-inspector-preview-empty">${versionCount
                    ? '无法确定要显示的版本。'
                    : '该资产还没有任何版本。'}</div>`;
            return '<section class="asset-inspector" aria-label="资产详情">'
                + '<div class="asset-inspector-head">'
                + `<div class="asset-inspector-title"><strong>${escapeHtml(name)}</strong>`
                + `<span>${escapeHtml(text(asset.id))}</span></div>`
                + '<div class="asset-inspector-badges">'
                + badge(asset.type, typeLabels)
                + badge(asset.source, sourceLabels)
                + badge(asset.status, statusLabels)
                + `<span class="asset-inspector-badge soft">v${escapeHtml(String(versionCount))}</span>`
                + '</div></div>'
                + (status.error ? `<div class="asset-inspector-note danger">${escapeHtml(status.error)}</div>` : '')
                + (status.loading ? '<div class="asset-inspector-note">正在读取版本历史…</div>' : '')
                + preview
                + '<div class="asset-inspector-section"><h4>元数据</h4>' + renderMetadata(asset) + '</div>'
                + '<div class="asset-inspector-section"><h4>版本历史</h4>'
                + renderVersions(asset, history, version ? version.id : '') + '</div>'
                + '<div class="asset-inspector-section"><h4>来源</h4>'
                + renderProvenance(version) + '</div>'
                + '<div class="asset-inspector-section"><h4>被引用于</h4>'
                + renderUsage(status.usage) + '</div>'
                + renderActions(asset, version)
                + '</section>';
        }

        function renderProvenance(version) {
            if (!version) return '<p class="asset-inspector-note">没有可追溯的版本。</p>';
            const provenance = objectOrEmpty(version.provenance);
            const source = text(provenance.source);
            const rows = [
                ['来源', sourceLabels[source] || source],
                ['来源引用', text(provenance.source_ref)],
                ['引入者', text(provenance.actor_id)],
                ['创建时间', shortTimestamp(version.created_at)],
                ['校验和', text(version.content && version.content.checksum)],
            ].filter(([, value]) => Boolean(value));
            return '<dl class="asset-inspector-meta">' + rows.map(([label, value]) =>
                `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('') + '</dl>';
        }

        return Object.freeze({
            render,
            previewLabel: () => kindLabels,
            activeVersion: (history, selectedVersionId) => activeVersion(history, selectedVersionId),
        });
    }

    global.WorkbenchAssetInspector = Object.freeze({
        TYPES, SOURCES, STATUSES, TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS,
        PREVIEW_KINDS, PREVIEW_LABELS, BASE_PATH,
        previewKind, isServableLocation, formatSize, shortTimestamp, dragPayload,
        createClient, createInspector,
    });
}(typeof window !== 'undefined' ? window : globalThis));
