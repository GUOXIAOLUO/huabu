/* Legacy Graph Compatibility Policy (card R4-25).
 *
 * Single owner of every Classic / Smart historical connect side effect that
 * does not belong in the Core graph model. The Core `GraphMutationService`
 * stays industry-neutral; the compatibility rules are documented here and
 * applied by the page-side helpers that own the actual save / render.
 *
 * Out of scope: edge / inputNodeIds persistence. That already goes through
 * `GraphMutationService.connect_nodes` and `WorkbenchNodeClient.connectNodes`
 * (R4-24). The policy answers the questions "what extra compatibility
 * projection should the page apply, given this from/to node pair, on top
 * of the durable edge commit?" — never "did the edge persist?".
 */
(function exposeLegacyGraphCompatibilityPolicy(global) {
    'use strict';

    const CLASSIC_GROUP_MEMBER_TYPES = Object.freeze(['image', 'prompt']);
    const SMART_LOOP_PREVIEW = Object.freeze({});

    function isClassicGroupMemberEligible(node) {
        return Boolean(node) && CLASSIC_GROUP_MEMBER_TYPES.includes(node.type);
    }

    function isSmartImageNode(node) {
        return Boolean(node && node.type === 'smart-image');
    }

    function isSmartPromptNode(node) {
        return Boolean(node && node.type === 'smart-prompt');
    }

    function isSmartGroupNode(node) {
        return Boolean(node && node.type === 'smart-group');
    }

    function isSmartLoopNode(node) {
        return Boolean(node && node.type === 'smart-loop');
    }

    function classicGroupShouldAddMember(group, groupedNode, commands) {
        if (!group || group.type !== 'group') return false;
        if (!isClassicGroupMemberEligible(groupedNode)) return false;
        if (commands && typeof commands.graphCommand === 'function'
            && commands.graphCommand('canvas.group.add-member', 'classic') !== 'classic') return false;
        const items = Array.isArray(group.items) ? group.items : [];
        return !items.includes(groupedNode.id);
    }

    function smartLoopLooksImage(fromNode, fromImageCount) {
        if (isSmartImageNode(fromNode)) return true;
        if (fromImageCount > 0) return true;
        return Boolean(fromNode && fromNode.type === 'smart-loop' && fromNode.imageInput);
    }

    function smartLoopLooksPrompt(fromNode, fromPromptCount) {
        if (isSmartPromptNode(fromNode)) return true;
        if (fromPromptCount > 0) return true;
        return Boolean(fromNode && fromNode.type === 'smart-loop' && fromNode.showPrompt);
    }

    function createLegacyGraphCompatibilityPolicy(options) {
        const settings = options || {};
        const commands = settings.commands || null;
        const groupAddMemberAllowed = settings.groupAddMemberAllowed !== false;

        function applyClassicConnect(input) {
            const fromNode = input && input.fromNode;
            const toNode = input && input.toNode;
            const fromId = input && input.fromId != null ? input.fromId : (fromNode && fromNode.id);
            const toId = input && input.toId != null ? input.toId : (toNode && toNode.id);
            const group = toNode && toNode.type === 'group' ? toNode : null;
            const groupAddMember = groupAddMemberAllowed
                ? classicGroupShouldAddMember(group, fromNode, commands)
                : false;
            const addedNodeIds = groupAddMember && fromNode ? [fromNode.id] : [];
            // Classic history runs both syncs unconditionally on every
            // connect commit — they were never gated on the node types.
            // They are surfaced as explicit flags so the page trigger stays
            // declarative and this module remains the single owner of the
            // rule; the only gate is that the id pair resolved.
            const pairResolved = Boolean(fromId && toId);
            return Object.freeze({
                groupAddMember,
                addedNodeIds: Object.freeze(addedNodeIds),
                shouldSyncOutput: pairResolved,
                shouldSyncGeneratorInputs: pairResolved,
            });
        }

        function inactiveSmartProjection() {
            return Object.freeze({
                shouldConnect: false,
                loopTouched: false,
                flipImageInput: false,
                flipShowPrompt: false,
                fit: false,
                toImageInput: null,
                toShowPrompt: null,
                appendInputNodeId: null,
            });
        }

        function prepareSmartConnect(input) {
            const fromNode = input && input.fromNode;
            const toNode = input && input.toNode;
            if (!fromNode || !toNode || fromNode.id === toNode.id) {
                return inactiveSmartProjection();
            }
            if (isSmartLoopNode(toNode)) {
                const fromImageCount = isSmartGroupNode(fromNode)
                    ? (typeof settings.smartGroupImageCount === 'function'
                        ? settings.smartGroupImageCount(fromNode)
                        : 0)
                    : 0;
                const fromPromptCount = isSmartGroupNode(fromNode)
                    ? (typeof settings.smartGroupPromptCount === 'function'
                        ? settings.smartGroupPromptCount(fromNode)
                        : 0)
                    : 0;
                const looksImage = smartLoopLooksImage(fromNode, fromImageCount);
                const looksPrompt = smartLoopLooksPrompt(fromNode, fromPromptCount);
                const flipImageInput = Boolean(looksImage) && !Boolean(toNode.imageInput);
                const flipShowPrompt = Boolean(looksPrompt) && !Boolean(toNode.showPrompt);
                // History: `loopTouched` follows `looksImage || looksPrompt`,
                // NOT the flips — a revisit that changes nothing still
                // re-fits the loop node. Preserved verbatim; this is the
                // difference between a refactor and a behavior change.
                const loopTouched = Boolean(looksImage) || Boolean(looksPrompt);
                // `canImage` / `canPrompt` are evaluated against the flags
                // AFTER the flips are applied (history mutates `to` first).
                const toImageInput = Boolean(toNode.imageInput) || flipImageInput;
                const toShowPrompt = Boolean(toNode.showPrompt) || flipShowPrompt;
                const canImage = toImageInput && Boolean(looksImage);
                const canPrompt = toShowPrompt && Boolean(looksPrompt);
                return Object.freeze({
                    shouldConnect: canImage || canPrompt,
                    loopTouched,
                    flipImageInput,
                    flipShowPrompt,
                    fit: loopTouched,
                    toImageInput,
                    toShowPrompt,
                    appendInputNodeId: null,
                });
            }
            // Non-loop Smart targets: the durable edge + target
            // `inputNodeIds` already persist under the application
            // boundary; the policy only describes the page-side append.
            return Object.freeze({
                shouldConnect: true,
                loopTouched: false,
                flipImageInput: false,
                flipShowPrompt: false,
                fit: false,
                toImageInput: null,
                toShowPrompt: null,
                appendInputNodeId: fromNode.id,
            });
        }

        return Object.freeze({
            applyClassicConnect,
            prepareSmartConnect,
        });
    }

    global.WorkbenchLegacyGraphCompatibility = Object.freeze({
        CLASSIC_GROUP_MEMBER_TYPES,
        SMART_LOOP_PREVIEW,
        isClassicGroupMemberEligible,
        isSmartImageNode,
        isSmartPromptNode,
        isSmartGroupNode,
        isSmartLoopNode,
        create: createLegacyGraphCompatibilityPolicy,
    });
}(typeof window !== 'undefined' ? window : globalThis));
