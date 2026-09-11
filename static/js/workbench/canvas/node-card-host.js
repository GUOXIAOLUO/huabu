/* Reusable node-card composition boundary. A Canvas page supplies a NodeRecord
   and receives intents; this host owns shell creation and renderer selection. */
(function exposeWorkbenchNodeCardHost(global) {
    'use strict';

    if (!global.WorkbenchRendererRegistry || !global.WorkbenchNodeShell) {
        throw new Error('NodeCardHost requires RendererRegistry and NodeShell');
    }

    const registry = global.WorkbenchRendererRegistry.create();
    function hasRenderer(id, version) {
        return registry.all().some(renderer => renderer.id === id && renderer.version === version);
    }

    function registerBuiltIns() {
        if (global.WorkbenchCollectionRichNode && !hasRenderer('collection-gallery', '1')) {
            registry.register({
                id: 'collection-gallery', version: '1', priority: 120,
                canRender: node => global.WorkbenchCollectionRichNode.isCompatible(node),
                mount: (shell, node, options) => global.WorkbenchCollectionRichNode.mount(shell, node, {
                    ...(options || {}), richNode: shell.collectionRichNode,
                }),
            });
        }
        if (global.WorkbenchMediaRenderer && !hasRenderer('media', '1')) {
            registry.register({
                id: 'media',
                version: '1',
                priority: 100,
                canRender: node => global.WorkbenchMediaRenderer.canRender(node),
                mount: (shell, node, options) => global.WorkbenchMediaRenderer.mount(shell, node, options),
            });
        }
        if (global.WorkbenchLegacyRenderer && !hasRenderer('source-payload', '1')) {
            registry.register({
                id: 'source-payload',
                version: '1',
                priority: 0,
                canRender: node => global.WorkbenchLegacyRenderer.canRender(node),
                mount: (shell, node, options) => global.WorkbenchLegacyRenderer.mount(shell, node, options),
            });
        }
    }

    registerBuiltIns();

    function resolveRenderer(settings) {
        const node = settings.node;
        if (!node) throw new TypeError('NodeCardHost requires a NodeRecord');
        registerBuiltIns();
        return registry.require(node, settings);
    }

    function rendererOptions(settings) {
        return settings.rendererOptions || settings;
    }

    function mount(options) {
        const settings = options || {};
        const node = settings.node;
        const renderer = resolveRenderer(settings);
        const shell = global.WorkbenchNodeShell.create({
            document: settings.document || global.document,
            node,
            viewState: settings.viewState || {},
            onIntent: settings.onIntent,
            showDelete: settings.showDelete,
            ports: settings.ports,
        });
        const mountedRenderer = renderer.mount(shell, node, rendererOptions(settings));
        shell.element.dataset.rendererId = renderer.id;
        shell.element.dataset.rendererVersion = renderer.version;
        return Object.freeze({
            element: shell.element,
            shell,
            renderer,
            mountedRenderer,
            destroy() {
                mountedRenderer && mountedRenderer.destroy && mountedRenderer.destroy();
                shell.destroy();
            },
        });
    }

    function mountContent(options) {
        const settings = options || {};
        const node = settings.node;
        const contentHost = settings.contentHost;
        if (!contentHost) throw new TypeError('NodeCardHost requires a content host');
        const renderer = resolveRenderer(settings);
        const mountedRenderer = renderer.mount({contentHost}, node, rendererOptions(settings));
        return Object.freeze({
            element: mountedRenderer?.element || contentHost,
            renderer,
            mountedRenderer,
            destroy() { mountedRenderer && mountedRenderer.destroy && mountedRenderer.destroy(); },
        });
    }

    global.WorkbenchNodeCardHost = Object.freeze({mount, mountContent, registry, registerBuiltIns});
}(window));
