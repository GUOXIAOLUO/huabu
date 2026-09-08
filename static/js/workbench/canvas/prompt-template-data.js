/* Pure prompt-template projections shared by the Canvas compatibility UI. */
(function exposePromptTemplateData(global) {
    'use strict';
    function name(template, english) { return english && template?.name_en ? template.name_en : template?.name || ''; }
    function scene(template, english) { return english && template?.scene_en ? template.scene_en : template?.scene || ''; }
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
    global.WorkbenchCanvasPromptTemplateData = Object.freeze({name, scene, text, searchText, visibleItems, defaultName, categoryLabel});
}(window));
