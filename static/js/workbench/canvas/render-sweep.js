/* Neutral Canvas render-sweep owner (R4-39 Wave 4).
 *
 * Owns the throwaway-render sweep algorithm: per-mode state capture,
 * live-media DOM reuse detection, per-node rebuild with error isolation
 * (one failing node must not prevent later nodes — including newly created
 * ones — from reaching the DOM), media element transplantation, state
 * restore, post-render passes, and the targeted-refresh path with its
 * fast-path and missing-DOM full-sweep fallback. The page supplies only the
 * product projections: the node builder, the live-media test, transplant,
 * capture/restore, post-passes and the refresh fast-path.
 */
(function exposeWorkbenchCanvasRenderSweep(global) {
    'use strict';

    function requiredFunction(settings, name) {
        if (typeof settings[name] !== 'function') {
            throw new TypeError(`RenderSweep requires ${name}`);
        }
        return settings[name];
    }

    function optionalFunction(settings, name, fallback) {
        return typeof settings[name] === 'function' ? settings[name] : fallback;
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const container = settings.container;
        if (!container || typeof container.querySelectorAll !== 'function' || typeof container.appendChild !== 'function') {
            throw new TypeError('RenderSweep requires a container element');
        }
        const getNodes = requiredFunction(settings, 'getNodes');
        const renderNode = requiredFunction(settings, 'renderNode');
        const runtime = settings.runtime || null;
        if (runtime && ['retain', 'rebuild', 'unmountAll'].some(name => typeof runtime[name] !== 'function')) {
            throw new TypeError('RenderSweep runtime requires retain, rebuild and unmountAll');
        }
        const buildNode = node => runtime ? runtime.rebuild(node.id, () => renderNode(node)) : renderNode(node);
        const isLiveMedia = optionalFunction(settings, 'isLiveMedia', () => false);
        const transplantMedia = optionalFunction(settings, 'transplantMedia', () => {});
        const applyViewport = optionalFunction(settings, 'applyViewport', () => {});
        const captureState = optionalFunction(settings, 'captureState', () => null);
        const restoreState = optionalFunction(settings, 'restoreState', () => {});
        const afterRender = optionalFunction(settings, 'afterRender', () => {});
        const refreshFastPath = typeof settings.refreshFastPath === 'function' ? settings.refreshFastPath : null;
        const escapeId = optionalFunction(settings, 'escapeId', value => {
            const css = global.CSS;
            return css && typeof css.escape === 'function' ? css.escape(value) : String(value);
        });

        function run() {
            const state = captureState('render');
            if (runtime) runtime.retain(getNodes().map(node => node.id));
            const reusable = new Map();
            container.querySelectorAll('.node').forEach(el => {
                const node = getNodes().find(n => n.id === el.dataset.id);
                if (isLiveMedia(node)) reusable.set(node.id, el);
            });
            applyViewport();
            [...container.children].forEach(child => {
                if (!reusable.has(child.dataset?.id)) child.remove();
            });
            getNodes().forEach(node => {
                try {
                    const fresh = buildNode(node);
                    const old = reusable.get(node.id);
                    container.appendChild(fresh);
                    if (old) {
                        transplantMedia(old, fresh);
                        if (old !== fresh) old.remove();
                    }
                } catch (error) {
                    console.error('[canvas] renderNode 失败，已跳过该节点：', node?.id, node?.type, error);
                }
            });
            restoreState('render', state);
            afterRender('render');
        }

        function refresh(ids) {
            const uniqueIds = [...new Set((ids || []).filter(Boolean))];
            if (!uniqueIds.length) return;
            const state = captureState('refresh');
            applyViewport();
            for (const id of uniqueIds) {
                const node = getNodes().find(n => n.id === id);
                if (!node) continue;
                if (refreshFastPath && refreshFastPath(node)) continue;
                const current = container.querySelector(`.node[data-id="${escapeId(id)}"]`);
                if (!current) {
                    // Missing DOM falls back to the full sweep, which captures
                    // and restores its own state; the outer captured state is
                    // deliberately dropped (characterized page behavior).
                    run();
                    return;
                }
                try {
                    const fresh = buildNode(node);
                    if (isLiveMedia(node)) transplantMedia(current, fresh);
                    current.replaceWith(fresh);
                } catch (error) {
                    console.error('[canvas] refreshNode 失败，已跳过该节点：', id, error);
                }
            }
            restoreState('refresh', state);
            afterRender('refresh');
        }

        function clear() {
            if (runtime) runtime.unmountAll();
            [...container.children].forEach(child => child.remove());
        }

        return Object.freeze({run, refresh, clear});
    }

    global.WorkbenchCanvasRenderSweep = Object.freeze({create});
}(typeof window !== 'undefined' ? window : globalThis));
