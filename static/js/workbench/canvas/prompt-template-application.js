/* Prompt-template application mutation. The page supplies the selected record and effects. */
(function exposePromptTemplateApplication(global) {
    'use strict';
    function apply(options = {}) {
        const template = options.template;
        const node = options.node;
        if (!template || !node || typeof options.textFor !== 'function') return false;
        node.text = options.textFor(template, options.mode || 'positive');
        if (typeof options.close === 'function') options.close();
        return true;
    }
    global.WorkbenchCanvasPromptTemplateApplication = Object.freeze({apply});
}(window));
