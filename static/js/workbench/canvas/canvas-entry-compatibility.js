/* One normal Canvas URL plus list-page navigation helpers. This module does
 * not load, persist, or reinterpret Canvas data. Smart product-page routing
 * was retired by card R4-35: the unified canvas.html is the single entry,
 * and no JS constructs a navigation to smart-canvas.html. */
(function exposeWorkbenchCanvasEntryCompatibility(global) {
    'use strict';

    function requiredId(value, label) {
        const normalized = String(value || '').trim();
        if (!normalized) throw new TypeError(`${label} is required`);
        return normalized;
    }

    function normalCanvasUrl(canvasId, projectId) {
        return `/static/canvas.html?id=${encodeURIComponent(requiredId(canvasId, 'canvasId'))}&project=${encodeURIComponent(requiredId(projectId, 'projectId'))}`;
    }

    function rememberCanvasListProject(projectId, options = {}) {
        const project = String(projectId || options.defaultProject || 'default');
        try { options.storage?.setItem?.(String(options.storageKey || ''), project); } catch (_error) {}
        return project;
    }

    function rememberedCanvasListProject(options = {}) {
        try { return options.storage?.getItem?.(String(options.storageKey || '')) || options.defaultProject || 'default'; } catch (_error) { return options.defaultProject || 'default'; }
    }

    function canvasListUrl(projectId, options = {}) {
        const project = rememberCanvasListProject(projectId, options);
        return `/static/canvas-list.html?project=${encodeURIComponent(project)}`;
    }

    global.WorkbenchCanvasEntryCompatibility = Object.freeze({normalCanvasUrl, rememberCanvasListProject, rememberedCanvasListProject, canvasListUrl});
}(window));
