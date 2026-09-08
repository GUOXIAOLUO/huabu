/*
 * Neutral Canvas application bootstrap.
 *
 * Owns startup ordering and record/list routing.  Product-specific rendering,
 * execution and persistence remain behind the injected host adapter.
 */
(function (global) {
    'use strict';

    const REQUIRED_OPS = [
        'initializeTheme',
        'initializeToolbar',
        'applyTranslations',
        'updateDocumentTitle',
        'initializeOutputCompare',
        'initializeOutputPreview',
        'applyViewport',
        'revealAssetControls',
        'loadConfiguration',
        'pruneConfiguration',
        'openCanvas',
        'canvasListUrl',
        'navigate',
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasAppBootstrap.create: host must be an object');
        }
        REQUIRED_OPS.forEach(name => {
            if (typeof host[name] !== 'function') {
                throw new TypeError(`WorkbenchCanvasAppBootstrap.create: missing required host op "${name}"`);
            }
        });

        async function start({search = ''} = {}) {
            host.initializeTheme();
            host.initializeToolbar();
            host.applyTranslations();
            host.updateDocumentTitle();
            host.initializeOutputCompare();
            host.initializeOutputPreview();
            host.applyViewport();
            host.revealAssetControls();
            await host.loadConfiguration();
            host.pruneConfiguration();

            const canvasId = new URLSearchParams(String(search || '')).get('id');
            if (canvasId) {
                await host.openCanvas(canvasId);
                return Object.freeze({destination: 'canvas', canvasId});
            }

            const url = String(host.canvasListUrl() || '');
            host.navigate(url);
            return Object.freeze({destination: 'list', url});
        }

        return Object.freeze({start});
    }

    global.WorkbenchCanvasAppBootstrap = Object.freeze({create, REQUIRED_OPS});
}(typeof window !== 'undefined' ? window : globalThis));
