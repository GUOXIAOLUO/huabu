/* Prompt-template modal HTML renderer. State and effects remain page callbacks. */
(function exposePromptTemplateRenderer(global) {
    'use strict';
    function render(options = {}) {
        const {
            groups = [], categories = [], counts = {}, category = 'all', groupEdit = false,
            items = [], selected = null, editable = false, editMode = false, promptGroups = [],
            tr = key => key, escapeHtml = value => value, escapeAttr = value => value,
            name = item => item?.name || '', scene = item => item?.scene || '', categoryLabel = value => value,
            sourceLabel = item => item?.builtin ? tr('smart.tplBuiltin') : tr('smart.tplMine'),
            positiveText = item => item?.positive || '', negativeText = item => item?.negative || '',
            paramsText = item => Object.entries(item?.params || {}).map(([key, value]) => `${key}: ${value}`).join('\n'),
        } = options;
        const builtins = ['view', 'storyboard', 'character', 'product', 'lighting', 'mine'];
        const categoriesHtml = groupEdit ? `
            <div class="prompt-template-group-panel"><div class="prompt-template-group-title"><div>
                <strong>${escapeHtml(tr('smart.tplGroupManage'))}</strong><span>${escapeHtml(tr('smart.tplGroupHint'))}</span>
            </div><div class="prompt-template-group-tools">
                <button type="button" data-template-cat-new><i data-lucide="plus"></i><span>${escapeHtml(tr('smart.tplAdd'))}</span></button>
                <button type="button" class="primary" data-template-group-edit><i data-lucide="check"></i><span>${escapeHtml(tr('smart.tplDone'))}</span></button>
            </div></div><div class="prompt-template-group-list">
                ${groups.map(group => `<div class="prompt-template-group-row ${builtins.includes(group.id) ? '' : 'has-delete'}">
                    <button type="button" class="group-name ${group.id === category ? 'active' : ''}" data-template-cat="${escapeAttr(group.id)}"><span>${escapeHtml(categoryLabel(group.id))}</span><small>${counts[group.id] || 0}</small></button>
                    <button type="button" class="group-tool" data-template-cat-edit="${escapeAttr(group.id)}" title="${escapeAttr(tr('smart.tplRename'))}"><i data-lucide="pencil"></i></button>
                    ${builtins.includes(group.id) ? '' : `<button type="button" class="group-tool danger" data-template-cat-delete="${escapeAttr(group.id)}" title="${escapeAttr(tr('common.delete'))}"><i data-lucide="trash-2"></i></button>`}
                </div>`).join('')}
            </div></div>` : `
            <div class="prompt-template-nav"><div class="prompt-template-tabs">
                ${categories.map(cat => `<button type="button" class="${cat.id === category ? 'active' : ''}" data-template-cat="${escapeAttr(cat.id)}"><span>${escapeHtml(cat.name)}</span><small>${counts[cat.id] || 0}</small></button>`).join('')}
            </div><button type="button" class="prompt-template-manage-groups" data-template-group-edit><i data-lucide="settings-2"></i><span>${escapeHtml(tr('smart.tplManageGroups'))}</span></button></div>`;
        const listHtml = items.length ? items.map(item => `<button type="button" class="prompt-template-card ${item.id === selected?.id ? 'active' : ''}" data-template-id="${escapeAttr(item.id)}"><span class="prompt-template-card-top"><span class="prompt-template-name">${escapeHtml(name(item))}</span><span class="prompt-template-source">${escapeHtml(sourceLabel(item))}</span></span><span class="prompt-template-scene">${escapeHtml(scene(item) || item.positive || '')}</span><span class="prompt-template-tag">${escapeHtml(categoryLabel(item.category || 'mine'))}</span></button>`).join('') : `<div class="prompt-template-list-empty">${escapeHtml(tr('smart.tplNoMatches'))}</div>`;
        const detailHtml = selected ? `<div class="prompt-template-detail-head"><div><strong>${escapeHtml(name(selected) || '')}</strong><span>${escapeHtml(categoryLabel(selected.category || ''))} · ${escapeHtml(selected.builtin ? tr('smart.tplBuiltinTemplate') : tr('smart.tplMineTemplate'))}</span></div>${editMode ? '' : `<div class="prompt-template-icon-actions"><button type="button" data-template-edit title="${escapeAttr(tr('smart.tplEditTemplate'))}"><i data-lucide="pencil"></i><span>${escapeHtml(tr('common.edit'))}</span></button><button type="button" class="danger" data-template-delete title="${escapeAttr(tr('smart.tplDeleteTemplate'))}"><i data-lucide="trash-2"></i><span>${escapeHtml(tr('common.delete'))}</span></button></div>`}</div>${editMode ? `<div class="prompt-template-edit-fields"><label>${escapeHtml(tr('smart.tplName'))}</label><input data-template-edit-name value="${escapeAttr(name(selected) || '')}" placeholder="${escapeAttr(tr('smart.tplName'))}"><label>${escapeHtml(tr('smart.tplGroup'))}</label><select data-template-edit-category>${promptGroups.map(group => `<option value="${escapeAttr(group.id)}" ${group.id === (selected.category || 'mine') ? 'selected' : ''}>${escapeHtml(categoryLabel(group.id))}</option>`).join('')}</select><label>${escapeHtml(tr('smart.tplContent'))}</label><textarea data-template-edit-text placeholder="${escapeAttr(tr('smart.tplContent'))}">${escapeHtml(positiveText(selected))}</textarea></div>` : `<div class="prompt-template-preview-content"><div class="prompt-template-section"><label>${escapeHtml(tr('smart.tplPositive'))}</label><p>${escapeHtml(positiveText(selected))}</p></div>${negativeText(selected) ? `<div class="prompt-template-section"><label>${escapeHtml(tr('smart.tplNegative'))}</label><p>${escapeHtml(negativeText(selected))}</p></div>` : ''}${paramsText(selected) ? `<div class="prompt-template-section"><label>${escapeHtml(tr('smart.tplParams'))}</label><p>${escapeHtml(paramsText(selected))}</p></div>` : ''}</div>`}<div class="prompt-template-actions">${editMode ? `<button type="button" data-template-edit-cancel><i data-lucide="x"></i><span>${escapeHtml(tr('common.cancel'))}</span></button><button type="button" class="danger" data-template-delete><i data-lucide="trash-2"></i><span>${escapeHtml(tr('common.delete'))}</span></button><button type="button" class="primary" data-template-edit-save><i data-lucide="save"></i><span>${escapeHtml(tr('common.save'))}</span></button>` : `<button type="button" data-template-apply="positive"><i data-lucide="corner-down-left"></i><span>${escapeHtml(tr('smart.tplApplyPositive'))}</span></button><button type="button" class="primary" data-template-apply="full"><i data-lucide="wand-sparkles"></i><span>${escapeHtml(tr('smart.tplApplyFull'))}</span></button>`}</div>` : `<div class="prompt-template-empty">${escapeHtml(tr('smart.tplPickOrCreate'))}</div>`;
        return Object.freeze({categories: categoriesHtml, body: `<div class="prompt-template-list"><div class="prompt-template-list-tools"><button type="button" ${editable ? '' : 'disabled'} data-template-save-current><i data-lucide="bookmark-plus"></i><span>${escapeHtml(tr('smart.tplSaveCurrent'))}</span></button><button type="button" ${editable ? '' : 'disabled'} data-template-new><i data-lucide="file-plus-2"></i><span>${escapeHtml(tr('smart.tplNewTemplate'))}</span></button></div>${listHtml}</div><div class="prompt-template-detail">${detailHtml}</div>`});
    }
    function renderPreviewInputs(promptInputs = [], escapeHtml = value => value) {
        const items = Array.isArray(promptInputs) ? promptInputs : [];
        if (!items.length) return '';
        return `<div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Prompts</div>${items.map(src => `<div class="text-[11px] text-slate-500 bg-slate-50 border border-slate-100 rounded-xl px-3 py-2 line-clamp-2">${escapeHtml(src?.label || '')}</div>`).join('')}`;
    }
    function previewState(promptInputs = []) {
        const items = Array.isArray(promptInputs) ? promptInputs.filter(item => item && String(item.label || '').trim()) : [];
        return Object.freeze({items, empty: items.length === 0});
    }
    global.WorkbenchCanvasPromptTemplateRenderer = Object.freeze({render, renderPreviewInputs, previewState});
}(window));
