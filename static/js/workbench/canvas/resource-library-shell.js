/* Unified Resources shell: one category rail, one unified search control and
 * one resource-kind filter row, all driven by an extensible resource registry.
 *
 * Ownership boundary: this module owns Resources *presentation and selection*
 * state only. It never persists a resource, resolves a provider/model/executor,
 * mutates a Canvas/NodeRecord, or reinterprets Canvas JSON. It is deliberately
 * pure: `render()` returns an HTML string and the host page owns the DOM.
 *
 * A registered category declares a surface:
 *   - `library` — the canonical per-category surface already lives in the host
 *     page (a tab), so the host keeps that surface and the shell only selects it;
 *   - `canvas`  — the canonical surface lives in the Unified Canvas, so the host
 *     delegates to its Canvas entry instead of inventing a second library.
 *
 * Category kinds follow the target product surface (Assets / Catalogs /
 * Prompts / Skills / Workflows / Knowledge / Models / Connections /
 * Integrations / Executors) so a later round registers a new category by name
 * without changing this module. */
(function exposeWorkbenchResourceLibraryShell(global) {
    'use strict';

    const SURFACES = Object.freeze(['library', 'canvas']);

    const KINDS = Object.freeze([
        'asset', 'artifact', 'catalog', 'collection', 'prompt', 'skill',
        'workflow', 'knowledge', 'model', 'connection', 'integration', 'executor',
    ]);

    const DEFAULT_KIND_LABELS = Object.freeze({
        asset: '资产', artifact: '成果', catalog: '目录', collection: '集合',
        prompt: '提示词', skill: '技能', workflow: '工作流', knowledge: '知识',
        model: '模型', connection: '连接', integration: '集成', executor: '执行器',
    });

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function requiredText(value, label) {
        const normalized = text(value);
        if (!normalized) throw new TypeError(`${label} is required`);
        return normalized;
    }

    function list(value) {
        return Array.isArray(value) ? value : [];
    }

    function normalizeDescriptor(input) {
        const raw = input || {};
        const id = requiredText(raw.id, 'Resource category id');
        const surface = text(raw.surface, 'library');
        if (!SURFACES.includes(surface)) throw new TypeError(`Unsupported resource surface: ${surface}`);
        const kind = requiredText(raw.kind, `Resource category kind (${id})`);
        if (!KINDS.includes(kind)) throw new TypeError(`Unsupported resource kind: ${kind}`);
        const label = requiredText(raw.label, `Resource category label (${id})`);
        return Object.freeze({
            id,
            kind,
            label,
            surface,
            order: Number.isFinite(raw.order) ? Number(raw.order) : 1000,
            icon: text(raw.icon, 'circle'),
            /* library surface: the host tab id plus the host search-input id the
             * unified search writes into (empty when the category has no item
             * query state yet). */
            tab: surface === 'library' ? text(raw.tab, id) : '',
            searchId: surface === 'library' ? text(raw.searchId) : '',
            /* canvas surface: the host's Canvas entry key. */
            entry: surface === 'canvas' ? text(raw.entry, 'canvas') : '',
        });
    }

    /* Extensible registry. Registration validates eagerly and rejects duplicate
     * ids, so an extension can never silently shadow an existing category. */
    function createRegistry(seedDescriptors) {
        const descriptors = new Map();

        function register(descriptor) {
            const normalized = normalizeDescriptor(descriptor);
            if (descriptors.has(normalized.id)) throw new TypeError(`Resource category already registered: ${normalized.id}`);
            descriptors.set(normalized.id, normalized);
            return normalized;
        }

        function listCategories() {
            return [...descriptors.values()].sort((left, right) => (left.order - right.order) || left.id.localeCompare(right.id));
        }

        function get(id) { return descriptors.get(text(id)) || null; }
        function bySurface(surface) { return listCategories().filter(item => item.surface === surface); }
        function ids() { return listCategories().map(item => item.id); }
        function kinds() { return [...new Set(listCategories().map(item => item.kind))]; }

        const registry = {
            register,
            list: listCategories,
            get,
            bySurface,
            ids,
            kinds,
            size: () => descriptors.size,
        };
        list(seedDescriptors).forEach(register);
        return Object.freeze(registry);
    }

    function createShell(options) {
        const settings = options || {};
        const registry = settings.registry;
        if (!registry || typeof registry.list !== 'function' || typeof registry.get !== 'function') {
            throw new TypeError('ResourceLibraryShell requires a resource registry');
        }
        const escapeHtml = settings.escapeHtml;
        if (typeof escapeHtml !== 'function') throw new TypeError('ResourceLibraryShell requires escapeHtml');
        const escapeAttr = typeof settings.escapeAttr === 'function' ? settings.escapeAttr : escapeHtml;
        const kindLabels = Object.assign({}, DEFAULT_KIND_LABELS, settings.kindLabels || {});
        const searchPlaceholder = text(settings.searchPlaceholder, '搜索资源');
        const searchInputId = text(settings.searchInputId, 'resourceShellSearch');
        const ariaLabel = text(settings.ariaLabel, '资源类别');

        let activeId = text(settings.activeCategory);
        let query = text(settings.query);
        let kindFilter = text(settings.kindFilter);

        /* No implicit fallback: until the host selects a category the shell has
         * no active category, so `render()` cannot mark one active or show a
         * search control for a category the host never chose. */
        function active() { return registry.get(activeId); }

        function setCategory(id) {
            const next = registry.get(id);
            if (!next) throw new TypeError(`Unknown resource category: ${id}`);
            activeId = next.id;
            return next;
        }

        function setQuery(value) { query = String(value ?? ''); return query; }

        /* The kind filter is a toggle: the same kind again clears it. It only
         * accepts a kind that is actually registered. */
        function setKindFilter(kind) {
            const next = text(kind);
            if (next && !registry.kinds().includes(next)) throw new TypeError(`Unknown resource kind filter: ${next}`);
            kindFilter = kindFilter === next ? '' : next;
            return kindFilter;
        }

        function matches(descriptor) {
            if (!kindFilter) return true;
            return (descriptor || {}).kind === kindFilter;
        }

        /* What the rail shows: the kind filter's matches plus the active
         * category, so filtering can never hide the category whose surface the
         * host is currently rendering. Selecting a kind therefore filters the
         * rail without silently switching the host's active category. */
        function visibleCategories() {
            return registry.list().filter(item => matches(item) || item.id === activeId);
        }

        function kindFilterOptions() {
            return registry.kinds().map(kind => ({id: kind, label: kindLabels[kind] || kind, active: kindFilter === kind}));
        }

        function renderCategory(descriptor) {
            const isActive = descriptor.id === active()?.id;
            /* Library categories keep the host page's `data-tab` contract so the
             * host keeps exactly one tab-switch path. Canvas categories are
             * entries, not tabs. */
            const tabAttr = descriptor.surface === 'library' ? ` data-tab="${escapeAttr(descriptor.tab)}"` : '';
            const entryAttr = descriptor.surface === 'canvas' ? ` data-resource-entry="${escapeAttr(descriptor.entry)}"` : '';
            return `<button class="resource-cat${isActive ? ' active' : ''}" type="button" role="tab"`
                + ` aria-selected="${isActive ? 'true' : 'false'}"`
                + ` data-resource-category="${escapeAttr(descriptor.id)}"`
                + ` data-resource-surface="${escapeAttr(descriptor.surface)}"`
                + ` data-resource-kind="${escapeAttr(descriptor.kind)}"`
                + tabAttr + entryAttr + '>'
                + `<i data-lucide="${escapeAttr(descriptor.icon)}"></i>`
                + `<span>${escapeHtml(descriptor.label)}</span>`
                + '</button>';
        }

        function renderKindFilter() {
            const options = kindFilterOptions();
            if (!options.length) return '';
            const chips = options.map(option => `<button class="resource-filter${option.active ? ' active' : ''}" type="button"`
                + ` data-resource-kind-filter="${escapeAttr(option.id)}"`
                + ` aria-pressed="${option.active ? 'true' : 'false'}">${escapeHtml(option.label)}</button>`).join('');
            return `<div class="resource-filters" role="group" aria-label="资源类型筛选">${chips}</div>`;
        }

        function renderSearch() {
            const category = active();
            if (!category || !category.searchId) return '';
            return '<label class="resource-search-wrap"><i data-lucide="search"></i>'
                + `<input id="${escapeAttr(searchInputId)}" class="resource-search" type="search"`
                + ` value="${escapeAttr(query)}" placeholder="${escapeAttr(searchPlaceholder)}"`
                + ` data-resource-search-category="${escapeAttr(category.id)}"></label>`;
        }

        function render() {
            return '<div class="resource-shell-head">'
                + `<div class="resource-shell-rail asset-tabs" role="tablist" aria-label="${escapeAttr(ariaLabel)}">`
                + visibleCategories().map(renderCategory).join('')
                + '</div>'
                + '<div class="resource-shell-tools">'
                + renderSearch()
                + renderKindFilter()
                + '</div>'
                + '</div>';
        }

        return Object.freeze({
            registry,
            active,
            activeId: () => activeId,
            setCategory,
            query: () => query,
            setQuery,
            kindFilter: () => kindFilter,
            setKindFilter,
            matches,
            visibleCategories,
            kindFilterOptions,
            render,
        });
    }

    global.WorkbenchResourceLibraryShell = Object.freeze({
        SURFACES,
        KINDS,
        createRegistry,
        createShell,
    });
}(typeof window !== 'undefined' ? window : globalThis));
