// Classic execution (card R4-33): runLLMNode's Canvas lifecycle/state writes
// route through the shared classic execution host; the LLM call itself stays
// page-side. Node-state, render, persist and error surfacing no longer touch
// Canvas state directly.
let classicExecutionHost = null;
let classicChatExecutionHost = null;
function ensureClassicExecutionHost(){
    if(!classicExecutionHost){
        classicExecutionHost = window.WorkbenchCanvasClassicExecutionHost.create({
            markRunning: (node, running) => { if(node) node.running = Boolean(running); },
            writeOutputText: (node, text) => { if(node) node.outputText = text; },
            setRunStatus: (node, status, error) => { if(node){ node.runStatus = status; node.runError = error; } },
            render: (node, output) => output ? refreshRunNodes(node, output) : refreshNodes([node.id]),
            save: () => scheduleSave(),
            notifyError: (message) => alert(message),
        });
    }
    return classicExecutionHost;
}
function ensureClassicChatExecutionHost(){
    if(!classicChatExecutionHost){
        classicChatExecutionHost = window.WorkbenchCanvasClassicExecutionHost.createChat({
            appendMessage: (node, message) => { if(node){ node.messages = node.messages || []; node.messages.push(message); } },
            clearChatInput: (node) => { if(node) node.chatInput = ''; },
            writeOutputText: (node, text) => { if(node) node.outputText = text; },
            markRunning: (node, running) => { if(node) node.running = Boolean(running); },
            render: (node) => refreshNodes([node.id]),
            save: () => scheduleSave(),
            notifyError: (message) => alert(message),
        });
    }
    return classicChatExecutionHost;
}
async function runLLMNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runLLMNode(nodeId, opts); }
// 判断是不是「链尾」节点：没有下游生成节点（直接相连或经 Output 中转都算）
function isTerminalGenerator(nodeId){
    const GEN_TYPES = canvasRunTypes();
    for(const c of connections.filter(c => c.from === nodeId)){
        const t = nodes.find(n => n.id === c.to);
        if(!t) continue;
        if(GEN_TYPES.includes(t.type)) return false;
        if(t.type === 'output'){
            for(const c2 of connections.filter(cc => cc.from === t.id)){
                const t2 = nodes.find(n => n.id === c2.to);
                if(t2 && GEN_TYPES.includes(t2.type)) return false;
            }
        }
    }
    return true;
}
function findLoopCascadeTarget(loopId){
    const runTypes = canvasRunTypes();
    const seen = new Set();
    const candidates = [];
    const walk = (id, depth=0) => {
        if(seen.has(id)) return;
        seen.add(id);
        connections.filter(c => c.from === id).forEach(c => {
            const next = nodes.find(n => n.id === c.to);
            if(!next) return;
            if(runTypes.includes(next.type)){
                candidates.push({id:next.id, depth:depth + 1, terminal:isTerminalGenerator(next.id)});
            }
            walk(next.id, depth + 1);
        });
    };
    walk(loopId);
    const terminal = candidates.filter(c => c.terminal).sort((a, b) => b.depth - a.depth)[0];
    return (terminal || candidates.sort((a, b) => b.depth - a.depth)[0])?.id || '';
}
function cascadeBtnHtml(node){
    // 仅链尾节点显示一键运行
    if(!isTerminalGenerator(node.id)) return '';
    // 也要求至少有上游生成节点，否则没意义
    const order = ensureClassicCascadeOrchestrator().computeCascadeOrder(node.id);
    const loop = resolveCascadeLoop(node.id);
    if(order.length <= 1 && !loop) return '';
    const suffix = loop ? ` × ${loop.count} ${tr('canvas.loopRounds')}` : '';
    if(ensureClassicCascadeOrchestrator().isCascadeActive(node.id)){
        const stopping = ensureClassicCascadeOrchestrator().isCascadeStopping(node.id);
        return `<button class="gen-cascade-btn gen-cascade-stop" type="button" data-cascade-stop="${node.id}" ${stopping ? 'disabled' : ''}><i data-lucide="square" class="w-4 h-4"></i><span>${stopping ? '停止中…' : '停止运行'}</span></button>`;
    }
    return `<button class="gen-cascade-btn" type="button" data-cascade="${node.id}" title="一键运行整条工作流（追溯所有上游生成节点）"><i data-lucide="play-circle" class="w-4 h-4"></i><span>一键运行 ${order.length} 个节点${suffix}</span></button>`;
}
function retryBarHtml(node){
    // 只在一键运行模式中失败才显示；普通单节点失败直接弹 alert，不显示这条
    if(node.runStatus !== 'failed' || !node._cascadeFailed) return '';
    return `<div class="node-retry-bar" data-retry-bar>
        <span class="node-retry-msg" title="${escapeAttr(node.runError||'')}">${escapeHtml((node.runError||tr('canvas.generationFailed')).slice(0,60))}</span>
        <button class="node-retry-btn" type="button" data-retry="${node.id}">重试</button>
        <button class="node-stop-btn" type="button" data-stop="${node.id}">停止</button>
    </div>`;
}
// —— 一键运行：从目标节点反向追溯到所有上游生成节点，按拓扑顺序串行执行 ——
// 失败重试：从该节点继续往下游跑
async function runLLMChat(nodeId){ return ensureClassicExecutorRuntime().runLLMChat(nodeId); }

