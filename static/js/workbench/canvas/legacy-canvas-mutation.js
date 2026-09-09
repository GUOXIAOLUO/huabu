/* Bounded Legacy Canvas mutation seam.
 *
 * These projections are retained only for historical Classic compatibility
 * actions that have no versioned graph command yet. Keeping the array writes
 * behind this named adapter prevents the Unified interaction module from
 * becoming a second persistence/mutation owner.
 */
(function exposeLegacyCanvasMutation(global) {
    'use strict';
    function appendNode(nodes, node) {
        if (!Array.isArray(nodes) || !node) return false;
        nodes.push(node);
        return true;
    }
    function appendConnection(connections, connection) {
        if (!Array.isArray(connections) || !connection) return false;
        connections.push(connection);
        return true;
    }
    function appendNodes(nodes, additions) {
        if (!Array.isArray(nodes) || !Array.isArray(additions)) return false;
        nodes.push(...additions);
        return true;
    }
    global.WorkbenchLegacyCanvasMutation = Object.freeze({
        appendNode,
        appendConnection,
        appendNodes,
        restoreSnapshot: (snapshot) => ({
            nodes: Array.isArray(snapshot?.nodes) ? snapshot.nodes : [],
            connections: Array.isArray(snapshot?.connections) ? snapshot.connections : [],
        }),
    });
}(window));
