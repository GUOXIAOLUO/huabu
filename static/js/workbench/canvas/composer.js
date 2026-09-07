/* Mountable composer lifecycle. Owns the floating composer card's container,
   open/close state, node-relative positioning, and debounced update
   scheduling. Subject resolution and the dynamic provider/media/prompt
   rendering stay with the caller (the Smart page), which injects them as
   callbacks — the composer shell is product-neutral; the controls are not.

   This is the lifecycle seam for card R4-28: smart-canvas.js keeps rendering
   `updateComposer`, but the shell mechanics below are no longer Smart-owned. */
(function exposeWorkbenchCanvasComposer(global) {
    'use strict';

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const container = settings.container;
        if (!container) throw new TypeError('WorkbenchCanvasComposer requires a container element');

        let updateTimer = 0;
        let updateSeq = 0;

        function setOpen(open) {
            container.classList.toggle('open', Boolean(open));
        }

        function isOpen() {
            return container.classList.contains('open');
        }

        function positionForRect(rect, position) {
            const opts = position && typeof position === 'object' ? position : {};
            const gap = Number.isFinite(Number(opts.gap)) ? Number(opts.gap) : 14;
            const cardWidth = Number.isFinite(Number(opts.cardWidth)) ? Number(opts.cardWidth) : 540;
            if (!rect || !Number.isFinite(Number(rect.x)) || !Number.isFinite(Number(rect.y))) return;
            container.style.width = `${cardWidth}px`;
            container.style.left = `${Number(rect.x) + Number(rect.width) / 2 - cardWidth / 2}px`;
            container.style.top = `${Number(rect.y) + Number(rect.height) + gap}px`;
        }

        function cancelPending() {
            if (updateTimer) {
                clearTimeout(updateTimer);
                updateTimer = 0;
            }
            updateSeq += 1;
        }

        function scheduleUpdate(delay, onUpdate) {
            if (updateTimer) {
                clearTimeout(updateTimer);
                updateTimer = 0;
            }
            const seq = ++updateSeq;
            updateTimer = setTimeout(() => {
                updateTimer = 0;
                if (seq !== updateSeq) return;
                if (typeof onUpdate === 'function') onUpdate();
            }, Math.max(0, Number(delay) || 0));
        }

        return Object.freeze({
            container,
            setOpen,
            isOpen,
            positionForRect,
            cancelPending,
            scheduleUpdate,
        });
    }

    global.WorkbenchCanvasComposer = Object.freeze({ create });
}(window));
