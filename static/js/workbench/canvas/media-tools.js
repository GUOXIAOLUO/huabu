/* Mountable Smart media-tool geometry. Owns the pure, stateless math shared by
   the retained Smart crop / draw / grid tools: resize-scale clamping, circled
   label numbering, pointer-to-canvas point mapping, grid split/join rectangle
   computation, and crop aspect-ratio parsing/fitting.

   This is the seam for card R4-29: smart-canvas.js keeps the editor modal,
   the canvas 2D rendering, the mode/state machine and the node mutation, but
   the product-neutral geometry below is no longer Smart-owned. The page reads
   its own DOM/state and passes plain values in — the module never touches the
   DOM, `window`, or any Smart adapter detail. */
(function exposeWorkbenchCanvasMediaTools(global) {
    'use strict';

    /* Clamp an image-resize scale to [0.05, 1]; non-finite input defaults to
       0.5. Mirrors the former `clampImageResizeScale` in smart-canvas.js. */
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

    global.WorkbenchCanvasMediaTools = Object.freeze({
        clampResizeScale,
        circledNumber,
        canvasPoint,
        gridSplitRects,
        gridSplitRectsCustom,
        parseCropRatio,
        fitCropRectToAspect,
    });
}(window));
