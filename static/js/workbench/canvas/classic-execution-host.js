/* Mountable Classic execution host. Owns the bounded contract for the Canvas
   lifecycle/state operations the retained pre-R8 Classic execution path needs,
   so execution no longer mutates page state directly. It is NOT an
   ExecutorRegistry / ExecutionRuntime — it never persists, selects providers,
   or substitutes a runtime (R8 owns that).

   This is the seam for card R4-33: the Classic page injects its concrete
   Canvas operations (the subject), and execution functions call this frozen
   handle (the shell). The module is product-neutral and owns no Canvas state. */
(function exposeWorkbenchCanvasClassicExecutionHost(global) {
    'use strict';

    function create(host) {
        if (!global.WorkbenchCanvasExecutionHost || typeof global.WorkbenchCanvasExecutionHost.createClassic !== 'function') {
            throw new Error('WorkbenchCanvasClassicExecutionHost requires WorkbenchCanvasExecutionHost');
        }
        return global.WorkbenchCanvasExecutionHost.createClassic(host);
    }

    function createChat(host) {
        if (!global.WorkbenchCanvasExecutionHost || typeof global.WorkbenchCanvasExecutionHost.createClassicChat !== 'function') {
            throw new Error('WorkbenchCanvasClassicExecutionHost requires WorkbenchCanvasExecutionHost');
        }
        return global.WorkbenchCanvasExecutionHost.createClassicChat(host);
    }

    global.WorkbenchCanvasClassicExecutionHost = Object.freeze({ create, createChat });
}(window));
