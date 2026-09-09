/* Pure prompt-template projections shared by the Canvas compatibility UI. */
(function exposePromptTemplateData(global) {
    'use strict';
    function name(template, english) { return english && template?.name_en ? template.name_en : template?.name || ''; }
    function scene(template, english) { return english && template?.scene_en ? template.scene_en : template?.scene || ''; }
    function positiveText(template) { return String(template?.positive || '').trim(); }
    function displayScene(template, english) { return scene(template, english) || positiveText(template); }
    function negativeText(template) { return String(template?.negative || '').trim(); }
    function text(template, mode = 'positive') {
        const positive = String(template?.positive || '').trim();
        if (mode === 'positive') return positive;
        const negative = String(template?.negative || '').trim();
        const params = Object.entries(template?.params || {}).map(([key, value]) => `${key}: ${value}`).join('\n');
        return [positive, negative ? `Negative prompt:\n${negative}` : '', params ? `Params:\n${params}` : ''].filter(Boolean).join('\n\n');
    }
    function searchText(template) {
        return [template?.name, template?.name_en, template?.scene, template?.scene_en, template?.positive, template?.negative, template?.libraryName].join(' ').toLowerCase();
    }
    function visibleItems({items = [], category = 'all', query = ''} = {}) {
        const needle = String(query || '').trim().toLowerCase();
        return (Array.isArray(items) ? items : []).filter(item => {
            if (category !== 'all' && item.category !== category) return false;
            return !needle || searchText(item).includes(needle);
        });
    }
    function defaultName(value) { return (String(value || '').trim().split(/\r?\n/)[0] || '新提示词').slice(0, 28); }
    function categoryLabel(category, options = {}) {
        if (category === 'all') return options.allLabel || 'all';
        const groups = Array.isArray(options.libraryGroups) ? options.libraryGroups : [];
        if (options.remote && groups.length) return groups.find(group => group.id === category)?.name || category || '';
        const builtin = options.builtinLabels || {};
        return builtin[category] || (Array.isArray(options.fallbackGroups) ? options.fallbackGroups.find(group => group.id === category)?.name : '') || category || '';
    }
    function categoryCounts(items = []) {
        return (Array.isArray(items) ? items : []).reduce((counts, item) => {
            const category = item?.category || 'mine';
            counts[category] = (counts[category] || 0) + 1;
            counts.all += 1;
            return counts;
        }, {all: 0});
    }
    function selectedId(items = [], current = '') {
        const list = Array.isArray(items) ? items : [];
        return list.some(item => item?.id === current) ? current : (list[0]?.id || '');
    }
    function selectedItem(items = [], current = '') {
        const list = Array.isArray(items) ? items : [];
        return list.find(item => item?.id === current) || list[0] || null;
    }
    function nodeText(nodes, nodeId) {
        const node = (Array.isArray(nodes) ? nodes : []).find(item => item?.id === nodeId && item?.type === 'prompt');
        return String(node?.text || '').trim();
    }
    function paramsText(template) {
        return Object.entries(template?.params || {}).map(([key, value]) => `${key}: ${value}`).join('\n');
    }
    function sourceLabel(template, labels = {}) {
        return template?.builtin ? (labels.builtin || '') : (labels.mine || '');
    }
    function detailSourceLabel(template, labels = {}) {
        return template?.builtin ? (labels.builtin || '') : (labels.mine || '');
    }
    function preview(template) {
        return Object.freeze({positive: positiveText(template), negative: negativeText(template), params: paramsText(template)});
    }
    function itemCard(item, selected, options = {}) {
        const escapeHtml = options.escapeHtml || (value => value);
        const escapeAttr = options.escapeAttr || (value => value);
        const nameValue = name(item, options.english);
        const sceneValue = displayScene(item, options.english);
        const category = options.categoryLabel ? options.categoryLabel(item?.category || 'mine') : item?.category || 'mine';
        const source = sourceLabel(item, options.sourceLabels || {});
        return `<button type="button" class="prompt-template-card ${item?.id === selected ? 'active' : ''}" data-template-id="${escapeAttr(item?.id || '')}"><span class="prompt-template-card-top"><span class="prompt-template-name">${escapeHtml(nameValue)}</span><span class="prompt-template-source">${escapeHtml(source)}</span></span><span class="prompt-template-scene">${escapeHtml(sceneValue)}</span><span class="prompt-template-tag">${escapeHtml(category)}</span></button>`;
    }
    function emptyState(label, escapeHtml = value => value) {
        return `<div class="prompt-template-list-empty">${escapeHtml(label || '')}</div>`;
    }
    function detailEmptyState(label, escapeHtml = value => value) {
        return `<div class="prompt-template-empty">${escapeHtml(label || '')}</div>`;
    }
    global.WorkbenchCanvasPromptTemplateData = Object.freeze({name, scene, displayScene, positiveText, negativeText, preview, itemCard, emptyState, detailEmptyState, text, searchText, visibleItems, defaultName, categoryLabel, categoryCounts, selectedId, selectedItem, nodeText, paramsText, sourceLabel, detailSourceLabel});
}(window));
