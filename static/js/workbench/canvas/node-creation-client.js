/* Versioned-node API client. Existing editors do not call this until P1.7 migration. */
(function exposeNodeCreationClient(global) {
    'use strict';

    async function request(path, method, body, actorId) {
        if (!actorId) throw new Error('A local actor id is required for versioned Canvas-node requests.');
        const response = await fetch(path, {
            method,
            headers: {'Content-Type': 'application/json', 'X-User-ID': actorId},
            body: body === undefined ? undefined : JSON.stringify(body),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail && payload.detail.message || payload.detail || `Request failed (${response.status})`);
        return payload;
    }

    function requirePositiveRevision(command) {
        const revision = Number(command && command.expected_revision);
        if (!Number.isInteger(revision) || revision < 1) {
            throw new Error('A positive expected_revision is required for connected Canvas creation.');
        }
    }

    function applyCreationResult(result, options) {
        const settings = options && typeof options === 'object' ? options : {};
        if (!Array.isArray(settings.nodes)) throw new TypeError('creation result requires a mutable nodes array');
        if (typeof settings.projectNode !== 'function') throw new TypeError('creation result requires a projectNode callback');
        const source = result && result.node;
        if (!source || !String(source.id || '')) throw new TypeError('creation result requires a created node id');
        const node = settings.projectNode(source);
        if (!node || String(node.id || '') !== String(source.id)) throw new TypeError('projectNode must preserve the created node id');
        settings.nodes.push(node);
        if (Array.isArray(settings.undoStack) && Object.prototype.hasOwnProperty.call(settings, 'undoSnapshot')) {
            settings.undoStack.push(settings.undoSnapshot);
            const limit = Number(settings.undoLimit);
            if (Number.isInteger(limit) && limit > 0 && settings.undoStack.length > limit) settings.undoStack.shift();
        }
        const revision = Number(result && result.canvas_revision);
        if (settings.canvas && Number.isFinite(revision) && revision > 0) settings.canvas.updated_at = revision;
        if (typeof settings.onRevision === 'function' && Number.isFinite(revision) && revision > 0) settings.onRevision(revision);
        if (typeof settings.onSelected === 'function') settings.onSelected(node);
        return node;
    }

    function applyGraphCreationResult(result, options) {
        const settings = options && typeof options === 'object' ? options : {};
        if (!Array.isArray(settings.nodes)) throw new TypeError('graph creation result requires a mutable nodes array');
        if (!Array.isArray(settings.connections)) throw new TypeError('graph creation result requires a mutable connections array');
        if (typeof settings.projectNode !== 'function') throw new TypeError('graph creation result requires a projectNode callback');
        if (typeof settings.projectEdge !== 'function') throw new TypeError('graph creation result requires a projectEdge callback');
        const source = result && result.node;
        const edgeSource = result && result.edge;
        if (!source || !String(source.id || '')) throw new TypeError('graph creation result requires a created node id');
        if (!edgeSource || !String(edgeSource.id || '')) throw new TypeError('graph creation result requires a created edge id');
        const node = settings.projectNode(source);
        if (!node || String(node.id || '') !== String(source.id)) throw new TypeError('projectNode must preserve the created node id');
        const edge = settings.projectEdge(edgeSource, node);
        if (!edge || !String(edge.id || '') || !String(edge.from || '') || !String(edge.to || '')) {
            throw new TypeError('projectEdge must return an id, from and to');
        }
        const target = String(edge.to) === String(node.id)
            ? node
            : settings.nodes.find(item => String(item && item.id || '') === String(edge.to));
        if (!target) throw new Error('The existing connection target is unavailable.');
        if (settings.syncTargetInput) {
            target.inputNodeIds = Array.from(new Set([...(target.inputNodeIds || []), edge.from]));
        }
        settings.nodes.push(node);
        settings.connections.push(edge);
        if (Array.isArray(settings.undoStack) && Object.prototype.hasOwnProperty.call(settings, 'undoSnapshot')) {
            settings.undoStack.push(settings.undoSnapshot);
            const limit = Number(settings.undoLimit);
            if (Number.isInteger(limit) && limit > 0 && settings.undoStack.length > limit) settings.undoStack.shift();
        }
        const revision = Number(result && result.canvas_revision);
        if (settings.canvas && Number.isFinite(revision) && revision > 0) settings.canvas.updated_at = revision;
        if (typeof settings.onRevision === 'function' && Number.isFinite(revision) && revision > 0) settings.onRevision(revision);
        if (typeof settings.onSelected === 'function') settings.onSelected(node);
        if (typeof settings.onAfterCommit === 'function') settings.onAfterCommit(node, edge);
        return node;
    }

    function applyConnectionResult(result, options) {
        const settings = options && typeof options === 'object' ? options : {};
        if (!Array.isArray(settings.connections)) throw new TypeError('connection result requires a mutable connections array');
        const source = result && result.edge;
        if (!source || !String(source.id || '')) throw new TypeError('connection result requires a created edge id');
        const fromId = String(settings.fromId || source.from || '');
        const toId = String(settings.toId || source.to || '');
        if (!fromId || !toId || String(source.from || '') !== fromId || String(source.to || '') !== toId) {
            throw new TypeError('connection result must preserve the requested edge endpoints');
        }
        const edge = typeof settings.projectEdge === 'function'
            ? settings.projectEdge(source)
            : {id: String(source.id), from: fromId, to: toId};
        if (!edge || !String(edge.id || '') || String(edge.from || '') !== fromId || String(edge.to || '') !== toId) {
            throw new TypeError('projectEdge must return the requested edge');
        }
        if (Array.isArray(settings.undoStack) && Object.prototype.hasOwnProperty.call(settings, 'undoSnapshot')) {
            settings.undoStack.push(settings.undoSnapshot);
            const limit = Number(settings.undoLimit);
            if (Number.isInteger(limit) && limit > 0 && settings.undoStack.length > limit) settings.undoStack.shift();
        }
        settings.connections.push(edge);
        const revision = Number(result && result.canvas_revision);
        if (settings.canvas && Number.isFinite(revision) && revision > 0) settings.canvas.updated_at = revision;
        if (typeof settings.onRevision === 'function' && Number.isFinite(revision) && revision > 0) settings.onRevision(revision);
        if (typeof settings.onAfterCommit === 'function') settings.onAfterCommit(edge);
        return edge;
    }

    global.WorkbenchNodeClient = Object.freeze({
        isLoopback: () => ['127.0.0.1', '::1', 'localhost'].includes(window.location.hostname),
        // R4 normal creation uses the canonical NodeCreationService on local
        // product routes. `versioned_nodes=0` is the bounded U7 rollback for
        // the retained adapter constructors; it is intentionally opt-out,
        // rather than an experimental opt-in.
        isEnabled: () => new URLSearchParams(window.location.search).get('versioned_nodes') !== '0',
        applyCreationResult,
        applyGraphCreationResult,
        applyConnectionResult,
        create: (canvasId, command, actorId) => request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/nodes`, 'POST', command, actorId),
        update: (canvasId, nodeId, command, actorId) => request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/nodes/${encodeURIComponent(nodeId)}`, 'PUT', command, actorId),
        remove: (canvasId, nodeId, command, actorId) => request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/nodes/${encodeURIComponent(nodeId)}`, 'DELETE', command, actorId),
        createNodeAndEdge: (canvasId, command, actorId) => {
            requirePositiveRevision(command);
            return request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/graph/create-node-and-edge`, 'POST', command, actorId);
        },
        connectNodes: (canvasId, command, actorId) => {
            requirePositiveRevision(command);
            return request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/graph/connect-nodes`, 'POST', command, actorId);
        },
        setGroupMembership: (canvasId, command, actorId) => {
            requirePositiveRevision(command);
            return request(`/api/v1/canvases/${encodeURIComponent(canvasId)}/graph/group-membership`, 'POST', command, actorId);
        },
    });
}(window));
