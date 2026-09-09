/* Mountable Smart media-tool geometry. Owns the pure, stateless math shared by
   the retained Smart crop / draw / grid tools: resize-scale clamping, circled
   label numbering, pointer-to-canvas point mapping, grid split/join rectangle
   computation, and crop aspect-ratio parsing/fitting.

   This is the seam for card R4-29: the Smart page used to keep the editor
   modal, the canvas 2D rendering, the mode/state machine and the node
   mutation, but the product-neutral geometry below is no longer page-owned.
   R4-34 made canvas.html the single entry, so the unified page now owns the
   editor modal and the node mutation; R4-36 retired the Smart page entirely
   and the geometry is consumed by the unified runtime. The module never
   touches the DOM, `window`, or any adapter detail. */
(function exposeWorkbenchCanvasMediaTools(global) {
    'use strict';

    /* Clamp an image-resize scale to [0.05, 1]; non-finite input defaults to
       0.5. (History: was the former `clampImageResizeScale` in smart-canvas.js,
       retired by R4-36.) */
    function clampResizeScale(value) {
        const num = Number(value);
        if (!Number.isFinite(num)) return 0.5;
        return Math.max(0.05, Math.min(1, Math.round(num * 100) / 100));
    }

    /* Circled number label: 1..20 → Unicode ①..⑳, otherwise String(n). */
    function circledNumber(n) {
        return n >= 1 && n <= 20 ? String.fromCharCode(0x2460 + n - 1) : String(n);
    }

    /* Map a client-space pointer position to canvas pixel coordinates. */
    function canvasPoint(clientX, clientY, rectLeft, rectTop, rectWidth, rectHeight, canvasWidth, canvasHeight) {
        return {
            x: (clientX - rectLeft) * canvasWidth / Math.max(1, rectWidth),
            y: (clientY - rectTop) * canvasHeight / Math.max(1, rectHeight),
        };
    }

    /* Uniform rows×cols grid split rectangles with an interior gap. Each rect
       is {row, col, x, y, w, h} in source-pixel coordinates. */
    function gridSplitRects(width, height, rows, cols, gap) {
        const halfGap = gap / 2, rects = [];
        for (let row = 0; row < rows; row++) {
            const topLine = row * height / rows, bottomLine = (row + 1) * height / rows;
            const y1 = Math.round(row === 0 ? 0 : topLine + halfGap), y2 = Math.round(row === rows - 1 ? height : bottomLine - halfGap);
            for (let col = 0; col < cols; col++) {
                const leftLine = col * width / cols, rightLine = (col + 1) * width / cols;
                const x1 = Math.round(col === 0 ? 0 : leftLine + halfGap), x2 = Math.round(col === cols - 1 ? width : rightLine - halfGap);
                if (x2 > x1 && y2 > y1) rects.push({ row, col, x: x1, y: y1, w: x2 - x1, h: y2 - y1 });
            }
        }
        return rects;
    }

    /* Custom-line grid split rectangles. `hCuts` / `vCuts` are the full cut
       coordinate arrays (each including 0 and the total width/height); `gap`
       is the interior gap. */
    function gridSplitRectsCustom(width, height, hCuts, vCuts, gap) {
        const halfGap = gap / 2, rects = [];
        for (let row = 0; row < hCuts.length - 1; row++) {
            for (let col = 0; col < vCuts.length - 1; col++) {
                const y1 = Math.round(row === 0 ? hCuts[row] : hCuts[row] + halfGap), y2 = Math.round(row === hCuts.length - 2 ? hCuts[row + 1] : hCuts[row + 1] - halfGap);
                const x1 = Math.round(col === 0 ? vCuts[col] : vCuts[col] + halfGap), x2 = Math.round(col === vCuts.length - 2 ? vCuts[col + 1] : vCuts[col + 1] - halfGap);
                if (x2 > x1 && y2 > y1) rects.push({ row, col, x: x1, y: y1, w: x2 - x1, h: y2 - y1 });
            }
        }
        return rects;
    }
    function customLineHit(lines, point, width, height) {
        if (!Array.isArray(lines) || !lines.length) return -1;
        const threshold = Math.max(8, Math.min(width, height) / 80);
        let best = -1, bestDist = Infinity;
        lines.forEach((line, index) => {
            const dist = line.type === 'h' ? Math.abs(point.y - line.pos * height) : Math.abs(point.x - line.pos * width);
            if (dist < bestDist && dist <= threshold) { best = index; bestDist = dist; }
        });
        return best;
    }
    function setCustomLinePosition(line, point, width, height) {
        if (!line) return;
        line.pos = line.type === 'h'
            ? Math.max(0.001, Math.min(0.999, point.y / Math.max(1, height)))
            : Math.max(0.001, Math.min(0.999, point.x / Math.max(1, width)));
    }
    function normalizeGridSettings(horizontalLines, verticalLines, gap) {
        const horizontal = Math.max(0, Math.min(20, Number(horizontalLines) || 0));
        const vertical = Math.max(0, Math.min(20, Number(verticalLines) || 0));
        return Object.freeze({rows: horizontal + 1, cols: vertical + 1, gap: Math.max(0, Math.min(240, Number(gap) || 0))});
    }
    function brushStyle(mode, size, color, maskAlpha = 115) {
        const mask = mode === 'mask';
        const stroke = mask ? `rgba(255,255,255,${maskAlpha / 255})` : (color || '#ff2d55');
        return Object.freeze({lineCap:'round', lineJoin:'round', lineWidth:Number(size) || 20, strokeStyle:stroke, fillStyle:stroke, globalCompositeOperation:'source-over'});
    }
    function labelStyle(size, color) {
        const normalized = Math.max(18, Number(size) || 18);
        return Object.freeze({font:`900 ${normalized}px Arial, sans-serif`, lineWidth:Math.max(3, normalized / 8), strokeStyle:'rgba(255,255,255,0.92)', fillStyle:color || '#ff2d55'});
    }
    function resizeOutpaintRect(start, mode, dx, dy, boundsW, boundsH) {
        let growX = 0, growY = 0;
        if (mode === 'outpaint-left') growX = -dx;
        else if (mode === 'outpaint-right') growX = dx;
        else if (mode === 'outpaint-top') growY = -dy;
        else if (mode === 'outpaint-bottom') growY = dy;
        else if (mode === 'outpaint-corner') { growX = dx; growY = dy; }
        const w = Math.max(boundsW, start.w + growX * 2), h = Math.max(boundsH, start.h + growY * 2);
        return {x:start.x + Math.round((w - start.w) / 2), y:start.y + Math.round((h - start.h) / 2), w, h};
    }
    function resizeFreeCropRect(start, handle, dx, dy) {
        let left = start.x, top = start.y, right = start.x + start.w, bottom = start.y + start.h;
        if (handle.includes('w')) left += dx;
        if (handle.includes('e') || handle === 'resize') right += dx;
        if (handle.includes('n')) top += dy;
        if (handle.includes('s') || handle === 'resize') bottom += dy;
        const x = Math.min(left, right - 24), y = Math.min(top, bottom - 24);
        return {x, y, w:Math.max(24, right - x), h:Math.max(24, bottom - y)};
    }
    function resizeAspectCropRect(start, handle, dx, dy, ratio, boundsW, boundsH) {
        const normalized = handle === 'resize' ? 'se' : handle;
        const centerX = start.x + start.w / 2, centerY = start.y + start.h / 2;
        if (normalized === 'e' || normalized === 'w') {
            let width = Math.max(24, normalized === 'e' ? start.w + dx : start.w - dx);
            const maxW = normalized === 'e' ? boundsW - start.x : start.x + start.w;
            const maxH = Math.max(24, 2 * Math.min(centerY, boundsH - centerY));
            width = Math.min(width, maxW, maxH * ratio);
            const height = width / ratio;
            return {x:Math.round(normalized === 'e' ? start.x : start.x + start.w - width), y:Math.round(centerY - height / 2), w:Math.round(width), h:Math.round(height)};
        }
        if (normalized === 'n' || normalized === 's') {
            let height = Math.max(24, normalized === 's' ? start.h + dy : start.h - dy);
            const maxH = normalized === 's' ? boundsH - start.y : start.y + start.h;
            const maxW = Math.max(24, 2 * Math.min(centerX, boundsW - centerX));
            height = Math.min(height, maxH, maxW / ratio);
            const width = height * ratio;
            return {x:Math.round(centerX - width / 2), y:Math.round(normalized === 's' ? start.y : start.y + start.h - height), w:Math.round(width), h:Math.round(height)};
        }
        const anchorX = normalized.includes('w') ? start.x + start.w : normalized.includes('e') ? start.x : centerX;
        const anchorY = normalized.includes('n') ? start.y + start.h : normalized.includes('s') ? start.y : centerY;
        const movingX = normalized.includes('w') ? start.x + dx : normalized.includes('e') ? start.x + start.w + dx : centerX;
        const movingY = normalized.includes('n') ? start.y + dy : normalized.includes('s') ? start.y + start.h + dy : centerY;
        return aspectCropToBounds(anchorX, anchorY, movingX, movingY, ratio, normalized, boundsW, boundsH);
    }
    function customGridRects(width, height, lines, gap) {
        const rawH = [...new Set((lines || []).filter(line => line.type === 'h').map(line => line.pos * height))].sort((a, b) => a - b);
        const rawV = [...new Set((lines || []).filter(line => line.type === 'v').map(line => line.pos * width))].sort((a, b) => a - b);
        return gridSplitRectsCustom(width, height, [0, ...rawH, height], [0, ...rawV, width], gap);
    }
    function initialCropRect(width, height, inset = 0.08) {
        const pad = Math.max(0, Math.min(0.45, Number(inset) || 0));
        return {x:Math.round(width * pad), y:Math.round(height * pad), w:Math.round(width * (1 - pad * 2)), h:Math.round(height * (1 - pad * 2))};
    }
    function clampCropRect(rect, boundsW, boundsH, minSize = 24) {
        const w = Math.max(minSize, Math.min(Number(rect?.w) || minSize, boundsW));
        const h = Math.max(minSize, Math.min(Number(rect?.h) || minSize, boundsH));
        return {x:Math.max(0, Math.min(Number(rect?.x) || 0, boundsW - w)), y:Math.max(0, Math.min(Number(rect?.y) || 0, boundsH - h)), w, h};
    }
    function scaleCropRect(rect, scale) {
        const factor = Number(scale);
        if (!Number.isFinite(factor) || factor <= 0) return {...rect};
        return {x:Math.round((Number(rect?.x) || 0) * factor), y:Math.round((Number(rect?.y) || 0) * factor), w:Math.round((Number(rect?.w) || 0) * factor), h:Math.round((Number(rect?.h) || 0) * factor)};
    }
    function cropBoxProjection(rect, mode) {
        const state = rect || {};
        const outpaint = String(mode || '') === 'outpaint';
        const x = Number(state.x) || 0;
        const y = Number(state.y) || 0;
        const w = Math.max(0, Number(state.w) || 0);
        const h = Math.max(0, Number(state.h) || 0);
        return Object.freeze({
            boxX: outpaint ? 0 : x,
            boxY: outpaint ? 0 : y,
            boxWidth: w,
            boxHeight: h,
            imageLeft: outpaint ? x : null,
            imageTop: outpaint ? y : null,
            frameLeft: outpaint ? 0 : x,
            frameTop: outpaint ? 0 : y,
            frameWidth: w,
            frameHeight: h,
        });
    }
    function resizeControlProjection(sourceW, sourceH, scale) {
        const dimensions = resizeDimensions(sourceW, sourceH, scale);
        return Object.freeze({...dimensions, text:`${dimensions.targetW}×${dimensions.targetH}`});
    }
    function editorZoomProjection(baseW, baseH, zoom) {
        const width = Math.max(0, Math.round((Number(baseW) || 0) * (Number(zoom) || 0)));
        const height = Math.max(0, Math.round((Number(baseH) || 0) * (Number(zoom) || 0)));
        return Object.freeze({width, height, label:`${Math.round((Number(zoom) || 0) * 100)}%`});
    }
    function editorOverflowProjection(cropWidth, cropHeight, stageWidth, stageHeight, padding = 36) {
        const pad = Math.max(0, Number(padding) || 0);
        const overflowX = (Number(cropWidth) || 0) + pad > (Number(stageWidth) || 0);
        const overflowY = (Number(cropHeight) || 0) + pad > (Number(stageHeight) || 0);
        return Object.freeze({overflowX, overflowY, overflowing:overflowX || overflowY});
    }
    function editorCanvasProjection(naturalW, naturalH, clientW, clientH) {
        return Object.freeze({
            width: Math.max(1, Number(naturalW) || Number(clientW) || 1),
            height: Math.max(1, Number(naturalH) || Number(clientH) || 1),
            cssWidth: Math.max(1, Number(clientW) || 1),
            cssHeight: Math.max(1, Number(clientH) || 1),
        });
    }
    function brushControlProjection(mode, maskSize, paintSize, color, maskAlpha = 115) {
        const mask = String(mode || '') === 'mask';
        const size = Number(mask ? maskSize : paintSize);
        return Object.freeze({
            size: Number.isFinite(size) && size > 0 ? size : 20,
            color: mask ? '#ffffff' : (color || '#ff2d55'),
            alpha: mask ? Math.max(0, Math.min(255, Number(maskAlpha) || 0)) : 255,
        });
    }
    function previewTransformProjection(zoom, pan = {}) {
        const scale = Number(zoom) > 0 ? Number(zoom) : 1;
        const x = Number(pan.x) || 0;
        const y = Number(pan.y) || 0;
        return Object.freeze({transform:`translate(${x}px, ${y}px) scale(${scale})`, zoomed:scale > 1.001});
    }
    function compareSliderProjection(clientX, left, width) {
        const span = Number(width) || 0;
        if (span <= 0) return Object.freeze({percent:0, clipPath:'inset(0 100% 0 0)'});
        const percent = Math.max(0, Math.min(100, ((Number(clientX) - Number(left)) / span) * 100));
        return Object.freeze({percent, clipPath:`inset(0 ${100 - percent}% 0 0)`});
    }
    function previewZoomProjection(zoom, pan = {}, deltaY, localX, localY) {
        const current = Number(zoom) > 0 ? Number(zoom) : 1;
        const factor = Number(deltaY) > 0 ? .9 : 1.1;
        const nextZoom = Math.max(1, Math.min(6, current * factor));
        if (nextZoom <= 1.001) return Object.freeze({zoom:1, pan:{x:0, y:0}});
        const beforeX = ((Number(localX) || 0) - (Number(pan.x) || 0)) / current;
        const beforeY = ((Number(localY) || 0) - (Number(pan.y) || 0)) / current;
        return Object.freeze({zoom:nextZoom, pan:{x:(Number(localX) || 0) - beforeX * nextZoom, y:(Number(localY) || 0) - beforeY * nextZoom}});
    }
    function previewPanProjection(drag, clientX, clientY) {
        if (!drag) return Object.freeze({x:0, y:0});
        return Object.freeze({x:(Number(drag.ox) || 0) + (Number(clientX) || 0) - (Number(drag.sx) || 0), y:(Number(drag.oy) || 0) + (Number(clientY) || 0) - (Number(drag.sy) || 0)});
    }
    function minimaxPaneProjection(values = {}, delta = {}, scale = 1) {
        const factor = Number(scale) > 0 ? Number(scale) : 1;
        const clamp = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));
        return Object.freeze({
            libraryW: Math.round(clamp((values.libraryW || 190) + (delta.x || 0) / factor, 170, 520)),
            previewH: Math.round(clamp((values.previewH || 220) + (delta.y || 0) / factor, 130, 760)),
            videoTrackH: Math.round(clamp((values.videoTrackH || 74) + (delta.y || 0) / factor, 48, 180)),
            refLaneH: Math.round(clamp((values.refLaneH || 36) + (delta.y || 0) / factor, 30, 130)),
        });
    }
    function minimaxPlayheadProjection(total, time) {
        const duration = Math.max(0, Number(total) || 0);
        const safeTime = Math.max(0, Math.min(duration, Number(time) || 0));
        const percent = duration ? (safeTime / duration) * 100 : 0;
        const format = value => `${(Number(value || 0)).toFixed(Number(value || 0) % 1 ? 1 : 0)}s`;
        return Object.freeze({safeTime, percent, label:`${format(safeTime)} / ${format(duration)}`});
    }
    function minimaxAspectValue(value) {
        const match = String(value || '').trim().match(/\d+\s*:\s*\d+/);
        return match ? match[0].replace(/\s+/g, '') : '16:9';
    }
    function minimaxNormalizeRef(ref, kindOf) {
        if (!ref?.url) return null;
        return {...ref, kind:typeof kindOf === 'function' ? kindOf(ref) : (ref.kind || 'file')};
    }
    function minimaxUniqueRefs(refs = [], kindOf) {
        const seen = new Set();
        return (refs || []).map(ref => minimaxNormalizeRef(ref, kindOf)).filter(Boolean).filter(ref => {
            const key = `${ref.kind}:${ref.url}`;
            if (seen.has(key)) return false;
            seen.add(key); return true;
        });
    }
    function minimaxRefSummary(refs = [], kindOf) {
        const counts = minimaxUniqueRefs(refs, kindOf).reduce((map, ref) => { map[ref.kind] = (map[ref.kind] || 0) + 1; return map; }, {});
        const parts = [];
        if (counts.image) parts.push(`${counts.image} 图`);
        if (counts.video) parts.push(`${counts.video} 视频`);
        if (counts.audio) parts.push(`${counts.audio} 音频`);
        return parts.join(' · ') || 'No refs';
    }
    function minimaxCompactSegments(segments = [], playhead = 0) {
        const next = (segments || []).slice().sort((a, b) => Number(a?.start || 0) - Number(b?.start || 0)).map(seg => ({...seg}));
        let cursor = 0;
        next.forEach(seg => { seg.start = cursor; seg.duration = Math.max(0.5, Number(seg.duration || 1) || 1); cursor += seg.duration; });
        return Object.freeze({segments:next, duration:Math.max(1, cursor), playhead:Math.min(Number(playhead || 0), Math.max(1, cursor))});
    }
    function minimaxActiveSegment(segments = [], time = 0, selectedId = '') {
        const values = Array.isArray(segments) ? segments : [];
        const current = Number(time) || 0;
        return values.find(seg => current >= Number(seg?.start || 0) && current <= Number(seg?.start || 0) + Number(seg?.duration || 0)) || values.find(seg => seg?.id === selectedId) || values[0] || null;
    }
    function minimaxSegmentRefs(segment, upstreamRefs = [], kindOf, limit = 0) {
        const own = minimaxUniqueRefs(segment?.refs || [], kindOf);
        const fallback = own.length ? own : minimaxUniqueRefs(upstreamRefs, kindOf);
        return limit > 0 ? fallback.slice(0, limit) : fallback;
    }
    function minimaxSegmentRefsByKind(refs = [], kind, kindOf) {
        return minimaxUniqueRefs(refs, kindOf).filter(ref => ref.kind === kind);
    }
    function minimaxSegmentResult(item, outputValue, defaultKind = 'video', defaultName = 'minimax.mp4') {
        const url = typeof outputValue === 'function' ? outputValue(item) : outputUrlValue(item);
        if (!url) return null;
        return typeof item === 'object' ? {...item, url, kind:item.kind || defaultKind} : {url, kind:defaultKind, name:defaultName};
    }
    function minimaxPrependUnique(items = [], item, outputValue) {
        const list = Array.isArray(items) ? items.slice() : [];
        const url = typeof outputValue === 'function' ? outputValue(item) : outputUrlValue(item);
        if (!url || list.some(existing => (typeof outputValue === 'function' ? outputValue(existing) : outputUrlValue(existing)) === url)) return list;
        list.unshift(item);
        return list;
    }
    function minimaxSourceProjection(sources = []) {
        const values = Array.isArray(sources) ? sources : [];
        return Object.freeze({
            sources: values,
            prompt: values.map(source => source?.prompt).filter(Boolean).join('\n\n'),
            refs: values.flatMap(source => Array.isArray(source?.refs) ? source.refs : []).filter(ref => ref?.url),
        });
    }
    function minimaxSegmentTiming(segment = {}, previousEnd = 0, fallbackDuration = 8) {
        const duration = Math.max(0.5, Number(segment.duration || fallbackDuration || 8) || 8);
        const start = Math.max(Math.max(0, Number(segment.start || 0) || 0), Number(previousEnd || 0));
        const trimIn = Math.max(0, Math.min(Number(segment.trimIn || 0), Math.max(0, duration - 0.1)));
        const trimOut = Math.max(trimIn + 0.1, Math.min(duration, Number(segment.trimOut || duration) || duration));
        return Object.freeze({start, duration, trimIn, trimOut});
    }
    function minimaxSegmentVisuals(segment = {}, nodeAspect = '16:9', nodeMegapixels = 0.4, normalizeAspect) {
        const aspect = typeof normalizeAspect === 'function' ? normalizeAspect(segment.aspectRatio || nodeAspect || '16:9') : String(segment.aspectRatio || nodeAspect || '16:9');
        const rawMegapixels = Number(segment.megapixels);
        return Object.freeze({aspectRatio:aspect, megapixels:Number.isFinite(rawMegapixels) ? rawMegapixels : Number(nodeMegapixels || 0.4)});
    }
    function minimaxReferenceMigration(segment = {}, kindOf, limit = 0) {
        const buckets = segment.refs && typeof segment.refs === 'object' && !Array.isArray(segment.refs) ? segment.refs : {};
        const migrated = [
            ...(Array.isArray(segment.refs) ? segment.refs : []),
            ...(Array.isArray(segment.refItems) ? segment.refItems : []),
            ...['image','video','audio'].flatMap(kind => Array.isArray(buckets[kind]) ? buckets[kind].map(ref => ({...ref, kind})) : [])
        ];
        const refs = minimaxUniqueRefs(migrated, kindOf);
        return limit > 0 ? refs.slice(0, limit) : refs;
    }
    function minimaxOutputProjection(segment = {}, materials = [], outputValue, kindOf) {
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        const kind = typeof kindOf === 'function' ? kindOf : (item => item?.kind || 'video');
        const result = segment.result && value(segment.result) ? {...segment.result, kind:segment.result.kind || kind(segment.result)} : null;
        const results = Array.isArray(segment.results) ? segment.results.filter(item => value(item)) : [];
        const owned = Array.isArray(materials) ? materials.filter(item => value(item)) : [];
        return Object.freeze({result, results, materials:owned});
    }
    function minimaxNodeConfig(node = {}, normalizeAspect, defaultWorkflow = 'MiniMax_H3.json', defaultWorkflowId = '') {
        const aspect = typeof normalizeAspect === 'function' ? normalizeAspect(node.aspectRatio || '16:9') : String(node.aspectRatio || '16:9');
        const megapixels = Number(node.megapixels);
        return Object.freeze({
            workflow: node.workflow || defaultWorkflow,
            minimaxRunningHubWorkflowId: node.minimaxRunningHubWorkflowId || defaultWorkflowId,
            rhPayment: node.rhPayment || 'free',
            aspectRatio: aspect,
            megapixels: Number.isFinite(megapixels) ? megapixels : 0.4,
        });
    }
    function minimaxSegmentList(segments, duration = 8, createId) {
        const values = Array.isArray(segments) ? segments.slice() : [];
        if (!values.length) values.push({start:0, duration:Number(duration || 8) || 8, prompt:'', refs:[], result:null, results:[], trimIn:0, trimOut:Number(duration || 8) || 8});
        values.forEach(segment => { if (!segment.id && typeof createId === 'function') segment.id = createId(); });
        return values;
    }
    function minimaxSelectionProjection(segments = [], selectedId = '', fallbackDuration = 0) {
        const values = Array.isArray(segments) ? segments : [];
        const selected = values.find(segment => segment?.id === selectedId) || values[0] || null;
        const duration = Math.max(1, Number(fallbackDuration || 0), ...values.map(segment => Number(segment?.start || 0) + Number(segment?.duration || 0)));
        return Object.freeze({selectedId:selected?.id || '', duration, selected});
    }
    function minimaxDownloadProjection(item, outputValue, fileName, safeName, fallback = 'minimax.mp4') {
        const value = typeof outputValue === 'function' ? outputValue(item) : outputUrlValue(item);
        if (!value) return null;
        const base = item?.name || (typeof fileName === 'function' ? fileName(value) : '') || fallback;
        return Object.freeze({url:value, name:typeof safeName === 'function' ? safeName(base, fallback) : base});
    }
    function minimaxTimelineInteraction(segments = [], total = 0, time = 0, selectedId = '') {
        const playhead = minimaxPlayheadProjection(total, time);
        const active = minimaxActiveSegment(segments, playhead.safeTime, selectedId);
        return Object.freeze({...playhead, active, selectedId:active?.id || '', selectionChanged:Boolean(active?.id && active.id !== selectedId)});
    }
    function cropHandleFromPoint(x, y, width, height, slop = 16) {
        const nearL = x <= slop, nearR = width - x <= slop, nearT = y <= slop, nearB = height - y <= slop;
        if (nearT && nearL) return 'nw'; if (nearT && nearR) return 'ne';
        if (nearB && nearL) return 'sw'; if (nearB && nearR) return 'se';
        if (nearT) return 'n'; if (nearR) return 'e'; if (nearB) return 's'; if (nearL) return 'w';
        return 'move';
    }
    function pointerDelta(startX, startY, currentX, currentY) {
        return {dx:Number(currentX) - Number(startX), dy:Number(currentY) - Number(startY)};
    }
    function createCropDrag(mode, clientX, clientY, cropState) {
        return Object.freeze({mode:String(mode || 'move'), sx:Number(clientX) || 0, sy:Number(clientY) || 0, start:{...(cropState || {})}});
    }

    /* Parse a crop aspect preset into a numeric ratio, or null for free form.
       `preset` is 'free' | 'source' | 'w:h'; `sourceRatio` is the caller's
       source width/height (already computed by the page for 'source'). */
    function parseCropRatio(preset, sourceRatio) {
        if (!preset || preset === 'free') return null;
        if (preset === 'source') {
            const r = Number(sourceRatio);
            return r > 0 && Number.isFinite(r) ? r : null;
        }
        const parts = String(preset).split(':').map(v => Math.max(0, Number(v)));
        return parts.length === 2 && parts[0] > 0 && parts[1] > 0 ? parts[0] / parts[1] : null;
    }

    /* Fit a crop rect to an aspect ratio (or clamp to bounds when ratio is
       null), keeping the rect centered. Returns {x, y, w, h} rounded the same
       way the former `fitCropRectToAspect` did; the caller applies it to its
       own state and runs its own boundary clamp. */
    function fitCropRectToAspect(ratio, boundsW, boundsH, rect) {
        const minSize = 24;
        let nextW = Math.max(minSize, Number(rect.w || boundsW));
        let nextH = Math.max(minSize, Number(rect.h || boundsH));
        if (ratio) {
            if (nextW / nextH > ratio) nextW = nextH * ratio;
            else nextH = nextW / ratio;
            if (nextW > boundsW) { nextW = boundsW; nextH = nextW / ratio; }
            if (nextH > boundsH) { nextH = boundsH; nextW = nextH * ratio; }
        } else {
            nextW = Math.min(nextW, boundsW);
            nextH = Math.min(nextH, boundsH);
        }
        const cx = Number(rect.x || 0) + Number(rect.w || nextW) / 2;
        const cy = Number(rect.y || 0) + Number(rect.h || nextH) / 2;
        const w = Math.round(nextW);
        const h = Math.round(nextH);
        return { x: Math.round(cx - w / 2), y: Math.round(cy - h / 2), w, h };
    }

    function resizeDimensions(sourceW, sourceH, scale) {
        const width = Math.max(1, Math.round(Number(sourceW) || 0));
        const height = Math.max(1, Math.round(Number(sourceH) || 0));
        const factor = clampResizeScale(scale);
        return {sourceW: width, sourceH: height, scale: factor, targetW: Math.max(1, Math.round(width * factor)), targetH: Math.max(1, Math.round(height * factor))};
    }

    function gridLayout(rects, groupId) {
        const items = Array.isArray(rects) ? rects : [];
        const rows = Math.max(1, ...items.map(rect => Number(rect?.row || 0) + 1));
        const cols = Math.max(1, ...items.map(rect => Number(rect?.col || 0) + 1));
        return {type: 'grid-split', groupId: String(groupId || ''), rows, cols};
    }

    function outputPoint(node, offsetY = 0) {
        return {x: (Number(node?.x) || 0) + Number(node?.w || 260) + 36, y: (Number(node?.y) || 0) + Number(offsetY || 0)};
    }

    function extensionFromNameOrUrl(name = '', url = '') {
        const source = [name, url].map(value => String(value || '').split('?')[0].split('#')[0]).find(value => /\.[a-z0-9]{2,8}$/i.test(value));
        return source?.match(/(\.[a-z0-9]{2,8})$/i)?.[1] || '.png';
    }

    function safeDownloadFileName(name, fallback = 'image.png') {
        return String(name || fallback).replace(/[\\/:*?"<>|]+/g, '_').trim() || fallback;
    }

    function baseNameWithoutExtension(name, fallback = 'image') {
        return String(name || fallback).replace(/\.[^.]+$/, '') || fallback;
    }

    function outputFileName(name, suffix, extension = '.png') {
        return `${baseNameWithoutExtension(name)}${suffix || ''}${String(extension || '.png').startsWith('.') ? extension : `.${extension}`}`;
    }

    function downloadNameForGroupImage(item, index = 0, outputName) {
        const fallback = `image-${String(index + 1).padStart(2, '0')}${extensionFromNameOrUrl(item?.name, item?.url)}`;
        const derived = typeof outputName === 'function' ? outputName(item?.url || '') : '';
        let name = safeDownloadFileName(item?.name || derived || fallback, fallback);
        if (!/\.[a-z0-9]{2,8}$/i.test(name)) name += extensionFromNameOrUrl(name, item?.url);
        return name;
    }

    function imageOutputUrls(items, kindOf) {
        return (Array.isArray(items) ? items : []).filter(item => typeof kindOf !== 'function' || kindOf(item) === 'image')
            .map(item => typeof item === 'string' ? item : item?.url || '').filter(Boolean);
    }

    function mediaRefsFromNode(node, options = {}) {
        if (!node) return [];
        const nodes = Array.isArray(options.nodes) ? options.nodes : [];
        const findNode = id => nodes.find(item => item?.id === id);
        const kindNode = typeof options.mediaKindForNode === 'function' ? options.mediaKindForNode : () => 'image';
        const kindOutput = typeof options.mediaKindForOutputItem === 'function' ? options.mediaKindForOutputItem : kindNode;
        const outputValue = typeof options.outputUrlValue === 'function' ? options.outputUrlValue : outputUrlValue;
        const outputName = typeof options.outputImageName === 'function' ? options.outputImageName : () => '';
        if (node.type === 'image' && node.url) {
            const kind = kindNode(node);
            return [{url:node.url, name:node.name || kind, role:node.role || '', kind}];
        }
        if (node.type === 'group') {
            return (node.items || []).map(findNode).filter(item => item?.type === 'image' && item.url)
                .map(item => ({url:item.url, name:item.name || kindNode(item), role:item.role || '', kind:kindNode(item)}));
        }
        if (node.type === 'output') {
            return (node.images || []).map((item, index) => {
                const url = outputValue(item);
                if (!url) return null;
                const kind = kindOutput(item);
                return {url, name:outputName(url) || `output-${index + 1}`, kind, nodeId:node.id, outputIndex:index};
            }).filter(Boolean);
        }
        if (typeof options.generatedImageRefs === 'function' && (options.mediaOutputTypes || []).includes(node.type)) {
            return options.generatedImageRefs(node);
        }
        return [];
    }

    function latestOutputReference(node, options = {}) {
        if (!node || node.type !== 'output' || !Array.isArray(node.images)) return null;
        const outputValue = typeof options.outputUrlValue === 'function' ? options.outputUrlValue : outputUrlValue;
        const kindOutput = typeof options.mediaKindForOutputItem === 'function' ? options.mediaKindForOutputItem : () => 'image';
        for (let index = node.images.length - 1; index >= 0; index -= 1) {
            const item = node.images[index], url = outputValue(item);
            if (url) {
                const kind = kindOutput(item);
                return {id:node.id, type:'outputImage', label:options.label || '上游输出', preview:url,
                    refs:[{url, name:options.name || 'output.png', kind, nodeId:node.id, outputIndex:index}], prompt:''};
            }
        }
        return null;
    }

    function generatedMediaSources(node, refs) {
        if (!node || !Array.isArray(refs) || !refs.length) return [];
        return refs.map((ref, index) => ({
            id:`${node.id}:generated:${index}:${ref.url}`,
            type:'generatedImage',
            label:`上游生成 ${index + 1}`,
            preview:ref.url,
            refs:[ref],
            prompt:''
        }));
    }

    function imageMediaSource(node, kindOf) {
        if (!node || node.type !== 'image' || !node.url) return null;
        const kind = typeof kindOf === 'function' ? kindOf(node) : 'image';
        return {id:node.id, type:kind, label:node.name || kind, preview:node.url,
            refs:[{url:node.url, name:node.name || kind, role:node.role || '', kind}], prompt:''};
    }

    function groupMediaSources(node, options = {}) {
        if (!node || node.type !== 'group' || !Array.isArray(options.nodes)) return [];
        const kindOf = typeof options.mediaKindForNode === 'function' ? options.mediaKindForNode : () => 'image';
        const findNode = id => options.nodes.find(item => item?.id === id);
        const items = (node.items || []).map(findNode).filter(Boolean);
        const sources = items.filter(item => item.type === 'image' && item.url).map(item => {
            const kind = kindOf(item);
            return {id:`${node.id}:${item.id}`, type:`group-${kind}`, groupId:node.id, imageId:item.id,
                label:item.name || kind, preview:item.url,
                refs:[{url:item.url, name:item.name || kind, role:item.role || '', kind}], prompt:''};
        });
        const prompts = items.filter(item => item.type === 'prompt').map(item => item.text || '').filter(Boolean);
        if (prompts.length) {
            const combined = prompts.join('\n\n');
            sources.push({id:`${node.id}:prompts`, type:'groupPrompt', groupId:node.id,
                label:combined.slice(0, 32), refs:[], prompt:combined});
        }
        return sources;
    }

    function promptMediaSource(node) {
        if (!node || node.type !== 'prompt') return null;
        const text = node.text || '';
        return {id:node.id, type:'prompt', label:(text || '提示词').slice(0, 32), refs:[], prompt:text};
    }

    function promptGroupMediaSource(node, options = {}) {
        if (!node || node.type !== 'promptGroup' || !Array.isArray(options.nodes)) return null;
        const prompts = (node.items || []).map(id => options.nodes.find(item => item?.id === id))
            .filter(item => item?.type === 'prompt').map(item => item.text || '').filter(Boolean);
        return {id:node.id, type:'promptGroup', label:`提示词 ${prompts.length} 个`, refs:[], prompt:prompts.join('\n\n')};
    }

    function llmMediaSource(node) {
        if (!node || node.type !== 'llm' || (node.mode || 'node') !== 'node' || !node.outputText) return null;
        const text = node.outputText || '';
        return {id:node.id, type:'llm', label:text.slice(0, 32), refs:[], prompt:text};
    }

    function loopFallbackSource(node, prompt, label = 'Loop') {
        if (!node || node.type !== 'loop') return null;
        return {id:node.id, type:'loop', label, refs:[], prompt:prompt || ''};
    }

    function loopImageMediaSources(node, refs, options = {}) {
        if (!node || node.type !== 'loop' || !Array.isArray(refs) || !refs.length) return [];
        const index = Math.max(1, Number(options.index || node.loopStart || 1) || 1);
        const prompt = options.prompt || '';
        const labelFor = typeof options.labelFor === 'function' ? options.labelFor : value => `Loop image ${value}`;
        return refs.map((ref, offset) => ({
            id:`${node.id}:image:${index + offset}:${ref.url}`,
            type:'loopImage',
            label:labelFor(index + offset),
            preview:ref.url,
            refs:[ref],
            prompt:offset === 0 ? prompt : ''
        }));
    }

    function orderedInputSources(node, sources) {
        if (!node) return [];
        const list = Array.isArray(sources) ? sources : [];
        const ids = new Set(list.map(source => source?.id));
        node.inputs = (node.inputs || []).filter(id => ids.has(id));
        list.forEach(source => { if (source?.id && !node.inputs.includes(source.id)) node.inputs.push(source.id); });
        return node.inputs.map(id => list.find(source => source?.id === id)).filter(Boolean);
    }

    function reorderInputIds(inputs, movedId, targetId, imageIds) {
        const current = Array.isArray(inputs) ? inputs.slice() : [];
        const mediaIds = new Set(Array.isArray(imageIds) ? imageIds : []);
        if (!movedId || movedId === targetId || !mediaIds.has(movedId) || !mediaIds.has(targetId)) return null;
        const promptIds = current.filter(id => !mediaIds.has(id));
        const ids = current.filter(id => mediaIds.has(id));
        const from = ids.indexOf(movedId), to = ids.indexOf(targetId);
        if (from < 0 || to < 0) return null;
        ids.splice(to, 0, ids.splice(from, 1)[0]);
        return [...ids, ...promptIds];
    }

    function imageInputSources(sources, refsOfKind) {
        const list = Array.isArray(sources) ? sources : [];
        const filterRefs = typeof refsOfKind === 'function' ? refsOfKind : refs => refs || [];
        return list.map(source => ({...source, refs:filterRefs(source?.refs || [])}))
            .filter(source => source.refs?.length);
    }

    function promptInputSources(sources) {
        return (Array.isArray(sources) ? sources : []).filter(source => source?.prompt && !source.refs?.length);
    }
    function inputViewProjection(sources, refsOfKind) {
        return {imageInputs:imageInputSources(sources, refsOfKind), promptInputs:promptInputSources(sources)};
    }

    function refSourceIds(sources) {
        return (Array.isArray(sources) ? sources : []).filter(source => source?.refs?.length).map(source => source.id).filter(Boolean);
    }

    function connectedInputNodes(targetId, connections, nodes) {
        const list = Array.isArray(nodes) ? nodes : [];
        const byId = new Map(list.map(node => [node?.id, node]));
        return (Array.isArray(connections) ? connections : [])
            .filter(connection => connection?.to === targetId)
            .map(connection => byId.get(connection.from)).filter(Boolean);
    }

    function generatedMediaRefs(node, options = {}) {
        if (!node) return [];
        const outputValue = typeof options.outputUrlValue === 'function' ? options.outputUrlValue : outputUrlValue;
        const kindOutput = typeof options.mediaKindForOutputItem === 'function' ? options.mediaKindForOutputItem : () => 'image';
        const outputName = typeof options.outputImageName === 'function' ? options.outputImageName : () => '';
        const keepAll = (options.mediaOutputTypes || ['rh', 'ltxDirector', 'video', 'minimax']).includes(node.type);
        return (node.generatedOutputs || []).map((item, index) => {
            const url = outputValue(item);
            if (!url) return null;
            const kind = kindOutput(item);
            return {url, name:outputName(url) || `${node.type || 'generated'}-${index + 1}`, kind, index};
        }).filter(Boolean).filter(ref => keepAll || ref.kind === 'image').map(ref => {
            const {index, ...clean} = ref;
            return clean;
        });
    }

    function groupImageItems(group, nodeById, options = {}) {
        if (!group || group.type !== 'group' || typeof nodeById !== 'function') return [];
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : () => 'image';
        const missing = typeof options.isMissing === 'function' ? options.isMissing : () => false;
        const outputName = typeof options.outputName === 'function' ? options.outputName : () => '';
        return (group.items || []).map(id => nodeById(id)).filter(node => node?.type === 'image' && node.url && kindOf(node) === 'image' && !missing(node.url))
            .map((node, index) => ({url:node.url, name:node.name || outputName(node.url) || `image-${index + 1}.png`, kind:'image', nodeId:node.id, __index:index}));
    }
    function downloadableImageUrls(images, outputUrlValue, isMissing) {
        return (images || []).map(outputUrlValue).filter(url => url && !isMissing(url) && (url.startsWith('/output/') || url.startsWith('/assets/')));
    }
    function outputResolutionParts(text, runMs) {
        return Object.freeze({resolution:String(text || '--'), runMs:Number(runMs) > 0 ? Number(runMs) : 0});
    }
    function outputResolutionMarkup(text, runMs, formatDuration) {
        const parts = outputResolutionParts(text, runMs);
        const html = [parts.resolution];
        if (parts.runMs && typeof formatDuration === 'function') html.push(`<span>${formatDuration(parts.runMs)}</span>`);
        return html.join('<span style="opacity:.38">|</span>');
    }
    function compareModeStyles(active) {
        return active ? Object.freeze({clipPath:'inset(0 50% 0 0)', sliderLeft:'50%'}) : Object.freeze({clipPath:'', sliderLeft:''});
    }
    function rerunOutputProjection(meta, point, makeId) {
        if (!meta?.run?.nodeType || typeof makeId !== 'function') return null;
        const base = JSON.parse(JSON.stringify(meta.run.node || {}));
        const p = point || {x:0, y:0};
        const node = {...base, id:makeId(base.type || meta.run.nodeType), type:meta.run.nodeType, x:p.x, y:p.y, inputs:[], running:false};
        const createdNodes = [node], createdConnections = [];
        const prompt = meta.run.prompt || '';
        if (prompt) {
            const promptNode = {id:makeId('pr'), type:'prompt', x:p.x - 340, y:p.y, text:prompt};
            createdNodes.push(promptNode); createdConnections.push({id:makeId('c'), from:promptNode.id, to:node.id});
        }
        (meta.run.refs || []).slice(0, 8).forEach((ref, index) => {
            const imageNode = {id:makeId('img'), type:'image', x:p.x - 340, y:p.y + 110 + index * 86, url:ref.url, name:ref.name || 'image'};
            createdNodes.push(imageNode); createdConnections.push({id:makeId('c'), from:imageNode.id, to:node.id});
        });
        return {nodes:createdNodes, connections:createdConnections};
    }
    function outputImageNodeProjection(url, point, id, nameOrResolver) {
        if (!url || typeof id !== 'function') return null;
        const p = point || {x:0, y:0};
        const name = typeof nameOrResolver === 'function' ? nameOrResolver(url) : nameOrResolver;
        return {id:id('img'), type:'image', x:p.x, y:p.y, url, name:name || outputImageName(url)};
    }
    function outputPromptProjection(meta, noPromptLabel = '') {
        const prompt = meta?.run?.prompt || '';
        return Object.freeze({prompt, open:Boolean(prompt || meta?.run), text:prompt || noPromptLabel});
    }
    function outputRerunAvailable(meta) {
        return Boolean(meta?.run?.nodeType);
    }
    function outputNodeProjection(point, id) {
        if (typeof id !== 'function') return null;
        const p = point || {x:0, y:0};
        return {id:id('out'), type:'output', x:p.x, y:p.y, images:[]};
    }
    function findOutputNodeForSource(sourceId, connections, nodes) {
        const list = Array.isArray(nodes) ? nodes : [];
        const byId = new Map(list.map(node => [node?.id, node]));
        return (Array.isArray(connections) ? connections : [])
            .filter(connection => connection?.from === sourceId)
            .map(connection => byId.get(connection.to))
            .find(node => node?.type === 'output') || null;
    }
    function latestGeneratedOutputItem(node, outputValue) {
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        return [...(node?.generatedOutputs || [])].reverse().find(item => value(item));
    }
    function outputHasUrl(output, url, outputValue) {
        if (!url) return false;
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        return (output?.images || []).some(item => value(item) === url);
    }
    function outputNodesForSource(sourceId, connections, nodes) {
        const list = Array.isArray(nodes) ? nodes : [];
        const byId = new Map(list.map(node => [node?.id, node]));
        return (Array.isArray(connections) ? connections : [])
            .filter(connection => connection?.from === sourceId)
            .map(connection => byId.get(connection.to)).filter(node => node?.type === 'output');
    }
    function outputItemsWithUrl(items, outputValue) {
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        return (Array.isArray(items) ? items : []).filter(item => value(item));
    }
    function outputDownloadProjection(node, options = {}) {
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : () => 'image';
        const value = typeof options.outputValue === 'function' ? options.outputValue : outputUrlValue;
        const missing = typeof options.isMissing === 'function' ? options.isMissing : () => false;
        return {urls:imageOutputUrls(node?.images, kindOf), downloadable:downloadableImageUrls(node?.images, value, missing)};
    }
    function uniqueOutputItems(output, items, outputValue) {
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        return outputItemsWithUrl(items, value).filter(item => !outputHasUrl(output, value(item), value));
    }
    function generatedImageNodeProjection(file, point, id, suffix, extra = {}) {
        if (!file?.url || typeof id !== 'function') return null;
        const p = point || {x:0, y:0};
        return {id:id('img'), type:'image', x:p.x, y:p.y, url:file.url, name:file.name || suffix, ...extra};
    }
    function inputGroupProjection(urls, point, id, nameForUrl) {
        const list = (Array.isArray(urls) ? urls : []).filter(Boolean);
        if (!list.length || typeof id !== 'function') return null;
        const cols = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(list.length))));
        const cardW = 260, cardH = 336, gap = 24, base = point || {x:0, y:0};
        const imageNodes = list.map((url, index) => ({
            id:id('img'), type:'image', x:base.x + 24 + (index % cols) * (cardW + gap),
            y:base.y + 58 + Math.floor(index / cols) * (cardH + gap), w:cardW, h:cardH,
            url, name:typeof nameForUrl === 'function' ? nameForUrl(url) : ''
        }));
        const rows = Math.ceil(list.length / cols);
        const group = {id:id('grp'), type:'group', x:base.x, y:base.y,
            w:cols * cardW + (cols - 1) * gap + 48, h:rows * cardH + (rows - 1) * gap + 90,
            items:imageNodes.map(node => node.id)};
        return {nodes:[...imageNodes, group], group};
    }
    function downstreamTargetIds(sourceId, connections) {
        return (Array.isArray(connections) ? connections : []).filter(connection => connection?.from === sourceId).map(connection => connection.to).filter(Boolean);
    }
    function archiveDownloadFilename(title, id, fallback = 'canvas-output') {
        const prefix = String(title || fallback).replace(/[\\/:*?"<>|]+/g, '_').slice(0, 48) || fallback;
        return `${prefix}-${id}.zip`;
    }
    function archiveDownloadPayload(urls, filename, extra = {}) {
        return {urls:(Array.isArray(urls) ? urls : []).filter(Boolean), filename:String(filename || 'canvas-output.zip'), ...extra};
    }
    function downloadHref(url, filename, originalUrl) {
        if (!url) return '';
        const raw = typeof originalUrl === 'function' ? originalUrl(url) : url;
        if (raw.startsWith('data:') || raw.startsWith('blob:') || raw.startsWith('/api/download-output')) return raw;
        return `/api/download-output?url=${encodeURIComponent(raw)}&name=${encodeURIComponent(filename || outputDownloadName(raw))}`;
    }
    function generatorSourceProjection(gen, connections, nodes, options = {}) {
        if (!gen) return [];
        const find = id => (nodes || []).find(node => node?.id === id);
        const sources = connectedInputNodes(gen.id, connections, nodes).map(node => {
            if (node.type === 'output' && (node.images || []).length) {
                const latest = latestOutputReference(node, {outputUrlValue:options.outputUrlValue, mediaKindForOutputItem:options.mediaKindForOutputItem, label:'上游输出', name:'output.png'});
                if (latest) return latest;
            }
            if ((options.mediaOutputTypes || []).includes(node.type)) {
                const refs = typeof options.generatedImageRefs === 'function' ? options.generatedImageRefs(node) : [];
                const generated = generatedMediaSources(node, refs);
                if (generated.length) return generated;
            }
            if (node.type === 'image' && node.url) return imageMediaSource(node, options.mediaKindForNode);
            if (node.type === 'group') return groupMediaSources(node, {nodes, mediaKindForNode:options.mediaKindForNode});
            if (node.type === 'prompt') return promptMediaSource(node);
            if (node.type === 'loop') {
                const ctx = gen._activeLoopCtx || options.loopContext || null;
                const prompt = typeof options.renderLoopPrompt === 'function' ? options.renderLoopPrompt(node, ctx) : '';
                const refs = typeof options.loopInputImageRefs === 'function' ? options.loopInputImageRefs(node, ctx) : [];
                const imageSources = loopImageMediaSources(node, refs, {index:ctx?.index, prompt, labelFor:options.loopImageLabel});
                return imageSources.length ? imageSources : loopFallbackSource(node, prompt, options.loopLabel ? options.loopLabel(node) : 'Loop');
            }
            if (node.type === 'promptGroup') return promptGroupMediaSource(node, {nodes});
            if (node.type === 'llm') return llmMediaSource(node);
            return null;
        });
        return sources.flat().filter(Boolean);
    }
    function outputDownloadName(url, timestamp = Date.now()) {
        const clean = String(url || '').split('?')[0];
        const ext = clean.includes('.') ? clean.split('.').pop() : 'png';
        return `canvas-output-${timestamp}.${ext || 'png'}`;
    }
    function formatRunDuration(ms) {
        const total = Math.max(0, Math.round(Number(ms || 0) / 1000));
        const minutes = Math.floor(total / 60), seconds = total % 60;
        return minutes ? `${minutes}m ${String(seconds).padStart(2, '0')}s` : `${seconds}s`;
    }
    function outputUrlValue(item) { return typeof item === 'string' ? item : item?.url || ''; }
    function outputDomKeyForItem(item) { return `url:${outputUrlValue(item)}`; }
    function outputDomKeyForPending(pending) { return `pending:${pending?.id || ''}`; }
    function outputMetaFor(images, url) {
        const item = (images || []).find(value => outputUrlValue(value) === url);
        return item && typeof item === 'object' ? item : {};
    }
    function outputImageName(url) {
        const clean = String(url || '').split('?')[0];
        const name = clean.split('/').filter(Boolean).pop();
        return name ? decodeURIComponent(name) : 'output image';
    }
    function outputGridLayout(images, layout) {
        if (!Array.isArray(images) || !images.length || !layout || layout.type !== 'grid-split' || !layout.groupId) return null;
        return images.every(item => item && typeof item === 'object' && item.grid?.groupId === layout.groupId) ? layout : null;
    }
    function outputGridPlacement(grid) {
        if (!grid) return null;
        return Object.freeze({row:Math.max(0, Number(grid.row) || 0), col:Math.max(0, Number(grid.col) || 0), w:Math.max(1, Number(grid.w) || 1), h:Math.max(1, Number(grid.h) || 1)});
    }
    function outputPresentation(item, options = {}) {
        const url = outputUrlValue(item), meta = item && typeof item === 'object' ? item : {};
        return Object.freeze({url, kind:options.kindOf ? options.kindOf(item) : '', name:meta.name || outputImageName(url), runMs:Number(meta.runMs) > 0 ? Number(meta.runMs) : 0, placement:options.useGrid ? outputGridPlacement(meta.grid) : null});
    }
    function appendOutputRecords(existing, images, compareRef, metas = [], layout = null) {
        const list = (images || []).filter(Boolean);
        const nextImages = layout?.type === 'grid-split' ? [] : [...(existing || [])];
        const records = list.map((url, index) => {
            const meta = metas[index] || metas[0] || {}, source = url && typeof url === 'object' ? url : {};
            const item = {url:outputUrlValue(url), viewed:false, runMs:meta.runMs || 0, run:meta.run || null};
            if (source.name) item.name = source.name;
            if (source.kind || source.mediaKind) item.kind = source.kind || source.mediaKind;
            if (meta.kind) item.kind = meta.kind;
            if (meta.grid) item.grid = meta.grid;
            return item;
        });
        const comparisons = {};
        if (compareRef?.url) list.forEach(url => { comparisons[outputUrlValue(url)] = {url:compareRef.url, name:compareRef.name || 'input image'}; });
        return {images:[...nextImages, ...records], outputLayout:layout?.type === 'grid-split' ? layout : null, imageComparisons:comparisons};
    }
    function appendUniqueOutputRecords(existing, images, compareRef, metas = [], layout = null, outputValue) {
        const value = typeof outputValue === 'function' ? outputValue : outputUrlValue;
        const current = {images:existing || []};
        const unique = uniqueOutputItems(current, images, value);
        return {...appendOutputRecords(existing, unique, compareRef, metas, layout), added:unique.length};
    }
    function markOutputViewed(images, url) {
        let changed = false;
        const next = (images || []).map(item => {
            if (typeof item === 'string') return item;
            if (item?.url === url && !item.viewed) { changed = true; return {...item, viewed:true}; }
            return item;
        });
        return {images:next, changed};
    }
    function outputCompareUrl(url, comparisons, images) {
        const source = comparisons?.[url];
        if (typeof source === 'string' && source) return source;
        if (source?.url) return source.url;
        return outputMetaFor(images, url)?.run?.refs?.find(ref => ref?.url)?.url || '';
    }
    function collectLightboxItems(options = {}) {
        const normalize = options.normalize || (() => null), sourceOut = options.sourceOut;
        if (sourceOut) {
            if (sourceOut.type === 'group') return (options.groupItems ? options.groupItems(sourceOut) : []).map(item => normalize(item, sourceOut)).filter(Boolean);
            if (sourceOut.type === 'image' && sourceOut.url) return [normalize({url:sourceOut.url, kind:options.imageKind?.(sourceOut)}, sourceOut)].filter(Boolean);
            return (sourceOut.images || []).map(item => normalize(item, sourceOut)).filter(Boolean);
        }
        const outputs = (options.outputNodes || []).flatMap(node => (node.images || []).map(item => normalize(item, node)).filter(Boolean));
        if (outputs.length) return outputs;
        return (options.logs || []).flatMap(log => (log.outputs || []).map(url => normalize(url, null)).filter(Boolean));
    }
    function nextLightboxItem(items, currentUrl, direction = 1) {
        if (!Array.isArray(items) || items.length < 2) return null;
        let index = items.findIndex(item => item.url === currentUrl);
        if (index < 0) index = 0;
        return items[(index + direction + items.length) % items.length] || null;
    }
    function clampListIndex(index, length) {
        const size = Math.max(0, Number(length) || 0);
        return size ? Math.max(0, Math.min(size - 1, Number(index) || 0)) : -1;
    }
    function lightboxVisibility(kind) {
        const video = kind === 'video';
        return Object.freeze({video, image:!video, compare:!video});
    }
    function lightboxProjection(options = {}) {
        const videoMode = options.kind === 'video';
        return Object.freeze({
            videoMode,
            visibility:lightboxVisibility(videoMode ? 'video' : 'image'),
            showDownloadAll:Number(options.groupCount) > 1,
            compareUrl:options.compareUrl || '',
        });
    }

    function aspectCropToBounds(anchorX, anchorY, movingX, movingY, ratio, handle, boundsW, boundsH) {
        const minSize = 24;
        let width = Math.max(minSize, Math.abs(movingX - anchorX));
        let height = Math.max(minSize, Math.abs(movingY - anchorY));
        const corner = /[ns][ew]/.test(handle);
        if (corner) {
            if (width / height > ratio) width = height * ratio;
            else height = width / ratio;
        } else if (handle === 'e' || handle === 'w') height = width / ratio;
        else width = height * ratio;
        const dirX = handle.includes('w') ? -1 : 1;
        const dirY = handle.includes('n') ? -1 : 1;
        const maxW = dirX < 0 ? anchorX : boundsW - anchorX;
        const maxH = dirY < 0 ? anchorY : boundsH - anchorY;
        width = Math.min(width, maxW);
        height = Math.min(height, maxH);
        if (width / height > ratio) width = height * ratio;
        else height = width / ratio;
        return {x: dirX < 0 ? anchorX - width : anchorX, y: dirY < 0 ? anchorY - height : anchorY, w: width, h: height};
    }

    function maskFromCanvas(source) {
        const mask = document.createElement('canvas');
        mask.width = source.width;
        mask.height = source.height;
        const sourceData = source.getContext('2d').getImageData(0, 0, source.width, source.height);
        const context = mask.getContext('2d');
        const output = context.createImageData(mask.width, mask.height);
        for (let i = 0; i < sourceData.data.length; i += 4) {
            const value = sourceData.data[i + 3] > 8 ? 255 : 0;
            output.data[i] = value;
            output.data[i + 1] = value;
            output.data[i + 2] = value;
            output.data[i + 3] = 255;
        }
        context.putImageData(output, 0, 0);
        return mask;
    }

    function clampOutpaintState(state, boundsW, boundsH) {
        if (!state) return state;
        const width = Number(boundsW) || 0;
        const height = Number(boundsH) || 0;
        state.w = Math.max(width, Number(state.w) || 0);
        state.h = Math.max(height, Number(state.h) || 0);
        state.x = Math.min(state.w - width, Math.max(0, Number(state.x) || 0));
        state.y = Math.min(state.h - height, Math.max(0, Number(state.y) || 0));
        return state;
    }

    function canvasHasPixels(canvas, includeText = false) {
        if (includeText === true) return true;
        const data = canvas?.getContext?.('2d')?.getImageData?.(0, 0, canvas.width, canvas.height)?.data || [];
        for (let i = 3; i < data.length; i += 4) if (data[i] > 0) return true;
        return false;
    }

    function resetOutpaintState(state, boundsW, boundsH) {
        if (!state) return state;
        const width = Number(boundsW) || 0;
        const height = Number(boundsH) || 0;
        state.x = 0;
        state.y = 0;
        state.w = width;
        state.h = height;
        return state;
    }

    function outpaintNaturalSize(cropState, naturalWidth, naturalHeight, clientWidth, clientHeight) {
        const scaleX = Math.max(1, Number(naturalWidth) || 1) / Math.max(1, Number(clientWidth) || 1);
        const scaleY = Math.max(1, Number(naturalHeight) || 1) / Math.max(1, Number(clientHeight) || 1);
        return {
            w: Math.max(1, Math.round((Number(cropState?.w) || 1) * scaleX)),
            h: Math.max(1, Math.round((Number(cropState?.h) || 1) * scaleY)),
        };
    }

    function cropRectFromDisplay(state, naturalWidth, naturalHeight, clientWidth, clientHeight) {
        const scaleX = (Number(naturalWidth) || 1) / (Number(clientWidth) || 1);
        const scaleY = (Number(naturalHeight) || 1) / (Number(clientHeight) || 1);
        return {
            x: Math.max(0, Math.round((Number(state?.x) || 0) * scaleX)),
            y: Math.max(0, Math.round((Number(state?.y) || 0) * scaleY)),
            w: Math.max(1, Math.round((Number(state?.w) || 1) * scaleX)),
            h: Math.max(1, Math.round((Number(state?.h) || 1) * scaleY)),
        };
    }

    function outpaintRectFromDisplay(state, naturalWidth, naturalHeight, clientWidth, clientHeight) {
        const rect = cropRectFromDisplay(state, naturalWidth, naturalHeight, clientWidth, clientHeight);
        return {
            x: rect.x,
            y: rect.y,
            w: Math.max(Number(naturalWidth) || 1, rect.w),
            h: Math.max(Number(naturalHeight) || 1, rect.h),
        };
    }

    async function resizedImageBlob(image, dimensions, documentRef = global.document) {
        if (!image?.naturalWidth || !image?.naturalHeight || !dimensions?.targetW || !dimensions?.targetH) return null;
        const canvas = documentRef.createElement('canvas');
        canvas.width = dimensions.targetW;
        canvas.height = dimensions.targetH;
        const context = canvas.getContext('2d');
        context.imageSmoothingEnabled = true;
        context.imageSmoothingQuality = 'high';
        context.drawImage(image, 0, 0, image.naturalWidth, image.naturalHeight, 0, 0, dimensions.targetW, dimensions.targetH);
        const blob = await toPngBlob(canvas);
        return blob ? {blob, ...dimensions} : null;
    }

    function composeBrushCanvas(image, drawLayer, textLayer, documentRef = global.document) {
        if (!image?.naturalWidth || !image?.naturalHeight) return null;
        const canvas = documentRef.createElement('canvas');
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        const context = canvas.getContext('2d');
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
        if (drawLayer) context.drawImage(drawLayer, 0, 0);
        if (textLayer) context.drawImage(textLayer, 0, 0);
        return canvas;
    }

    async function cropImageBlob(image, rect, documentRef = global.document) {
        if (!image?.naturalWidth || !image?.naturalHeight || !rect?.w || !rect?.h) return null;
        const canvas = documentRef.createElement('canvas');
        canvas.width = rect.w;
        canvas.height = rect.h;
        canvas.getContext('2d').drawImage(image, rect.x, rect.y, rect.w, rect.h, 0, 0, rect.w, rect.h);
        return toPngBlob(canvas);
    }

    async function outpaintImageBlob(image, rect, documentRef = global.document) {
        if (!image?.naturalWidth || !image?.naturalHeight || !rect?.w || !rect?.h) return null;
        const width = Math.max(image.naturalWidth, rect.w);
        const height = Math.max(image.naturalHeight, rect.h);
        const canvas = documentRef.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, width, height);
        context.drawImage(image, rect.x, rect.y, image.naturalWidth, image.naturalHeight);
        return toPngBlob(canvas);
    }

    async function splitImageBlobs(image, rects, documentRef = global.document) {
        if (!image?.naturalWidth || !image?.naturalHeight || !Array.isArray(rects)) return [];
        const results = [];
        for (const rect of rects) {
            if (!rect?.w || !rect?.h) continue;
            const canvas = documentRef.createElement('canvas');
            canvas.width = rect.w;
            canvas.height = rect.h;
            canvas.getContext('2d').drawImage(image, rect.x, rect.y, rect.w, rect.h, 0, 0, rect.w, rect.h);
            const blob = await toPngBlob(canvas);
            if (blob) results.push({blob, row:rect.row, col:rect.col, w:rect.w, h:rect.h});
        }
        return results;
    }

    function toPngBlob(canvas) {
        if (!canvas?.toBlob) return Promise.resolve(null);
        return new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    }

    global.WorkbenchCanvasMediaTools = Object.freeze({
        clampResizeScale,
        circledNumber,
        canvasPoint,
        gridSplitRects,
        gridSplitRectsCustom,
        customLineHit,
        setCustomLinePosition,
        normalizeGridSettings,
        brushStyle,
        labelStyle,
        resizeOutpaintRect,
        resizeFreeCropRect,
        resizeAspectCropRect,
        customGridRects,
        initialCropRect,
        clampCropRect,
        scaleCropRect,
        cropBoxProjection,
        resizeControlProjection,
        editorZoomProjection,
        editorOverflowProjection,
        editorCanvasProjection,
        brushControlProjection,
        previewTransformProjection,
        compareSliderProjection,
        previewZoomProjection,
        previewPanProjection,
        minimaxPaneProjection,
        minimaxPlayheadProjection,
        minimaxAspectValue,
        minimaxNormalizeRef,
        minimaxUniqueRefs,
        minimaxRefSummary,
        minimaxCompactSegments,
        minimaxActiveSegment,
        minimaxSegmentRefs,
        minimaxSegmentRefsByKind,
        minimaxSegmentResult,
        minimaxPrependUnique,
        minimaxSourceProjection,
        minimaxSegmentTiming,
        minimaxSegmentVisuals,
        minimaxReferenceMigration,
        minimaxOutputProjection,
        minimaxNodeConfig,
        minimaxSegmentList,
        minimaxSelectionProjection,
        minimaxDownloadProjection,
        minimaxTimelineInteraction,
        cropHandleFromPoint,
        pointerDelta,
        createCropDrag,
        parseCropRatio,
        fitCropRectToAspect,
        resizeDimensions,
        gridLayout,
        outputPoint,
        extensionFromNameOrUrl,
        safeDownloadFileName,
        baseNameWithoutExtension,
        outputFileName,
        downloadNameForGroupImage,
        imageOutputUrls,
        mediaRefsFromNode,
        latestOutputReference,
        generatedMediaSources,
        imageMediaSource,
        groupMediaSources,
        promptMediaSource,
        promptGroupMediaSource,
        llmMediaSource,
        loopFallbackSource,
        loopImageMediaSources,
        orderedInputSources,
        reorderInputIds,
        imageInputSources,
        promptInputSources,
        inputViewProjection,
        refSourceIds,
        connectedInputNodes,
        generatedMediaRefs,
        groupImageItems,
        downloadableImageUrls,
        outputResolutionParts,
        outputResolutionMarkup,
        compareModeStyles,
        rerunOutputProjection,
        outputImageNodeProjection,
        outputNodeProjection,
        findOutputNodeForSource,
        latestGeneratedOutputItem,
        outputHasUrl,
        outputNodesForSource,
        outputItemsWithUrl,
        outputDownloadProjection,
        uniqueOutputItems,
        generatedImageNodeProjection,
        inputGroupProjection,
        downstreamTargetIds,
        archiveDownloadFilename,
        archiveDownloadPayload,
        downloadHref,
        generatorSourceProjection,
        outputPromptProjection,
        outputRerunAvailable,
        outputDownloadName,
        formatRunDuration,
        outputUrlValue,
        outputDomKeyForItem,
        outputDomKeyForPending,
        outputMetaFor,
        outputImageName,
        outputGridLayout,
        outputGridPlacement,
        outputPresentation,
        appendOutputRecords,
        appendUniqueOutputRecords,
        markOutputViewed,
        outputCompareUrl,
        collectLightboxItems,
        nextLightboxItem,
        clampListIndex,
        lightboxVisibility,
        lightboxProjection,
        aspectCropToBounds,
        maskFromCanvas,
        clampOutpaintState,
        canvasHasPixels,
        resetOutpaintState,
        outpaintNaturalSize,
        cropRectFromDisplay,
        outpaintRectFromDisplay,
        resizedImageBlob,
        composeBrushCanvas,
        cropImageBlob,
        outpaintImageBlob,
        splitImageBlobs,
        toPngBlob,
    });
}(window));
