// 监听 API 设置页面的变更广播，实时刷新画布的模型/平台下拉
try {
    const apiChannel = new BroadcastChannel('studio-api');
    apiChannel.onmessage = async (e) => {
        if(e.data?.type === 'providers-changed' || e.data?.type === 'workflows-changed' || e.data?.type === 'comfy-instances-changed'){
            await refreshCanvasConfigFromSettings();
        }
    };
} catch(e) { /* 不支持 BroadcastChannel 的旧浏览器忽略 */ }
function msChatModelOptions(selected){
    // 单一数据源：从 API 设置里 modelscope 平台的 chat_models 取
    const msProvider = apiProviders.find(p => p.id === 'modelscope');
    const list = uniqueModels(msProvider?.chat_models || []);
    if(!list.length){
        return `<option value="" disabled selected>${tr('canvas.noModelsHint') || '暂无模型，请到 API 设置添加'}</option>`;
    }
    const sel = selected && list.includes(selected) ? selected : list[0];
    return list.map(m => `<option value="${escapeHtml(m)}" ${m === sel ? 'selected' : ''}>${escapeHtml(m.split('/').pop().split(':')[0])}</option>`).join('');
}
async function loadCanvasList(openFirst=true){
    try {
        const res = await fetch('/api/canvases');
        if(!res.ok) throw new Error(tr('canvas.canvasListFailed'));
        const data = await res.json();
        canvases = data.canvases || [];
        sortCanvasListByUpdated();
        refreshGateViewControls();
        renderCanvasList();
        refreshTrashCount();
        if(openFirst && canvases[0]) await openCanvas(canvases[0].id);
        else if(!canvas) {
            setCanvasMode(false);
            setStatus(trashMode ? (deletedCanvases.length ? tr('canvas.trash') : tr('canvas.trashEmpty')) : (canvases.length ? tr('canvas.chooseFirst') : tr('canvas.noCanvasCreateFirst')));
        }
    } catch(e) {
        setStatus(tr('canvas.canvasListFailed'));
        console.error(e);
    }
}
async function loadTrashList(){
    try {
        const res = await fetch('/api/canvases/trash');
        if(!res.ok) throw new Error(tr('canvas.trashLoadFailed'));
        const data = await res.json();
        deletedCanvases = data.canvases || [];
        refreshGateViewControls();
        renderCanvasList();
        setStatus(deletedCanvases.length ? tr('canvas.trash') : tr('canvas.trashEmpty'));
    } catch(e) {
        setStatus(tr('canvas.trashLoadFailed'));
        console.error(e);
    }
}
async function refreshTrashCount(){
    if(trashMode) return;
    try {
        const res = await fetch('/api/canvases/trash');
        if(!res.ok) return;
        const data = await res.json();
        deletedCanvases = data.canvases || [];
        refreshGateViewControls();
    } catch(e) {}
}
async function setTrashMode(active){
    trashMode = active;
    creatingCanvas = false;
    pendingDeleteCanvasId = null;
    pendingPurgeCanvasId = null;
    closeCanvasMetaPopover();
    canvasGate.classList.toggle('creating', false);
    refreshGateViewControls();
    if(trashMode) await loadTrashList();
    else await loadCanvasList(false);
    refreshIcons();
}
function renderCanvasList(){
    // 选画布 gate 已拆分到独立页面 canvas-list.html；编辑器页不再有该 DOM，调用直接跳过。
    if(!gateCanvasList) return;
    renderCanvasListInto(gateCanvasList);
}
function compareCanvasRecords(a, b){
    // 置顶始终排在最前；其余按当前排序模式（最近编辑 / 名称）。
    const ap = a.pinned ? 1 : 0, bp = b.pinned ? 1 : 0;
    if(ap !== bp) return bp - ap;
    if(canvasSortMode === 'name'){
        const cmp = String(a.title || '').localeCompare(String(b.title || ''), 'zh-Hans-CN', {numeric:true, sensitivity:'base'});
        if(cmp !== 0) return cmp;
    }
    return Number(b.updated_at || b.created_at || 0) - Number(a.updated_at || a.created_at || 0);
}
function sortCanvasListByUpdated(){
    canvases.sort(compareCanvasRecords);
}
function setCanvasSortMode(mode){
    const next = mode === 'name' ? 'name' : 'recent';
    if(next === canvasSortMode) { refreshGateViewControls(); return; }
    canvasSortMode = next;
    try { localStorage.setItem('canvasSortMode', canvasSortMode); } catch(e){}
    sortCanvasListByUpdated();
    renderCanvasList();
    refreshGateViewControls();
}
async function patchCanvasMeta(id, patch){
    const item = canvases.find(c => c.id === id);
    if(item) Object.assign(item, patch);
    if(canvas?.id === id) Object.assign(canvas, patch);
    sortCanvasListByUpdated();
    renderCanvasList();
    try {
        const res = await fetch(`/api/canvases/${encodeURIComponent(id)}/meta`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(patch)
        });
        if(!res.ok) throw new Error('meta save failed');
        const data = await res.json();
        if(data.canvas) updateCanvasListRecord(data.canvas);
    } catch(e){
        setStatus(tr('canvas.metaSaveFailed') || '保存失败');
        console.error(e);
        await loadCanvasList(false);
    }
}
function togglePinCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    const item = canvases.find(c => c.id === id);
    closeCanvasMetaPopover();
    patchCanvasMeta(id, {pinned: !(item && item.pinned)});
}
function setCanvasColorValue(id, color, event){
    event?.preventDefault();
    event?.stopPropagation();
    patchCanvasMeta(id, {color: color || ''});
}
function commitCanvasOwner(id, value){
    const owner = String(value || '').trim().slice(0, 40);
    const item = canvases.find(c => c.id === id);
    if((item?.owner || '') === owner) return;
    patchCanvasMeta(id, {owner});
}
function updateCanvasListRecord(record){
    if(!record?.id) return;
    const index = canvases.findIndex(item => item.id === record.id);
    if(index >= 0) canvases[index] = {...canvases[index], ...record};
    else canvases.unshift(record);
    sortCanvasListByUpdated();
    renderCanvasList();
}
function renderCanvasListInto(list){
    if(!list) return;
    refreshGateViewControls();
    const items = trashMode ? deletedCanvases : canvases;
    list.innerHTML = '';
    if(!items.length){
        const empty = document.createElement('div');
        empty.className = 'gate-list-empty';
        empty.innerHTML = trashMode
            ? `<div class="gate-list-empty-icon"><i data-lucide="trash-2" class="w-6 h-6"></i></div>${tr('canvas.trashEmpty')}`
            : `<div class="gate-list-empty-icon"><i data-lucide="layout-grid" class="w-6 h-6"></i></div>${tr('canvas.noCanvas')}<br>${tr('canvas.startWithNewCanvas')}`;
        list.appendChild(empty);
        refreshIcons();
        return;
    }
    items.forEach(item => {
        const row = document.createElement('div');
        const isSmartCanvas = (item.kind || 'classic') === 'smart';
        const color = String(item.color || '').trim();
        const owner = String(item.owner || '').trim();
        const pinned = !!item.pinned && !trashMode;
        row.className = `canvas-item ${isSmartCanvas ? 'smart-canvas' : ''} ${canvas?.id === item.id ? 'active' : ''} ${pinned ? 'pinned' : ''} ${color ? 'has-color' : ''}`;
        row.dataset.canvasId = item.id;
        const ownerChip = owner
            ? `<span class="canvas-owner-chip" role="button" tabindex="0" title="${escapeAttr(owner)}"><i data-lucide="user-round" class="w-3 h-3"></i><span class="canvas-owner-text">${escapeHtml(owner)}</span></span>`
            : '';
        row.innerHTML = `
            <div class="canvas-open" role="button" tabindex="${trashMode ? '-1' : '0'}">
                <div class="canvas-card-icon-row">
                    <span class="canvas-preview-mark ${color ? `icon-has-color cc-${escapeAttr(color)}` : ''}" role="button" tabindex="0" title="${trashMode ? tr('canvas.deletedCanvas') : (tr('canvas.editMeta') || '编辑图标 / 颜色 / 负责人')}">${renderCanvasIcon(isSmartCanvas && /[^\x00-\x7F]/.test(item.icon || '') ? 'sparkles' : item.icon, 16)}</span>
                    ${isSmartCanvas ? `<span class="canvas-kind-chip">${tr('canvas.smartCanvasShort')}</span>` : ''}
                </div>
                <div class="canvas-card-title">${escapeHtml(item.title)}</div>
                ${ownerChip}
                <div class="canvas-card-meta">
                    <span class="canvas-card-meta-dot"></span>
                    <div class="canvas-card-time">${trashMode ? `${tr('canvas.deletedAt')} ${formatCanvasTime(item.deleted_at)}` : formatCanvasTime(item.updated_at || item.created_at)}</div>
                </div>
            </div>
            ${trashMode ? (pendingPurgeCanvasId === item.id ? `
                <div class="canvas-delete-confirm">
                    <div class="canvas-delete-box">
                        <div class="canvas-delete-title">${tr('canvas.purgeConfirm')}</div>
                        <div class="canvas-delete-actions">
                            <button class="canvas-confirm-btn" type="button">${tr('common.confirm')}</button>
                            <button class="canvas-cancel-btn" type="button">${tr('common.cancel')}</button>
                        </div>
                    </div>
                </div>
            ` : `
                <button class="canvas-delete canvas-restore" type="button" title="${tr('canvas.restoreCanvas')}" aria-label="${tr('canvas.restoreCanvas')} ${escapeHtml(item.title)}" style="right:42px">
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                </button>
                <button class="canvas-delete canvas-purge" type="button" title="${tr('canvas.purgeCanvas')}" aria-label="${tr('canvas.purgeCanvas')} ${escapeHtml(item.title)}">
                    <i data-lucide="x" class="w-3.5 h-3.5"></i>
                </button>
            `) : (pendingDeleteCanvasId === item.id ? `
                <div class="canvas-delete-confirm">
                    <div class="canvas-delete-box">
                        <div class="canvas-delete-title">${tr('canvas.moveToTrashConfirm')}</div>
                        <div class="canvas-delete-actions">
                            <button class="canvas-confirm-btn" type="button">${tr('common.confirm')}</button>
                            <button class="canvas-cancel-btn" type="button">${tr('common.cancel')}</button>
                        </div>
                    </div>
                </div>
            ` : `
                <button class="canvas-pin-btn ${pinned ? 'active' : ''}" type="button" title="${pinned ? (tr('canvas.unpin') || '取消置顶') : (tr('canvas.pin') || '置顶')}" aria-label="${pinned ? (tr('canvas.unpin') || '取消置顶') : (tr('canvas.pin') || '置顶')}">
                    <i data-lucide="pin" class="w-3.5 h-3.5"></i>
                </button>
                <button class="canvas-card-edit" type="button" title="${tr('canvas.rename')}" aria-label="${tr('canvas.rename')} ${escapeHtml(item.title)}">
                    <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
                </button>
                <button class="canvas-delete" type="button" title="${tr('canvas.moveToTrash')}" aria-label="${tr('canvas.moveToTrash')} ${escapeHtml(item.title)}">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            `)}
        `;
        if(!trashMode) row.querySelector('.canvas-open').onclick = () => openCanvas(item.id);
        const titleEl = row.querySelector('.canvas-card-title');
        const editBtn = row.querySelector('.canvas-card-edit');
        if(editBtn && titleEl && !trashMode) {
            editBtn.onmousedown = e => e.stopPropagation();
            editBtn.onclick = e => { e.stopPropagation(); startTitleEdit(item.id, titleEl); };
        }
        const iconBtn = row.querySelector('.canvas-preview-mark');
        if(iconBtn && !trashMode) {
            iconBtn.onclick = e => toggleEmojiPicker(item.id, e);
            iconBtn.onkeydown = e => {
                if(e.key === 'Enter' || e.key === ' ') toggleEmojiPicker(item.id, e);
            };
        }
        row.querySelectorAll('.emoji-option').forEach(btn => {
            btn.onclick = e => setCanvasIcon(item.id, btn.dataset.icon, e);
        });
        const pinBtn = row.querySelector('.canvas-pin-btn');
        if(pinBtn){
            pinBtn.onmousedown = e => e.stopPropagation();
            pinBtn.onclick = e => togglePinCanvas(item.id, e);
        }
        const ownerChipEl = row.querySelector('.canvas-owner-chip');
        if(ownerChipEl && !trashMode){
            ownerChipEl.onmousedown = e => e.stopPropagation();
            ownerChipEl.onclick = e => { e.stopPropagation(); toggleEmojiPicker(item.id, e); };
        }
        const deleteBtn = row.querySelector('.canvas-delete');
        if(deleteBtn) deleteBtn.onclick = e => requestDeleteCanvas(item.id, e);
        const confirmBtn = row.querySelector('.canvas-confirm-btn');
        if(confirmBtn) confirmBtn.onclick = e => trashMode ? purgeCanvas(item.id, e) : deleteCanvas(item.id, e);
        const cancelBtn = row.querySelector('.canvas-cancel-btn');
        if(cancelBtn) cancelBtn.onclick = e => cancelDeleteCanvas(e);
        const restoreBtn = row.querySelector('.canvas-restore');
        if(restoreBtn) restoreBtn.onclick = e => restoreCanvas(item.id, e);
        const purgeBtn = row.querySelector('.canvas-purge');
        if(purgeBtn) purgeBtn.onclick = e => requestPurgeCanvas(item.id, e);
        list.appendChild(row);
    });
    refreshIcons();
    renderCanvasMetaPopover();
}
function closeCanvasMetaPopover(){
    emojiPickerCanvasId = null;
    canvasMetaAnchorId = '';
    document.querySelector('.canvas-meta-pop')?.remove();
}
function renderCanvasMetaPopover(){
    document.querySelector('.canvas-meta-pop')?.remove();
    if(trashMode || !emojiPickerCanvasId) return;
    const item = canvases.find(entry => entry.id === emojiPickerCanvasId);
    if(!item) return;
    const color = String(item.color || '').trim();
    const owner = String(item.owner || '').trim();
    const pop = document.createElement('div');
    pop.className = 'canvas-meta-pop';
    pop.dataset.canvasMetaPop = item.id;
    pop.innerHTML = `
        <div class="canvas-meta-section">
            <div class="canvas-meta-label">${tr('canvas.ownerLabel') || '负责人 / 项目'}</div>
            <input class="canvas-owner-input" type="text" maxlength="40" value="${escapeAttr(owner)}" placeholder="${escapeAttr(tr('canvas.ownerPlaceholder') || '如：张三 / 双十一项目')}">
        </div>
        <div class="canvas-meta-section">
            <div class="canvas-meta-label">${tr('canvas.colorLabel') || '颜色标记'}</div>
            <div class="canvas-color-row">
                <button class="canvas-color-swatch cc-none ${!color ? 'active' : ''}" type="button" data-color="" title="${tr('canvas.colorNone') || '无'}"><i data-lucide="ban" class="w-3 h-3"></i></button>
                ${CANVAS_COLOR_OPTIONS.map(c => `<button class="canvas-color-swatch cc-${c} ${color === c ? 'active' : ''}" type="button" data-color="${c}" aria-label="${c}"></button>`).join('')}
            </div>
        </div>
        <div class="canvas-meta-section">
            <div class="canvas-meta-label">${tr('canvas.changeIcon')}</div>
            <div class="emoji-picker-grid">
                ${CANVAS_EMOJIS.map(icon => `<button class="emoji-option" type="button" data-icon="${escapeHtml(icon)}">${renderCanvasIcon(icon, 14)}</button>`).join('')}
            </div>
        </div>
    `;
    document.body.appendChild(pop);
    pop.querySelectorAll('.emoji-option').forEach(btn => {
        btn.onclick = e => setCanvasIcon(item.id, btn.dataset.icon, e);
    });
    pop.querySelectorAll('.canvas-color-swatch').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = e => setCanvasColorValue(item.id, btn.dataset.color || '', e);
    });
    const ownerInput = pop.querySelector('.canvas-owner-input');
    if(ownerInput){
        ownerInput.onmousedown = e => e.stopPropagation();
        ownerInput.onclick = e => e.stopPropagation();
        ownerInput.onkeydown = e => {
            e.stopPropagation();
            if(e.key === 'Enter'){ e.preventDefault(); ownerInput.blur(); }
            if(e.key === 'Escape'){ e.preventDefault(); closeCanvasMetaPopover(); renderCanvasList(); }
        };
        ownerInput.onblur = () => commitCanvasOwner(item.id, ownerInput.value);
    }
    refreshIcons();
    requestAnimationFrame(positionCanvasMetaPopover);
}
function positionCanvasMetaPopover(){
    if(!emojiPickerCanvasId) return;
    const pop = document.querySelector('.canvas-meta-pop');
    const anchorId = canvasMetaAnchorId || emojiPickerCanvasId;
    const row = document.querySelector(`.canvas-item[data-canvas-id="${CSS.escape(anchorId)}"]`);
    const icon = row?.querySelector('.canvas-preview-mark') || row?.querySelector('.canvas-owner-chip');
    if(!pop || !icon) return;
    const iconRect = icon.getBoundingClientRect();
    const width = pop.offsetWidth || 212;
    const height = pop.offsetHeight || 260;
    const margin = 12;
    let left = Math.min(Math.max(iconRect.left, margin), window.innerWidth - width - margin);
    let top = iconRect.bottom + 8;
    if(top + height > window.innerHeight - margin) top = iconRect.top - height - 8;
    if(top < margin) top = margin;
    pop.style.left = `${Math.round(left)}px`;
    pop.style.top = `${Math.round(top)}px`;
}
async function createCanvas(){
    const customTitle = gateTitleInput?.value.trim();
    const isSmart = createCanvasKind === 'smart';
    const titleBase = isSmart ? tr('canvas.newSmartCanvas') : tr('canvas.newCanvas');
    const title = customTitle || `${titleBase} ${new Date().toLocaleTimeString(window.StudioI18n?.lang() === 'en' ? 'en-US' : 'zh-CN', {hour:'2-digit', minute:'2-digit'})}`;
    trashMode = false;
    refreshGateViewControls();
    setStatus('Creating...');
    try {
        const res = await fetch('/api/canvases', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({title, icon:isSmart ? 'sparkles' : '🧩', kind:isSmart ? 'smart' : 'classic'})
        });
        if(!res.ok) throw new Error(tr('canvas.createFailed'));
        const data = await res.json();
        if(isSmart){
            setCreateMode(false);
            await loadCanvasList(false);
            window.location.href = window.WorkbenchCanvasEntryCompatibility.normalCanvasUrl(
                data.canvas?.id,
                data.canvas?.project || 'default'
            );
            return;
        }
        ensureClassicCascadeOrchestrator().resetCascadeRuntimeState();
        canvas = data.canvas;
        canvas.logs = canvas.logs || [];
        nodes = canvas.nodes || [];
        connections = canvas.connections || [];
        adoptCanvasRuntimeState(localViewportForCanvas(canvas.id, canvas.viewport || {x:0, y:0, scale:1}));
        canvas.viewport = {...viewport};
        resetTransientRunState(nodes);
        sanitizeConnections();
        selected.clear();
        setCanvasMode(true);
        render();
        setStatus('Saved');
        setCreateMode(false);
        await loadCanvasList(false);
        renderCanvasList();
    } catch(e) {
        setStatus(tr('canvas.createFailed'));
        console.error(e);
    }
}
async function createSmartCanvas(){
    setCreateMode(true, 'smart');
}
function toggleEmojiPicker(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    pendingDeleteCanvasId = null;
    const opening = emojiPickerCanvasId !== id;
    emojiPickerCanvasId = opening ? id : null;
    canvasMetaAnchorId = opening ? id : '';
    renderCanvasList();
}
async function setCanvasIcon(id, icon, event){
    event?.preventDefault();
    event?.stopPropagation();
    const item = canvases.find(c => c.id === id);
    if(item) item.icon = icon || 'layers';
    closeCanvasMetaPopover();
    renderCanvasList();
    try {
        const res = await fetch(`/api/canvases/${encodeURIComponent(id)}/meta`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({icon:icon || 'layers'})
        });
        if(!res.ok) throw new Error('图标保存失败');
        const data = await res.json();
        if(data.canvas){
            if(canvas?.id === id) canvas.icon = data.canvas.icon;
            const idx = canvases.findIndex(item => item.id === id);
            if(idx >= 0) canvases[idx] = {...canvases[idx], ...data.canvas};
        }
        await loadCanvasList(false);
    } catch(e) {
        setStatus('图标保存失败');
        console.error(e);
    }
}
function startTitleEdit(id, titleEl){
    if(!titleEl || titleEl.querySelector('input')) return;
    const item = canvases.find(c => c.id === id);
    const current = item?.title || titleEl.textContent || '';
    const input = document.createElement('input');
    input.type = 'text';
    input.maxLength = 80;
    input.value = current;
    input.className = 'canvas-card-title-input';
    titleEl.innerHTML = '';
    titleEl.appendChild(input);
    input.onmousedown = e => e.stopPropagation();
    input.onclick = e => e.stopPropagation();
    input.focus();
    input.select();
    let done = false;
    const finish = async (commit) => {
        if(done) return;
        done = true;
        const newTitle = input.value.trim();
        if(commit && newTitle && newTitle !== current){
            await setCanvasTitle(id, newTitle);
        } else {
            renderCanvasList();
        }
    };
    input.onblur = () => finish(true);
    input.onkeydown = e => {
        e.stopPropagation();
        if(e.key === 'Enter'){ e.preventDefault(); finish(true); }
        if(e.key === 'Escape'){ e.preventDefault(); finish(false); }
    };
}
async function setCanvasTitle(id, title){
    const item = canvases.find(c => c.id === id);
    if(item) item.title = title;
    if(canvas?.id === id) canvas.title = title;
    renderCanvasList();
    try {
        const res = await fetch(`/api/canvases/${encodeURIComponent(id)}/meta`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({title})
        });
        if(!res.ok) throw new Error('重命名失败');
        const data = await res.json();
        if(data.canvas){
            if(canvas?.id === id) canvas.title = data.canvas.title;
            const idx = canvases.findIndex(item => item.id === id);
            if(idx >= 0) canvases[idx] = {...canvases[idx], ...data.canvas};
        }
        if(currentCanvasTitle && canvas?.id === id) currentCanvasTitle.textContent = title;
        await loadCanvasList(false);
    } catch(e){
        setStatus('重命名失败');
        console.error(e);
    }
}
async function openCanvas(id){
    canvasRenderSweep?.clear();
    try {
        await ensureCanvasSession().open(id);
    } catch(e) {
        setStatus(tr('canvas.openFailed'));
        console.error(e);
        // 打开失败（id 无效/已删除）：回到选画布页面，避免停在空白编辑器。
        window.location.replace(canvasListUrlForProject(canvas?.project || requestedCanvasListProject() || rememberedCanvasListProject()));
    }
}
async function applyCanvasSessionRecord(record, context={}){
    const source = String(context.source || 'open');
    if(source === 'saved'){
        const localViewport = {...viewport};
        canvas = {...canvas, ...record, nodes, connections, viewport:localViewport};
        canvas.updated_at = Number(record.updated_at || canvas.updated_at || Date.now());
        if(currentCanvasTime) currentCanvasTime.textContent = formatCanvasTime(canvas.updated_at);
        loadCanvasList(false);
        return;
    }
    ensureClassicCascadeOrchestrator().resetCascadeRuntimeState();
    const localSelectedIds = source === 'remote' ? new Set(selected) : new Set();
    const nextViewport = source === 'remote'
        ? localViewportForCanvas(record.id, viewport || record.viewport || {x:0, y:0, scale:1})
        : localViewportForCanvas(record.id, record.viewport || {x:0, y:0, scale:1});
    canvas = record;
    if(source === 'open') rememberCanvasListProject(canvas.project || 'default');
    canvas.logs = canvas.logs || [];
    nodes = canvas.nodes || [];
    connections = canvas.connections || [];
    adoptCanvasRuntimeState(nextViewport);
    canvas.viewport = {...viewport};
    resetTransientRunState(nodes);
    sanitizeConnections();
    pruneMissingComfyWorkflows();
    await refreshMissingCanvasAssets();
    if(source === 'remote'){
        selected.replace([...localSelectedIds].filter(id => nodes.some(node => node.id === id)));
    } else {
        selected.clear();
        setCanvasMode(true);
    }
    renderCanvasList();
    render();
    resumeCanvasImageTasks();
    if(source === 'remote'){
        if(currentCanvasTitle) currentCanvasTitle.textContent = canvas.title || tr('canvas.untitled');
        if(currentCanvasTime) currentCanvasTime.textContent = formatCanvasTime(canvas.updated_at || canvas.created_at);
    }
}
function resetTransientRunState(list=nodes){
    const executionHost = ensureClassicExecutionHost();
    (list || []).forEach(node => {
        if(!node) return;
        if(node.running) executionHost.markRunning(node, false);
        if(node.runStatus || node.runError) executionHost.setRunStatus(node, '', '');
        if(node._cascadeIdx) node._cascadeIdx = '';
        if(node._cascadeFailed) node._cascadeFailed = false;
    });
}
function canvasLocalAssetUrls(){ return ensureClassicAssetRuntime().canvasLocalAssetUrls(); }
async function refreshMissingCanvasAssets(){ return ensureClassicAssetRuntime().refreshMissingCanvasAssets(); }
async function syncRemoteCanvasNow(){
    return ensureCanvasSession().sync();
}
async function checkRemoteCanvasVersion(){
    return ensureCanvasSession().sync();
}
function handleCanvasUpdatedMessage(data){
    return ensureCanvasSession().handleUpdate(data);
}
async function returnToCanvasManager(){
    if(canvasSession) await canvasSession.close();
    canvas = null;
    nodes = [];
    connections = [];
    selected.clear();
    adoptCanvasRuntimeState({x: -1800, y: -1000, scale: 1});
    setCanvasMode(false);
    trashMode = false;
    pendingPurgeCanvasId = null;
    refreshGateViewControls();
    await loadCanvasList(false);
    setCreateMode(false);
}
function requestDeleteCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    closeCanvasMetaPopover();
    pendingPurgeCanvasId = null;
    pendingDeleteCanvasId = id;
    renderCanvasList();
}
function requestPurgeCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    closeCanvasMetaPopover();
    pendingDeleteCanvasId = null;
    pendingPurgeCanvasId = id;
    renderCanvasList();
}
function cancelDeleteCanvas(event){
    event?.preventDefault();
    event?.stopPropagation();
    pendingDeleteCanvasId = null;
    pendingPurgeCanvasId = null;
    renderCanvasList();
}
async function deleteCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    setStatus('Moving to trash...');
    try {
        const res = await fetch(`/api/canvases/${id}`, {method:'DELETE'});
        if(!res.ok) throw new Error(tr('canvas.moveToTrashFailed'));
        const deletingCurrent = canvas?.id === id;
        pendingDeleteCanvasId = null;
        canvases = canvases.filter(item => item.id !== id);
        if(deletingCurrent){
            canvas = null;
            nodes = [];
            connections = [];
            selected.clear();
            adoptCanvasRuntimeState({x: -1800, y: -1000, scale: 1});
            setCanvasMode(false);
        }
        renderCanvasList();
        setStatus(canvases.length ? tr('canvas.movedToTrash') : tr('canvas.noCanvasCreateFirst'));
        await loadCanvasList(false);
    } catch(e) {
        setStatus(tr('canvas.moveToTrashFailed'));
        console.error(e);
    }
}
async function restoreCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    setStatus('Restoring...');
    try {
        const res = await fetch(`/api/canvases/${id}/restore`, {method:'POST'});
        if(!res.ok) throw new Error(tr('canvas.restoreFailed'));
        pendingPurgeCanvasId = null;
        deletedCanvases = deletedCanvases.filter(item => item.id !== id);
        await loadCanvasList(false);
        await loadTrashList();
        setStatus(tr('canvas.restored'));
    } catch(e) {
        setStatus(tr('canvas.restoreFailed'));
        console.error(e);
    }
}
async function purgeCanvas(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    setStatus('Deleting...');
    try {
        const res = await fetch(`/api/canvases/${id}/purge`, {method:'DELETE'});
        if(!res.ok) throw new Error(tr('canvas.purgeFailed'));
        pendingPurgeCanvasId = null;
        deletedCanvases = deletedCanvases.filter(item => item.id !== id);
        renderCanvasList();
        setStatus(deletedCanvases.length ? tr('canvas.purged') : tr('canvas.trashEmpty'));
        await loadTrashList();
    } catch(e) {
        setStatus(tr('canvas.purgeFailed'));
        console.error(e);
    }
}
window.createCanvas = createCanvas;
window.createSmartCanvas = createSmartCanvas;
window.loadCanvasList = loadCanvasList;
window.openCanvas = openCanvas;
window.deleteCanvas = deleteCanvas;
window.returnToCanvasManager = returnToCanvasManager;
// 选画布 gate 已拆分到 canvas-list.html；编辑器页不再含这些元素，用可选链避免空引用报错。
gateCreateBtn?.addEventListener('click', () => setCreateMode(true));
gateCreateSmartBtn?.addEventListener('click', createSmartCanvas);
gateBackBtn?.addEventListener('click', () => setTrashMode(false));
gateTrashBtn?.addEventListener('click', () => setTrashMode(true));
gateRefreshBtn?.addEventListener('click', () => trashMode ? loadTrashList() : loadCanvasList(false));
document.getElementById('gateSortSwitch')?.addEventListener('click', e => {
    const btn = e.target.closest('[data-sort]');
    if(btn) setCanvasSortMode(btn.dataset.sort);
});
gateConfirmBtn?.addEventListener('click', createCanvas);
gateCancelBtn?.addEventListener('click', () => setCreateMode(false));
gateTitleInput?.addEventListener('keydown', e => {
    if(e.key === 'Enter') createCanvas();
    if(e.key === 'Escape') setCreateMode(false);
});
document.addEventListener('mousedown', e => {
    if(emojiPickerCanvasId === null) return;
    if(e.target.closest('.canvas-meta-pop') || e.target.closest('.canvas-preview-mark') || e.target.closest('.canvas-owner-chip')) return;
    closeCanvasMetaPopover();
    renderCanvasList();
});
gateCanvasList?.addEventListener('scroll', () => requestAnimationFrame(positionCanvasMetaPopover), {passive:true});
window.addEventListener('resize', () => {
    requestAnimationFrame(positionCanvasMetaPopover);
    if(cropState) syncImageEditOverflow();
});
window.addEventListener('studio-theme-change', event => applyTheme(event.detail?.theme || 'light'));
function cropDragModeFromPointer(event){
    const explicit = event.target.closest?.('[data-crop-handle]')?.dataset?.cropHandle;
    if(explicit) return `crop-${explicit}`;
    if(imageEditMode !== 'crop') return 'move';
    const box = document.getElementById('cropBox');
    const rect = box?.getBoundingClientRect?.();
    if(!rect) return 'move';
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const handle = WorkbenchCanvasMediaTools.cropHandleFromPoint(x, y, rect.width, rect.height);
    return handle === 'move' ? handle : `crop-${handle}`;
}
document.getElementById('cropBox').addEventListener('mousedown', event => beginCropDrag(event, cropDragModeFromPointer(event)));
document.querySelectorAll('[data-crop-handle]').forEach(handle => {
    handle.addEventListener('mousedown', event => beginCropDrag(event, `crop-${handle.dataset.cropHandle || 'se'}`));
});
document.querySelectorAll('[data-crop-ratio]').forEach(btn => {
    btn.addEventListener('click', event => {
        event.stopPropagation();
        setCropAspectPreset(btn.dataset.cropRatio || 'free');
    });
});
document.getElementById('outpaintFrame')?.addEventListener('mousedown', event => {
    if(event.target.closest('[data-outpaint-handle]')) return;
    document.getElementById('cropCanvas')?.classList.add('dragging-image');
    beginCropDrag(event, 'image');
});
document.querySelectorAll('[data-outpaint-handle]').forEach(handle => {
    handle.addEventListener('mousedown', event => beginCropDrag(event, `outpaint-${handle.dataset.outpaintHandle || 'corner'}`));
});
document.getElementById('cropImage')?.addEventListener('mousedown', event => {
    if(imageEditMode !== 'outpaint' || !cropState) return;
    document.getElementById('cropCanvas')?.classList.add('dragging-image');
    beginCropDrag(event, 'image');
});
document.querySelectorAll('[data-image-edit-mode]').forEach(btn => {
    btn.addEventListener('click', event => {
        event.stopPropagation();
        setImageEditMode(btn.dataset.imageEditMode || 'crop', true);
    });
});
document.getElementById('editDrawCanvas').addEventListener('pointerdown', beginEditDraw);
document.getElementById('editDrawCanvas').addEventListener('pointermove', moveEditDraw);
document.getElementById('editDrawCanvas').addEventListener('pointerup', endEditDraw);
document.getElementById('editDrawCanvas').addEventListener('pointercancel', endEditDraw);
document.getElementById('editDrawCanvas').addEventListener('pointerleave', endEditDraw);
document.getElementById('editTextCanvas')?.addEventListener('pointerdown', beginEditText);
document.getElementById('editTextCanvas')?.addEventListener('pointermove', moveEditText);
document.getElementById('editTextCanvas')?.addEventListener('pointerup', endEditText);
document.getElementById('editTextCanvas')?.addEventListener('pointercancel', endEditText);
document.getElementById('editTextCanvas')?.addEventListener('pointerleave', endEditText);
document.getElementById('editTextCanvas')?.addEventListener('dblclick', event => {
    if(imageEditMode !== 'brush' || brushTool !== 'text') return;
    event.preventDefault();
    event.stopPropagation();
    const hit = hitEditTextItem(editTextPoint(event));
    if(hit){
        setSelectedEditTextItem(hit.id);
        beginEditTextInline(hit);
    }
});
['paintBrushSize','paintBrushColor'].forEach(id => {
    const control = document.getElementById(id);
    if(!control) return;
    control.addEventListener('input', syncSelectedEditTextStyleFromBrush);
    control.addEventListener('change', () => { editTextDirty = false; });
});
['gridHorizontalLines','gridVerticalLines','gridGapSize'].forEach(id => {
    document.getElementById(id).addEventListener('input', () => {
        syncGridGapValue();
        refreshGridSplitPreview();
    });
});
['imageResizeScaleRange','imageResizeScaleInput'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', event => setImageResizeScale(event.target.value));
});
// 图片编辑区滚轮缩放
document.getElementById('imageEditStage').addEventListener('wheel', event => {
    if(!cropState) return;
    event.preventDefault();
    event.stopPropagation();
    const stage = event.currentTarget;
    const oldZoom = imageEditZoom;
    const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
    imageEditZoom = Math.max(0.15, Math.min(6.0, imageEditZoom * factor));
    // 焦点缩放：保持鼠标指向的图片位置不动
    const stageRect = stage.getBoundingClientRect();
    const mx = event.clientX - stageRect.left; // 鼠标在 stage 内偏移
    const my = event.clientY - stageRect.top;
    const contentX = stage.scrollLeft + mx;
    const contentY = stage.scrollTop + my;
    applyImageEditZoom();
    const scale = imageEditZoom / oldZoom;
    stage.scrollLeft = contentX * scale - mx;
    stage.scrollTop = contentY * scale - my;
}, {passive: false});
function rememberCanvasListProject(projectId){
    return window.WorkbenchCanvasEntryCompatibility.rememberCanvasListProject(projectId, {storage:localStorage, storageKey:CANVAS_LIST_PROJECT_KEY});
}

