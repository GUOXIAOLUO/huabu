// Canonical Project API client. Page code owns rendering and interaction only.
(function(global){
    'use strict';

    const BASE = '/api/v1/projects';

    async function request(path = '', options = {}){
        const response = await fetch(`${BASE}${path}`, {
            ...options,
            headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        });
        let body = null;
        try { body = await response.json(); } catch(e) {}
        if(!response.ok){
            const detail = body?.detail;
            const message = typeof detail === 'string' ? detail : (detail?.message || `Project API request failed (${response.status})`);
            const error = new Error(message);
            error.status = response.status;
            error.code = detail?.code || 'project_api_error';
            throw error;
        }
        return body;
    }

    const client = Object.freeze({
        list: async () => request(''),
        create: async name => request('', { method: 'POST', body: JSON.stringify({ name }) }),
        update: async (projectId, payload) => request(`/${encodeURIComponent(projectId)}`, { method: 'PUT', body: JSON.stringify(payload) }),
        archive: async projectId => request(`/${encodeURIComponent(projectId)}`, { method: 'DELETE' }),
    });

    global.WorkbenchProjectApiClient = client;
})(window);
