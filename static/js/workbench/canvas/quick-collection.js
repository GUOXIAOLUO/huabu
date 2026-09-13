/* Quick Collection application seam. It turns ordered selected resource nodes
   into a persisted Collection, then creates a normal Canvas Collection node. */
(function exposeWorkbenchQuickCollection(global) {
    'use strict';

    const REFERENCE_TYPES = Object.freeze(['asset_version', 'artifact_version', 'collection']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function mediaReference(node) {
        if (!node || typeof node !== 'object') return null;
        const nodeType = text(node.type || node.kind).toLowerCase();
        const collectionId = text(node.collection?.id || node.config?.collection?.id);
        const url = text(node.url || node.config?.url);
        const mediaKind = text(node.mediaKind || node.config?.mediaKind, 'image').toLowerCase();
        const isMedia = Boolean(url) && ['image', 'video', 'audio'].includes(mediaKind);
        const isResource = ['asset', 'artifact', 'collection'].includes(nodeType);
        if (!isMedia && !isResource) return null;
        const referenceType = collectionId || nodeType === 'collection'
            ? 'collection' : node.artifact_version_id || node.artifactVersionId || node.output_ref_id || nodeType === 'artifact'
                ? 'artifact_version' : 'asset_version';
        const referenceId = text(referenceType === 'artifact_version'
            ? (node.artifact_version_id || node.artifactVersionId || node.output_ref_id || node.version_id || node.id)
            : referenceType === 'collection' ? collectionId || node.id
                : (node.asset_version_id || node.assetVersionId || node.asset_id || node.version_id || node.id));
        if (!referenceId) return null;
        return Object.freeze({referenceType, referenceId, url, kind:mediaKind, label:text(node.name || node.title, 'Media')});
    }

    function eligibleReferences(nodes) {
        return Object.freeze((nodes || []).map(mediaReference).filter(Boolean));
    }

    function buildPayload({projectId, title, references, canvasId}) {
        const refs = references || [];
        const usedTypes = REFERENCE_TYPES.filter(type => refs.some(reference => reference.referenceType === type));
        const columns = usedTypes.map(type => ({
            id: `quick-${type}`,
            key: type,
            label: type === 'artifact_version' ? 'Artifact' : type === 'collection' ? 'Collection' : 'Asset',
            value_type: type,
        }));
        return {
            project_id:text(projectId), name:text(title, 'Quick Collection'),
            schema:{id:'quick-collection-schema', name:'Quick Collection', columns},
            items:refs.map((reference, index) => ({
                id:`quick-item-${index + 1}`, order:index,
                values:{[reference.referenceType]:{type:'reference', reference_type:reference.referenceType, reference_id:reference.referenceId, metadata:{url:reference.url, kind:reference.kind, name:reference.label}}},
            })),
            default_view:{mode:'grid'}, metadata:{source:'quick_collection', canvas_id:text(canvasId)},
        };
    }

    async function create(options) {
        const settings = options || {};
        const references = eligibleReferences(settings.nodes);
        if (references.length < 2) return Object.freeze({created:false, reason:'insufficient_eligible_references', references});
        const title = typeof settings.prompt === 'function' ? settings.prompt('Collection title', 'Quick Collection') : 'Quick Collection';
        if (title === null || title === undefined || !text(title)) return Object.freeze({created:false, reason:'cancelled', references});
        if (typeof settings.createCollection !== 'function' || typeof settings.createNode !== 'function') throw new TypeError('QuickCollection requires application boundaries');
        const collection = await settings.createCollection(buildPayload({projectId:settings.projectId, title, references, canvasId:settings.canvasId}));
        const node = await settings.createNode({
            title:text(title), collection,
            position:settings.position || {x:0, y:0},
        });
        return Object.freeze({created:true, collection, node, references});
    }

    global.WorkbenchQuickCollection = Object.freeze({mediaReference, eligibleReferences, buildPayload, create});
}(window));
