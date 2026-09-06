/* Shared Canvas-record version polling for temporary editor adapters. */
(function exposeCanvasRemoteSync(global) {
    'use strict';

    function positiveNumber(value, fallback) {
        const number = Number(value);
        return Number.isFinite(number) && number > 0 ? number : fallback;
    }

    function create(options) {
        const settings = options || {};
        if (typeof settings.canvasId !== 'function') throw new TypeError('canvasId callback is required');
        if (typeof settings.currentUpdatedAt !== 'function') throw new TypeError('currentUpdatedAt callback is required');
        if (typeof settings.onNewer !== 'function') throw new TypeError('onNewer callback is required');
        const isEligible = typeof settings.isEligible === 'function' ? settings.isEligible : () => true;
        const intervalMs = positiveNumber(settings.intervalMs, 5000);
        let timer = null;
        let checking = false;

        async function check() {
            if (checking || !isEligible()) return false;
            const canvasId = settings.canvasId();
            if (!canvasId) return false;
            checking = true;
            try {
                const result = await global.WorkbenchCanvasPersistence.metadata(canvasId);
                if (!result.ok) return false;
                // Revision ordering first; the timestamp comparison remains the
                // bounded fallback for revision-less (legacy) version probes.
                const remoteRevision = Number(result.revision || 0);
                const newer = remoteRevision > 0
                    ? remoteRevision > Number(typeof settings.currentRevision === 'function' ? settings.currentRevision() : 0)
                    : result.updatedAt > Number(settings.currentUpdatedAt() || 0);
                if (!newer) return false;
                await settings.onNewer(result);
                return true;
            } catch (error) {
                return false;
            } finally {
                checking = false;
            }
        }

        function start() {
            if (timer !== null) return;
            timer = setInterval(() => { check(); }, intervalMs);
        }

        function stop() {
            if (timer === null) return;
            clearInterval(timer);
            timer = null;
        }

        return Object.freeze({check, start, stop, isRunning: () => timer !== null});
    }

    global.WorkbenchCanvasRemoteSync = Object.freeze({create});
}(window));
