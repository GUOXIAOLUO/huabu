/* Mountable Classic provider-control host. Owns the bounded contract for
   applying a provider-card control change to Canvas state (write a node field,
   persist, re-render), so provider-shaped controls no longer mutate page state
   directly. It is NOT an R7 provider registry — it never resolves
   provider/model metadata or renders a body.

   This is the seam for card R4-32: the Classic page injects its concrete
   Canvas operations (the subject), and provider-card controls call this frozen
   handle (the shell). The module is product-neutral and owns no Canvas state. */
(function exposeWorkbenchCanvasProviderControls(global) {
    'use strict';

    const REQUIRED_OPERATIONS = ['setField', 'save', 'render'];

    function create(host) {
        const h = host && typeof host === 'object' ? host : {};
        for (const op of REQUIRED_OPERATIONS) {
            if (typeof h[op] !== 'function') {
                throw new TypeError(`WorkbenchCanvasProviderControls requires a '${op}' function`);
            }
        }
        return Object.freeze({
            setField(node, key, value) {
                h.setField(node, key, value);
            },
            save() {
                h.save();
            },
            render() {
                h.render();
            },
        });
    }

    global.WorkbenchCanvasProviderControls = Object.freeze({ create });
}(window));
