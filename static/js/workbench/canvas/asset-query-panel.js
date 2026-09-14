/* Canonical asset search: the filter an asset search is, the canonical API
 * request it becomes, and the presentation of one result page.
 *
 * Ownership boundary: this module owns *query state* (the filter vocabulary and
 * the page window) and the rendering of results — including which row is marked
 * as the selected one, which the host passes in as `selectedAssetId`. It never
 * persists an asset, never reads or writes Canvas JSON, never reimplements the
 * resource tree, and never talks to SQLite — the host page supplies the
 * transport, the actor and every event, and `AssetService.query` /
 * `/api/v1/assets/query` own what a filter means.
 *
 * It is deliberately pure where it can be: `render()` returns an HTML string
 * and the host page owns the DOM, so the host keeps its single focus and IME
 * handling path instead of this module growing a second one.
 *
 * The filter vocabulary is the domain's own closed sets. A value the server
 * would reject is rejected here first, so a typo fails at the control the user
 * touched rather than as an empty result page. */
(function exposeWorkbenchAssetQueryPanel(global) {
    'use strict';

    const TYPES = Object.freeze(['image', 'video', 'audio', 'document', 'model', 'workflow', 'other']);
    const SOURCES = Object.freeze(['upload', 'url', 'local_path', 'provider', 'import', 'execution']);
    const STATUSES = Object.freeze(['draft', 'ready', 'archived']);
    const PAGE_SIZES = Object.freeze([24, 48, 96]);
    const DEFAULT_PAGE_SIZE = 24;
    const MAX_TEXT_LENGTH = 200;
    const MAX_TAG_LENGTH = 64;
    const BASE_PATH = '/api/v1/assets/query';

    const TYPE_LABELS = Object.freeze({
        image: '图片', video: '视频', audio: '音频', document: '文档',
        model: '模型', workflow: '工作流', other: '其他',
    });
    const SOURCE_LABELS = Object.freeze({
        upload: '上传', url: '链接', local_path: '本地路径', provider: '供应商', import: '导入', execution: '执行结果',
    });
    const STATUS_LABELS = Object.freeze({draft: '草稿', ready: '就绪', archived: '归档'});

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function boundedText(value, label, maxLength) {
        const normalized = String(value ?? '').trim();
        if (normalized.length > maxLength) throw new TypeError(`${label} must be at most ${maxLength} characters`);
        return normalized;
    }

    function memberOf(value, allowed, label) {
        const normalized = text(value);
        if (!allowed.includes(normalized)) throw new TypeError(`Unsupported ${label}: ${normalized}`);
        return normalized;
    }

    function toggle(list, value) {
        return list.includes(value) ? list.filter(item => item !== value) : [...list, value];
    }

    function allowedInteger(values, allowed, label) {
        const normalized = Number(values);
        if (!allowed.includes(normalized)) throw new TypeError(`Unsupported ${label}: ${values}`);
        return normalized;
    }

    /* One page request against one project's assets. Everything the server will
     * validate is validated here too, so a host cannot build a query the
     * canonical service would have to reject. */
    function createQuery(seed) {
        const raw = seed || {};
        let projectId = text(raw.projectId);
        if (!projectId) throw new TypeError('Asset query requires a project id');
        let queryText = boundedText(raw.text, 'Asset query text', MAX_TEXT_LENGTH);
        let types = (raw.types || []).map(value => memberOf(value, TYPES, 'asset type'));
        let sources = (raw.sources || []).map(value => memberOf(value, SOURCES, 'asset source'));
        let statuses = (raw.statuses || []).map(value => memberOf(value, STATUSES, 'asset status'));
        let tags = [];
        (raw.tags || []).forEach(value => {
            const tag = boundedText(value, 'Asset query tag', MAX_TAG_LENGTH);
            if (!tag) throw new TypeError('Asset query tag cannot be empty');
            const folded = tag.toLowerCase();
            if (!tags.includes(folded)) tags.push(folded);
        });
        let limit = allowedInteger(raw.limit ?? DEFAULT_PAGE_SIZE, PAGE_SIZES, 'asset page size');
        let offset = Number(raw.offset ?? 0);
        if (!Number.isInteger(offset) || offset < 0) throw new TypeError('Asset query offset must be a non-negative integer');

        /* Any change to *what* matches resets the window: staying on page 4 of a
         * narrower result set would show an empty page and read as "no match". */
        function refilter() { offset = 0; }

        function params() {
            return {
                project_id: projectId, q: queryText,
                type: types.slice(), source: sources.slice(), status: statuses.slice(),
                tag: tags.slice(), limit, offset,
            };
        }

        /* Built by hand rather than through URLSearchParams so the request shape
         * is explicit and identical in every host (and in the sandboxed tests
         * that drive this module). */
        function toSearch() {
            const pairs = [['project_id', projectId]];
            if (queryText) pairs.push(['q', queryText]);
            types.forEach(value => pairs.push(['type', value]));
            sources.forEach(value => pairs.push(['source', value]));
            statuses.forEach(value => pairs.push(['status', value]));
            tags.forEach(value => pairs.push(['tag', value]));
            pairs.push(['limit', String(limit)], ['offset', String(offset)]);
            return pairs
                .map(pair => `${encodeURIComponent(pair[0])}=${encodeURIComponent(pair[1])}`)
                .join('&');
        }

        return Object.freeze({
            projectId: () => projectId,
            text: () => queryText,
            setText: value => { queryText = boundedText(value, 'Asset query text', MAX_TEXT_LENGTH); refilter(); return queryText; },
            types: () => types.slice(),
            toggleType: value => { types = toggle(types, memberOf(value, TYPES, 'asset type')); refilter(); return types.slice(); },
            sources: () => sources.slice(),
            toggleSource: value => { sources = toggle(sources, memberOf(value, SOURCES, 'asset source')); refilter(); return sources.slice(); },
            statuses: () => statuses.slice(),
            toggleStatus: value => { statuses = toggle(statuses, memberOf(value, STATUSES, 'asset status')); refilter(); return statuses.slice(); },
            tags: () => tags.slice(),
            addTag: value => {
                const tag = boundedText(value, 'Asset query tag', MAX_TAG_LENGTH).toLowerCase();
                if (!tag) throw new TypeError('Asset query tag cannot be empty');
                if (!tags.includes(tag)) tags = [...tags, tag];
                refilter();
                return tags.slice();
            },
            removeTag: value => { tags = tags.filter(tag => tag !== text(value).toLowerCase()); refilter(); return tags.slice(); },
            clearTags: () => { tags = []; refilter(); return tags.slice(); },
            limit: () => limit,
            setLimit: value => { limit = allowedInteger(value, PAGE_SIZES, 'asset page size'); offset = 0; return limit; },
            offset: () => offset,
            setOffset: value => {
                const next = Number(value);
                if (!Number.isInteger(next) || next < 0) throw new TypeError('Asset query offset must be a non-negative integer');
                offset = next;
                return offset;
            },
            nextPage: () => { offset += limit; return offset; },
            previousPage: () => { offset = Math.max(0, offset - limit); return offset; },
            resetPage: () => { offset = 0; return offset; },
            reset: () => {
                queryText = ''; types = []; sources = []; statuses = []; tags = [];
                limit = DEFAULT_PAGE_SIZE; offset = 0;
            },
            isFiltered: () => Boolean(queryText || types.length || sources.length || statuses.length || tags.length),
            activeFilterCount: () => types.length + sources.length + statuses.length + tags.length + (queryText ? 1 : 0),
            params,
            toSearch,
        });
    }

    /* The canonical transport. It builds one request and normalizes the reply;
     * what the server means by a filter is not re-decided here. */
    function createClient(options) {
        const settings = options || {};
        const fetchImpl = settings.fetch || global.fetch;
        if (typeof fetchImpl !== 'function') throw new TypeError('AssetQueryClient requires fetch');
        const actorId = text(settings.actorId);
        if (!actorId) throw new TypeError('AssetQueryClient requires an actor id');
        const basePath = text(settings.basePath, BASE_PATH);

        async function query(queryState) {
            if (!queryState || typeof queryState.toSearch !== 'function') {
                throw new TypeError('AssetQueryClient.query requires an asset query');
            }
            const response = await fetchImpl(`${basePath}?${queryState.toSearch()}`, {
                method: 'GET',
                headers: {'X-User-ID': actorId},
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                const detail = payload && payload.detail;
                throw new Error(typeof detail === 'string' ? detail : `资产检索失败（${response.status}）`);
            }
            const items = Array.isArray(payload.items) ? payload.items : [];
            return {
                items,
                total: Number(payload.total || 0),
                limit: Number(payload.limit || queryState.limit()),
                offset: Number(payload.offset || queryState.offset()),
                hasMore: Boolean(payload.has_more),
            };
        }

        return Object.freeze({query, basePath: () => basePath});
    }

    /* Pure presentation of one page. The host owns the DOM, the events and the
     * focus, so this never touches a live element. */
    function createPanel(options) {
        const settings = options || {};
        const escapeHtml = settings.escapeHtml;
        if (typeof escapeHtml !== 'function') throw new TypeError('AssetQueryPanel requires escapeHtml');
        const escapeAttr = typeof settings.escapeAttr === 'function' ? settings.escapeAttr : escapeHtml;
        const typeLabels = Object.assign({}, TYPE_LABELS, settings.typeLabels || {});
        const sourceLabels = Object.assign({}, SOURCE_LABELS, settings.sourceLabels || {});
        const statusLabels = Object.assign({}, STATUS_LABELS, settings.statusLabels || {});
        const placeholder = text(settings.placeholder, '按名称、编号或元数据检索资产');
        const tagPlaceholder = text(settings.tagPlaceholder, '按标签过滤后回车');
        const pageSizes = Array.isArray(settings.pageSizes) && settings.pageSizes.length
            ? settings.pageSizes.slice() : PAGE_SIZES.slice();

        function chip(attribute, id, label, active) {
            return `<button class="asset-query-chip${active ? ' active' : ''}" type="button"`
                + ` ${attribute}="${escapeAttr(id)}" aria-pressed="${active ? 'true' : 'false'}">`
                + `${escapeHtml(label)}</button>`;
        }

        function renderChips(attribute, ids, labels, selected) {
            return ids.map(id => chip(attribute, id, labels[id] || id, selected.includes(id))).join('');
        }

        function renderTagChips(query) {
            const tags = query.tags();
            if (!tags.length) return '';
            return '<div class="asset-query-tags">'
                + tags.map(tag => `<button class="asset-query-tag" type="button" data-asset-query-tag="${escapeAttr(tag)}"`
                    + ` aria-label="移除标签 ${escapeAttr(tag)}">#${escapeHtml(tag)}<i data-lucide="x"></i></button>`).join('')
                + '</div>';
        }

        function assetTitle(asset) {
            const name = asset && asset.metadata && typeof asset.metadata === 'object' ? asset.metadata.name : '';
            return text(name, text(asset && asset.id));
        }

        function renderRow(asset, selectedAssetId) {
            const versions = Array.isArray(asset.version_ids) ? asset.version_ids.length : 0;
            const id = text(asset.id);
            const selected = id !== '' && id === text(selectedAssetId);
            /* The row is a button because selecting it is the action that shows
             * the asset's inspector. The host owns the click; `aria-pressed`
             * mirrors the selection so the state is not carried by colour alone. */
            return `<li class="asset-query-row${selected ? ' active' : ''}">`
                + `<button class="asset-query-row-btn" type="button" data-asset-query-select="${escapeAttr(id)}"`
                + ` aria-pressed="${selected ? 'true' : 'false'}">`
                + '<span class="asset-query-row-main">'
                + `<strong>${escapeHtml(assetTitle(asset))}</strong>`
                + `<span class="asset-query-row-id">${escapeHtml(id)}</span>`
                + '</span>'
                + '<span class="asset-query-row-meta">'
                + `<span class="asset-query-badge">${escapeHtml(typeLabels[asset.type] || text(asset.type))}</span>`
                + `<span class="asset-query-badge soft">${escapeHtml(sourceLabels[asset.source] || text(asset.source))}</span>`
                + `<span class="asset-query-badge soft">${escapeHtml(statusLabels[asset.status] || text(asset.status))}</span>`
                + `<span class="asset-query-badge soft">v${escapeHtml(versions)}</span>`
                + '</span></button></li>';
        }

        function renderResults(page, status) {
            if (status.error) return `<div class="asset-query-note danger">${escapeHtml(status.error)}</div>`;
            if (status.loading) return '<div class="asset-query-note">正在检索…</div>';
            if (!page) return '<div class="asset-query-note">尚未检索。</div>';
            if (!page.items.length) return '<div class="asset-query-note">没有匹配的资产，试试放宽类型、来源或标签。</div>';
            return '<ul class="asset-query-list">'
                + page.items.map(asset => renderRow(asset, status.selectedAssetId)).join('')
                + '</ul>';
        }

        function renderPager(query, page, status) {
            if (!page || status.error) return '';
            const from = page.items.length ? page.offset + 1 : 0;
            const to = page.offset + page.items.length;
            const sizes = pageSizes.map(size => `<option value="${escapeAttr(size)}"`
                + `${size === query.limit() ? ' selected' : ''}>${escapeHtml(size)} / 页</option>`).join('');
            return '<div class="asset-query-pager">'
                + `<span class="asset-query-range">${from}-${to} / ${page.total}</span>`
                + `<button class="asset-btn" type="button" data-asset-query-page="prev"${page.offset > 0 ? '' : ' disabled'}>`
                + '<i data-lucide="chevron-left"></i><span>上一页</span></button>'
                + `<button class="asset-btn" type="button" data-asset-query-page="next"${page.hasMore ? '' : ' disabled'}>`
                + '<span>下一页</span><i data-lucide="chevron-right"></i></button>'
                + `<label class="asset-query-size"><i data-lucide="rows-3"></i>`
                + `<select data-asset-query-size aria-label="每页数量">${sizes}</select></label>`
                + '</div>';
        }

        function render(query, page, status) {
            if (!query) throw new TypeError('AssetQueryPanel.render requires an asset query');
            const state = status || {};
            const filters = query.activeFilterCount();
            return '<section class="asset-query" aria-label="资产检索">'
                + '<div class="asset-query-head">'
                + '<div class="asset-query-title"><strong>资产检索</strong>'
                + `<span>${filters ? `已启用 ${filters} 个筛选条件` : '按类型、来源、标签与元数据检索本项目资产'}</span></div>`
                + `<button class="asset-btn" type="button" data-asset-query-reset${filters ? '' : ' disabled'}>`
                + '<i data-lucide="rotate-ccw"></i><span>重置</span></button>'
                + '</div>'
                + '<div class="asset-query-filters">'
                + '<label class="asset-search-wrap"><i data-lucide="search"></i>'
                + `<input class="asset-search" type="search" data-asset-query-text value="${escapeAttr(query.text())}"`
                + ` placeholder="${escapeAttr(placeholder)}" aria-label="检索资产"></label>`
                + `<div class="asset-query-chip-row" role="group" aria-label="资产类型">${renderChips('data-asset-query-type', TYPES, typeLabels, query.types())}</div>`
                + `<div class="asset-query-chip-row" role="group" aria-label="资产来源">${renderChips('data-asset-query-source', SOURCES, sourceLabels, query.sources())}</div>`
                + '<label class="asset-search-wrap"><i data-lucide="tag"></i>'
                + `<input class="asset-search" type="text" data-asset-query-tag-input value="" placeholder="${escapeAttr(tagPlaceholder)}" aria-label="标签过滤"></label>`
                + '</div>'
                + renderTagChips(query)
                + '<div class="asset-query-body">' + renderResults(page, state) + '</div>'
                + renderPager(query, page, state)
                + '</section>';
        }

        return Object.freeze({render, pageSizes: () => pageSizes.slice(), basePath: () => BASE_PATH});
    }

    global.WorkbenchAssetQueryPanel = Object.freeze({
        TYPES, SOURCES, STATUSES, PAGE_SIZES, DEFAULT_PAGE_SIZE, BASE_PATH,
        TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS,
        createQuery, createClient, createPanel,
    });
}(typeof window !== 'undefined' ? window : globalThis));
