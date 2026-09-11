/* One Canvas card-host boundary. Page adapters provide normalized records and
   optional lossless DOM content; renderer selection and NodeShell construction
   are shared and do not branch by page or node family. */
(function exposeWorkbenchUnifiedRenderHost(global) {
    'use strict';
    if (!global.WorkbenchNodeCardHost) throw new Error('UnifiedRenderHost requires NodeCardHost');

    function adoptLegacyContent(settings) {
        if (settings.legacyContent || !settings.legacyContentHost) return settings.legacyContent || null;
        const documentRef = settings.document || settings.legacyContentHost.ownerDocument || global.document;
        const content = documentRef.createElement('div');
        content.className = settings.legacyContentClassName || 'workbench-legacy-renderer__legacy-content';
        while (settings.legacyContentHost.firstChild) content.appendChild(settings.legacyContentHost.firstChild);
        return content;
    }

    function mountShellAtCardBoundary(settings) {
        const options = settings || {};
        const card = options.card;
        const contentHost = options.contentHost;
        const shell = options.shell;
        if (!card || !contentHost || !shell || !shell.element) {
            throw new TypeError('UnifiedRenderHost requires a card, content host, and NodeShell');
        }
        const inputPort = shell.element.querySelector('.workbench-node-shell__port--input');
        const outputPort = shell.element.querySelector('.workbench-node-shell__port--output');
        contentHost.replaceChildren(shell.element);
        if (inputPort) card.append(inputPort);
        if (outputPort) card.append(outputPort);
        return Object.freeze({inputPort, outputPort});
    }

    function mount(options) {
        const settings = options || {};
        if (!settings.node) throw new TypeError('UnifiedRenderHost requires a NodeRecord');
        const legacyContent = adoptLegacyContent(settings);
        return global.WorkbenchNodeCardHost.mount({
            ...settings,
            rendererOptions:{...(settings.rendererOptions || {}), legacyContent},
        });
    }
    function mountContent(options) {
        const settings = options || {};
        if (!settings.node) throw new TypeError('UnifiedRenderHost requires a NodeRecord');
        const legacyContent = adoptLegacyContent(settings);
        return global.WorkbenchNodeCardHost.mountContent({
            ...settings,
            rendererOptions:{...(settings.rendererOptions || {}), legacyContent},
        });
    }
    function mountCard(settings) {
        const mounted = mount(settings);
        mountShellAtCardBoundary({card:settings.card, contentHost:settings.contentHost, shell:mounted.shell});
        return mounted;
    }
    function mountAdapterCard(settings) {
        const options = settings || {};
        if (!options.card) throw new TypeError('UnifiedRenderHost requires a card');
        const controlSettings = options.controlSettings;
        if (options.removeControlsBeforeMount && controlSettings) {
            removeCardControls({card: options.card, ...controlSettings});
        }
        const mountSettings = options.preserveLegacyContent
            ? {...options, legacyContentHost: options.contentHost}
            : options;
        const mounted = mountCard(mountSettings);
        if (!options.removeControlsBeforeMount && controlSettings) {
            removeCardControls({card: options.card, ...controlSettings});
        }
        const classes = options.cardClasses || [];
        if (!Array.isArray(classes)) throw new TypeError('UnifiedRenderHost cardClasses must be an array');
        if (options.card.classList) options.card.classList.add(...classes.filter(Boolean));
        return mounted;
    }
    function mountAdapterContent(settings) {
        const options = settings || {};
        if (!options.contentHost) throw new TypeError('UnifiedRenderHost requires a content host');
        const mountSettings = options.preserveLegacyContent
            ? {...options, legacyContentHost: options.contentHost}
            : options;
        const mounted = mountContent(mountSettings);
        const classes = options.cardClasses || [];
        if (!Array.isArray(classes)) throw new TypeError('UnifiedRenderHost cardClasses must be an array');
        if (options.card?.classList) options.card.classList.add(...classes.filter(Boolean));
        return mounted;
    }
    function mountAdapterCards(entries) {
        if (!Array.isArray(entries)) throw new TypeError('UnifiedRenderHost adapter entries must be an array');
        return Object.freeze(entries.map(entry => mountAdapterCard(entry)).filter(Boolean));
    }
    function createIntentAdapter(handlers) {
        const callbacks = handlers || {};
        return intent => {
            if (!intent?.nodeId) return;
            const handler = callbacks[intent.type];
            if (typeof handler === 'function') handler(intent);
        };
    }
    function cardShellView(options) {
        const settings = options || {};
        return Object.freeze({
            viewState: Object.freeze({selected: Boolean(settings.selected), presentation: settings.presentation || 'card'}),
            onIntent: settings.onIntent,
            showDelete: settings.showDelete !== false,
            ...(settings.ports ? {ports: settings.ports} : {}),
        });
    }
    function removeCardControls(settings) {
        const options = settings || {};
        const card = options.card;
        const selectors = options.selectors || [];
        const firstSelectors = options.firstSelectors || [];
        if (!card || !Array.isArray(selectors) || !Array.isArray(firstSelectors)) throw new TypeError('UnifiedRenderHost requires a card and control selectors');
        let removed = 0;
        firstSelectors.forEach(selector => {
            const control = card.querySelector(selector);
            if (!control) return;
            control.remove();
            removed += 1;
        });
        selectors.forEach(selector => {
            card.querySelectorAll(selector).forEach(control => {
                control.remove();
                removed += 1;
            });
        });
        return removed;
    }
    global.WorkbenchUnifiedRenderHost = Object.freeze({adoptLegacyContent, mount, mountContent, mountShellAtCardBoundary, mountCard, mountAdapterCard, mountAdapterCards, mountAdapterContent, createIntentAdapter, cardShellView, removeCardControls});
}(window));
