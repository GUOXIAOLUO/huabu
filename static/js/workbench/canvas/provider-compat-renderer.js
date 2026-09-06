/* Compatibility renderer for provider-shaped Classic cards (llm, generator,
   midjourney, msgen, video, comfy, rh, ltxDirector, minimax). It adopts the
   page-built legacy body verbatim — provider/execution presentation stays with
   the page for now — and carries per-card cleanup through the mounted-handle
   lifecycle: destroy() removes the adopted DOM and invokes the page-supplied
   onCardDestroy hook, so flows like the LTX timeline editor teardown happen at
   the RenderRuntime unmount boundary instead of inside page delete handlers.
   Provider identities never become Core NodeKinds. */
(function exposeWorkbenchProviderCompatRenderer(global) {
    'use strict';

    if (!global.WorkbenchNodeCardHost || !global.WorkbenchNodeCardHost.registry) {
        throw new Error('ProviderCompatRenderer requires NodeCardHost with a registry');
    }

    const PROVIDER_TYPES = ['llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax'];

    function legacyPayload(node) {
        return node?.extensions?.legacy?.payload || null;
    }

    const providerCompatRenderer = {
        id: 'provider-compat',
        version: '1',
        priority: 5,
        canRender: node => {
            const ref = node?.definition_ref;
            return ref?.type === 'legacy' && PROVIDER_TYPES.includes(ref.id);
        },
        mount(shell, node, options) {
            const settings = options || {};
            const contentHost = shell.contentHost;
            if (!contentHost) throw new TypeError('ProviderCompatRenderer requires a shell content host');
            const documentRef = settings.document || contentHost.ownerDocument || global.document;
            const root = documentRef.createElement('div');
            root.className = 'workbench-provider-compat-renderer';
            const legacyContent = settings.legacyContent;
            if (legacyContent) root.append(legacyContent);
            else root.textContent = legacyPayload(node)?.type || node.title || 'Provider card';
            contentHost.replaceChildren(root);
            return Object.freeze({
                element: root,
                destroy() {
                    try { settings.onCardDestroy?.(legacyPayload(node)); } catch (_error) {}
                    root.remove();
                },
            });
        },
    };

    global.WorkbenchNodeCardHost.registry.register(providerCompatRenderer);
}(window));
