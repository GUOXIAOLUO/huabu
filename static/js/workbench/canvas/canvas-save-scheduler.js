/* Shared Canvas save scheduling: debounce, in-flight coalescing, retry marking,
   plus one deferred remote-apply retry owner per editor. */
(function exposeCanvasSaveScheduler(global) {
    'use strict';

    function positiveNumber(value, fallback) {
        const number = Number(value);
        return Number.isFinite(number) && number > 0 ? number : fallback;
    }

    function create(options) {
        const settings = options || {};
        if (typeof settings.run !== 'function') throw new TypeError('run callback is required');
        const debounceMs = positiveNumber(settings.debounceMs, 500);
        // allowOverlap preserves adapters whose save request may run concurrently
        // with an in-flight one; the default coalesces into one retry instead.
        const allowOverlap = settings.allowOverlap === true;
        const onRetry = typeof settings.onRetry === 'function' ? settings.onRetry : () => {};
        let timer = null;
        let retryTimer = null;
        let inFlightCount = 0;
        let again = false;
        const activeRuns = new Set();

        function schedule(delayMs) {
            if (inFlightCount > 0 && !allowOverlap) {
                clearTimeout(timer);
                timer = null;
                again = true;
                return;
            }
            clearTimeout(timer);
            timer = setTimeout(() => {
                timer = null;
                flush();
            }, positiveNumber(delayMs, debounceMs));
        }

        async function flush() {
            if (inFlightCount > 0 && !allowOverlap) {
                again = true;
                return false;
            }
            inFlightCount += 1;
            again = false;
            const run = (async () => {
                try {
                    await settings.run();
                } finally {
                    inFlightCount -= 1;
                    if (inFlightCount === 0 && again) {
                        again = false;
                        onRetry();
                        retryTimer = setTimeout(() => {
                            retryTimer = null;
                            flush();
                        }, 0);
                    }
                }
                return true;
            })();
            activeRuns.add(run);
            try {
                return await run;
            } finally {
                activeRuns.delete(run);
            }
        }

        function cancel() {
            clearTimeout(timer);
            timer = null;
            clearTimeout(retryTimer);
            retryTimer = null;
            again = false;
        }

        async function drain() {
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
                again = true;
            }
            if (retryTimer !== null) {
                clearTimeout(retryTimer);
                retryTimer = null;
                again = true;
            }
            while (activeRuns.size > 0 || again) {
                if (activeRuns.size > 0) {
                    await Promise.all(Array.from(activeRuns));
                } else if (again) {
                    await flush();
                }
                if (retryTimer !== null) {
                    clearTimeout(retryTimer);
                    retryTimer = null;
                    again = true;
                }
            }
        }

        function markAgain() {
            if (!allowOverlap) again = true;
        }

        return Object.freeze({
            schedule,
            flush,
            drain,
            cancel,
            markAgain,
            isInFlight: () => inFlightCount > 0,
            hasPendingAgain: () => again,
            hasScheduled: () => timer !== null,
        });
    }

    // One pending remote-apply/reload retry per editor. The adapter supplies the
    // apply action, its deferral conditions and its policy delays; this owner
    // keeps the single pending slot and replaces any pending attempt, matching
    // both adapters' prior clear-then-set timer behavior.
    function createRemoteApply(options) {
        const settings = options || {};
        if (typeof settings.apply !== 'function') throw new TypeError('apply callback is required');
        const defaultDelayMs = positiveNumber(settings.defaultDelayMs, 200);
        let timer = null;

        function schedule(delayMs) {
            clearTimeout(timer);
            timer = setTimeout(() => {
                timer = null;
                settings.apply();
            }, positiveNumber(delayMs, defaultDelayMs));
        }

        function cancel() {
            clearTimeout(timer);
            timer = null;
        }

        return Object.freeze({
            schedule,
            cancel,
            hasPending: () => timer !== null,
        });
    }

    global.WorkbenchCanvasSaveScheduler = Object.freeze({create, createRemoteApply});
}(window));
