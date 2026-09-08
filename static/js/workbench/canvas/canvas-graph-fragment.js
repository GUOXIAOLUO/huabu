/* Pure graph-fragment operations shared by temporary Canvas adapters. */
(function exposeCanvasGraphFragment(global) {
    'use strict';

    function selectedSubgraph({nodes = [], connections = [], selectedIds = [], serializeNode, order = 'source'} = {}) {
        const sourceNodes = Array.isArray(nodes) ? nodes : [];
        const selected = new Set((Array.isArray(selectedIds) ? selectedIds : []).filter(id =>
            sourceNodes.some(node => node?.id === id)
        ));
        const orderedNodes = order === 'selection'
            ? (Array.isArray(selectedIds) ? selectedIds : []).filter((id, index, ids) =>
                selected.has(id) && ids.indexOf(id) === index
            ).map(id => sourceNodes.find(node => node?.id === id)).filter(Boolean)
            : sourceNodes.filter(node => selected.has(node?.id));
        const serialize = typeof serializeNode === 'function' ? serializeNode : node => node;
        return {
            nodes: orderedNodes.map(serialize),
            connections: (Array.isArray(connections) ? connections : [])
                .filter(connection => selected.has(connection?.from) && selected.has(connection?.to))
                .map(connection => JSON.parse(JSON.stringify(connection))),
        };
    }

    function materializeImportedSubgraph({
        nodes = [], connections = [], target = {x: 0, y: 0}, anchor = 'min', serializeNode,
        createNodeId, prepareNode, createConnection,
    } = {}) {
        const sourceNodes = Array.isArray(nodes) ? nodes.filter(Boolean) : [];
        if (!sourceNodes.length) return {nodes: [], connections: [], idMap: new Map()};
        const xs = sourceNodes.map(node => Number(node.x || 0));
        const ys = sourceNodes.map(node => Number(node.y || 0));
        const originX = anchor === 'center' ? (Math.min(...xs) + Math.max(...xs)) / 2 : Math.min(...xs);
        const originY = anchor === 'center' ? (Math.min(...ys) + Math.max(...ys)) / 2 : Math.min(...ys);
        const offsetX = Number(target?.x || 0) - originX;
        const offsetY = Number(target?.y || 0) - originY;
        const serialize = typeof serializeNode === 'function' ? serializeNode : node => ({...node});
        const newId = typeof createNodeId === 'function' ? createNodeId : () => '';
        const prepare = typeof prepareNode === 'function' ? prepareNode : node => node;
        const idMap = new Map();
        const materializedNodes = sourceNodes.map(source => {
            const copy = serialize(source);
            if (!copy || typeof copy !== 'object') return null;
            const oldId = copy.id || newId(copy.type || 'node');
            copy.id = newId(copy.type || 'node');
            copy.x = Number(copy.x || 0) + offsetX;
            copy.y = Number(copy.y || 0) + offsetY;
            idMap.set(oldId, copy.id);
            return prepare(copy, {oldId, idMap});
        }).filter(Boolean);
        const makeConnection = typeof createConnection === 'function'
            ? createConnection
            : (connection, endpoints) => ({...connection, ...endpoints});
        const materializedConnections = (Array.isArray(connections) ? connections : []).filter(Boolean)
            .map(connection => makeConnection(connection, {
                from: idMap.get(connection.from), to: idMap.get(connection.to),
            }, idMap))
            .filter(connection => connection?.from && connection?.to);
        return {nodes: materializedNodes, connections: materializedConnections, idMap};
    }

    function expandNodeIds({nodes = [], initialIds = [], childIds} = {}) {
        const sourceNodes = Array.isArray(nodes) ? nodes : [];
        const byId = new Map(sourceNodes.filter(Boolean).map(node => [node.id, node]));
        const expanded = new Set();
        const resolveChildren = typeof childIds === 'function' ? childIds : () => [];
        const visit = id => {
            if (!id || expanded.has(id)) return;
            expanded.add(id);
            const node = byId.get(id);
            if (!node) return;
            const children = resolveChildren(node);
            (Array.isArray(children) ? children : []).forEach(visit);
        };
        (Array.isArray(initialIds) ? initialIds : []).forEach(visit);
        return expanded;
    }

    function removeGraphRecords({nodes = [], connections = [], removeIds = []} = {}) {
        const removed = removeIds instanceof Set ? removeIds : new Set(removeIds || []);
        return {
            nodes: (Array.isArray(nodes) ? nodes : []).filter(node => !removed.has(node?.id)),
            connections: (Array.isArray(connections) ? connections : [])
                .filter(connection => !removed.has(connection?.from) && !removed.has(connection?.to)),
        };
    }

    function removeConnection({connections = [], connectionId = ''} = {}) {
        const id = String(connectionId || '');
        if (!id) return Array.isArray(connections) ? connections.slice() : [];
        return (Array.isArray(connections) ? connections : []).filter(connection => String(connection?.id || '') !== id);
    }

    function duplicateSubgraph({node, nodes = [], connections = [], serializeNode, createNodeId, childIds, preserveConnections = false, canConnect} = {}) {
        if (!node) return {root: null, copies: [], connections: []};
        const serialize = typeof serializeNode === 'function' ? serializeNode : source => JSON.parse(JSON.stringify(source));
        const makeId = typeof createNodeId === 'function' ? createNodeId : type => `${type || 'node'}_${Date.now()}`;
        const resolveChildren = typeof childIds === 'function' ? childIds : () => [];
        const sourceById = new Map((Array.isArray(nodes) ? nodes : []).filter(Boolean).map(item => [item.id, item]));
        const sourceIds = new Set([node.id]);
        const idMap = new Map();
        const sources = [node, ...resolveChildren(node).map(id => sourceById.get(id)).filter(Boolean)];
        const copies = sources.map(source => {
            const copy = serialize(source);
            copy.id = makeId(source.type || 'node');
            copy.running = false;
            sourceIds.add(source.id);
            idMap.set(source.id, copy.id);
            return copy;
        });
        const root = copies[0];
        if (Array.isArray(root?.items)) root.items = root.items.map(id => idMap.get(id) || id);
        const copiedConnections = preserveConnections
            ? (Array.isArray(connections) ? connections : []).filter(connection => sourceIds.has(connection?.to)).map(connection => ({
                ...connection,
                id: makeId('c'),
                from: idMap.get(connection.from) || connection.from,
                to: idMap.get(connection.to) || connection.to,
            })).filter(connection => connection.from && connection.to && connection.from !== connection.to)
                .filter(connection => typeof canConnect !== 'function' || canConnect(connection.from, connection.to))
            : [];
        return {root, copies, connections: copiedConnections, idMap};
    }

    global.WorkbenchCanvasGraphFragment = Object.freeze({
        selectedSubgraph,
        materializeImportedSubgraph,
        expandNodeIds,
        removeGraphRecords,
        removeConnection,
        duplicateSubgraph,
    });
}(window));
