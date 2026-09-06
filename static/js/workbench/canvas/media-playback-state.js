/* Native media playback-state preservation shared by temporary Canvas adapters. */
(function exposeCanvasMediaPlaybackState(global) {
    'use strict';

    const DEFAULT_SELECTOR = 'video[data-url], audio[data-url]';

    function capture(media) {
        if (!media) return null;
        return {
            currentTime:Number.isFinite(media.currentTime) ? media.currentTime : 0,
            paused:Boolean(media.paused),
            playbackRate:Number.isFinite(media.playbackRate) ? media.playbackRate : 1,
            muted:Boolean(media.muted),
            volume:Number.isFinite(media.volume) ? media.volume : 1
        };
    }

    function restore(media, state) {
        if (!media || !state) return;
        try { media.playbackRate = state.playbackRate || 1; } catch (_error) {}
        try { media.muted = state.muted; } catch (_error) {}
        try { media.volume = state.volume; } catch (_error) {}
        const applyTime = () => {
            if (Number.isFinite(state.currentTime) && state.currentTime > 0 && Math.abs((media.currentTime || 0) - state.currentTime) > 0.2) {
                try { media.currentTime = state.currentTime; } catch (_error) {}
            }
            if (!state.paused && typeof media.play === 'function') {
                const promise = media.play();
                if (promise?.catch) promise.catch(() => {});
            }
        };
        if (media.readyState >= 1) applyTime();
        else media.addEventListener('loadedmetadata', applyTime, {once:true});
    }

    function signature(media) {
        if (!media) return '';
        const tag = String(media.tagName || '').toLowerCase();
        const url = media.dataset?.url || media.getAttribute?.('src') || '';
        return tag && url ? `${tag}:${url}` : '';
    }

    function matchingMedia(root, options = {}) {
        const media = root?.querySelectorAll?.(options.selector || DEFAULT_SELECTOR) || [];
        if (!options.exclude) return [...media];
        return [...media].filter(item => !item.closest?.(options.exclude));
    }

    function captureAll(root, options = {}) {
        const states = new Map();
        matchingMedia(root, options).forEach(media => {
            const key = signature(media);
            if (key) states.set(key, capture(media));
        });
        return states;
    }

    function restoreAll(root, states, options = {}) {
        if (!states?.size) return;
        matchingMedia(root, options).forEach(media => restore(media, states.get(signature(media))));
    }

    global.WorkbenchCanvasMediaPlaybackState = Object.freeze({capture, restore, signature, captureAll, restoreAll});
}(window));
