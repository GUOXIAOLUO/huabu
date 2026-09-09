/* Neutral layout projections for loop-node compatibility panels. */
(function exposeLoopLayoutProjection(global) {
    'use strict';
    function nodeSize(node = {}, opening) {
        const width = opening ? Math.max(Number(node.w || 0), 336) : Math.min(Number(node.w || 336), 336);
        const height = opening ? Math.max(Number(node.h || 0), 360) : null;
        return Object.freeze({width, height});
    }
    function panelSize(node = {}) {
        const width = Math.max(Number(node.w || 0), 336);
        const panels = (node.showPrompt ? 1 : 0) + (node.imageInput ? 1 : 0);
        const height = panels === 0 ? null : panels === 1 ? (node.showPrompt ? 330 : 320) : (node.showPrompt && node.imageInput ? 390 : 380);
        return Object.freeze({width, height});
    }
    function bodyState(node = {}, imageInputCount = 0, promptItemCount = 0) {
        const images = Math.max(0, Number(imageInputCount) || 0);
        const prompts = Math.max(0, Number(promptItemCount) || 0);
        return Object.freeze({
            imageInput: Boolean(node.imageInput),
            showPrompt: Boolean(node.showPrompt),
            imageInputCount: images,
            promptItemCount: prompts,
            hasUpstreamPrompt: prompts > 0,
        });
    }
    function runState(options = {}) {
        const targetId = String(options.targetId || '');
        const orderLength = Math.max(0, Number(options.orderLength) || 0);
        return Object.freeze({
            hasTarget: Boolean(targetId),
            targetId,
            active: Boolean(options.active),
            stopping: Boolean(options.stopping),
            orderLength,
            count: Math.max(1, Number(options.count) || 1),
        });
    }
    global.WorkbenchCanvasLoopLayoutProjection = Object.freeze({nodeSize, panelSize, bodyState, runState});
}(window));
