/* Mountable Smart execution host. Owns the bounded contract for the Canvas
   lifecycle/state operations the retained pre-R8 execution path needs, so
   execution no longer mutates page state directly. It is NOT an
   ExecutorRegistry / ExecutionRuntime — it never persists, selects providers,
   or substitutes a runtime (R8 owns that).

   This is the seam for card R4-30: the Smart page injects its concrete Canvas
   operations (the subject), and execution functions call this frozen handle
   (the shell). The module is product-neutral and owns no Canvas state. */
(function exposeWorkbenchCanvasExecutionHost(global) {
    'use strict';

    const REQUIRED_OPERATIONS = ['markRunning', 'writePromptResult', 'save', 'render', 'notifyError'];

    function create(host) {
        const h = host && typeof host === 'object' ? host : {};
        for (const op of REQUIRED_OPERATIONS) {
            if (typeof h[op] !== 'function') {
                throw new TypeError(`WorkbenchCanvasExecutionHost requires a '${op}' function`);
            }
        }
        return Object.freeze({
            markRunning(node, running) {
                h.markRunning(node, Boolean(running));
            },
            writePromptResult(node, result) {
                h.writePromptResult(node, result);
            },
            save() {
                h.save();
            },
            render() {
                h.render();
            },
            notifyError(message) {
                h.notifyError(message);
            },
        });
    }

    global.WorkbenchCanvasExecutionHost = Object.freeze({ create });
}(window));
