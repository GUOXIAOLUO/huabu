/* Canvas adapter for the generic workspace session. It projects current
   selection/canvas context without taking ownership of Canvas persistence. */
(function exposeWorkbenchCanvasWorkspaceSession(global) {
    'use strict';

    function create(options) {
        const settings = options || {};
        const Runtime = global.WorkbenchWorkspaceSession;
        if (!Runtime) throw new Error('WorkspaceSession runtime is required');
        if (typeof settings.getSelection !== 'function') {
            throw new TypeError('Canvas workspace session requires getSelection');
        }
        if (typeof settings.getCanvas !== 'function') {
            throw new TypeError('Canvas workspace session requires getCanvas');
        }
        const session = Runtime.create(settings);

        function openFromSelection(nodeId) {
            const key = String(nodeId || '').trim();
            if (!key) throw new TypeError('workspace nodeId is required');
            const canvas = settings.getCanvas();
            const selection = settings.getSelection();
            return session.open({
                ...(typeof settings.getContext === 'function' ? (settings.getContext() || {}) : {}),
                nodeId: key,
                selection: Array.isArray(selection) ? selection : [],
                canvasId: canvas?.id || null,
                projectId: canvas?.project || null,
            });
        }

        return Object.freeze({...session, openFromSelection});
    }

    global.WorkbenchCanvasWorkspaceSession = Object.freeze({create});
}(window));
