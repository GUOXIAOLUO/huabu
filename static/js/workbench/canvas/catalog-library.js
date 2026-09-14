/* Generic Catalog presentation helpers for the Resources surface. */
(function(global){
    function text(value){ return String(value ?? '').toLowerCase(); }
    function filterItems(items, query, attributeKey){
        const needle = text(query).trim();
        return (Array.isArray(items) ? items : []).filter(item => {
            const version = item.current_version || item.currentVersion || {};
            const attributes = version.attributes || item.attributes || {};
            if(attributeKey && !String(attributes[attributeKey] ?? '').trim()) return false;
            if(!needle) return true;
            return [item.title, item.id, JSON.stringify(attributes), JSON.stringify(item.metadata)]
                .some(value => text(value).includes(needle));
        });
    }
    function dragPayload(catalog, item, version){
        const versionId = version?.id || item?.current_version_id || '';
        return {
            type:'catalog_item_version',
            catalog_id:catalog?.id || item?.catalog_id || '',
            item_id:item?.id || '',
            catalog_item_version_id:versionId,
            version_id:versionId,
            reference_only:true
        };
    }
    function render(state, helpers){
        const h = helpers.escapeHtml;
        const catalogs = Array.isArray(state.catalogs) ? state.catalogs : [];
        const catalog = catalogs.find(item => item.id === state.selectedCatalogId) || null;
        const schema = catalog?.schema || catalog?.catalog_schema || {attributes:[]};
        const attributes = Array.isArray(schema.attributes) ? schema.attributes : [];
        const filtered = filterItems(state.items, state.query, state.attributeKey);
        const cards = filtered.map(item => {
            const version = (state.versions || []).find(entry => entry.id === item.current_version_id);
            const itemAttributes = version?.attributes || {};
            const summary = Object.entries(itemAttributes).slice(0, 3).map(([key, value]) => `${h(key)}: ${h(typeof value === 'object' ? JSON.stringify(value) : value)}`).join(' · ');
            return `<button type="button" class="catalog-item-card ${item.id === state.selectedItemId ? 'active' : ''}" draggable="true" data-catalog-item-select="${h(item.id)}" data-catalog-item="${h(item.id)}"><strong>${h(item.title)}</strong><span>${h(item.id)} · ${item.version_ids?.length || 0} 个版本</span><small>${summary || '暂无属性'}</small></button>`;
        }).join('');
        const inspector = state.selectedItem ? `<section class="catalog-inspector" aria-label="目录条目详情"><div class="asset-view-head"><div><h3>${h(state.selectedItem.title)}</h3><p>${h(state.selectedItem.id)} · 当前版本 ${h(state.selectedItem.current_version_id || '未设置')}</p></div></div><div class="catalog-version-list">${(state.versions || []).map(version => `<button type="button" class="catalog-version ${version.id === state.selectedVersionId ? 'active' : ''}" data-catalog-version="${h(version.id)}">v${version.ordinal} · ${h(version.id)}${version.id === state.selectedItem.current_version_id ? ' · 当前' : ''}</button>`).join('') || '<span class="asset-empty">暂无版本</span>'}</div>${state.selectedVersion ? `<dl class="catalog-attributes">${Object.entries(state.selectedVersion.attributes || {}).map(([key, value]) => `<div><dt>${h(key)}</dt><dd>${h(typeof value === 'object' ? JSON.stringify(value) : value)}</dd></div>`).join('') || '<div><dt>属性</dt><dd>暂无</dd></div>'}</dl><div class="catalog-media-refs">媒体引用：${state.selectedVersion.media_refs?.length || 0} 个</div><p class="catalog-drag-hint">可将条目拖入支持引用的集合或任务。</p>` : ''}</section>` : '<section class="catalog-inspector asset-empty">选择一个目录条目查看详情。</section>';
        return `<div class="catalog-manager"><aside class="catalog-list"><div class="asset-view-head"><div><h2>目录</h2><p>浏览通用目录与版本化条目。</p></div></div>${catalogs.map(item => `<button type="button" class="catalog-card ${item.id === state.selectedCatalogId ? 'active' : ''}" data-catalog-select="${h(item.id)}"><strong>${h(item.name)}</strong><span>${item.item_ids?.length || 0} 个条目 · ${h(item.scope)}</span></button>`).join('') || '<p class="asset-empty">暂无可用目录。</p>'}</aside><section class="catalog-content"><div class="catalog-toolbar"><span>${h(catalog?.name || '目录')}</span><span>${filtered.length} / ${state.items.length} 个条目</span></div><div class="catalog-filters"><button type="button" class="catalog-filter ${!state.attributeKey ? 'active' : ''}" data-catalog-attribute-filter="">全部</button>${attributes.map(attribute => `<button type="button" class="catalog-filter ${state.attributeKey === attribute.key ? 'active' : ''}" data-catalog-attribute-filter="${h(attribute.key)}">${h(attribute.label)}</button>`).join('')}</div><div class="catalog-item-grid">${cards || '<p class="asset-empty">没有匹配的目录条目。</p>'}</div></section>${inspector}</div>`;
    }
    global.WorkbenchCatalogLibrary = Object.freeze({filterItems, dragPayload, render});
})(window);
