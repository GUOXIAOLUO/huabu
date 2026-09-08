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
    global.WorkbenchCanvasMediaEditorState = Object.freeze({MODES, normalize, presentation});
}(window));
