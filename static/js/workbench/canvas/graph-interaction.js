/* Shared, business-neutral graph interaction intents. Page adapters decide
   compatibility, side effects, persistence, and user feedback. */
(function exposeWorkbenchCanvasGraphInteraction(global) {
    'use strict';

    function endpoint(value) {
        const source = value && typeof value === 'object' ? value : {};
        const nodeId = String(source.nodeId || source.id || '');
        const port = source.port === 'out' ? 'out' : source.port === 'in' ? 'in' : '';
        return Object.freeze({nodeId, port});
    }

    function edgeIntentFromPortDrop(origin, target) {
        const start = endpoint(origin);
        const end = endpoint(target);
        if(!start.nodeId || !end.nodeId || start.nodeId === end.nodeId || !start.port || !end.port || start.port === end.port) return null;
        const from = start.port === 'out' ? start.nodeId : end.nodeId;
        const to = start.port === 'out' ? end.nodeId : start.nodeId;
        return Object.freeze({from, to, fromPort:'out', toPort:'in'});
    }

    function edgePresentationClass(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const from = settings.fromNode && typeof settings.fromNode === 'object' ? settings.fromNode : {};
        const to = settings.toNode && typeof settings.toNode === 'object' ? settings.toNode : {};
        const classes = ['link'];
        if (settings.hovered) classes.push('link-hover');
        if (settings.selected) classes.push('link-active');
        if ([from, to].some(node => node.state === 'running' || node.running === true)) classes.push('link-running');
        return classes.join(' ');
    }

    global.WorkbenchCanvasGraphInteraction = Object.freeze({endpoint, edgeIntentFromPortDrop, edgePresentationClass});
}(window));
