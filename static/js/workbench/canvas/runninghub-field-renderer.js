/* Neutral markup renderer for RunningHub parameter fields. */
(function exposeRunningHubFieldRenderer(global) {
    'use strict';
    function render(options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const a = options.escapeAttr || e;
        const label = e(options.label || '');
        const key = a(options.key || '');
        const wide = options.wide ? ' wide' : '';
        if (options.kind === 'boolean') return `<div class="gen-settings-row rh-param-row${wide}"><button type="button" class="setting-check ${options.active ? 'active' : ''}" data-rh-param="${key}" data-rh-type="boolean"><span class="check-dot"></span>${label}</button></div>`;
        if (options.kind === 'slider') return `<div class="gen-settings-row rh-param-row${wide}"><label class="field" style="flex:1"><div class="setting-title" style="display:flex;justify-content:space-between"><span>${label}</span><span class="rh-param-val">${e(options.numericValue)}</span></div><input type="range" class="canvas-range rh-param-input" data-rh-param="${key}" data-rh-type="slider" min="${a(options.min)}" max="${a(options.max)}" step="${a(options.step)}" value="${a(options.numericValue)}"></label></div>`;
        if (options.options?.length) return `<div class="gen-settings-row rh-param-row${wide}"><label class="field"><div class="setting-title">${label}</div><select class="select-lite rh-param-input" data-rh-param="${key}" data-rh-type="select" style="width:100%">${options.options.map(opt => `<option value="${a(opt)}" ${String(options.value) === String(opt) ? 'selected' : ''}>${e(opt)}</option>`).join('')}</select></label></div>`;
        if (options.random) return `<div class="gen-settings-row rh-param-row${wide}"><div class="comfy-random-field"><label class="field"><div class="setting-title">${label}</div><input class="setting-input rh-param-input" type="number" data-rh-param="${key}" data-rh-type="number" value="${a(options.value)}" ${options.randomActive ? 'disabled' : ''}></label><button class="tool-btn comfy-random-btn ${options.randomActive ? 'active' : ''}" type="button" data-rh-random="${key}" title="${options.randomActive ? '随机已开启，点击关闭' : '随机已关闭，点击开启'}"><i data-lucide="dice-5" class="w-4 h-4"></i></button></div></div>`;
        return `<div class="gen-settings-row rh-param-row${wide}"><label class="field"><div class="setting-title">${label}</div><input class="setting-input rh-param-input" type="${options.kind === 'number' ? 'number' : 'text'}" data-rh-param="${key}" data-rh-type="${a(options.kind)}" value="${a(options.value)}"></label></div>`;
    }
    function promptMarkup(options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const a = options.escapeAttr || e;
        return `<label class="field rh-prompt-field"><div class="setting-title">${e(options.label || 'Prompt')}</div><textarea class="setting-input rh-param-input" data-rh-param="${a(options.key || '')}" data-rh-role="prompt">${e(options.value || '')}</textarea></label>`;
    }
    function promptFields(fields = [], options = {}) {
        const roleOf = typeof options.roleOf === 'function' ? options.roleOf : fieldRole;
        const keyOf = typeof options.keyOf === 'function' ? options.keyOf : paramKey;
        const valueOf = typeof options.valueOf === 'function' ? options.valueOf : (() => '');
        return (Array.isArray(fields) ? fields : [])
            .filter(field => roleOf(field) === 'prompt')
            .map(field => Object.freeze({
                field,
                key: keyOf(field?.nodeId, field?.fieldName),
                label: field?.label || field?.fieldName || 'Prompt',
                value: valueOf(field),
            }));
    }
    function settingField(field, key, kind, label, value, options = [], randomEnabled = false, randomActive = false) {
        if (kind === 'boolean') return Object.freeze({kind, key, label, active: String(value).toLowerCase() === 'true'});
        if (kind === 'slider') {
            const min = Number.isFinite(Number(field?.min)) ? Number(field.min) : 0;
            const max = Number.isFinite(Number(field?.max)) && Number(field.max) > min ? Number(field.max) : 1;
            const step = Number.isFinite(Number(field?.step)) && Number(field.step) > 0 ? Number(field.step) : 0.01;
            const numericValue = Number.isFinite(Number(value)) ? Number(value) : min;
            return Object.freeze({kind, key, label, numericValue, min, max, step});
        }
        if (Array.isArray(options) && options.length) return Object.freeze({kind, key, label, value, options});
        if (randomEnabled || (kind === 'number' && field?.random_enabled === true)) return Object.freeze({kind, key, label, value, random: true, randomActive});
        return Object.freeze({kind, key, label, value});
    }
    function entryOptions(groups = {}, selected = '', options = {}) {
        const escapeHtml = options.escapeHtml || (value => String(value ?? ''));
        const escapeAttr = options.escapeAttr || escapeHtml;
        const idOf = options.idOf || ((entry) => entry?.id || entry?.value || '');
        const labelOf = options.labelOf || ((entry) => entry?.name || idOf(entry));
        const names = options.names || {model:'模型 API', app:'AI 应用', workflow:'工作流'};
        const order = options.order || ['model', 'app', 'workflow'];
        if (!order.some(kind => Array.isArray(groups[kind]) && groups[kind].length)) return '<option value="">请先在 API 设置里添加 RunningHub 配置</option>';
        return order.map(kind => {
            const entries = Array.isArray(groups[kind]) ? groups[kind] : [];
            if (!entries.length) return '';
            return `<optgroup label="${escapeHtml(names[kind] || kind)}">${entries.map(entry => {
                const id = idOf(entry, kind), key = `${kind}:${id}`;
                return `<option value="${escapeAttr(key)}" ${String(selected || '') === key ? 'selected' : ''}>${escapeHtml(labelOf(entry, kind))}</option>`;
            }).join('')}</optgroup>`;
        }).join('');
    }
    function paymentOptions(selected = 'free', capabilities = {}) {
        const value = selected === 'wallet' ? 'wallet' : 'free';
        return `<option value="free" ${value === 'free' ? 'selected' : ''}>RunningHub币 Key${capabilities.has_key ? '' : '（未配置）'}</option><option value="wallet" ${value === 'wallet' ? 'selected' : ''}>账户余额 Key${capabilities.has_wallet_key ? '' : '（未配置）'}</option>`;
    }
    async function loadWorkflow(workflowId, cache, fetcher) {
        const id = String(workflowId || '').trim();
        if (!id) return null;
        if (cache && cache[id]) return cache[id];
        const response = await fetcher(id);
        if (!response || !response.ok) {
            if (cache) delete cache[id];
            return null;
        }
        const payload = await response.json();
        const workflow = payload?.workflow || null;
        if (cache) cache[id] = workflow;
        return workflow;
    }
    function fieldText(field) {
        return [field?.nodeId, field?.fieldName, field?.label, field?.group, field?.title, field?.description, field?.source].filter(v => v !== undefined && v !== null).map(String).join(' ').toLowerCase();
    }
    function fieldMatches(field, patterns = [], fallbackKeys = [], keyOf) {
        const key = typeof keyOf === 'function' ? keyOf(field?.nodeId, field?.fieldName) : '';
        if ((fallbackKeys || []).includes(key)) return true;
        const text = fieldText(field);
        return (patterns || []).some(pattern => pattern.test(text));
    }
    function fullAspectLabel(ratio, normalize) {
        const clean = typeof normalize === 'function' ? normalize(ratio) : String(ratio || '');
        if (clean === '16:9') return '16:9 (Widescreen)';
        if (clean === '9:16') return '9:16 (Portrait)';
        if (clean === '1:1') return '1:1 (Square)';
        return clean;
    }
    function isFullAspectField(field, defaultValue) {
        return /widescreen|portrait|square|画面比例|比例/.test(fieldText(field)) && String(typeof defaultValue === 'function' ? defaultValue(field) : '').includes('(');
    }
    function valueForField(field, desired, options = {}) {
        const text = fieldText(field);
        const isFullAspect = /widescreen|portrait|square|画面比例|比例/.test(text) && String((options.defaultValue || (() => ''))(field) || '').includes('(');
        if (isFullAspect) return fullAspectLabel(desired, options.normalize);
        const value = String(desired ?? '');
        const values = (options.extractOptions || (() => []))(field) || [];
        if (!values.length) return desired;
        const normalized = value.replace(/\s+/g, '');
        return values.find(option => String(option).replace(/\s+/g, '') === normalized) || values.find(option => String(option).replace(/\s+/g, '').startsWith(normalized)) || value;
    }
    function setParam(params, fields, patterns, fallbackKeys, desired, options = {}) {
        const field = (fields || []).find(item => fieldMatches(item, patterns, fallbackKeys, options.keyOf));
        if (!field) return false;
        params[options.keyOf(field.nodeId, field.fieldName)] = {value:valueForField(field, desired, options)};
        return true;
    }
    function compactJson(value, limit = 1800) {
        try { const text = JSON.stringify(value); return text.length > limit ? `${text.slice(0, limit)}...` : text; }
        catch (error) { return String(value || ''); }
    }
    function detailedError(message, details = {}) {
        const error = new Error(message);
        error.miniMaxDetails = details;
        return error;
    }
    function readableError(error, engine = 'comfyui', fallback = 'Generation failed') {
        const text = String(error?.message || error || fallback).trim();
        const jsonStart = text.indexOf('{');
        if (jsonStart < 0) return text;
        try {
            const payload = JSON.parse(text.slice(jsonStart));
            const parts = [];
            const main = payload?.error;
            if (main?.message) parts.push(String(main.message));
            if (main?.details && !parts.includes(String(main.details))) parts.push(String(main.details));
            Object.entries(payload?.node_errors || {}).slice(0, 3).forEach(([nodeId, nodeError]) => {
                const details = (nodeError?.errors || []).slice(0, 2).map(item => item?.details || item?.message).filter(Boolean);
                if (details.length) parts.push(`节点 ${nodeId}${nodeError?.class_type ? `（${nodeError.class_type}）` : ''}：${details.join('；')}`);
            });
            const prefix = engine === 'runninghub' ? 'RunningHub 工作流执行失败' : 'ComfyUI 拒绝了工作流';
            return parts.length ? `${prefix}：${parts.join('；')}` : text;
        } catch (parseError) { return text; }
    }
    function payloadError(stage, data, fallback, extra = {}) {
        const detailObj = data?.detail && typeof data.detail === 'object' ? data.detail : null;
        const rawDetail = detailObj?.message || data?.detail || data?.error || data?.message || data?.failReason || data?.msg || fallback || 'RunningHub 失败';
        const detail = typeof rawDetail === 'object' ? compactJson(rawDetail, 1200) : String(rawDetail || '');
        const raw = detailObj?.raw || data?.raw || data?.data?.raw || data;
        const code = detailObj?.code ?? data?.code ?? data?.data?.code ?? raw?.code ?? '';
        const taskId = detailObj?.taskId || detailObj?.task_id || data?.taskId || data?.task_id || data?.data?.taskId || extra.taskId || '';
        const parts = [`RunningHub ${stage}失败`, detail].filter(Boolean);
        if (taskId) parts.push(`taskId=${taskId}`);
        if (code !== '') parts.push(`code=${code}`);
        return detailedError(parts.join('：'), {stage, taskId, code, raw, ...(detailObj || {}), ...extra});
    }
    function logErrorText(error, engine = 'comfyui', fallback = 'Generation failed') {
        const base = readableError(error, engine, fallback);
        const details = error?.miniMaxDetails || {};
        const lines = [base];
        if (details.taskId && !base.includes(details.taskId)) lines.push(`taskId: ${details.taskId}`);
        if (details.code !== undefined && details.code !== null && details.code !== '') lines.push(`code: ${details.code}`);
        if (details.stage) lines.push(`stage: ${details.stage}`);
        if (details.workflowId) lines.push(`workflowId: ${details.workflowId}`);
        if (details.nodeInfoList) lines.push(`nodeInfoList: ${compactJson(details.nodeInfoList, 1800)}`);
        if (details.raw) lines.push(`raw: ${compactJson(details.raw, 4200)}`);
        return lines.filter(Boolean).join('\n');
    }
    function selectEntry(workflows = [], currentId = '', title = '', defaultId = '', idOf) {
        const values = Array.isArray(workflows) ? workflows : [];
        const normalize = value => String(value || '').toLowerCase().replace(/\s+/g, '');
        const keyOf = typeof idOf === 'function' ? idOf : item => item?.id || item?.workflowId || '';
        const titleKey = normalize(title);
        return values.find(item => normalize(item?.title || item?.name) === titleKey)
            || values.find(item => keyOf(item) === String(currentId || ''))
            || values.find(item => keyOf(item) === String(defaultId || ''))
            || null;
    }
    function applyPresetParams(params, fields, specs = [], options = {}) {
        const target = params || {};
        (specs || []).forEach(spec => setParam(target, fields, spec.patterns, spec.fallbackKeys, spec.value, options));
        return target;
    }
    function fieldValue(field, param, media = {}, index = 0, options = {}) {
        const kind = typeof options.kindOf === 'function' ? options.kindOf(field) : field?.kind;
        const role = typeof options.roleOf === 'function' ? options.roleOf(field) : field?.role;
        const defaultValue = typeof options.defaultValue === 'function' ? options.defaultValue(field) : field?.defaultValue;
        const mediaKinds = ['image', 'video', 'audio'];
        if (field?.sourceFromUpstream === false && !mediaKinds.includes(kind) && !param) return Object.freeze({skip:true, value:''});
        if (mediaKinds.includes(kind)) {
            if (field?.sourceFromUpstream === false) return Object.freeze({value:param?.value ?? defaultValue, upload:false});
            return Object.freeze({value:media[kind]?.[index]?.url || param?.value || defaultValue, upload:true});
        }
        const value = role === 'prompt' ? (param?.value ?? (media.prompt || defaultValue)) : (param?.value ?? defaultValue);
        return Object.freeze({value:['number','slider'].includes(kind) && String(value ?? '').trim() !== '' && !Number.isNaN(Number(value)) ? Number(value) : value, upload:false});
    }
    function mediaInputState(fields = [], media = {}, options = {}) {
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : field => field?.kind;
        const keyOf = typeof options.keyOf === 'function' ? options.keyOf : (nodeId, fieldName) => `${nodeId}::${fieldName}`;
        const indexes = options.indexes || {};
        const requiredOf = typeof options.requiredOf === 'function' ? options.requiredOf : field => field?.required === true;
        const missingRequired = [];
        const missingOptional = [];
        (fields || []).forEach(field => {
            const kind = kindOf(field);
            if (!['image','video','audio'].includes(kind)) return;
            const key = keyOf(field?.nodeId, field?.fieldName);
            const index = indexes[key] || 0;
            const hasInput = Boolean(media?.[kind]?.[index]?.url);
            if (hasInput) return;
            (requiredOf(field) ? missingRequired : missingOptional).push(field);
        });
        return Object.freeze({missingRequired, missingOptional});
    }
    function mediaIndexes(fields = [], options = {}) {
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : field => field?.kind;
        const keyOf = typeof options.keyOf === 'function' ? options.keyOf : (nodeId, fieldName) => `${nodeId}::${fieldName}`;
        const counters = {image:0, video:0, audio:0};
        const map = {};
        const ordered = [...fields].sort((a, b) => {
            const ak = kindOf(a), bk = kindOf(b);
            if (ak === 'image' && bk === 'image') return (Number(a?.imageOrder) || 9999) - (Number(b?.imageOrder) || 9999);
            return 0;
        });
        ordered.forEach(field => {
            const kind = kindOf(field);
            if (Object.prototype.hasOwnProperty.call(counters, kind)) map[keyOf(field?.nodeId, field?.fieldName)] = counters[kind]++;
        });
        return Object.freeze(map);
    }
    function pruneWorkflowForMissingFields(workflowJson, missingFields = [], options = {}) {
        if (!workflowJson || typeof workflowJson !== 'object' || !missingFields.length) return null;
        const workflow = JSON.parse(JSON.stringify(workflowJson));
        const removeIds = new Set();
        const nodeInfoListOf = typeof options.nodeInfoListOf === 'function' ? options.nodeInfoListOf : value => Object.keys(value?.inputs || {});
        const linkOf = typeof options.linkOf === 'function' ? options.linkOf : value => Array.isArray(value) && value.length === 2;
        missingFields.forEach(field => {
            const node = workflow[String(field?.nodeId)];
            if (node?.inputs && Object.prototype.hasOwnProperty.call(node.inputs, field.fieldName)) delete node.inputs[field.fieldName];
            if (node && nodeInfoListOf({[field.nodeId]: node}).length <= 0) removeIds.add(String(field.nodeId));
        });
        removeIds.forEach(id => delete workflow[id]);
        Object.values(workflow).forEach(node => {
            if (!node?.inputs || typeof node.inputs !== 'object') return;
            Object.entries(node.inputs).forEach(([name, value]) => {
                if (linkOf(value) && removeIds.has(String(value[0]))) delete node.inputs[name];
            });
        });
        return workflow;
    }
    function fieldLabel(field) {
        return field?.label || field?.fieldName || `#${field?.nodeId || ''}`;
    }
    function isWorkflowLinkValue(value) {
        return Array.isArray(value) && value.length === 2 && typeof value[0] === 'string' && Number.isInteger(value[1]);
    }
    function usableFields(fields = []) {
        const list = Array.isArray(fields) ? fields : [];
        if (!list.length) return [];
        const enabled = list.filter(field => field?.enabled === true);
        return enabled.length ? enabled : list;
    }
    function sortFields(fields = [], options = {}) {
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : field => field?.kind;
        return [...fields].sort((a, b) => {
            const ak = kindOf(a), bk = kindOf(b);
            if (ak === 'image' && bk === 'image') {
                const ao = Number(a?.imageOrder) || 9999, bo = Number(b?.imageOrder) || 9999;
                if (ao !== bo) return ao - bo;
            }
            if (ak === 'image' && bk !== 'image') return -1;
            if (ak !== 'image' && bk === 'image') return 1;
            return String(a?.nodeId || '').localeCompare(String(b?.nodeId || ''), undefined, {numeric:true})
                || String(a?.fieldName || '').localeCompare(String(b?.fieldName || ''));
        });
    }
    function paramKey(nodeId, fieldName) {
        return `${nodeId ?? ''}::${fieldName ?? ''}`;
    }
    function fieldKind(field) {
        const type = String(field?.fieldType || '').trim().toUpperCase();
        if (type === 'IMAGE') return 'image';
        if (type === 'VIDEO') return 'video';
        if (type === 'AUDIO') return 'audio';
        if (type === 'SLIDER') return 'slider';
        if (['NUMBER','FLOAT','INTEGER','INT'].includes(type)) return 'number';
        if (['BOOLEAN','BOOL'].includes(type)) return 'boolean';
        const key = `${field?.fieldName || ''} ${field?.fieldValue || ''}`.toLowerCase();
        if (/\b(image|img|mask|photo|picture)\b/.test(key) || /\.(png|jpe?g|webp|gif|bmp)(\?|$)/i.test(key)) return 'image';
        if (/\b(video|movie|mp4)\b/.test(key) || /\.(mp4|webm|mov|m4v|mkv)(\?|$)/i.test(key)) return 'video';
        if (/\b(audio|sound|music|voice)\b/.test(key) || /\.(mp3|wav|ogg|m4a|flac|aac)(\?|$)/i.test(key)) return 'audio';
        return 'text';
    }
    function fieldRole(field) {
        const kind = fieldKind(field);
        if (['image','video','audio','number','slider','boolean'].includes(kind)) return kind;
        const text = `${field?.fieldName || ''} ${field?.label || ''} ${field?.group || ''}`.toLowerCase();
        return /prompt|positive|negative|text|caption|description|关键词|提示词|正向|负向/.test(text) ? 'prompt' : 'text';
    }
    function defaultValue(field) {
        let value = field?.fieldValue;
        if (Array.isArray(value)) value = value[0];
        return value === undefined || value === null || typeof value === 'object' ? '' : String(value);
    }
    function extractOptions(field, knownOptions = {}) {
        const candidates = [field?.fieldData, field?.options, field?.list, field?.values, field?.enum, field?.choices, field?.items, field?.selectOptions, field?.dropdown];
        for (const candidate of candidates) {
            if (!Array.isArray(candidate) || !candidate.length) continue;
            if (candidate.every(value => ['string','number'].includes(typeof value))) return candidate.map(String);
            if (candidate.every(value => value && typeof value === 'object' && ('value' in value || 'label' in value || 'name' in value))) return candidate.map(value => value.value ?? value.label ?? value.name).filter(value => value !== undefined && value !== null).map(String);
        }
        const fieldType = String(field?.fieldType || '').toUpperCase();
        if (['LIST','SELECT','DROPDOWN','COMBO','ENUM'].includes(fieldType) && Array.isArray(field?.fieldValue)) return field.fieldValue.filter(value => ['string','number'].includes(typeof value)).map(String);
        const name = String(field?.fieldName || '').trim();
        if (!name) return null;
        if (Array.isArray(knownOptions[name])) return knownOptions[name].map(String);
        const hit = Object.keys(knownOptions).find(key => key.toLowerCase() === name.toLowerCase());
        return hit ? knownOptions[hit].map(String) : null;
    }
    function randomEnabled(field, options = {}) {
        const kind = typeof options.kindOf === 'function' ? options.kindOf(field) : fieldKind(field);
        return kind === 'number' && field?.random_enabled === true;
    }
    function randomActive(state, key) {
        return state?.[key] !== false;
    }
    function toggleRandomActive(state, key) {
        const next = {...(state || {})};
        next[key] = next[key] === false;
        return Object.freeze(next);
    }
    function sourceSummary(sources = [], options = {}) {
        const kindOf = typeof options.kindOf === 'function' ? options.kindOf : () => '';
        const refs = sources.flatMap(source => source?.refs || []).filter(ref => ref?.url);
        const byKind = kind => refs.filter(ref => kindOf(ref) === kind);
        const image = byKind('image');
        const imageLimit = Number(options.imageLimit);
        return Object.freeze({refs, image:imageLimit > 0 ? image.slice(0, imageLimit) : image, video:byKind('video'), audio:byKind('audio'), prompt:sources.map(source => source?.prompt).filter(Boolean).join('\n\n')});
    }
    function sourceProjection(sources, options = {}) {
        const list = typeof options.order === 'function' ? options.order(sources || []) : (sources || []);
        return {sources:list, ...sourceSummary(list, options)};
    }
    function inferWorkflowFieldType(fieldName, fieldValue) {
        const key = `${fieldName || ''} ${fieldValue || ''}`.toLowerCase();
        if (/\b(image|img|mask|photo|picture)\b/.test(key) || /\.(png|jpe?g|webp|gif|bmp)(\?|$)/i.test(key)) return 'IMAGE';
        if (/\b(video|movie|mp4)\b/.test(key) || /\.(mp4|webm|mov|m4v|mkv)(\?|$)/i.test(key)) return 'VIDEO';
        if (/\b(audio|sound|music|voice)\b/.test(key) || /\.(mp3|wav|ogg|m4a|flac|aac)(\?|$)/i.test(key)) return 'AUDIO';
        if (/^(true|false)$/i.test(String(fieldValue || ''))) return 'BOOLEAN';
        if (String(fieldValue || '').trim() !== '' && !Number.isNaN(Number(fieldValue))) return 'NUMBER';
        return 'TEXT';
    }
    function workflowNodeInfoList(data, options = {}) {
        const list = [];
        const linkOf = typeof options.linkOf === 'function' ? options.linkOf : isWorkflowLinkValue;
        if (!data || typeof data !== 'object' || Array.isArray(data)) return list;
        Object.entries(data).forEach(([nodeId, nodeContent]) => {
            const inputs = nodeContent?.inputs || {};
            if (!inputs || typeof inputs !== 'object') return;
            Object.entries(inputs).forEach(([fieldName, rawValue]) => {
                if (linkOf(rawValue)) return;
                let fieldValue = rawValue;
                if (fieldValue !== null && typeof fieldValue === 'object') fieldValue = JSON.stringify(fieldValue);
                else if (fieldValue === undefined || fieldValue === null) fieldValue = '';
                else fieldValue = String(fieldValue);
                list.push({nodeId:String(nodeId), fieldName:String(fieldName), fieldValue, fieldType:inferWorkflowFieldType(fieldName, fieldValue), source:'workflow'});
            });
        });
        return list;
    }
    function entryId(entry, kind) {
        if (kind === 'model') return String(typeof entry === 'string' ? entry : (entry?.model || entry?.id || entry?.name || '')).trim();
        return String(kind === 'workflow' ? (entry?.workflowId || entry?.id || '') : (entry?.appId || entry?.id || '')).trim();
    }
    function entryLabel(entry, kind) {
        const id = entryId(entry, kind);
        if (kind === 'model') return entry?.title || entry?.name || id;
        return entry?.title || entry?.name || (kind === 'workflow' ? `工作流 ${id.slice(-6)}` : `AI 应用 ${id.slice(-6)}`);
    }
    function entryKey(kind, id) { return `${kind}:${String(id || '').trim()}`; }
    function parseEntryKey(value) {
        const match = String(value || '').trim().match(/^(app|workflow|model):(.+)$/);
        return match ? {kind:match[1], id:match[2]} : null;
    }
    function allEntries(entries = {}, options = {}) {
        const idOf = typeof options.idOf === 'function' ? options.idOf : entryId;
        return ['model','app','workflow'].flatMap(kind => (entries[kind] || []).map(entry => ({kind, id:idOf(entry, kind), entry}))).filter(item => item.id);
    }
    function resolveEntryRef(node = {}, entries = []) {
        const parsed = parseEntryKey(node?.rhConfigKey);
        if (parsed) {
            const hit = entries.find(item => item.kind === parsed.kind && item.id === parsed.id);
            if (hit) return hit;
        }
        const workflowId = String(node?.workflowId || '').trim();
        if (workflowId) {
            const hit = entries.find(item => item.kind === 'workflow' && item.id === workflowId);
            if (hit) return hit;
        }
        const appId = String(node?.webappId || '').trim();
        if (appId) {
            const hit = entries.find(item => item.kind === 'app' && item.id === appId);
            if (hit) return hit;
        }
        return null;
    }
    function visibleEntries(entries = []) {
        return Array.isArray(entries) ? entries.filter(entry => entry?.enabled !== false && entry?.hidden !== true) : [];
    }
    function entryFields(entry) { return Array.isArray(entry?.fields) ? entry.fields : []; }
    function workflowEntryHasSavedConfig(entry) {
        return entryFields(entry).length > 0
            || !!(entry?.workflowJson && typeof entry.workflowJson === 'object' && Object.keys(entry.workflowJson).length)
            || !!(entry?.raw && typeof entry.raw === 'object' && Object.keys(entry.raw).length);
    }
    function firstObjectSource(...sources) {
        return sources.find(source => source && typeof source === 'object' && Object.keys(source).length) || {};
    }
    function currentKind(node = {}, selectedKind = '') {
        if (selectedKind) return selectedKind;
        return ['model','workflow','app'].includes(node?.rhMode) ? node.rhMode : 'app';
    }
    function currentEntry(ref) { return ref?.entry || null; }
    global.WorkbenchCanvasRunningHubFieldRenderer = Object.freeze({render, promptMarkup, promptFields, settingField, entryOptions, paymentOptions, loadWorkflow, fieldText, fieldMatches, fullAspectLabel, isFullAspectField, valueForField, setParam, applyPresetParams, fieldValue, mediaInputState, mediaIndexes, pruneWorkflowForMissingFields, fieldLabel, isWorkflowLinkValue, usableFields, sortFields, paramKey, fieldKind, fieldRole, defaultValue, extractOptions, randomEnabled, randomActive, toggleRandomActive, sourceSummary, sourceProjection, inferWorkflowFieldType, workflowNodeInfoList, entryId, entryLabel, entryKey, parseEntryKey, allEntries, resolveEntryRef, visibleEntries, entryFields, workflowEntryHasSavedConfig, firstObjectSource, currentKind, currentEntry, compactJson, detailedError, readableError, payloadError, logErrorText, selectEntry});
}(window));