function deleteNode(id, event){
    event?.stopPropagation();
    pushUndo();
    const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[id]});
    nodes = remaining.nodes;
    connections = remaining.connections;
    selected.delete(id);
    render();
    scheduleSave();
}
function clearNodeContentBeforeDelete(id){
    const node = nodes.find(n => n.id === id);
    if(!node) return false;
    if(node.type === 'image' && node.url){
        pushUndo();
        node.url = '';
        node.mediaKind = 'image';
        node.name = tr('canvas.imageCard');
        render();
        scheduleSave();
        return true;
    }
    if(node.type === 'output' && ((node.images || []).length || (node._pending || []).length)){
        pushUndo();
        node.images = [];
        node._pending = [];
        node.imageComparisons = {};
        refreshNodes([node.id]);
        scheduleSave();
        return true;
    }
    return false;
}
function canUseVersionedBlankImageDelete(node){
    if(!canUseVersionedImageCreation() || !node || node.type !== 'image' || node.url) return false;
    // Group membership retains page-specific visual semantics. Do not route it
    // through the narrow service until the complete group mutation contract is
    // migrated; standalone blank Images have no such compatibility state.
    return !nodes.some(candidate => Array.isArray(candidate.items) && candidate.items.includes(node.id));
}
async function commitVersionedBlankImagePosition(drag){
    const node = drag?.node;
    const changed = Number(node?.x) !== Number(drag?.ox) || Number(node?.y) !== Number(drag?.oy);
    if(drag?.isLocalCopy || (drag?.children || []).length || !changed || !canUseVersionedBlankImageDelete(node)) return false;
    try {
        const result = await window.WorkbenchNodeClient.update(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
            position:{x:Number(node.x) || 0, y:Number(node.y) || 0},
        }, CLIENT_ID);
        adoptCanvasRevision(result.canvas_revision, Date.now());
    } catch(error) {
        // Position is a canonical expected-revision write. Revert the visual
        // optimistic move on failure instead of issuing a raw Canvas save.
        console.error('Versioned blank Image position update failed', error);
        node.x = drag.ox;
        node.y = drag.oy;
        applyCanvasRuntimeNodeMove(node);
        render();
        setStatus('Move failed');
    }
    return true;
}
function canUseVersionedBlankPromptDelete(node){
    if(!canUseVersionedImageCreation() || !node || node.type !== 'prompt' || String(node.text || '').trim()) return false;
    if(connections.some(connection => connection.from === node.id || connection.to === node.id)) return false;
    return !nodes.some(candidate => Array.isArray(candidate.items) && candidate.items.includes(node.id));
}
async function commitVersionedBlankPromptPosition(drag){
    const node = drag?.node;
    const changed = Number(node?.x) !== Number(drag?.ox) || Number(node?.y) !== Number(drag?.oy);
    if(drag?.isLocalCopy || (drag?.children || []).length || !changed || !canUseVersionedBlankPromptDelete(node)) return false;
    try {
        const result = await window.WorkbenchNodeClient.update(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
            position:{x:Number(node.x) || 0, y:Number(node.y) || 0},
        }, CLIENT_ID);
        adoptCanvasRevision(result.canvas_revision, Date.now());
    } catch(error) {
        console.error('Versioned blank Prompt position update failed', error);
        node.x = drag.ox;
        node.y = drag.oy;
        applyCanvasRuntimeNodeMove(node);
        render();
        setStatus('Move failed');
    }
    return true;
}
function canUseVersionedBlankLoopDelete(node){
    if(!canUseVersionedImageCreation() || !node || node.type !== 'loop') return false;
    if(Number(node.count || 3) !== 3 || node.mode === 'parallel' || node.showPrompt || node.imageInput || node.videoInput) return false;
    if(Number(node.loopStart || 1) !== 1 || Number(node.imageBatchSize || 1) !== 1 || Number(node.videoBatchSize || 1) !== 1) return false;
    if(String(node.variablePrompt || '').trim() || String(node.fixedPrompt || '').trim()) return false;
    if(connections.some(connection => connection.from === node.id || connection.to === node.id)) return false;
    return !nodes.some(candidate => Array.isArray(candidate.items) && candidate.items.includes(node.id));
}
function canUseVersionedBlankOutputDelete(node){
    if(!canUseVersionedImageCreation() || !node || node.type !== 'output') return false;
    if((node.images || []).length || (node._pending || []).length || Object.keys(node.imageComparisons || {}).length) return false;
    if(connections.some(connection => connection.from === node.id || connection.to === node.id)) return false;
    return !nodes.some(candidate => Array.isArray(candidate.items) && candidate.items.includes(node.id));
}
function canUseVersionedEmptyGroupDelete(node){
    if(!canUseVersionedImageCreation() || !node || node.type !== 'group' || (node.items || []).length) return false;
    if(connections.some(connection => connection.from === node.id || connection.to === node.id)) return false;
    return !nodes.some(candidate => Array.isArray(candidate.items) && candidate.items.includes(node.id));
}
async function commitVersionedBlankLoopPosition(drag){
    const node = drag?.node;
    const changed = Number(node?.x) !== Number(drag?.ox) || Number(node?.y) !== Number(drag?.oy);
    if(drag?.isLocalCopy || (drag?.children || []).length || !changed || !canUseVersionedBlankLoopDelete(node)) return false;
    try {
        const result = await window.WorkbenchNodeClient.update(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
            position:{x:Number(node.x) || 0, y:Number(node.y) || 0},
        }, CLIENT_ID);
        adoptCanvasRevision(result.canvas_revision, Date.now());
    } catch(error) {
        console.error('Versioned blank Loop position update failed', error);
        node.x = drag.ox;
        node.y = drag.oy;
        applyCanvasRuntimeNodeMove(node);
        render();
        setStatus('Move failed');
    }
    return true;
}
async function commitVersionedBlankOutputPosition(drag){
    const node = drag?.node;
    const changed = Number(node?.x) !== Number(drag?.ox) || Number(node?.y) !== Number(drag?.oy);
    if(drag?.isLocalCopy || (drag?.children || []).length || !changed || !canUseVersionedBlankOutputDelete(node)) return false;
    try {
        const result = await window.WorkbenchNodeClient.update(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
            position:{x:Number(node.x) || 0, y:Number(node.y) || 0},
        }, CLIENT_ID);
        adoptCanvasRevision(result.canvas_revision, Date.now());
    } catch(error) {
        console.error('Versioned blank Output position update failed', error);
        node.x = drag.ox;
        node.y = drag.oy;
        applyCanvasRuntimeNodeMove(node);
        render();
        setStatus('Move failed');
    }
    return true;
}
async function commitVersionedEmptyGroupPosition(drag){
    const node = drag?.node;
    const changed = Number(node?.x) !== Number(drag?.ox) || Number(node?.y) !== Number(drag?.oy);
    if(drag?.isLocalCopy || (drag?.children || []).length || !changed || !canUseVersionedEmptyGroupDelete(node)) return false;
    try {
        const result = await window.WorkbenchNodeClient.update(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
            position:{x:Number(node.x) || 0, y:Number(node.y) || 0},
        }, CLIENT_ID);
        adoptCanvasRevision(result.canvas_revision, Date.now());
    } catch(error) {
        console.error('Versioned empty Group position update failed', error);
        node.x = drag.ox;
        node.y = drag.oy;
        applyCanvasRuntimeNodeMove(node);
        render();
        setStatus('Move failed');
    }
    return true;
}
async function commitVersionedBlankClassicPosition(drag){
    if(await commitVersionedBlankImagePosition(drag)) return true;
    if(await commitVersionedBlankPromptPosition(drag)) return true;
    if(await commitVersionedBlankLoopPosition(drag)) return true;
    if(await commitVersionedBlankOutputPosition(drag)) return true;
    return commitVersionedEmptyGroupPosition(drag);
}
async function deleteVersionedBlankImageNode(id){
    const node = nodes.find(item => item.id === id);
    if(!canUseVersionedBlankImageDelete(node)) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.remove(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
        }, CLIENT_ID);
        const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[node.id]});
        nodes = remaining.nodes;
        connections = remaining.connections;
        selected.delete(node.id);
        undoStack.push(undoSnapshot);
        if(undoStack.length > UNDO_MAX) undoStack.shift();
        adoptCanvasRevision(result.canvas_revision, Date.now());
        render();
    } catch(error) {
        // A stale or rejected service mutation must not fall through to a raw
        // adapter save, which could overwrite the canonical revision.
        console.error('Versioned blank Image deletion failed', error);
        setStatus('Delete failed');
    }
    return true;
}
async function deleteVersionedBlankPromptNode(id){
    const node = nodes.find(item => item.id === id);
    if(!canUseVersionedBlankPromptDelete(node)) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.remove(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
        }, CLIENT_ID);
        const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[node.id]});
        nodes = remaining.nodes;
        connections = remaining.connections;
        selected.delete(node.id);
        undoStack.push(undoSnapshot);
        if(undoStack.length > UNDO_MAX) undoStack.shift();
        adoptCanvasRevision(result.canvas_revision, Date.now());
        render();
    } catch(error) {
        console.error('Versioned blank Prompt deletion failed', error);
        setStatus('Delete failed');
    }
    return true;
}
async function deleteVersionedBlankLoopNode(id){
    const node = nodes.find(item => item.id === id);
    if(!canUseVersionedBlankLoopDelete(node)) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.remove(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
        }, CLIENT_ID);
        const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[node.id]});
        nodes = remaining.nodes;
        connections = remaining.connections;
        selected.delete(node.id);
        undoStack.push(undoSnapshot);
        if(undoStack.length > UNDO_MAX) undoStack.shift();
        adoptCanvasRevision(result.canvas_revision, Date.now());
        render();
    } catch(error) {
        console.error('Versioned blank Loop deletion failed', error);
        setStatus('Delete failed');
    }
    return true;
}
async function deleteVersionedBlankOutputNode(id){
    const node = nodes.find(item => item.id === id);
    if(!canUseVersionedBlankOutputDelete(node)) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.remove(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
        }, CLIENT_ID);
        const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[node.id]});
        nodes = remaining.nodes;
        connections = remaining.connections;
        selected.delete(node.id);
        undoStack.push(undoSnapshot);
        if(undoStack.length > UNDO_MAX) undoStack.shift();
        adoptCanvasRevision(result.canvas_revision, Date.now());
        render();
    } catch(error) {
        console.error('Versioned blank Output deletion failed', error);
        setStatus('Delete failed');
    }
    return true;
}
async function deleteVersionedEmptyGroupNode(id){
    const node = nodes.find(item => item.id === id);
    if(!canUseVersionedEmptyGroupDelete(node)) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.remove(canvas.id, node.id, {
            project_id:canvas.project,
            expected_revision:currentCanvasRevision(),
        }, CLIENT_ID);
        const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[node.id]});
        nodes = remaining.nodes;
        connections = remaining.connections;
        selected.delete(node.id);
        undoStack.push(undoSnapshot);
        if(undoStack.length > UNDO_MAX) undoStack.shift();
        adoptCanvasRevision(result.canvas_revision, Date.now());
        render();
    } catch(error) {
        console.error('Versioned empty Group deletion failed', error);
        setStatus('Delete failed');
    }
    return true;
}
async function deleteNodeFromButton(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    if(clearNodeContentBeforeDelete(id)) return;
    if(await deleteVersionedBlankImageNode(id)) return;
    if(await deleteVersionedBlankPromptNode(id)) return;
    if(await deleteVersionedBlankLoopNode(id)) return;
    if(await deleteVersionedBlankOutputNode(id)) return;
    if(await deleteVersionedEmptyGroupNode(id)) return;
    deleteNode(id, event);
}
function deleteConnection(id, event){
    event?.preventDefault();
    event?.stopPropagation();
    pushUndo();
    connections = window.WorkbenchCanvasGraphFragment.removeConnection({connections, connectionId:id});
    if(hoveredConnectionId === id) hoveredConnectionId = '';
    syncGeneratorInputs();
    render();
    scheduleSave();
}
function outputDownloadName(url){
    return WorkbenchCanvasMediaTools.outputDownloadName(url);
}
function isVideoUrl(url){
    return window.WorkbenchCanvasMediaKind.isKindForUrl(canvasOriginalMediaUrl(url), 'video', {includeFlv:true});
}
function mediaKindForOutputItem(item){
    return window.WorkbenchCanvasMediaKind.kindForItem(item, {
        originalUrl:value => canvasOriginalMediaUrl(outputUrlValue(value)),
        includeFlv:true,
    });
}
function formatRunDuration(ms){
    return WorkbenchCanvasMediaTools.formatRunDuration(ms);
}
function nowMs(){ return Date.now(); }
function outputUrlValue(item){
    return WorkbenchCanvasMediaTools.outputUrlValue(item);
}
function isMissingAssetUrl(url){ return ensureClassicAssetRuntime().isMissingAssetUrl(url); }
function missingAssetHtml(url, compact=false){ return ensureClassicAssetRuntime().missingAssetHtml(url, compact); }
function outputMetaFor(url, out){
    return WorkbenchCanvasMediaTools.outputMetaFor(out?.images, url);
}
function runSnapshot(node, prompt, refs=[]){ return ensureClassicExecutorRuntime().runSnapshot(node, prompt, refs); }
function runPlatformLabel(run){ return ensureClassicExecutorRuntime().runPlatformLabel(run); }
function runTaskLabel(run){ return ensureClassicExecutorRuntime().runTaskLabel(run); }
function comfyLabelFromWorkflow(workflow){
    const name = String(workflow || '').toLowerCase();
    if(!name) return '';
    if(name === 'z-image.json') return tr('canvas.comfyText');
    if(name === 'z-image-enhance.json' || name === 'upscale.json') return tr('canvas.comfyEnhance');
    if(name === 'flux2-klein.json') return tr('canvas.comfyEdit');
    return workflow;
}
function logTaskLabel(log){
    const req = log?.request || {};
    if(log?.platform === 'ComfyUI'){
        const byWorkflow = comfyLabelFromWorkflow(req.workflow_json || req.workflow);
        if(byWorkflow) return byWorkflow;
    }
    return log?.model || '-';
}
async function importWorkflowAssetUrl(url, name='workflow'){ return ensureClassicAssetRuntime().importWorkflowAssetUrl(url, name); }
function openCanvasLog(event){
    event?.preventDefault?.();
    event?.stopPropagation?.();
    event?.stopImmediatePropagation?.();
    const modal = document.getElementById('logModal') || (typeof logModal !== 'undefined' ? logModal : null);
    const list = document.getElementById('logList') || (typeof logList !== 'undefined' ? logList : null);
    modal?.classList.add('open');
    if(list && !list.innerHTML) list.innerHTML = `<div class="log-empty">${tr('canvas.noLogs')}</div>`;
    try {
        renderCanvasLog();
    } catch(err) {
        console.error('renderCanvasLog failed', err);
        if(list) list.innerHTML = `<div class="log-empty">${escapeHtml(err?.message || String(err))}</div>`;
    }
}
function closeCanvasLog(){
    const modal = document.getElementById('logModal') || (typeof logModal !== 'undefined' ? logModal : null);
    modal?.classList.remove('open');
}
window.openCanvasLog = openCanvasLog;
window.closeCanvasLog = closeCanvasLog;
function makePending(id, run, task={}){
    return {id, startedAt:nowMs(), run, ...task};
}
function makePendingForRun(id, run, node, options={}){ return ensureClassicExecutorRuntime().makePendingForRun(id, run, node, options); }
function mergeGeneratedOutputs(node, outputs, append=false){
    if(!node) return;
    const keepGeneratedMedia = ['rh','ltxDirector','video','minimax'].includes(node.type);
    const clean = (outputs || []).map(item => {
        const url = outputUrlValue(item);
        if(!url) return null;
        const kind = ['video','minimax'].includes(node.type)
            ? 'video'
            : ['rh','ltxDirector'].includes(node.type) && isVideoUrl(url)
                ? 'video'
                : mediaKindForOutputItem(item);
        if(!keepGeneratedMedia && kind !== 'image') return null;
        return kind === 'image' ? url : {url, kind};
    }).filter(Boolean);
    if(!append){
        node.generatedOutputs = clean;
        syncConnectedOutputsFromGenerated(node, clean);
        return;
    }
    const seen = new Set((node.generatedOutputs || []).map(outputUrlValue).filter(Boolean));
    const added = clean.filter(item => {
        const url = outputUrlValue(item);
        return url && !seen.has(url) && seen.add(url);
    });
    node.generatedOutputs = [...(node.generatedOutputs || []), ...added];
    syncConnectedOutputsFromGenerated(node, added);
}
function pendingById(out, id){
    return (out?._pending || []).find(p => p.id === id) || null;
}
function collectRunMetas(out, ids){
    return (ids || []).map(id => pendingById(out, id)).filter(Boolean).map(p => ({
        runMs: nowMs() - Number(p.startedAt || nowMs()),
        run: p.run || {},
    }));
}
function collectRunMeta(out, id){
    return collectRunMetas(out, [id])[0] || {runMs:0, run:{}};
}
function findOutputByPendingId(pendingId){
    return nodes.find(n => n.type === 'output' && (n._pending || []).some(p => p.id === pendingId));
}
function findPendingTask(taskId){
    for(const out of nodes.filter(n => n.type === 'output')){
        const pending = (out._pending || []).find(p => p.canvasTaskId === taskId);
        if(pending) return {out, pending};
    }
    return null;
}
async function createCanvasImageTask(payload, options={}){ return ensureClassicExecutorRuntime().createCanvasImageTask(payload, options); }
async function createCanvasComfyTask(payload, options={}){ return ensureClassicExecutorRuntime().createCanvasComfyTask(payload, options); }
async function waitCanvasComfyTaskResult(taskId, options={}){ return ensureClassicExecutorRuntime().waitCanvasComfyTaskResult(taskId, options); }
async function runQueuedComfyGenerate(payload, options={}){ return ensureClassicExecutorRuntime().runQueuedComfyGenerate(payload, options); }
function extractUpstreamTaskId(text){
    const match = String(text || '').match(/(?:task_id|taskId|task id)\s*[=:：]\s*([A-Za-z0-9_.:-]+)/i);
    return match ? match[1] : '';
}
function providerIdForPending(pending){
    return pending?.providerId
        || pending?.run?.request?.provider_id
        || pending?.run?.node?.apiProvider
        || pending?.run?.node?.provider_id
        || 'comfly';
}
function completeRecoverPendingOutput(out, pending, result){
    if(!out || !pending || !result) return;
    const images = result.images || [];
    if(!images.length) return;
    const meta = {
        runMs: nowMs() - Number(pending.startedAt || nowMs()),
        run: pending.run || {},
    };
    meta.run.request = requestMetaFromResult(result);
    out._pending = (out._pending || []).filter(p => p.id !== pending.id);
    appendOutputImages(out, images, meta.run?.refs?.[0], [meta]);
    const gen = nodes.find(n => n.id === meta.run?.node?.id);
    const executionHost = gen ? ensureClassicExecutionHost() : null;
    if(gen){
        mergeGeneratedOutputs(gen, images, Boolean(pending.appendGenerated));
        executionHost.setRunStatus(gen, 'done', '');
        executionHost.markRunning(gen, false);
    }
    addGenerationLog({run:meta.run, outputs:images, runMs:meta.runMs || 0});
    if(gen) executionHost.render(gen, out);
    if(gen) executionHost.save();
}
async function queryRecoverPendingOutput(pendingId){
    const out = findOutputByPendingId(pendingId);
    const pending = pendingById(out, pendingId);
    if(!out || !pending || pending.querying) return;
    const taskId = pending.recoverTaskId || extractUpstreamTaskId(pending.error || '');
    if(!taskId){
        showErrorModal('没有任务 ID，无法查询结果', tr('canvas.apiFailed'));
        return;
    }
    pending.querying = true;
    pending.recoverTaskId = taskId;
    refreshNodes([out.id]);
    try {
        const res = await fetch('/api/image-task-query', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({provider_id:providerIdForPending(pending), task_id:taskId})
        });
        if(!res.ok) throw new Error(await responseErrorMessage(res, '查询失败'));
        const data = await res.json();
        if(data.status === 'succeeded'){
            completeRecoverPendingOutput(out, pending, data);
            return;
        }
        if(data.status === 'failed'){
            pending.error = data.error || tr('canvas.generationFailed');
            showErrorModal(pending.error, tr('canvas.apiFailed'));
        } else {
            pending.error = data.message || '任务仍在生成中，请稍后再查询';
            setStatus(pending.error);
        }
    } catch(err) {
        pending.error = err.message || '查询失败';
        showErrorModal(pending.error, tr('canvas.apiFailed'));
    } finally {
        const latest = pendingById(out, pendingId);
        if(latest){
            latest.querying = false;
            refreshNodes([out.id]);
            scheduleSave();
        }
    }
}
function sleep(ms){ return new Promise(resolve => setTimeout(resolve, ms)); }
async function pollCanvasImageTask(taskId, options={}){ return ensureClassicExecutorRuntime().pollCanvasImageTask(taskId, options); }
async function waitCanvasImageTaskResult(taskId, options={}){ return ensureClassicExecutorRuntime().waitCanvasImageTaskResult(taskId, options); }
function completeCanvasImageTask(taskId, result){
    const found = findPendingTask(taskId);
    if(!found) return;
    const {out, pending} = found;
    const meta = {
        runMs: nowMs() - Number(pending.startedAt || nowMs()),
        run: pending.run || {},
    };
    meta.run.request = requestMetaFromResult(result);
    const images = result.images || [];
    out._pending = (out._pending || []).filter(p => p.id !== pending.id);
    appendOutputImages(out, images, meta.run?.refs?.[0], [meta]);
    const gen = nodes.find(n => n.id === meta.run?.node?.id);
    const executionHost = gen ? ensureClassicExecutionHost() : null;
    if(gen){
        mergeGeneratedOutputs(gen, images, Boolean(pending.appendGenerated));
        executionHost.setRunStatus(gen, 'done', '');
        executionHost.markRunning(gen, false);
    }
    addGenerationLog({run:meta.run, outputs:images, runMs:meta.runMs || 0});
    if(gen) executionHost.render(gen, out);
    if(gen) executionHost.save();
}
function failCanvasImageTask(taskId, message, taskData={}){ return ensureClassicExecutorRuntime().failCanvasImageTask(taskId, message, taskData); }
function resumeCanvasImageTasks(){
    nodes.filter(n => n.type === 'output').forEach(out => {
        (out._pending || []).forEach(p => {
            if(p.canvasTaskType === 'online-image' && p.canvasTaskId && !p.failed) pollCanvasImageTask(p.canvasTaskId, {cascadeTargetId:p.cascadeTargetId || ''});
        });
    });
}
