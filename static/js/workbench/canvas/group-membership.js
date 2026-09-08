/* Shared, business-neutral membership queries and move-driven membership
   transitions for Canvas composite nodes.  Adapters supply the set of records
   that act as groups plus their geometry / connect policy callbacks. */
(function exposeWorkbenchCanvasGroupMembership(global) {
    'use strict';

    function groupItems(group) {
        return Array.isArray(group?.items)
            ? Array.from(new Set(group.items.map(String).filter(Boolean)))
            : [];
    }

    function membershipIndex(groups) {
        const index = new Map();
        Array.from(groups || []).forEach(group => {
            const groupId = String(group?.id || '');
            if(!groupId) return;
            groupItems(group).forEach(memberId => {
                if(memberId !== groupId && !index.has(memberId)) index.set(memberId, groupId);
            });
        });
        return index;
    }

    function containingGroupId(groups, nodeId) {
        return membershipIndex(groups).get(String(nodeId || '')) || '';
    }

    function scopeId(groups, groupIds, nodeId) {
        const id = String(nodeId || '');
        return containingGroupId(groups, id) || (new Set(Array.from(groupIds || [], String)).has(id) ? id : '');
    }

    // Re-parent existing child -> generator edges when a page creates a new
    // group around those children. This is the same graph transition used by
    // move-driven membership; callers supply only records, type policy and
    // the Core compatibility predicate.
    function handoffChildEdgesToGroup(options) {
        const settings = options || {};
        const group = settings.group;
        const children = Array.from(settings.children || []);
        const edges = Array.isArray(settings.edges) ? settings.edges : [];
        const nodeById = typeof settings.nodeById === 'function' ? settings.nodeById : () => null;
        const generatorTypes = new Set(settings.generatorTypes || []);
        const canConnect = typeof settings.canConnect === 'function' ? settings.canConnect : () => false;
        const newEdgeId = typeof settings.newEdgeId === 'function' ? settings.newEdgeId : () => '';
        if (!group || !group.id) throw new TypeError('handoffChildEdgesToGroup requires group');
        const childEligible = typeof settings.childEligible === 'function'
            ? settings.childEligible
            : child => ['image', 'prompt'].includes(child?.type);
        const targetEligible = typeof settings.targetEligible === 'function'
            ? settings.targetEligible
            : node => generatorTypes.has(node?.type);
        const childIds = new Set(children.filter(childEligible).map(child => child.id));
        if (!childIds.size) return Object.freeze({changed: false, edgesRemoved: 0, edgesAdded: 0});
        const targetIds = new Set(edges
            .filter(edge => childIds.has(edge.from) || edge.from === group.id)
            .map(edge => nodeById(edge.to))
            .filter(node => node && targetEligible(node))
            .map(node => node.id));
        if (!targetIds.size) return Object.freeze({changed: false, edgesRemoved: 0, edgesAdded: 0});
        let edgesRemoved = 0;
        let edgesAdded = 0;
        for (let index = edges.length - 1; index >= 0; index -= 1) {
            if (childIds.has(edges[index].from) && targetIds.has(edges[index].to)) {
                edges.splice(index, 1);
                edgesRemoved += 1;
            }
        }
        targetIds.forEach(targetId => {
            if (!edges.some(edge => edge.from === group.id && edge.to === targetId)
                && canConnect(group.id, targetId)) {
                edges.push({id: newEdgeId(), from: group.id, to: targetId});
                edgesAdded += 1;
            }
        });
        return Object.freeze({changed: edgesRemoved > 0 || edgesAdded > 0, edgesRemoved, edgesAdded});
    }

    /* One owner for the move-driven membership transition algorithm: geometric
       containment detection, membership add/remove across the supplied group
       records, and the connection handoff from an absorbed child to its
       containing group (the child's direct generator edges are re-parented to
       the group).  Group items and the injected edge list are mutated in
       place; pages keep only their DOM-backed geometry (rectOf), node lookup,
       eligibility and connect policy, and the post-change side effects. */
    function resolveMembershipTransition(options) {
        const settings = options || {};
        const groups = Array.from(settings.groups || []);
        const children = Array.from(settings.children || []);
        const rectOf = settings.rectOf;
        const nodeById = typeof settings.nodeById === 'function' ? settings.nodeById : () => null;
        const handoffEligible = typeof settings.handoffEligible === 'function' ? settings.handoffEligible : () => false;
        const edges = Array.isArray(settings.edges) ? settings.edges : [];
        const generatorTypes = Array.from(settings.generatorTypes || []);
        const canConnect = typeof settings.canConnect === 'function' ? settings.canConnect : () => false;
        const newEdgeId = typeof settings.newEdgeId === 'function' ? settings.newEdgeId : () => '';
        if (typeof rectOf !== 'function') {
            throw new TypeError('resolveMembershipTransition requires rectOf');
        }
        let changed = false;
        let membersAdded = 0;
        let membersRemoved = 0;
        let edgesRemoved = 0;
        let edgesAdded = 0;
        children.forEach(child => {
            if (!child) return;
            const cr = rectOf(child);
            const containing = groups.find(g => {
                const gr = rectOf(g);
                return cr.cx >= gr.x && cr.cx <= gr.x + gr.w && cr.cy >= gr.y && cr.cy <= gr.y + gr.h;
            });
            groups.forEach(g => {
                if (g === containing) return;
                const items = Array.isArray(g.items) ? g.items : [];
                const idx = items.indexOf(child.id);
                if (idx >= 0) {
                    items.splice(idx, 1);
                    g.items = items;
                    membersRemoved += 1;
                    changed = true;
                }
            });
            if (containing) {
                const items = Array.isArray(containing.items) ? containing.items : [];
                if (!items.includes(child.id)) {
                    items.push(child.id);
                    containing.items = items;
                    membersAdded += 1;
                    changed = true;
                }
                if (handoffEligible(containing, child)) {
                    const handoff = handoffChildEdgesToGroup({
                        group: containing, children: [child], edges, nodeById,
                        generatorTypes, childEligible: child => handoffEligible(containing, child),
                        targetEligible: node => generatorTypes.includes(node?.type), canConnect, newEdgeId,
                    });
                    edgesRemoved += handoff.edgesRemoved;
                    edgesAdded += handoff.edgesAdded;
                    changed = changed || handoff.changed;
                }
            }
        });
        return Object.freeze({changed, membersAdded, membersRemoved, edgesRemoved, edgesAdded});
    }

    global.WorkbenchCanvasGroupMembership = Object.freeze({groupItems, membershipIndex, containingGroupId, scopeId, handoffChildEdgesToGroup, resolveMembershipTransition});
}(window));
