/* Pure Classic provider-node factory seam.
 *
 * Owns the type-specific default records and field sets for the three
 * non-blank Classic provider nodes (generator / midjourney / msgen). Each
 * factory constructs a record and delegates the durable creation to the
 * page's `addNode` via the host. The seam holds the *kind* knowledge
 * (provider card shape, default model, default size, default ratio, etc.);
 * the page holds the *state* knowledge (provider list, model catalog,
 * point helpers, id generator).
 *
 * History: R4-31 inventoried these three factories as MIGRATE-able to
 * the unified creation/mutation boundary; R4-38 Wave 2 closes the loop by
 * extracting the record construction to this product-neutral seam and
 * leaving canvas.js with the dispatcher wiring + a thin
 * `ensureClassicNodeFactories()` initializer. The dispatcher's call
 * shape (`ensureClassicNodeFactories().addGenerator({point})`) is the
 * pattern other Classic factory migrations will follow (video-player,
 * output-node, ...). */
(function exposeCanvasClassicNodeFactories(global) {
    'use strict';

    const REQUIRED = {
        addNode: 'function',
        uid: 'function',
        defaultPoint: 'function',
        imageApiProviders: 'function',
        allImageModels: 'function',
        defaultApiImageResolution: 'function',
        resolveMidjourneyProviderId: 'function',
        modelscopeImageModels: 'function',
    };

    function assertHost(host) {
        if (!host) throw new TypeError('classic-node-factories host is required');
        for (const key of Object.keys(REQUIRED)) {
            if (typeof host[key] !== REQUIRED[key]) {
                throw new TypeError(`classic-node-factories host must provide ${key}() as ${REQUIRED[key]}`);
            }
        }
    }

    function create(host) {
        assertHost(host);

        const api = Object.freeze({
            addGenerator({point} = {}) {
                const p = point || host.defaultPoint(120, 0);
                const providerId = host.imageApiProviders()[0]?.id || '';
                const model = host.allImageModels(providerId)[0] || '';
                return host.addNode({
                    id: host.uid('gen'),
                    type: 'generator',
                    x: p.x,
                    y: p.y,
                    apiProvider: providerId,
                    model,
                    ratio: 'square',
                    resolution: host.defaultApiImageResolution(model),
                    customRatio: '',
                    customSize: '',
                    customRatioWidth: '',
                    customRatioHeight: '',
                    customWidth: '',
                    customHeight: '',
                    inputs: [],
                });
            },
            addMidjourney({point} = {}) {
                const p = point || host.defaultPoint(140, 0);
                return host.addNode({
                    id: host.uid('mj'),
                    type: 'midjourney',
                    x: p.x,
                    y: p.y,
                    apiProvider: host.resolveMidjourneyProviderId(''),
                    mode: 'imagine',
                    size: '1:1',
                    version: '6.1',
                    speed: 'relax',
                    inputs: [],
                    running: false,
                    lastTaskId: '',
                    lastAction: '',
                    lastTaskStatus: '',
                    lastImageCount: 0,
                    lastPrompt: '',
                    mjModalTaskId: '',
                    mjModalPrompt: '',
                });
            },
            addMsGen({point} = {}) {
                const p = point || host.defaultPoint(140, 0);
                return host.addNode({
                    id: host.uid('msgen'),
                    type: 'msgen',
                    x: p.x,
                    y: p.y,
                    msgenModel: 'zimage',
                    msWidth: 1024,
                    msHeight: 1024,
                    msCustomModel: host.modelscopeImageModels()[0] || 'Tongyi-MAI/Z-Image-Turbo',
                    msRatio: 'square',
                    msResolution: '1k',
                    msCustomRatio: '',
                    msCustomSize: '',
                    msCustomRatioWidth: '',
                    msCustomRatioHeight: '',
                    msCustomWidth: '',
                    msCustomHeight: '',
                    count: 1,
                    fitImage: false,
                    inputs: [],
                    running: false,
                });
            },
        });
        return api;
    }

    global.WorkbenchCanvasClassicNodeFactories = Object.freeze({create});
}(typeof window !== 'undefined' ? window : globalThis));
