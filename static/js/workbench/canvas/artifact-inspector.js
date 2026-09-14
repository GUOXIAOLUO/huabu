/* Canonical Artifact Inspector.  This module is presentation and transport
 * only: ArtifactService owns identity/version truth, while the page owns DOM
 * events and navigation.  It never creates or mutates Canvas nodes. */
(function exposeWorkbenchArtifactInspector(global) {
    'use strict';
    const BASE_PATH = '/api/v1/artifacts';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }
    function objectOrEmpty(value) {
        return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    }
    function servable(location) {
        const value = text(location);
        return value.startsWith('/') && !value.startsWith('//') || /^https?:\/\//i.test(value);
    }
    function shortTime(value) {
        const raw = text(value);
        return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(raw) ? raw.slice(0, 16).replace('T', ' ') : raw;
    }
    function activeVersion(history, id) {
        const versions = Array.isArray(history?.versions) ? history.versions : [];
        return versions.find(item => item.id === text(id)) || versions.find(item => item.id === text(history?.current_version_id)) || null;
    }
    function createClient(options) {
        const settings = options || {};
        const fetchImpl = settings.fetch || global.fetch;
        const actorId = text(settings.actorId);
        if (typeof fetchImpl !== 'function') throw new TypeError('ArtifactInspectorClient requires fetch');
        if (!actorId) throw new TypeError('ArtifactInspectorClient requires an actor id');
        const basePath = text(settings.basePath, BASE_PATH);
        async function request(url) {
            const response = await fetchImpl(url, {headers: {'X-User-ID': actorId}});
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(payload?.detail || `读取产物失败（${response.status}）`);
            return payload;
        }
        return Object.freeze({
            list: projectId => request(`${basePath}?project_id=${encodeURIComponent(text(projectId))}`),
            history: async artifactId => {
                const id = text(artifactId);
                if (!id) throw new TypeError('ArtifactInspectorClient.history requires an artifact id');
                const [artifact, versions] = await Promise.all([
                    request(`${basePath}/${encodeURIComponent(id)}`),
                    request(`${basePath}/${encodeURIComponent(id)}/versions`),
                ]);
                const versionList = Array.isArray(versions) ? versions : [];
                return {artifact, current_version_id: artifact.version_ids?.at(-1) || versionList.at(-1)?.id || null, versions: versionList};
            },
        });
    }
    function createInspector(options) {
        const settings = options || {};
        const escapeHtml = settings.escapeHtml;
        const escapeAttr = settings.escapeAttr || escapeHtml;
        if (typeof escapeHtml !== 'function') throw new TypeError('ArtifactInspector requires escapeHtml');
        function row(version, history, selected, compare) {
            const lineage = objectOrEmpty(version.lineage);
            const current = version.id === text(history?.current_version_id);
            const marked = version.id === text(selected);
            const compareMarked = version.id === text(compare);
            const content = objectOrEmpty(version.content_ref);
            return `<li class="artifact-inspector-version ${marked ? 'active' : ''}">`
                + `<button type="button" class="artifact-inspector-version-btn" data-artifact-version="${escapeAttr(version.id)}" aria-pressed="${marked}">`
                + `<strong>v${escapeHtml(version.ordinal)}</strong>${current ? '<span class="artifact-inspector-current">当前</span>' : ''}`
                + `<span>${escapeHtml(shortTime(version.created_at))}</span>`
                + `<small>${escapeHtml(content.mime_type || '')} · ${escapeHtml(content.checksum || '')}</small></button>`
                + `<button type="button" class="artifact-inspector-compare ${compareMarked ? 'active' : ''}" data-artifact-compare="${escapeAttr(version.id)}">${compareMarked ? '已选择' : '比较'}</button>`
                + `<span class="artifact-inspector-lineage">run ${escapeHtml(lineage.run_id || '')} · attempt ${escapeHtml(lineage.attempt_id || '')}</span></li>`;
        }
        function lineage(version) {
            if (!version) return '<p class="artifact-inspector-note">没有可追溯版本。</p>';
            const ref = objectOrEmpty(version.content_ref);
            const source = objectOrEmpty(version.lineage);
            const rows = [['run', source.run_id], ['attempt', source.attempt_id], ['inputs', (source.input_refs || []).join(', ')], ['prompt', source.prompt_version_ref], ['model', source.model_ref], ['skill', source.skill_version_ref], ['位置', ref.location]];
            return '<dl class="artifact-inspector-meta">' + rows.filter(([, value]) => text(value)).map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('') + '</dl>';
        }
        function compare(history, first, second) {
            const versions = Array.isArray(history?.versions) ? history.versions : [];
            const a = versions.find(item => item.id === first);
            const b = versions.find(item => item.id === second);
            if (!a || !b || a.id === b.id) return '';
            return `<div class="artifact-inspector-compare-panel"><h4>版本比较</h4><div class="artifact-inspector-compare-grid">${[a, b].map(version => `<div><strong>v${escapeHtml(version.ordinal)}</strong>${lineage(version)}</div>`).join('')}</div></div>`;
        }
        function render(artifact, history, state) {
            if (!artifact) return '<section class="artifact-inspector empty"><p class="artifact-inspector-note">未选择产物</p></section>';
            const status = state || {};
            const version = activeVersion(history, status.selectedVersionId);
            const versions = Array.isArray(history?.versions) ? history.versions.slice().sort((a, b) => Number(b.ordinal || 0) - Number(a.ordinal || 0)) : [];
            const name = text(artifact.title, artifact.id);
            const location = text(version?.content_ref?.location);
            const openable = servable(location);
            const selected = text(status.selectedVersionId, version?.id);
            return `<section class="artifact-inspector" aria-label="产物详情"><header><div><strong>${escapeHtml(name)}</strong><span>${escapeHtml(artifact.id)}</span></div><span class="artifact-inspector-badge">${escapeHtml(artifact.state || 'draft')}</span></header>`
                + (status.loading ? '<p class="artifact-inspector-note">正在读取版本历史…</p>' : '')
                + (status.error ? `<p class="artifact-inspector-note danger">${escapeHtml(status.error)}</p>` : '')
                + `<div class="artifact-inspector-current-preview"><strong>${version ? `当前查看 v${escapeHtml(version.ordinal)}` : '暂无版本'}</strong><span>${escapeHtml(version?.content_ref?.mime_type || '尚无内容')}</span></div>`
                + `<section><h4>版本历史（${versions.length}）</h4>${versions.length ? `<ol class="artifact-inspector-versions">${versions.map(item => row(item, history, selected, status.compareVersionId)).join('')}</ol>` : '<p class="artifact-inspector-note">该产物还没有版本。</p>'}</section>`
                + `<section><h4>来源与 lineage</h4>${lineage(version)}</section>`
                + compare(history, text(status.selectedVersionId, version?.id), status.compareVersionId)
                + `<div class="artifact-inspector-actions"><button type="button" data-artifact-open="${escapeAttr(location)}" ${openable ? '' : 'disabled'}>打开</button><button type="button" data-artifact-materialize="${escapeAttr(version?.id || '')}" ${version ? '' : 'disabled'}>物化到画布</button></div></section>`;
        }
        return Object.freeze({render, activeVersion});
    }
    global.WorkbenchArtifactInspector = Object.freeze({BASE_PATH, servable, shortTime, createClient, createInspector});
}(typeof window !== 'undefined' ? window : globalThis));
