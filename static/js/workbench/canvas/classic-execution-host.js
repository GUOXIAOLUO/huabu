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

    const REQUIRED_OPERATIONS = ['markRunning', 'writeOutputText', 'setRunStatus', 'render', 'save', 'notifyError'];

    function create(host) {
        const h = host && typeof host === 'object' ? host : {};
        for (const op of REQUIRED_OPERATIONS) {
            if (typeof h[op] !== 'function') {
                throw new TypeError(`WorkbenchCanvasClassicExecutionHost requires a '${op}' function`);
            }
        }
        return Object.freeze({
            markRunning(node, running) {
                h.markRunning(node, Boolean(running));
            },
            writeOutputText(node, text) {
                h.writeOutputText(node, text);
            },
            setRunStatus(node, status, error) {
                h.setRunStatus(node, status, error);
            },
            render(node) {
                h.render(node);
            },
            save() {
                h.save();
            },
            notifyError(message) {
                h.notifyError(message);
            },
        });
    }

    global.WorkbenchCanvasClassicExecutionHost = Object.freeze({ create });
}(window));
