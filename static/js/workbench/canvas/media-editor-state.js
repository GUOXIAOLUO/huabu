/* Neutral image-editor mode rules. DOM and mutation remain adapter-owned. */
(function exposeMediaEditorState(global) {
    'use strict';
    const MODES = Object.freeze(['preview', 'crop', 'outpaint', 'mask', 'brush', 'resize', 'grid']);
    function normalize(mode) { return MODES.includes(mode) ? mode : 'crop'; }
    function presentation(mode) {
        const current = normalize(mode);
        if (current === 'preview') return Object.freeze({mode: current, preview: true, icon: '', labelKey: '', titleKey: 'canvas.previewImage', subKey: 'canvas.previewHint'});
        if (current === 'resize') return Object.freeze({mode: current, preview: false, icon: 'minimize-2', labelKey: '', titleKey: '', subKey: ''});
        const values = {
            crop: ['crop', 'canvas.applyCrop', 'canvas.cropImage', 'canvas.cropHint'],
            outpaint: ['expand', 'canvas.applyOutpaint', 'canvas.outpaintImage', 'canvas.outpaintHint'],
            mask: ['brush', 'canvas.applyMask', 'canvas.maskEdit', 'canvas.maskHint2'],
            brush: ['paintbrush', 'canvas.applyBrush', 'canvas.brushEdit', 'canvas.brushHint'],
            grid: ['grid-3x3', 'canvas.applyGrid', 'canvas.modeGrid', 'canvas.gridHint'],
        }[current];
        return Object.freeze({mode: current, preview: false, icon: values[0], labelKey: values[1], titleKey: values[2], subKey: values[3]});
    }
    function applyAction(mode) {
        return {
            outpaint: 'applyImageOutpaint',
            mask: 'applyImageMask',
            brush: 'applyImageBrush',
            resize: 'applyImageResize',
            grid: 'applyImageGridSplit',
            crop: 'applyImageCrop',
            preview: 'applyImageCrop',
        }[normalize(mode)];
    }
    function uiProjection(mode, previousMode = '') {
        const current = normalize(mode);
        const details = presentation(current);
        const preview = current === 'preview';
        return Object.freeze({
            mode: current,
            preview,
            activeModes: Object.freeze({
                crop: current === 'crop', mask: current === 'mask', brush: current === 'brush',
                resize: current === 'resize', grid: current === 'grid', outpaint: current === 'outpaint',
            }),
            applyVisible: !preview,
            icon: details.icon,
            titleKey: preview ? 'canvas.previewImage' : details.titleKey,
            subKey: preview ? 'canvas.previewHint' : details.subKey,
            clearDrawing: preview || current === 'crop' || current === 'resize' || normalize(previousMode) === 'grid',
            refreshGrid: current === 'grid',
            resetOutpaint: current === 'outpaint',
        });
    }
    function brushToolProjection(tool, mode = 'brush') {
        const tools = ['free', 'rect', 'ellipse', 'label', 'text'];
        const current = tools.includes(tool) ? tool : 'free';
        return Object.freeze({tool: current, textMode: normalize(mode) === 'brush' && current === 'text'});
    }
    function dispatch(mode, handlers = {}) {
        const action = applyAction(mode);
        return typeof handlers[action] === 'function' ? handlers[action]() : undefined;
    }
    global.WorkbenchCanvasMediaEditorState = Object.freeze({MODES, normalize, presentation, uiProjection, brushToolProjection, applyAction, dispatch});
}(window));
