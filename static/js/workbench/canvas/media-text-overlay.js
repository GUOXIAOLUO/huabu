/* Neutral geometry and record rules for image-editor text overlays. */
(function exposeMediaTextOverlay(global) {
    'use strict';
    function sizeOf(item, fallback = 28) { return Math.max(10, Math.min(120, Number(item?.size) || fallback)); }
    function font(item) { return `900 ${sizeOf(item)}px Arial, sans-serif`; }
    function create(text, point, options = {}) {
        const brushSize = Number(options.brushSize) || 7;
        const size = Math.max(10, Math.min(120, Number(options.size) || Math.max(14, Math.min(120, Math.round(brushSize * 2)))));
        return {id:options.createId(), text:String(text || options.defaultText()).trim(), x:Number(point?.x || 0), y:Number(point?.y || 0), color:options.color || '#ffffff', size};
    }
    function measure(item, ctx) {
        if (!item || !ctx) return {x:0, y:0, w:0, h:0};
        const size = sizeOf(item); ctx.save(); ctx.font = font(item);
        const metrics = ctx.measureText(String(item.text || '')); ctx.restore();
        const width = Math.max(1, metrics.width || 1);
        const ascent = Number.isFinite(metrics.actualBoundingBoxAscent) ? metrics.actualBoundingBoxAscent : size * 0.8;
        const descent = Number.isFinite(metrics.actualBoundingBoxDescent) ? metrics.actualBoundingBoxDescent : size * 0.25;
        const pad = Math.max(4, Math.round(size * 0.18));
        return {x:item.x - width / 2 - pad, y:item.y - (ascent + descent) / 2 - pad, w:width + pad * 2, h:ascent + descent + pad * 2, textW:width, textH:ascent + descent, pad};
    }
    function hit(items, point, ctx) {
        if (!ctx || !point) return null;
        for (let index = items.length - 1; index >= 0; index -= 1) { const item = items[index], box = measure(item, ctx); if (point.x >= box.x && point.x <= box.x + box.w && point.y >= box.y && point.y <= box.y + box.h) return item; }
        return null;
    }
    global.WorkbenchCanvasMediaTextOverlay = Object.freeze({sizeOf, font, create, measure, hit});
}(window));