function rememberedCanvasListProject(){
    return window.WorkbenchCanvasEntryCompatibility.rememberedCanvasListProject({storage:localStorage, storageKey:CANVAS_LIST_PROJECT_KEY});
}

function requestedCanvasListProject(){
    try { return new URLSearchParams(window.location.search).get('project') || ''; } catch(e){ return ''; }
}

function canvasListUrlForProject(projectId){
    return window.WorkbenchCanvasEntryCompatibility.canvasListUrl(projectId, {storage:localStorage, storageKey:CANVAS_LIST_PROJECT_KEY});
}

function addNode(node){
    if(!ensureCanvas()) return;
    nodes.push(node);
    render();
    scheduleSave();
    return node;
}
function defaultPoint(dx=0, dy=0){ return screenToWorld(window.innerWidth / 2 + dx, window.innerHeight / 2 + dy); }
function canUseVersionedImageCreation(){
    return Boolean(window.WorkbenchNodeClient?.isLoopback?.() && window.WorkbenchNodeClient?.isEnabled?.() && canvas?.id && canvas?.project);
}
async function addVersionedBlankImageNode(point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(-120, 0);
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID,
            source:'context_menu',
            definitionRef:{type:'legacy', id:'image', version:'0'},
            position:{x:p.x, y:p.y},
            expectedRevision:currentCanvasRevision(),
            title:'空白图片',
            apply: {
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'image', x:p.x, y:p.y, url:'', name:created.title || '空白图片'}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        render();
        return node;
    } catch(error) {
        console.error('Versioned Image creation failed', error);
        setStatus('Create failed');
        return null;
    }
}
async function createVersionedDroppedMediaNode(file, point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(0, 0);
    const kind = file?.kind || 'image';
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'file_drop',
            definitionRef:{type:'legacy', id:'image', version:'0'}, position:{x:p.x, y:p.y},
            expectedRevision:currentCanvasRevision(),
            title:file?.name || nodeTitleForMedia({mediaKind:kind}),
            initialConfig:{url:file?.url || '', name:file?.name || '', mediaKind:kind},
            apply:{
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'image', x:p.x, y:p.y, url:file?.config?.url || file?.url || '', name:file?.config?.name || file?.name || created.title, mediaKind:file?.config?.mediaKind || kind}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        return node;
    } catch(error) { console.error('Versioned file-drop creation failed', error); throw error; }
}
async function addVersionedBlankPromptNode(point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(0, 0);
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'context_menu',
            definitionRef:{type:'legacy', id:'prompt', version:'0'},
            position:{x:p.x, y:p.y}, expectedRevision:currentCanvasRevision(),
            initialConfig:{text:''}, title:'Prompt',
            apply: {
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'prompt', x:p.x, y:p.y, text:''}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        render();
        return node;
    } catch(error) {
        console.error('Versioned Prompt creation failed', error);
        setStatus('Create failed');
        return null;
    }
}
async function addVersionedBlankLoopNode(point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(40, 0);
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'context_menu',
            definitionRef:{type:'legacy', id:'loop', version:'0'},
            position:{x:p.x, y:p.y}, expectedRevision:currentCanvasRevision(),
            initialConfig:{count:3}, title:'Loop',
            apply: {
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'loop', x:p.x, y:p.y, count:3, mode:'serial', showPrompt:false, imageInput:false, videoInput:false, loopStart:1, imageBatchSize:1, videoBatchSize:1, variablePrompt:'', fixedPrompt:''}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        render();
        return node;
    } catch(error) {
        console.error('Versioned Loop creation failed', error);
        setStatus('Create failed');
        return null;
    }
}
function addImageNode(point){
    const p = point || defaultPoint(-120, 0);
    return addNode({id:uid('img'), type:'image', x:p.x, y:p.y, url:'', name:'空白图片'});
}
function addPromptNode(point){
    const p = point || defaultPoint(0, 0);
    return addNode({id:uid('prompt'), type:'prompt', x:p.x, y:p.y, text:''});
}
function addLoopNode(point){
    const p = point || defaultPoint(40, 0);
    return addNode({
        id:uid('loop'),
        type:'loop',
        x:p.x,
        y:p.y,
        count:3,
        mode:'serial',
        showPrompt:false,
        imageInput:false,
        videoInput:false,
        loopStart:1,
        imageBatchSize:1,
        videoBatchSize:1,
        variablePrompt:'',
        fixedPrompt:''
    });
}
async function addVersionedBlankGroupNode(point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(40, 0);
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'context_menu',
            definitionRef:{type:'legacy', id:'group', version:'0'},
            position:{x:p.x, y:p.y}, expectedRevision:currentCanvasRevision(), title:'Group',
            apply: {
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'group', x:p.x, y:p.y, w:300, h:220, items:[]}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        render();
        return node;
    } catch(error) {
        console.error('Versioned Group creation failed', error);
        setStatus('Create failed');
        return null;
    }
}
async function addVersionedBlankOutputNode(point){
    if(!canUseVersionedImageCreation()) return null;
    const p = point || defaultPoint(260, 0);
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'context_menu',
            definitionRef:{type:'legacy', id:'output', version:'0'},
            position:{x:p.x, y:p.y}, expectedRevision:currentCanvasRevision(), title:'Output',
            apply: {
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => ({id:created.id, type:'output', x:p.x, y:p.y, images:[]}),
                onRevision:revision => { adoptCanvasRevision(revision); },
            },
        });
        render();
        return node;
    } catch(error) {
        console.error('Versioned Output creation failed', error);
        setStatus('Create failed');
        return null;
    }
}
function addGroupNode(point){
    const p = point || defaultPoint(40, 0);
    return addNode({id:uid('grp'), type:'group', x:p.x, y:p.y, w:300, h:220, items:[]});
}
function pickMediaForNode(nodeId){
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*,video/*,audio/*';
    input.multiple = true;
    input.onchange = () => {
        if(input.files?.length) fillImageNode(nodeId, input.files, {group:input.files.length > 1});
    };
    input.click();
}
function addLLMNode(point){
    const p = point || defaultPoint(80, 0);
    const providerId = chatApiProviders()[0]?.id || 'comfly';
    return addNode({
        id:uid('llm'),
        type:'llm',
        x:p.x,
        y:p.y,
        llmProvider:providerId,
        model:resolveChatModel('', providerId),
        mode:'node',
        systemPrompt:'You are a helpful assistant. Rewrite the input into a concise image prompt.',
        chatInput:'',
        messages:[],
        outputText:'',
        llmInputHeight:110,
        llmOutputHeight:150,
        running:false
    });
}
async function getImageDimensions(url){
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve({width: img.naturalWidth, height: img.naturalHeight});
        img.onerror = () => reject(new Error('图片加载失败'));
        img.src = url;
    });
}
async function urlToBase64(url){
    const res = await fetch(url);
    if(!res.ok) throw new Error('图片读取失败');
    const blob = await res.blob();
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
function syncClassicCreateMenuCommands(){
    if(!createMenu || !window.WorkbenchCanvasCommands) return;
    const buttons = createMenu.querySelectorAll(':scope > [data-canvas-command]');
    const catalog = window.WorkbenchCanvasCommands.creationCatalogFor('classic');
    window.WorkbenchCanvasCommands.orderCreateMenuItems(buttons, catalog).forEach(button => createMenu.append(button));
}
function openCreateMenu(clientX, clientY){
    menuPoint = screenToWorld(clientX, clientY);
    closeLinkCreateMenu();
    syncClassicCreateMenuCommands();
    createMenu.style.left = `${clientX}px`;
    createMenu.style.top = `${clientY}px`;
    createMenu.classList.add('open');
    refreshIcons();
}
function closeCreateMenu(){
    createMenu.classList.remove('open');
    closeLinkCreateMenu();
    closeImageNodeMenu();
}
function linkCreateOptions(state){
    const node = nodes.find(n => n.id === state?.originId);
    if(!node) return [];
    if(state.originKind === 'out'){
        if(['image','prompt','loop','group','promptGroup','llm','output'].includes(node.type)){
            return [
                {type:'generator', label:tr('canvas.apiGenerate'), icon:'wand-sparkles'},
                {type:'midjourney', label:'Midjourney', icon:'panel-top'},
                {type:'msgen', label:tr('canvas.modelscopeGenerate'), icon:'cloud-lightning'},
                {type:'comfy', label:tr('canvas.comfyGenerate'), icon:'workflow'},
                {type:'rh', label:tr('canvas.rhGenerate'), icon:'workflow'},
                {type:'minimax', label:'MiniMax H3', icon:'sparkles'},
                {type:'ltxDirector', label:tr('canvas.ltxDirector'), icon:'film'},
                {type:'video', label:tr('canvas.videoGenerateNode'), icon:'clapperboard'},
                ...(node.type === 'output' ? [] : [{type:'llm', label:'LLM', icon:'message-square-text'}])
            ];
        }
        return [];
    }
    if(CANVAS_GENERATOR_TYPES.includes(node.type) || node.type === 'llm'){
        return [
            {type:'image', label:tr('canvas.imageCard'), icon:'image-plus'},
            {type:'prompt', label:tr('canvas.prompt'), icon:'text-cursor-input'},
            {type:'loop', label:tr('canvas.loopNode'), icon:'repeat-2'},
            {type:'group', label:tr('canvas.group'), icon:'group'},
            {type:'llm', label:'LLM', icon:'message-square-text'}
        ];
    }
    return [];
}
function openLinkCreateMenu(originId, originKind, clientX, clientY){
    if(!window.WorkbenchCanvasCommands?.graphCommand('canvas.graph.create-connected', 'classic')) return false;
    const state = {originId, originKind, point:screenToWorld(clientX, clientY)};
    const options = linkCreateOptions(state);
    if(!options.length) return false;
    linkCreateState = state;
    createMenu.classList.remove('open');
    linkCreateMenu.innerHTML = options.map(opt => `<button class="menu-btn" data-link-create="${escapeAttr(opt.type)}"><i data-lucide="${escapeAttr(opt.icon)}" class="w-4 h-4"></i><span>${escapeHtml(opt.label)}</span></button>`).join('');
    linkCreateMenu.style.left = `${clientX}px`;
    linkCreateMenu.style.top = `${clientY}px`;
    linkCreateMenu.classList.add('open');
    linkCreateMenu.querySelectorAll('[data-link-create]').forEach(btn => {
        btn.onclick = e => {
            e.stopPropagation();
            createLinkedNode(btn.dataset.linkCreate);
        };
    });
    refreshIcons();
    return true;
}
function openGeneratorNodeMenu(nodeId, clientX, clientY){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || !CANVAS_GENERATOR_TYPES.includes(node.type)) return false;
    const el = nodesEl.querySelector(`.node[data-id="${CSS.escape(nodeId)}"]`);
    const rect = el?.getBoundingClientRect();
    const point = screenToWorld(clientX, clientY);
    const inputOptions = linkCreateOptions({originId:nodeId, originKind:'in', point});
    const outputOptions = [
        {type:'output', label:'Output', icon:'circle-dot'},
        ...(CANVAS_IMAGE_OUTPUT_TYPES.includes(node.type) ? [
            {type:'generator', label:tr('canvas.apiGenerate'), icon:'wand-sparkles'},
            {type:'midjourney', label:'Midjourney', icon:'panel-top'},
            {type:'msgen', label:tr('canvas.modelscopeGenerate'), icon:'cloud-lightning'},
            {type:'comfy', label:tr('canvas.comfyGenerate'), icon:'workflow'},
            {type:'minimax', label:'MiniMax H3', icon:'sparkles'},
            {type:'ltxDirector', label:tr('canvas.ltxDirector'), icon:'film'},
            {type:'video', label:tr('canvas.videoGenerateNode'), icon:'clapperboard'}
        ] : [])
    ];
    const buttonsHtml = (options, kind) => `<div class="node-port-menu-grid">${options.map(opt => `<button class="menu-btn" data-link-create="${escapeAttr(opt.type)}" data-link-kind="${kind}" title="${escapeAttr(opt.label)}"><i data-lucide="${escapeAttr(opt.icon)}"></i><span>${escapeHtml(opt.label.replace('生成', ''))}</span></button>`).join('')}</div>`;
    linkCreateState = {originId:nodeId, originKind:'in', point};
    createMenu.classList.remove('open');
    linkCreateMenu.classList.remove('open');
    nodeInputMenu.classList.add('node-port-menu');
    nodeOutputMenu.classList.add('node-port-menu');
    nodeInputMenu.innerHTML = `<div class="menu-section-title">添加输入</div>${buttonsHtml(inputOptions, 'in')}`;
    nodeOutputMenu.innerHTML = `<div class="menu-section-title">添加输出</div>${buttonsHtml(outputOptions, 'out')}`;
    const inputLeft = Math.max(10, (rect?.left || clientX) - 158);
    const outputLeft = Math.min(window.innerWidth - 158, (rect?.right || clientX) + 10);
    const menuTop = Math.max(10, Math.min(window.innerHeight - 260, (rect?.top || clientY) + 36));
    nodeInputMenu.style.left = `${inputLeft}px`;
    nodeInputMenu.style.top = `${menuTop}px`;
    nodeOutputMenu.style.left = `${outputLeft}px`;
    nodeOutputMenu.style.top = `${menuTop}px`;
    nodeInputMenu.classList.add('open');
    nodeOutputMenu.classList.add('open');
    [nodeInputMenu, nodeOutputMenu].forEach(menu => menu.querySelectorAll('[data-link-create]').forEach(btn => {
        btn.onclick = e => {
            e.stopPropagation();
            linkCreateState = {originId:nodeId, originKind:btn.dataset.linkKind || 'in', point};
            createLinkedNode(btn.dataset.linkCreate);
        };
    }));
    refreshIcons();
    return true;
}
function closeLinkCreateMenu(){
    linkCreateMenu.classList.remove('open');
    linkCreateMenu.innerHTML = '';
    nodeInputMenu.classList.remove('open');
    nodeOutputMenu.classList.remove('open');
    nodeInputMenu.classList.remove('node-port-menu');
    nodeOutputMenu.classList.remove('node-port-menu');
    nodeInputMenu.innerHTML = '';
    nodeOutputMenu.innerHTML = '';
    linkCreateState = null;
}
function openImageNodeMenu(nodeId, clientX, clientY){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'image') return;
    closeCreateMenu();
    const kind = mediaKindForNode(node);
    const canPreview = node.url && !isMissingAssetUrl(node.url) && ['image','video'].includes(kind);
    const canEdit = node.url && !isMissingAssetUrl(node.url) && kind === 'image';
    imageNodeMenu.innerHTML = `
        ${canPreview ? `<button class="menu-btn" data-image-preview="${escapeAttr(nodeId)}"><i data-lucide="eye" class="w-4 h-4"></i><span>预览</span></button>` : ''}
        ${canEdit ? `<button class="menu-btn" data-image-edit="${escapeAttr(nodeId)}"><i data-lucide="pencil" class="w-4 h-4"></i><span>编辑</span></button>` : ''}
        <button class="menu-btn" data-image-replace="${escapeAttr(nodeId)}"><i data-lucide="image-plus" class="w-4 h-4"></i><span>替换</span></button>
    `;
    imageNodeMenu.style.left = `${clientX}px`;
    imageNodeMenu.style.top = `${clientY}px`;
    imageNodeMenu.classList.add('open');
    const previewBtn = imageNodeMenu.querySelector('[data-image-preview]');
    if(previewBtn){
        previewBtn.onclick = e => {
            e.stopPropagation();
            closeImageNodeMenu();
            openImageNodePreview(nodeId);
        };
    }
    const editBtn = imageNodeMenu.querySelector('[data-image-edit]');
    if(editBtn){
        editBtn.onclick = e => {
            e.stopPropagation();
            closeImageNodeMenu();
            openImageEditor(nodeId);
        };
    }
    imageNodeMenu.querySelector('[data-image-replace]').onclick = e => {
        e.stopPropagation();
        closeImageNodeMenu();
        pickImageForNode(nodeId);
    };
    refreshIcons();
}
function openImageNodePreview(nodeId){
    const node = nodes.find(n => n.id === nodeId);
    if(!node?.url || isMissingAssetUrl(node.url)) return;
    const kind = mediaKindForNode(node);
    if(!['image','video'].includes(kind)) return;
    openOutputLightbox(node.url, node);
}
function openOutputNodeMenu(nodeId, clientX, clientY){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'output') return;
    closeCreateMenu();
    const imageCount = outputImageUrls(node).length;
    const downloadableCount = outputDownloadableImageUrls(node).length;
    imageNodeMenu.classList.add('output-node-menu');
    imageNodeMenu.innerHTML = `
        <div class="menu-section-title">${tr('canvas.outputGroupActions')}</div>
        <button class="menu-btn" data-output-convert="${escapeAttr(nodeId)}" ${imageCount ? '' : 'disabled'}><i data-lucide="replace" class="w-4 h-4"></i><span>${tr('canvas.outputConvertToInputGroup')}</span></button>
        <button class="menu-btn" data-output-copy="${escapeAttr(nodeId)}" ${imageCount ? '' : 'disabled'}><i data-lucide="copy-plus" class="w-4 h-4"></i><span>${tr('canvas.outputCopyToInputGroup')}</span></button>
        <div class="menu-divider"></div>
        <div class="menu-section-title">${tr('canvas.outputFileActions')}</div>
        <button class="menu-btn" data-output-download="${escapeAttr(nodeId)}" ${downloadableCount ? '' : 'disabled'}><i data-lucide="download" class="w-4 h-4"></i><span>${tr('canvas.outputDownloadAllImages')}</span></button>
    `;
    const menuWidth = 260;
    imageNodeMenu.style.left = `${Math.max(10, Math.min(window.innerWidth - menuWidth - 10, clientX))}px`;
    imageNodeMenu.style.top = `${clientY}px`;
    imageNodeMenu.classList.add('open');
    const convertBtn = imageNodeMenu.querySelector('[data-output-convert]');
    if(convertBtn){
        convertBtn.onclick = e => {
            e.stopPropagation();
            convertOutputNodeToInputGroup(nodeId);
            closeImageNodeMenu();
        };
    }
    imageNodeMenu.querySelector('[data-output-copy]').onclick = e => {
        e.stopPropagation();
        copyOutputNodeToInputGroup(nodeId);
        closeImageNodeMenu();
    };
    const downloadBtn = imageNodeMenu.querySelector('[data-output-download]');
    if(downloadBtn){
        downloadBtn.onclick = e => {
            e.stopPropagation();
            downloadOutputNodeImages(nodeId);
            closeImageNodeMenu();
        };
    }
    refreshIcons();
}
function closeImageNodeMenu(){
    imageNodeMenu.classList.remove('open');
    imageNodeMenu.classList.remove('output-node-menu');
    imageNodeMenu.innerHTML = '';
}
function outputImageUrls(node){
    return WorkbenchCanvasMediaTools.outputDownloadProjection(node, {kindOf:mediaKindForOutputItem, outputValue:outputUrlValue, isMissing:isMissingAssetUrl}).urls;
}
function outputDownloadableImageUrls(node){
    return WorkbenchCanvasMediaTools.outputDownloadProjection(node, {kindOf:mediaKindForOutputItem, outputValue:outputUrlValue, isMissing:isMissingAssetUrl}).downloadable;
}
function groupImageItems(group){
    return window.WorkbenchCanvasMediaTools.groupImageItems(group, id => nodes.find(n => n.id === id), {
        kindOf:mediaKindForNode,
        isMissing:isMissingAssetUrl,
        outputName:outputImageName,
    });
}
function extensionFromNameOrUrl(name='', url=''){
    return window.WorkbenchCanvasMediaTools.extensionFromNameOrUrl(name, url);
}
function safeDownloadFileName(name, fallback='image.png'){
    return window.WorkbenchCanvasMediaTools.safeDownloadFileName(name, fallback);
}
function downloadNameForGroupImage(item, index=0){
    return window.WorkbenchCanvasMediaTools.downloadNameForGroupImage(item, index, outputImageName);
}
function createInputGroupFromOutput(node, point){
    const urls = outputImageUrls(node);
    if(!node || !urls.length) return null;
    const projection = WorkbenchCanvasMediaTools.inputGroupProjection(urls, point || {x:Number(node.x || 0), y:Number(node.y || 0)}, uid, outputImageName);
    if(!projection) return null;
    nodes.push(...projection.nodes);
    return projection.group;
}
function convertOutputNodeToInputGroup(nodeId){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'output') return;
    if(!outputImageUrls(node).length) return;
    pushUndo();
    const downstream = WorkbenchCanvasMediaTools.downstreamTargetIds(nodeId, connections);
    const group = createInputGroupFromOutput(node, {x:Number(node.x || 0), y:Number(node.y || 0)});
    if(!group) return;
    const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[nodeId]});
    nodes = remaining.nodes;
    connections = remaining.connections;
    downstream.forEach(toId => {
        if(canConnect(group.id, toId) && !connections.some(c => c.from === group.id && c.to === toId)){
            connections.push({id:uid('c'), from:group.id, to:toId});
        }
    });
    selected.clear();
    selected.add(group.id);
    syncGeneratorInputs();
    refreshGeneratorInputViews();
    render();
    scheduleSave();
}
function copyOutputNodeToInputGroup(nodeId){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'output') return;
    if(!outputImageUrls(node).length) return;
    pushUndo();
    const group = createInputGroupFromOutput(node, {x:Number(node.x || 0) + 36, y:Number(node.y || 0) + 36});
    if(!group) return;
    selected.clear();
    selected.add(group.id);
    syncGeneratorInputs();
    refreshGeneratorInputViews();
    render();
    scheduleSave();
}
async function downloadOutputNodeImages(nodeId){
    const node = nodes.find(n => n.id === nodeId);
    const urls = outputDownloadableImageUrls(node);
    if(!node || !urls.length){
        alert(tr('canvas.outputDownloadEmpty'));
        return;
    }
    try {
        const filename = WorkbenchCanvasMediaTools.archiveDownloadFilename(canvas?.title, node.id, 'canvas-output');
        const payload = WorkbenchCanvasMediaTools.archiveDownloadPayload(urls, filename);
        const res = await fetch('/api/canvas-assets/download', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(payload)
        });
        if(!res.ok) throw new Error(await responseErrorMessage(res, tr('canvas.outputDownloadEmpty')));
        const blob = await res.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } catch(err) {
        alert(err.message || tr('canvas.outputDownloadEmpty'));
    }
}
async function downloadGroupNodeImages(groupId){
    const group = nodes.find(n => n.id === groupId);
    const items = groupImageItems(group);
    if(!group || !items.length){
        alert(tr('canvas.outputDownloadEmpty'));
        return;
    }
    const filename = WorkbenchCanvasMediaTools.archiveDownloadFilename(canvas?.title, group.id, 'canvas-group');
    const payload = WorkbenchCanvasMediaTools.archiveDownloadPayload(items.map(item => item.url), filename, {items:items.map((item, index) => ({url:item.url, name:downloadNameForGroupImage(item, index)}))});
    try {
        const res = await fetch('/api/canvas-assets/download', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(payload)
        });
        if(!res.ok) throw new Error(await responseErrorMessage(res, tr('canvas.outputDownloadEmpty')));
        const blob = await res.blob();
        const href = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = href;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(href), 1200);
    } catch(err) {
        alert(err.message || tr('canvas.outputDownloadEmpty'));
    }
}
