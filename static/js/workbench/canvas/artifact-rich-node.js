/* Generic rich presentation for formal work outputs. The adapter is
   version-ready but does not own durable artifact persistence or approvals. */
(function exposeWorkbenchArtifactRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function outputItems(node) {
        const source = node && typeof node === 'object' ? node : {};
        const legacy = source.extensions?.legacy?.payload;
        const values = [source.output_refs, legacy?.outputs, legacy?.artifacts].flatMap(value => Array.isArray(value) ? value : value == null ? [] : [value]);
        const seen = new Set();
        return Object.freeze(values.map(item => {
            const value = typeof item === 'string' ? {url: item} : item || {};
            const id = text(value.id || value.artifact_id || value.url || value.src);
            if (!id || seen.has(id)) return null;
            seen.add(id);
            return Object.freeze({
                id, url: text(value.url || value.src), kind: text(value.kind || value.type, 'file'),
                version: text(value.version || value.revision, 'unversioned'),
            });
        }).filter(Boolean));
    }

    function compatible(node) {
        return Boolean(node && typeof node === 'object' && (node.kind === 'artifact' || outputItems(node).length));
    }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!compatible(node)) throw new TypeError('ArtifactRichNode requires an output-compatible NodeRecord');
        const presentation = settings.presentation || global.WorkbenchPresentationState?.create({
            initial: settings.presentationState,
            storage: settings.storage,
            storageKey: settings.storageKey || `workbench.artifact.presentation:${text(node.id, 'unknown')}`,
            onChange: settings.onChange,
        });
        if (!presentation || typeof presentation.state !== 'function' || typeof presentation.transition !== 'function') {
            throw new Error('ArtifactRichNode requires WorkbenchPresentationState');
        }
        function snapshot() {
            return Object.freeze({
                nodeId: text(node.id), title: text(node.title, 'Artifact'),
                presentation: presentation.state(), outputs: outputItems(node),
                versionReady: true, approvals: 'deferred',
            });
        }
        return Object.freeze({
            presentations: PRESENTATIONS, snapshot, state: presentation.state,
            canTransition: presentation.canTransition,
            transition: next => { presentation.transition(next); return snapshot(); },
        });
    }

    global.WorkbenchArtifactRichNode = Object.freeze({PRESENTATIONS, compatible, outputItems, create});
}(window));
