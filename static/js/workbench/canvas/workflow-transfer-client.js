/* Transport-only workflow archive boundary shared by temporary Canvas adapters. */
(function exposeWorkflowTransferClient(global) {
    'use strict';

    function httpError() {
        const formatter = global.WorkbenchCanvasHttpError;
        if (!formatter) throw new Error('Canvas HTTP error module is unavailable');
        return formatter;
    }

    function errorMessage(payload, fallback) { return httpError().message(payload, fallback); }
    function responseError(response, fallback) { return httpError().responseMessage(response, fallback); }

    async function exportArchive(payload, filename) {
        const response = await fetch('/api/canvas-workflows/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({...payload, include_resources: true, filename}),
        });
        if (!response.ok) throw new Error(await responseError(response, '导出工作流失败'));
        return response.blob();
    }

    async function importArchive(file) {
        const form = new FormData();
        form.append('file', file);
        const response = await fetch('/api/canvas-workflows/import', {method: 'POST', body: form});
        if (!response.ok) throw new Error(await responseError(response, '导入工作流失败'));
        return response.json();
    }

    function normalizeImported(data) {
        const records = (nodes, connections) => ({nodes:(Array.isArray(nodes) ? nodes : []).filter(Boolean), connections:(Array.isArray(connections) ? connections : []).filter(Boolean)});
        if (Array.isArray(data)) return records(data, []);
        if (Array.isArray(data?.nodes)) {
            return records(data.nodes, data.connections);
        }
        if (Array.isArray(data?.workflow?.nodes)) {
            return records(data.workflow.nodes, data.workflow.connections);
        }
        return records([], []);
    }
    function exportPayload(subgraph, exportedAt = Date.now()) {
        return {
            format: 'infinite-canvas-workflow', version: 1, exported_at: exportedAt,
            nodes: (Array.isArray(subgraph?.nodes) ? subgraph.nodes : []).filter(Boolean),
            connections: (Array.isArray(subgraph?.connections) ? subgraph.connections : []).filter(Boolean),
        };
    }

    function jsonExportBlob(payload) {
        return new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'});
    }

    function filenameForExport(title, extension, timestamp) {
        const safeTitle = String(title || 'canvas-workflow').replace(/[\\/:*?"<>|]+/g, '_').slice(0, 48) || 'canvas-workflow';
        const stamp = new Date(timestamp == null ? Date.now() : timestamp).toISOString().replace(/[-:]/g, '').slice(0, 15);
        return `${safeTitle}-${stamp}.${String(extension || 'json').replace(/^\./, '')}`;
    }
    function exportProjection(subgraph, title, extension, timestamp) {
        return {payload:exportPayload(subgraph, timestamp), filename:filenameForExport(title, extension, timestamp)};
    }

    function downloadBlob(blob, filename, options = {}) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || options.fallbackFilename || '';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), Number(options.revokeAfterMs) || 0);
    }

    global.WorkbenchCanvasWorkflowTransfer = Object.freeze({
        exportArchive,
        importArchive,
        normalizeImported,
        exportPayload,
        jsonExportBlob,
        filenameForExport,
        exportProjection,
        downloadBlob,
        errorMessage,
    });
}(window));
