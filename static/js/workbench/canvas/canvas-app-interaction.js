function groupSelectedImages(){
    if(!window.WorkbenchCanvasCommands?.selectionCommand('canvas.selection.group', 'classic')) return;
    if(!ensureCanvas()) return;
    const targets = [...selected].map(id => nodes.find(n => n.id === id)).filter(n => n?.type === 'image' || n?.type === 'prompt');
    let group;
    pushUndo();
    if(targets.length){
        const box = nodeBounds(targets.map(n => n.id));
        group = {id:uid('grp'), type:'group', x:box.x - 24, y:box.y - 58, w:box.w + 48, h:box.h + 90, items:targets.map(n => n.id)};
    } else {
        const p = defaultPoint(0, 0);
        group = {id:uid('grp'), type:'group', x:p.x, y:p.y, w:300, h:220, items:[]};
    }
    window.WorkbenchLegacyCanvasMutation.appendNode(nodes, group);
    if(targets.length) handoffExistingInputsToGroup(group, targets);
    selected.clear();
    selected.add(group.id);
    syncGeneratorInputs();
    refreshGeneratorInputViews();
    render();
    scheduleSave();
}
function nodeBounds(ids){
    const rects = ids.map(id => {
        const n = nodes.find(item => item.id === id);
        const el = nodesEl.querySelector(`.node[data-id="${id}"]`);
        if(!n) return null;
        return {x:n.x, y:n.y, w:el?.offsetWidth || n.w || 260, h:el?.offsetHeight || n.h || 220};
    }).filter(Boolean);
    const x1 = Math.min(...rects.map(r => r.x));
    const y1 = Math.min(...rects.map(r => r.y));
    const x2 = Math.max(...rects.map(r => r.x + r.w));
    const y2 = Math.max(...rects.map(r => r.y + r.h));
    return {x:x1, y:y1, w:x2 - x1, h:y2 - y1};
}

function startSelection(e){
    e.preventDefault();
    e.stopPropagation();
    if(document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    selectDrag = {sx:e.clientX, sy:e.clientY, x:e.clientX, y:e.clientY};
    document.body.classList.add('canvas-selecting');
    selectionBox.style.display = 'block';
    updateSelectionBox(e.clientX, e.clientY);
    ensureInteractionController().begin({kind:'box-selection', onMove:e2 => updateSelectionBox(e2.clientX, e2.clientY), onEnd:finishSelection});
}
function updateSelectionBox(x, y){
    if(!selectDrag) return;
    selectDrag.x = x; selectDrag.y = y;
    const left = Math.min(selectDrag.sx, x);
    const top = Math.min(selectDrag.sy, y);
    selectionBox.style.left = `${left}px`;
    selectionBox.style.top = `${top}px`;
    selectionBox.style.width = `${Math.abs(x - selectDrag.sx)}px`;
    selectionBox.style.height = `${Math.abs(y - selectDrag.sy)}px`;
}
function finishSelection(){
    if(!selectDrag) return;
    const rect = selectionBox.getBoundingClientRect();
    selectionBox.style.display = 'none';
    const selectedIds = [];
    nodesEl.querySelectorAll('.node').forEach(el => {
        const r = el.getBoundingClientRect();
        const overlaps = r.left < rect.right && r.right > rect.left && r.top < rect.bottom && r.bottom > rect.top;
        if(overlaps) selectedIds.push(el.dataset.id);
    });
    // The overlap calculation is adapter-specific DOM work; the completed
    // selection transition belongs to the default Unified runtime.
    if(!applyCanvasRuntimeSelection(selectedIds)) selected.replace(selectedIds);
    selectDrag = null;
    document.body.classList.remove('canvas-selecting');
    ensureInteractionController().end();
    render();
    if(workflowTransferModal?.classList.contains('open')) updateWorkflowTransferMeta();
}
let floatingActionBar = null;
let canvasWorkspaceSession = null;
function ensureCanvasWorkspaceSession(){
    if(canvasWorkspaceSession || !window.WorkbenchCanvasWorkspaceSession) return canvasWorkspaceSession;
    canvasWorkspaceSession = window.WorkbenchCanvasWorkspaceSession.create({
        getSelection:() => [...selected],
        getCanvas:() => canvas,
    });
    return canvasWorkspaceSession;
}
function openSelectedWorkspace(nodeId){
    const session = ensureCanvasWorkspaceSession();
    if(!session) return false;
    session.openFromSelection(nodeId);
    return true;
}
function ensureFloatingActionBar(){
    if(floatingActionBar || !window.WorkbenchFloatingActionBar || !selectionHub) return floatingActionBar;
    floatingActionBar = window.WorkbenchFloatingActionBar.create({
        document,
        container: selectionHub,
        actions: [
            {id:'open', label:langIsEn() ? 'Open' : '打开', icon:'external-link', order:10, when:context => context.count === 1},
            {id:'copy', label:langIsEn() ? 'Copy' : '复制', icon:'copy', order:20, when:context => context.count > 0},
            {id:'group', label:langIsEn() ? 'Group' : '分组', icon:'folder-plus', order:30, when:context => context.count > 1},
            {id:'delete', label:langIsEn() ? 'Delete' : '删除', icon:'trash-2', order:40, when:context => context.count > 0},
        ],
        onIntent: intent => {
            if(intent.actionId === 'open') {
                openSelectedWorkspace(intent.nodeIds[0]);
                exitZoomPreviewToNode(intent.nodeIds[0]);
            }
            else if(intent.actionId === 'copy') copySelectedNodes();
            else if(intent.actionId === 'group') groupSelectedImages();
            else if(intent.actionId === 'delete') deleteSelectedNodes();
        },
    });
    return floatingActionBar;
}
function renderSelectionHub(){
    const bar = ensureFloatingActionBar();
    if(!bar) return;
    const selectedNodes = [...selected].map(id => nodes.find(node => node.id === id)).filter(Boolean);
    const result = bar.update({nodeIds:selectedNodes.map(node => node.id), nodes:selectedNodes});
    if(!result.visible.length) return;
    const boardRect = board.getBoundingClientRect();
    const rects = selectedNodes.map(node => nodesEl.querySelector(`.node[data-id="${CSS.escape(node.id)}"]`)?.getBoundingClientRect()).filter(Boolean);
    if(!rects.length) return;
    const left = Math.max(12, Math.min(boardRect.width - selectionHub.offsetWidth - 12, rects.reduce((sum, rect) => sum + rect.left, 0) / rects.length - boardRect.left));
    const top = Math.max(12, Math.min(boardRect.height - selectionHub.offsetHeight - 12, Math.min(...rects.map(rect => rect.top - boardRect.top)) - selectionHub.offsetHeight - 10));
    selectionHub.style.left = `${Math.round(left)}px`;
    selectionHub.style.top = `${Math.round(top)}px`;
    refreshIcons();
}
function startSelectionLink(e, kind){
    e.preventDefault();
    e.stopPropagation();
    const p = screenToWorld(e.clientX, e.clientY);
    tempLink = {from:`selection:${kind}`, x1:p.x, y1:p.y, x2:p.x, y2:p.y};
    ensureInteractionController().begin({
        kind:'selection-link',
        onMove:e2 => { const next = screenToWorld(e2.clientX, e2.clientY); tempLink.x2 = next.x; tempLink.y2 = next.y; renderLinks(); },
        onEnd:e2 => {
            const targetPort = nearestPort(e2.clientX, e2.clientY, 'in');
            const target = targetPort?.closest('.generator-node');
            if(target) connectSelectionToGenerator(kind, target.dataset.id);
            tempLink = null;
            render();
            scheduleSave();
        },
    });
}
function connectSelectionToGenerator(kind, genId){
    const ids = [...selected];
    let source = null;
    if(kind === 'images'){
        const imgs = ids.map(id => nodes.find(n => n.id === id)).filter(n => n?.type === 'image' && n.url);
        if(!imgs.length) return;
        const box = nodeBounds(imgs.map(n => n.id));
        source = {id:uid('grp'), type:'group', x:box.x - 24, y:box.y - 58, w:box.w + 48, h:box.h + 90, items:imgs.map(n => n.id)};
    } else {
        const prompts = ids.map(id => nodes.find(n => n.id === id)).filter(n => n?.type === 'prompt');
        if(!prompts.length) return;
        const box = nodeBounds(prompts.map(n => n.id));
        source = {id:uid('pg'), type:'promptGroup', x:box.x - 24, y:box.y - 58, w:box.w + 48, h:box.h + 90, items:prompts.map(n => n.id)};
    }
    window.WorkbenchLegacyCanvasMutation.appendNode(nodes, source);
    window.WorkbenchLegacyCanvasMutation.appendConnection(connections, {id:uid('c'), from:source.id, to:genId});
    selected.clear();
    selected.add(source.id);
    syncGeneratorInputs();
}

function pushUndo(){
    if(!canvas) return;
    undoStack.push({nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))});
    if(undoStack.length > UNDO_MAX) undoStack.shift();
}
function performUndo(){
    if(!canvas || !undoStack.length) return;
    const state = undoStack.pop();
    const restored = window.WorkbenchLegacyCanvasMutation.restoreSnapshot(state);
    nodes = restored.nodes;
    connections = restored.connections;
    selected.clear();
    render();
    scheduleSave();
}
function cloneNode(n, dx, dy){
    const copy = JSON.parse(JSON.stringify(serializableCanvasNode(n)));
    copy.id = uid(n.type);
    copy.x = n.x + dx;
    copy.y = n.y + dy;
    copy.running = false;
    return copy;
}
function duplicateNodesForAltDrag(node, preserveConnections=false){
    const duplicated = window.WorkbenchCanvasGraphFragment.duplicateSubgraph({
        node,
        nodes,
        connections,
        serializeNode:source => cloneNode(source, 0, 0),
        createNodeId:type => uid(type || 'n'),
        childIds:source => (source.type === 'group' || source.type === 'promptGroup') ? source.items || [] : [],
        preserveConnections,
        canConnect,
    });
    window.WorkbenchLegacyCanvasMutation.appendNodes(nodes, duplicated.copies);
    duplicated.connections.forEach(connection => {
        if(!connections.some(existing => existing.from === connection.from && existing.to === connection.to)) {
            window.WorkbenchLegacyCanvasMutation.appendConnection(connections, connection);
        }
    });
    return duplicated.root;
}
function copySelectedNodes(){
    if(!canvas || !selected.size) return;
    const el = document.activeElement;
    if(el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) return;
    const subgraph = window.WorkbenchCanvasGraphFragment.selectedSubgraph({
        nodes,
        connections,
        selectedIds:[...selected],
        serializeNode:serializableCanvasNode,
        order:'selection',
    });
    if(!subgraph.nodes.length) return;
    clipboard = JSON.parse(JSON.stringify(subgraph));
}
function clipboardNodeCount(){
    if(Array.isArray(clipboard)) return clipboard.length;
    if(Array.isArray(clipboard?.nodes)) return clipboard.nodes.length;
    return 0;
}
// Clipboard paste candidate: only a single, connection-free node whose durable
// Legacy shape round-trips losslessly through the compatibility repository
// (image: url/name/mediaKind; prompt: text) may create through the versioned
// boundary. Multi-node fragments, groups, connected nodes and every other
// type stay on the adapter-owned fragment path below.
function clipboardVersionedCandidate(clipNodes, clipConnections){
    if(!clipConnections.length && clipNodes.length === 1){
        const source = clipNodes[0];
        if(source?.type === 'image'){
            const config = {url:String(source.url || ''), name:String(source.name || ''), mediaKind:String(source.mediaKind || 'image')};
            return {
                definitionId:'image', title:config.name || undefined, config,
                projectNode:(created, p) => ({id:created.id, type:'image', x:p.x, y:p.y, url:String(created.config?.url ?? config.url), name:String(created.config?.name || config.name || created.title || ''), mediaKind:String(created.config?.mediaKind || config.mediaKind)}),
            };
        }
        if(source?.type === 'prompt'){
            const config = {text:String(source.text || '')};
            return {
                definitionId:'prompt', title:undefined, config,
                projectNode:(created, p) => ({id:created.id, type:'prompt', x:p.x, y:p.y, text:String(created.config?.text ?? config.text)}),
            };
        }
    }
    return null;
}
async function createVersionedPastedNode(candidate, point){
    if(!canUseVersionedImageCreation()) return null;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const node = await ensureCreationController().createNode({
            canvasId:canvas.id, projectId:canvas.project, clientId:CLIENT_ID, source:'clipboard',
            definitionRef:{type:'legacy', id:candidate.definitionId, version:'0'}, position:{x:point.x, y:point.y},
            expectedRevision:currentCanvasRevision(),
            ...(candidate.title !== undefined ? {title:candidate.title} : {}),
            initialConfig:candidate.config,
            apply:{
                nodes, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
                projectNode:created => candidate.projectNode(created, point),
                onRevision:revision => { adoptCanvasRevision(revision); },
                onSelected:created => { selected.clear(); selected.add(created.id); },
            },
        });
        render();
        return node;
    } catch(error) { console.error('Versioned clipboard creation failed', error); return null; }
}
async function pasteNodes(){
    if(!canvas || !clipboard) return;
    const clipNodes = Array.isArray(clipboard) ? clipboard : (Array.isArray(clipboard.nodes) ? clipboard.nodes : []);
    const clipConnections = Array.isArray(clipboard?.connections) ? clipboard.connections : [];
    if(!clipNodes.length) return;
    const candidate = clipboardVersionedCandidate(clipNodes, clipConnections);
    if(candidate && canUseVersionedImageCreation()){
        const placed = window.WorkbenchCanvasGraphFragment.materializeImportedSubgraph({
            nodes:clipNodes,
            connections:clipConnections,
            target:lastMouseBoard,
            anchor:'center',
            serializeNode:serializableCanvasNode,
            createNodeId:type => uid(type || 'n'),
        });
        const created = await createVersionedPastedNode(candidate, {x:placed.nodes[0].x, y:placed.nodes[0].y});
        if(created) return;
    }
    pushUndo();
    const materialized = window.WorkbenchCanvasGraphFragment.materializeImportedSubgraph({
        nodes:clipNodes,
        connections:clipConnections,
        target:lastMouseBoard,
        anchor:'center',
        serializeNode:serializableCanvasNode,
        createNodeId:type => uid(type || 'n'),
        prepareNode:copy => {
            copy.running = false;
            return copy;
        },
        createConnection:(connection, endpoints) => ({...connection, id:uid('c'), ...endpoints}),
    });
    const {nodes:copies, connections:newConnections, idMap} = materialized;
    copies.forEach(c => {
        if((c.type === 'group' || c.type === 'promptGroup') && c.items)
            c.items = c.items.map(id => idMap.get(id) || id);
    });
    window.WorkbenchLegacyCanvasMutation.appendNodes(nodes, copies);
    newConnections.forEach(connection => window.WorkbenchLegacyCanvasMutation.appendConnection(connections, connection));
    selected.clear();
    copies.forEach(c => selected.add(c.id));
    sanitizeConnections();
    syncGeneratorInputs();
    render();
    scheduleSave();
}
function selectedWorkflowPayload(){
    return selectedWorkflowExportProjection('json').payload;
}
function selectedWorkflowExportProjection(extension='json'){
    const subgraph = window.WorkbenchCanvasGraphFragment.selectedSubgraph({
        nodes, connections, selectedIds:[...selected], serializeNode:serializableCanvasNode, order:'selection'
    });
    return window.WorkbenchCanvasWorkflowTransfer.exportProjection(subgraph, canvas?.title, extension);
}
function workflowFilename(ext){
    return window.WorkbenchCanvasWorkflowTransfer.exportProjection({nodes:[], connections:[]}, canvas?.title, ext).filename;
}
function downloadUrl(url, filename='download'){
    if(!url) return Promise.resolve(false);
    const href = WorkbenchCanvasMediaTools.downloadHref(url, filename, canvasOriginalMediaUrl);
    const link = document.createElement('a');
    link.href = href;
    link.download = filename || '';
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    link.remove();
    return Promise.resolve(true);
}
let workflowTransferUi = null;
function ensureWorkflowTransferUi(){
    if(!workflowTransferUi){
        workflowTransferUi = window.WorkbenchCanvasWorkflowTransferUi.create({
            modal:workflowTransferModal, toggle:workflowTransferToggle, dropZone:workflowImportDropZone,
            meta:workflowExportMeta, sub:workflowTransferSub, refreshIcons,
            payload:selectedWorkflowPayload, hasCanvas:() => Boolean(canvas),
            needCanvasMessage:tr('canvas.needCanvas'),
            closeAssetLibrary:() => { if(canvasAssetLibraryOpen) toggleCanvasAssetLibrary(false); }, setStatus,
        });
    }
    return workflowTransferUi;
}
function openWorkflowTransferModal(){ return ensureWorkflowTransferUi().open(); }
function closeWorkflowTransferModal(){ return ensureWorkflowTransferUi().close(); }
function updateWorkflowTransferMeta(){ return ensureWorkflowTransferUi().update(); }
function setWorkflowLibraryExportState(state='idle', text='导出到资产库'){ return ensureClassicAssetRuntime().setWorkflowLibraryExportState(state, text); }
async function exportSelectedWorkflow(includeResources=false){ return ensureClassicAssetRuntime().exportSelectedWorkflow(includeResources); }
function defaultWorkflowAssetTarget(){ return ensureClassicAssetRuntime().defaultWorkflowAssetTarget(); }
async function exportSelectedWorkflowToLibrary(){ return ensureClassicAssetRuntime().exportSelectedWorkflowToLibrary(); }
function findCanvasAssetCategoryForItem(itemId){ return ensureClassicAssetRuntime().findCanvasAssetCategoryForItem(itemId); }
function insertWorkflowIntoCanvas(imported){
    const srcNodes = (imported.nodes || []).filter(Boolean);
    const srcConnections = (imported.connections || []).filter(Boolean);
    if(!canvas || !srcNodes.length) throw new Error('工作流中没有可导入的节点');
    pushUndo();
    const target = lastMouseBoard && Number.isFinite(lastMouseBoard.x) ? lastMouseBoard : defaultPoint(0, 0);
    const materialized = window.WorkbenchCanvasGraphFragment.materializeImportedSubgraph({
        nodes:srcNodes,
        connections:srcConnections,
        target,
        serializeNode:n => JSON.parse(JSON.stringify(serializableCanvasNode(n))),
        createNodeId:type => uid(type || 'n'),
        prepareNode:copy => {
            copy.running = false;
            return copy;
        },
        createConnection:(connection, endpoints) => ({...connection, id:uid('c'), ...endpoints}),
    });
    const {nodes:newNodes, connections:newConnections, idMap} = materialized;
    newNodes.forEach(node => {
        if((node.type === 'group' || node.type === 'promptGroup') && Array.isArray(node.items)){
            node.items = node.items.map(id => idMap.get(id) || id).filter(id => idMap.has(id) || nodes.some(n => n.id === id));
        }
    });
    window.WorkbenchLegacyCanvasMutation.appendNodes(nodes, newNodes);
    newConnections.forEach(connection => window.WorkbenchLegacyCanvasMutation.appendConnection(connections, connection));
    selected.clear();
    newNodes.forEach(n => selected.add(n.id));
    sanitizeConnections();
    syncGeneratorInputs();
    render();
    scheduleSave();
    setStatus(`已导入 ${newNodes.length} 个节点`);
}
async function importWorkflowFile(file){ return ensureClassicAssetRuntime().importWorkflowFile(file); }
function startNodeDrag(e, node){
    if(e.button !== 0) return;
    if(startKnifeDrag(e)) return;
    e.preventDefault();
    e.stopPropagation();
    let dragTarget = node;
    if(e.altKey){
        setKnifeMode(false);
        const copy = duplicateNodesForAltDrag(node, e.shiftKey);
        selected.clear();
        selected.add(copy.id);
        dragTarget = copy;
        if(e.shiftKey){
            sanitizeConnections();
            syncGeneratorInputs();
        }
        render();
    }
    const isGroup = dragTarget.type === 'group' || dragTarget.type === 'promptGroup';
    const collected = new Map();
    const collect = n => {
        if(!n || collected.has(n.id) || n.id === dragTarget.id) return;
        collected.set(n.id, {node:n, ox:n.x, oy:n.y});
        if(n.type === 'group' || n.type === 'promptGroup'){
            (n.items || []).map(id => nodes.find(x => x.id === id)).forEach(collect);
        }
    };
    if(isGroup){
        (dragTarget.items || []).map(id => nodes.find(n => n.id === id)).forEach(collect);
    }
    // 如果被拖节点在多选里，所有其他选中节点（含其组成员）一起移动
    if(selected.has(dragTarget.id) && selected.size > 1){
        [...selected].forEach(id => collect(nodes.find(n => n.id === id)));
    }
    const children = [...collected.values()];
    const dragSession = canvasUnifiedRuntimeEnabled
        ? ensureNodeDragSessionFactory()({
            start:{x:e.clientX, y:e.clientY},
            scale:viewport.scale,
            members:[{id:dragTarget.id, ox:dragTarget.x, oy:dragTarget.y}, ...children.map(child => ({id:child.node.id, ox:child.ox, oy:child.oy}))],
        })
        : null;
    dragNode = {node: dragTarget, children, sx:e.clientX, sy:e.clientY, ox:dragTarget.x, oy:dragTarget.y, isLocalCopy:Boolean(e.altKey), dragSession};
    document.body.classList.add('canvas-node-drag');
    ensureInteractionController().begin({kind:'node-drag', onMove:onNodeDrag, onEnd:endDrag});
}
function onNodeDrag(e){
    if(!dragNode) return;
    const drag = dragNode.dragSession?.move({x:e.clientX, y:e.clientY}, {scale:viewport.scale});
    const sharedPositions = drag ? new Map(drag.positions.map(item => [item.id, item])) : null;
    const dx = drag ? drag.dx : (e.clientX - dragNode.sx) / viewport.scale;
    const dy = drag ? drag.dy : (e.clientY - dragNode.sy) / viewport.scale;
    const dragPosition = (id, ox, oy) => sharedPositions?.get(id) || {x:ox + dx, y:oy + dy};
    const mainPosition = dragPosition(dragNode.node.id, dragNode.ox, dragNode.oy);
    dragNode.node.x = mainPosition.x;
    dragNode.node.y = mainPosition.y;
    applyCanvasRuntimeNodeMove(dragNode.node);
    const el = nodesEl.querySelector(`.node[data-id="${dragNode.node.id}"]`);
    if(el){
        el.style.left = `${dragNode.node.x}px`;
        el.style.top = `${dragNode.node.y}px`;
    }
    (dragNode.children || []).forEach(childDrag => {
        const childPosition = dragPosition(childDrag.node.id, childDrag.ox, childDrag.oy);
        childDrag.node.x = childPosition.x;
        childDrag.node.y = childPosition.y;
        applyCanvasRuntimeNodeMove(childDrag.node);
        const childEl = nodesEl.querySelector(`.node[data-id="${childDrag.node.id}"]`);
        if(childEl){
            childEl.style.left = `${childDrag.node.x}px`;
            childEl.style.top = `${childDrag.node.y}px`;
        }
    });
    scheduleLinksRender();
    renderSelectionHub();
    if(workflowTransferModal?.classList.contains('open')) updateWorkflowTransferMeta();
    scheduleMinimapRender();
}
function startNodeResize(e, node){
    e.preventDefault();
    e.stopPropagation();
    const el = nodesEl.querySelector(`.node[data-id="${node.id}"]`);
    const rect = el?.getBoundingClientRect();
    const sw = (rect?.width ? rect.width / viewport.scale : node.w || defaultNodeSize(node.type).w);
    const sh = (rect?.height ? rect.height / viewport.scale : node.h || defaultNodeSize(node.type).h || 160);
    const resizeSession = canvasUnifiedRuntimeEnabled
        ? ensureNodeResizeSessionFactory()({start:{x:e.clientX, y:e.clientY}, scale:viewport.scale, startWidth:sw, startHeight:sh})
        : null;
    resizeNode = {node, sx:e.clientX, sy:e.clientY, sw, sh, resizeSession};
    document.body.classList.add('canvas-node-resize');
    ensureInteractionController().begin({kind:'node-resize', onMove:onNodeResize, onEnd:endDrag});
}
function onNodeResize(e){
    if(!resizeNode) return;
    const resize = resizeNode.resizeSession?.move({x:e.clientX, y:e.clientY}, {scale:viewport.scale});
    const min = defaultNodeSize(resizeNode.node.type);
    const nextW = Math.max(Math.min(min.w, 220), resize ? resize.width : resizeNode.sw + (e.clientX - resizeNode.sx) / viewport.scale);
    const nextH = Math.max(96, resize ? resize.height : resizeNode.sh + (e.clientY - resizeNode.sy) / viewport.scale);
    resizeNode.node.w = Math.round(nextW);
    resizeNode.node.h = Math.round(nextH);
    applyCanvasRuntimeNodeResize(resizeNode.node);
    const el = nodesEl.querySelector(`.node[data-id="${resizeNode.node.id}"]`);
    if(el){
        el.classList.add('sized');
        el.style.width = `${resizeNode.node.w}px`;
        el.style.height = `${resizeNode.node.h}px`;
    }
    scheduleLinksRender();
    renderSelectionHub();
    scheduleMinimapRender();
}
let classicConnectionGesture = null;
function ensureClassicConnectionGesture(){
    if(!classicConnectionGesture){
        classicConnectionGesture = window.WorkbenchInteractionController.createConnectionGestureController({
            windowRef: window,
            resolveTarget: (gesture, e2) => {
                const targetKind = gesture.originKind === 'out' ? 'in' : 'out';
                const targetPort = nearestPort(e2.clientX, e2.clientY, targetKind);
                const target = targetPort?.closest('.node');
                return target ? {nodeId: target.dataset.id, port: targetKind} : null;
            },
            validate: (gesture, target) => {
                const intent = window.WorkbenchCanvasGraphInteraction?.edgeIntentFromPortDrop(
                    {nodeId:gesture.fromId, port:gesture.originKind}, {nodeId:target.nodeId, port:target.port}
                );
                const fromNode = nodes.find(node => node.id === intent?.from);
                const toNode = nodes.find(node => node.id === intent?.to);
                const portsCompatible = window.WorkbenchCanvasPortCompatibility?.isCompatible(
                    {direction:'out', dataType:fromNode?.output_port_type || fromNode?.port_type || 'legacy.any'},
                    {direction:'in', dataType:toNode?.input_port_type || toNode?.port_type || 'legacy.any'},
                );
                if(!intent || portsCompatible === false || !canConnect(intent.from, intent.to)) return null;
                if(connections.some(c => c.from === intent.from && c.to === intent.to)) return null;
                return {intent};
            },
            move: (gesture, e2) => {
                const p = screenToWorld(e2.clientX, e2.clientY);
                tempLink.x2 = p.x;
                tempLink.y2 = p.y;
                renderLinks();
            },
            drop: (gesture, result, e2) => {
                const {from:fromId, to:toId} = result.intent;
                if(canUseVersionedImageCreation()){
                    void createVersionedConnection(fromId, toId).then(created => {
                        if(!created) commitClassicConnection(fromId, toId);
                    });
                    return;
                }
                commitClassicConnection(fromId, toId);
            },
            noTarget: (gesture, e2) => {
                const source = gesture.source;
                if(gesture.originKind === 'out'){
                    if(source && CANVAS_GENERATOR_TYPES.includes(source.type)){
                        const p = screenToWorld(e2.clientX, e2.clientY);
                        pushUndo();
                        const out = {id:uid('out'), type:'output', x:p.x, y:p.y - 63, images:[]};
                        window.WorkbenchLegacyCanvasMutation.appendNode(nodes, out);
                        window.WorkbenchLegacyCanvasMutation.appendConnection(connections, {id:uid('c'), from:source.id, to:out.id});
                        syncLatestGeneratedOutputToConnection(source.id, out.id);
                        syncGeneratorInputs();
                        scheduleSave();
                        render();
                    } else {
                        openLinkCreateMenu(gesture.fromId, gesture.originKind, e2.clientX, e2.clientY);
                    }
                } else {
                    openLinkCreateMenu(gesture.fromId, gesture.originKind, e2.clientX, e2.clientY);
                }
            },
            finish: () => {
                tempLink = null;
                renderLinks();
            },
        });
    }
    return classicConnectionGesture;
}
// Classic graph-connect side effects stay page-owned: group membership, latest
// output sync and generator-input sync are Classic compatibility behavior and
// must never enter the Core graph model (card R4-24). Which of them fire is
// decided by the shared compatibility policy (card R4-25); this function only
// applies the projection it returns.
let classicLegacyGraphCompatibility = null;
function ensureLegacyGraphCompatibilityPolicy(){
    if(!classicLegacyGraphCompatibility){
        classicLegacyGraphCompatibility = window.WorkbenchLegacyGraphCompatibility.create({
            commands: window.WorkbenchCanvasCommands || null,
        });
    }
    return classicLegacyGraphCompatibility;
}
function applyClassicConnectionSideEffects(fromId, toId){
    const projection = ensureLegacyGraphCompatibilityPolicy().applyClassicConnect({
        fromId, toId,
        fromNode: nodes.find(node => node.id === fromId),
        toNode: nodes.find(node => node.id === toId),
    });
    if(projection.groupAddMember){
        const group = nodes.find(node => node.id === toId && node.type === 'group');
        if(group){
            group.items = Array.isArray(group.items) ? group.items : [];
            projection.addedNodeIds.forEach(id => { if(!group.items.includes(id)) group.items.push(id); });
        }
    }
    if(projection.shouldSyncOutput) syncLatestGeneratedOutputToConnection(fromId, toId);
    if(projection.shouldSyncGeneratorInputs) syncGeneratorInputs();
}
function commitClassicConnection(fromId, toId){
    // Legacy adapter-owned commit: raw edge append plus page save.
    pushUndo();
    window.WorkbenchLegacyCanvasMutation.appendConnection(connections, {id:uid('c'), from:fromId, to:toId});
    applyClassicConnectionSideEffects(fromId, toId);
    scheduleSave();
    render();
}
async function createVersionedConnection(fromId, toId){
    if(!canUseVersionedImageCreation()) return false;
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.connectNodes(canvas.id, {
            project_id:canvas.project, expected_revision:currentCanvasRevision(),
            edge_id:uid('c'), from_node_id:fromId, to_node_id:toId,
        }, CLIENT_ID);
        window.WorkbenchNodeClient.applyConnectionResult(result, {
            connections,
            fromId,
            toId,
            undoStack,
            undoSnapshot,
            undoLimit: UNDO_MAX,
            onRevision: revision => adoptCanvasRevision(revision, Date.now()),
        });
        applyClassicConnectionSideEffects(fromId, toId);
        scheduleSave();
        render();
        return true;
    } catch(error) { console.error('Versioned connection creation failed', error); return false; }
}
function startLink(e, originId, originKind){
    if(!window.WorkbenchCanvasCommands?.graphCommand('canvas.graph.connect', 'classic')) return;
    originKind = originKind || 'out';
    const src = portPoint(originId, originKind);
    const source = nodes.find(n => n.id === originId);
    if(!ensureClassicConnectionGesture().beginGesture(e, {fromId:originId, originKind, source, x1:src.x, y1:src.y})){
        return;
    }
    e.stopPropagation();
    tempLink = {from:originId, originKind, x1:src.x, y1:src.y, x2:src.x, y2:src.y};
}
function nearestPort(clientX, clientY, kind){
    const selector = kind === 'out'
        ? '.port.out, .workbench-node-shell__port--output'
        : '.port.in, .workbench-node-shell__port--input';
    const direct = document.elementFromPoint(clientX, clientY)?.closest(selector);
    if(direct) return direct;
    let best = null;
    let bestDistance = Infinity;
    nodesEl.querySelectorAll(selector).forEach(port => {
        const r = port.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        const d = Math.hypot(clientX - cx, clientY - cy);
        if(d < bestDistance){
            bestDistance = d;
            best = port;
        }
    });
    return bestDistance <= 48 ? best : null;
}
function canConnect(fromId, toId){
    return window.WorkbenchLegacyGraphCompatibility.canClassicConnect({nodes, connections, fromId, toId});
}
function sanitizeConnections(){
    connections = (connections || []).filter(c => canConnect(c.from, c.to));
}
function endDrag(event=null){
    const hadContentDrag = Boolean(dragNode || resizeNode || llmPaneDrag || knifeChanged || tempLink);
    const hadViewportDrag = Boolean(dragBoard || minimapDrag);
    const nodeDrag = dragNode;
    let versionedPositionCommit = null;
    if(nodeDrag){
        const moved = [nodeDrag.node, ...(nodeDrag.children || []).map(c => c.node)].filter(Boolean);
        // 拖动 group/promptGroup 自身时不重新评估（成员跟着一起走，包含关系不变）
        const draggedGroup = moved.some(n => n.type === 'group' || n.type === 'promptGroup');
        if(!draggedGroup) updateGroupMembership(moved);
        versionedPositionCommit = nodeDrag;
    }
    dragNode = null;
    dragBoard = null;
    resizeNode = null;
    llmPaneDrag = null;
    knifeActive = false;
    knifePoint = null;
    knifeTrail = [];
    const shouldRenderKnife = knifeNeedsRender;
    knifeChanged = false;
    knifeNeedsRender = false;
    if(!event?.shiftKey) setKnifeMode(false);
    if(textSelectionGuard) textSelectionGuard.active = false;
    document.body.classList.remove('canvas-node-drag', 'canvas-node-resize', 'canvas-selecting', 'canvas-board-pan');
    ensureInteractionController().end();
    if(shouldRenderKnife) render();
    scheduleMinimapRender();
    if(hadContentDrag) {
        // The narrow versioned move covers only standalone blank Image/Prompt nodes;
        // every richer Legacy drag remains on its compatibility mutation path.
        if(versionedPositionCommit) {
            void commitVersionedBlankClassicPosition(versionedPositionCommit).then(handled => {
                if(!handled) scheduleSave();
            });
        } else scheduleSave();
    }
    else if(hadViewportDrag) scheduleViewportSave();
}
function nodeRect(n){
    const el = nodesEl.querySelector(`.node[data-id="${n.id}"]`);
    const w = el?.offsetWidth || n.w || 260;
    const h = el?.offsetHeight || n.h || 200;
    return {x:n.x, y:n.y, w, h, cx:n.x + w/2, cy:n.y + h/2};
}
function connectedClusterIds(seedId){
    const ids = new Set(nodes.map(n => n.id));
    if(!ids.has(seedId)) return [];
    const seen = new Set([seedId]);
    const queue = [seedId];
    while(queue.length){
        const id = queue.shift();
        connections.forEach(c => {
            if(c.from !== id && c.to !== id) return;
            const next = c.from === id ? c.to : c.from;
            if(!ids.has(next) || seen.has(next)) return;
            seen.add(next);
            queue.push(next);
        });
    }
    return [...seen];
}
function canvasArrangeAtomicIds(ids){
    const out = new Set((ids || []).filter(id => nodes.some(n => n.id === id)));
    const groups = nodes.filter(n => (n.type === 'group' || n.type === 'promptGroup') && Array.isArray(n.items));
    const memberships = window.WorkbenchCanvasGroupMembership?.membershipIndex(groups);
    let changed = true;
    while(changed){
        changed = false;
        [...out].forEach(itemId => {
            const groupId = memberships?.get(itemId) || groups.find(group => (group.items || []).includes(itemId))?.id;
            if(!groupId || out.has(groupId)) return;
            out.delete(itemId);
            out.add(groupId);
            changed = true;
        });
    }
    return [...out];
}
function translateCanvasNodeWithMembers(node, dx, dy, seen=new Set()){
    if(!node || seen.has(node.id)) return;
    seen.add(node.id);
    node.x = Math.round((Number(node.x) || 0) + dx);
    node.y = Math.round((Number(node.y) || 0) + dy);
    if(node.type === 'group' || node.type === 'promptGroup'){
        (node.items || []).forEach(id => translateCanvasNodeWithMembers(nodes.find(n => n.id === id), dx, dy, seen));
    }
}
function moveCanvasNodeAtom(node, x, y){
    const dx = Math.round(x - (Number(node.x) || 0));
    const dy = Math.round(y - (Number(node.y) || 0));
    translateCanvasNodeWithMembers(node, dx, dy);
}
function arrangeIdsByConnections(ids){
    const idSet = new Set(canvasArrangeAtomicIds(ids));
    const selectedNodes = [...idSet].map(id => nodes.find(n => n.id === id)).filter(Boolean);
    if(selectedNodes.length < 2) return false;
    const rects = selectedNodes.map(n => ({node:n, rect:nodeRect(n)}));
    const startX = Math.min(...rects.map(item => item.rect.x));
    const startY = Math.min(...rects.map(item => item.rect.y));
    const internal = connections.filter(c => idSet.has(c.from) && idSet.has(c.to));
    const depth = new Map(selectedNodes.map(n => [n.id, 0]));
    if(internal.length){
        const indegree = new Map(selectedNodes.map(n => [n.id, 0]));
        internal.forEach(c => indegree.set(c.to, (indegree.get(c.to) || 0) + 1));
        const roots = [...indegree.entries()].filter(([, n]) => n === 0).map(([id]) => id);
        const queue = roots.length ? roots.slice() : [selectedNodes[0].id];
        const seen = new Set(queue);
        while(queue.length){
            const id = queue.shift();
            internal.filter(c => c.from === id).forEach(c => {
                depth.set(c.to, Math.max(depth.get(c.to) || 0, (depth.get(id) || 0) + 1));
                if(!seen.has(c.to)){
                    seen.add(c.to);
                    queue.push(c.to);
                }
            });
        }
    }
    const groups = new Map();
    selectedNodes.forEach(n => {
        const d = depth.get(n.id) || 0;
        if(!groups.has(d)) groups.set(d, []);
        groups.get(d).push(n);
    });
    const sortedDepths = [...groups.keys()].sort((a, b) => a - b);
    let x = startX;
    sortedDepths.forEach(d => {
        const col = groups.get(d).slice().sort((a, b) => nodeRect(a).y - nodeRect(b).y || String(a.id).localeCompare(String(b.id)));
        let y = startY;
        let maxW = 0;
        col.forEach(n => {
            const r = nodeRect(n);
            moveCanvasNodeAtom(n, x, y);
            y += Math.max(120, r.h) + 56;
            maxW = Math.max(maxW, Math.max(220, r.w));
        });
        x += maxW + 180;
    });
    return true;
}
function arrangeSelectedCanvasNodes(){
    if(!canvas || !selected.size) return;
    const explicit = [...selected].filter(id => nodes.some(n => n.id === id));
    const ids = canvasArrangeAtomicIds(explicit.length > 1 ? explicit : connectedClusterIds(explicit[0]));
    if(ids.length < 2) return;
    pushUndo();
    if(!arrangeIdsByConnections(ids)) return;
    render();
    scheduleSave();
}
function handoffExistingInputsToGroup(group, children){
    if(!group || group.type !== 'group') return false;
    return window.WorkbenchCanvasGroupMembership.handoffChildEdgesToGroup({
        group, children, edges:connections,
        nodeById: id => nodes.find(node => node.id === id),
        generatorTypes: CANVAS_GENERATOR_TYPES,
        childEligible: child => ['image','prompt'].includes(child?.type),
        targetEligible: node => CANVAS_GENERATOR_TYPES.includes(node?.type),
        canConnect,
        newEdgeId: () => uid('c'),
    }).changed;
}
function updateGroupMembership(movedNodes){
    const pairs = [
        {childType:'image', groupType:'group'},
        {childType:'prompt', groupType:'group'},
        {childType:'prompt', groupType:'promptGroup'}
    ];
    let changed = false;
    pairs.forEach(({childType, groupType}) => {
        const groups = nodes.filter(n => n.type === groupType);
        const children = movedNodes.filter(n => n?.type === childType);
        if(!children.length || !groups.length) return;
        const result = window.WorkbenchCanvasGroupMembership.resolveMembershipTransition({
            groups,
            children,
            rectOf: nodeRect,
            nodeById: id => nodes.find(n => n.id === id),
            handoffEligible: (group, child) => group?.type === 'group' && ['image','prompt'].includes(child?.type),
            edges: connections,
            generatorTypes: CANVAS_GENERATOR_TYPES,
            canConnect,
            newEdgeId: () => uid('c'),
        });
        if(result.changed) changed = true;
    });
    if(changed){
        syncGeneratorInputs();
        refreshGeneratorInputViews();
        render();
        scheduleSave();
    }
}

function portPoint(id, kind){
    const n = nodes.find(x => x.id === id);
    if(!n) return {x:0,y:0};  // 真正的孤儿连线（节点已删除）：renderLinks 会跳过它
    const el = nodesEl.querySelector(`.node[data-id="${CSS.escape(id)}"]`);
    const port = el?.querySelector(kind === 'out'
        ? '.port.out, .workbench-node-shell__port--output'
        : '.port.in, .workbench-node-shell__port--input');
    if(port){
        const r = port.getBoundingClientRect();
        return screenToWorld(r.left + r.width / 2, r.top + r.height / 2);
    }
    // 没有 DOM（节点渲染失败被跳过）或没找到端口时，用节点存储的几何坐标兜底，
    // 让连线仍画在节点附近，而不是落到 (0,0) 或干脆消失。
    const size = defaultNodeSize(n.type);
    const bounds = {x:Number(n.x) || 0, y:Number(n.y) || 0, width:(el?.offsetWidth) || n.w || size.w, height:(el?.offsetHeight) || n.h || size.h};
    if(window.WorkbenchCanvasGraphGeometry){
        return window.WorkbenchCanvasGraphGeometry.portAnchor(bounds, kind === 'out' ? 'right' : 'left');
    }
    return kind === 'out'
        ? {x:bounds.x + bounds.width, y:bounds.y + bounds.height / 2}
        : {x:bounds.x, y:bounds.y + bounds.height / 2};
}
function canResolvePort(id){
    // 只跳过“真正的孤儿连线”（端点节点已不存在）；节点存在但暂时没 DOM 的，portPoint 会用几何坐标兜底。
    return Boolean(nodes.find(x => x.id === id));
}
function renderLinks(){
    linksEl.innerHTML = '';
    linkControlsEl.innerHTML = '';
    // 先批量读取所有端点坐标（portPoint 里有 getBoundingClientRect），再统一写入 DOM。
    // 否则“读一条 rect → append 一条线”交错进行，每次 append 都让布局失效，下一次读 rect 就触发一次
    // 全量强制重排（layout thrashing），连线一多拖动就掉帧。读写分离后每帧只强制重排一次。
    const segments = [];
    connections.forEach(c => {
        // 端点无法解析（节点已删除、或尚未渲染出 DOM）就跳过，否则连线会被画到 (0,0)，
        // 看起来像很多连线都从同一个空白处中转。
        if(!canResolvePort(c.from) || !canResolvePort(c.to)) return;
        segments.push({c, a:portPoint(c.from, 'out'), b:portPoint(c.to, 'in')});
    });
    segments.forEach(({c, a, b}) => {
        const relClass = isConnectionSelected(c) ? ' link-active' : '';
        linksEl.appendChild(pathEl(a.x, a.y, b.x, b.y, `link${relClass}`));
        linkControlsEl.appendChild(linkDeleteButton(c, a, b));
        linksEl.appendChild(linkHitEl(a.x, a.y, b.x, b.y, c.id));
    });
    if(tempLink){
        linksEl.appendChild(pathEl(tempLink.x1, tempLink.y1, tempLink.x2, tempLink.y2, 'link temp'));
    }
    renderKnifeTrail();
}
function renderKnifeTrail(){
    if(!knifeActive || knifeTrail.length < 2) return;
    const poly = document.createElementNS('http://www.w3.org/2000/svg','polyline');
    poly.setAttribute('points', knifeTrail.map(p => `${p.x},${p.y}`).join(' '));
    poly.setAttribute('class', 'link knife-trail');
    linksEl.appendChild(poly);
}
function linkDeleteButton(connection, a, b){
    const btn = document.createElement('button');
    btn.className = `link-delete ${isConnectionSelected(connection) ? 'visible' : ''} ${hoveredConnectionId === connection.id ? 'hover' : ''}`;
    btn.type = 'button';
    btn.title = tr('canvas.deleteLink');
    btn.setAttribute('aria-label', tr('canvas.deleteLink'));
    btn.dataset.connectionId = connection.id;
    btn.style.left = `${(a.x + b.x) / 2}px`;
    btn.style.top = `${(a.y + b.y) / 2}px`;
    btn.textContent = '×';
    btn.onclick = e => deleteConnection(connection.id, e);
    return btn;
}
function linkHitEl(x1,y1,x2,y2,id){
    const p = pathEl(x1, y1, x2, y2, 'link-hit');
    p.dataset.connectionId = id;
    return p;
}
function setHoveredConnection(id){
    if(hoveredConnectionId === id) return;
    const oldId = hoveredConnectionId;
    hoveredConnectionId = id || '';
    if(oldId){
        const oldBtn = linkControlsEl.querySelector(`[data-connection-id="${CSS.escape(oldId)}"]`);
        if(oldBtn) oldBtn.classList.remove('hover');
    }
    if(hoveredConnectionId){
        const btn = linkControlsEl.querySelector(`[data-connection-id="${CSS.escape(hoveredConnectionId)}"]`);
        if(btn) btn.classList.add('hover');
    }
}
function connectionDistanceToPoint(connection, point){
    const from = portPoint(connection.from, 'out');
    const to = portPoint(connection.to, 'in');
    let min = Infinity;
    let prev = cubicPoint(from, to, 0);
    for(let i = 1; i <= 28; i++){
        const cur = cubicPoint(from, to, i / 28);
        min = Math.min(min, pointSegmentDistance(point, prev, cur));
        prev = cur;
    }
    return min;
}
function updateConnectionHoverFromMouse(e){
    if(!canvas || tempLink || dragNode || dragBoard || resizeNode || knifeActive){
        setHoveredConnection('');
        return;
    }
    const button = document.elementFromPoint(e.clientX, e.clientY)?.closest?.('.link-delete');
    if(button?.dataset.connectionId){
        setHoveredConnection(button.dataset.connectionId);
        return;
    }
    const point = screenToWorld(e.clientX, e.clientY);
    const threshold = Math.max(12, 16 / viewport.scale);
    let bestId = '';
    let best = Infinity;
    connections.forEach(c => {
        const d = connectionDistanceToPoint(c, point);
        if(d < best){ best = d; bestId = c.id; }
    });
    setHoveredConnection(best <= threshold ? bestId : '');
}
function isConnectionSelected(connection){
    return selected.has(connection.from) || selected.has(connection.to);
}
function refreshSelectionVisuals(){
    nodesEl.querySelectorAll('.node').forEach(el => {
        el.classList.toggle('selected', selected.has(el.dataset.id));
    });
    syncCanvasSelectedImageResolution(nodesEl);
    renderLinks();
    renderSelectionHub();
    if(workflowTransferModal?.classList.contains('open')) updateWorkflowTransferMeta();
    scheduleMinimapRender();
}
function pathEl(x1,y1,x2,y2,cls){
    const p = document.createElementNS('http://www.w3.org/2000/svg','path');
    const dx = Math.max(80, Math.abs(x2 - x1) * .45);
    p.setAttribute('d', `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`);
    p.setAttribute('class', cls);
    return p;
}
function pointSegmentDistance(p, a, b){
    const dx = b.x - a.x, dy = b.y - a.y;
    const len2 = dx * dx + dy * dy;
    if(!len2) return Math.hypot(p.x - a.x, p.y - a.y);
    const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / len2));
    return Math.hypot(p.x - (a.x + dx * t), p.y - (a.y + dy * t));
}
function segmentsIntersect(a, b, c, d){
    const orient = (p, q, r) => (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x);
    const onSeg = (p, q, r) => Math.min(p.x, r.x) <= q.x && q.x <= Math.max(p.x, r.x) && Math.min(p.y, r.y) <= q.y && q.y <= Math.max(p.y, r.y);
    const o1 = orient(a, b, c), o2 = orient(a, b, d), o3 = orient(c, d, a), o4 = orient(c, d, b);
    if(o1 === 0 && onSeg(a, c, b)) return true;
    if(o2 === 0 && onSeg(a, d, b)) return true;
    if(o3 === 0 && onSeg(c, a, d)) return true;
    if(o4 === 0 && onSeg(c, b, d)) return true;
    return (o1 > 0) !== (o2 > 0) && (o3 > 0) !== (o4 > 0);
}
function segmentIntersectsRect(a, b, r){
    if(a.x >= r.x && a.x <= r.x + r.w && a.y >= r.y && a.y <= r.y + r.h) return true;
    if(b.x >= r.x && b.x <= r.x + r.w && b.y >= r.y && b.y <= r.y + r.h) return true;
    const p1 = {x:r.x, y:r.y}, p2 = {x:r.x + r.w, y:r.y}, p3 = {x:r.x + r.w, y:r.y + r.h}, p4 = {x:r.x, y:r.y + r.h};
    return segmentsIntersect(a, b, p1, p2) || segmentsIntersect(a, b, p2, p3) || segmentsIntersect(a, b, p3, p4) || segmentsIntersect(a, b, p4, p1);
}
function cubicPoint(a, b, t){
    const dx = Math.max(80, Math.abs(b.x - a.x) * .45);
    const p1 = {x:a.x + dx, y:a.y};
    const p2 = {x:b.x - dx, y:b.y};
    const u = 1 - t;
    return {
        x:u*u*u*a.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t*t*t*b.x,
        y:u*u*u*a.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t*t*t*b.y
    };
}
function knifeHitsConnection(a, b, connection){
    const from = portPoint(connection.from, 'out');
    const to = portPoint(connection.to, 'in');
    const threshold = Math.max(8, 12 / viewport.scale);
    let prev = cubicPoint(from, to, 0);
    for(let i = 1; i <= 28; i++){
        const cur = cubicPoint(from, to, i / 28);
        if(segmentsIntersect(a, b, prev, cur) || pointSegmentDistance(prev, a, b) <= threshold || pointSegmentDistance(cur, a, b) <= threshold) return true;
        prev = cur;
    }
    return false;
}
function applyKnifeCut(from, to){
    if(!canvas || !connections.length || !from || !to) return;
    const nodeHits = new Set();
    nodes.forEach(n => {
        const el = nodesEl.querySelector(`.node[data-id="${n.id}"]`);
        if(!el) return;
        const r = nodeRect(n);
        if(segmentIntersectsRect(from, to, r)) nodeHits.add(n.id);
    });
    const next = connections.filter(c => !nodeHits.has(c.from) && !nodeHits.has(c.to) && !knifeHitsConnection(from, to, c));
    if(next.length === connections.length) return;
    if(!knifeChanged) pushUndo();
    knifeChanged = true;
    connections = next;
    syncGeneratorInputs();
    refreshGeneratorInputViews();
    knifeNeedsRender = true;
    renderLinks();
    renderSelectionHub();
    scheduleSave();
}
function setKnifeMode(active){
    document.body.classList.toggle('canvas-knife', Boolean(active && canvas));
    if(!active){
        knifeActive = false;
        knifePoint = null;
        knifeTrail = [];
        knifeChanged = false;
        knifeNeedsRender = false;
        renderLinks();
    }
}
function startKnifeDrag(e){
    if(!canvas || e.button !== 0 || !e.shiftKey || e.altKey || isEditableTarget(e.target)) return false;
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation?.();
    closeCreateMenu();
    setKnifeMode(true);
    knifeActive = true;
    knifeChanged = false;
    knifeNeedsRender = false;
    knifePoint = screenToWorld(e.clientX, e.clientY);
    knifeTrail = [knifePoint];
    renderLinks();
    ensureInteractionController().begin({kind:'knife-drag', onMove:continueKnifeDrag, onEnd:endDrag});
    return true;
}
function continueKnifeDrag(e){
    if(!canvas || !knifeActive) return;
    if(!e.shiftKey){
        setKnifeMode(false);
        return;
    }
    const point = screenToWorld(e.clientX, e.clientY);
    if(knifePoint) applyKnifeCut(knifePoint, point);
    knifePoint = point;
    knifeTrail.push(point);
    if(knifeTrail.length > 120) knifeTrail = knifeTrail.slice(-120);
    renderLinks();
}
function isEditableTarget(target){
    return WorkbenchCanvasInteractionTargets.isEditableTarget(target);
}
let minimapController = null;
function ensureMinimapController(){
    if(!minimapController){
        minimapController = window.WorkbenchInteractionController.createMinimapController({
            windowRef: window,
            pointerRef: minimap,
            canBegin: () => Boolean(canvas),
            onPointerDown: e => {
                if(e.button !== 0) return false;
                if(e.target.closest?.('#canvasArrangeBtn')) return false;
                e.preventDefault();
                e.stopPropagation();
                return true;
            },
            beginSession: () => { minimapDrag = true; },
            project: minimapEventToWorld,
            apply: worldPoint => centerViewportOnWorldPoint(worldPoint),
            endSession: () => {
                minimapDrag = false;
                scheduleViewportSave();
            },
        });
    }
    return minimapController;
}
ensureMinimapController();
canvasArrangeBtn?.addEventListener('mousedown', e => e.stopPropagation());
canvasArrangeBtn?.addEventListener('click', e => {
    e.preventDefault();
    e.stopPropagation();
    arrangeSelectedCanvasNodes();
});
function isZoomPreviewIgnoredTarget(target){
    return !!target?.closest?.('#createMenu, #linkCreateMenu, #nodeInputMenu, #nodeOutputMenu, #imageNodeMenu, .minimap, #canvasAssetPanel, #assetManagerModal, #workflowTransferModal, #logModal, #promptTemplateModal, #imageEditModal, #outputLightbox');
}
board.addEventListener('mousedown', e => {
    if(!zoomPreviewState || e.button !== 0) return;
    if(isZoomPreviewIgnoredTarget(e.target)) return;
    e.preventDefault();
    e.stopPropagation();
}, true);
board.addEventListener('click', e => {
    if(!zoomPreviewState || e.button !== 0) return;
    if(isZoomPreviewIgnoredTarget(e.target)) return;
    e.preventDefault();
    e.stopPropagation();
    const nodeEl = e.target.closest?.('.node');
    if(nodeEl?.dataset?.id) exitZoomPreviewToNode(nodeEl.dataset.id);
    else exitZoomPreview(screenToWorld(e.clientX, e.clientY));
}, true);
function startBoardPan(e, opts={}){
    if(!canvas) return false;
    if(isEditableTarget(e.target) || e.target.closest?.('#createMenu, #linkCreateMenu, #nodeInputMenu, #nodeOutputMenu, #imageNodeMenu, .minimap')) return false;
    e.preventDefault();
    e.stopPropagation();
    closeCreateMenu();
    if(document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    const panSession = canvasUnifiedRuntimeEnabled
        ? window.WorkbenchCanvasRuntime?.createViewportPanSession?.({start:{x:e.clientX, y:e.clientY}, viewport, threshold:4})
        : null;
    dragBoard = {sx:e.clientX, sy:e.clientY, ox:viewport.x, oy:viewport.y, moved:false, panSession, clearSelectionOnClick:Boolean(opts.clearSelectionOnClick)};
    document.body.classList.add('canvas-board-pan');
    ensureInteractionController().begin({kind:'board-pan', onMove:e2 => {
        const pan = dragBoard.panSession?.move({x:e2.clientX, y:e2.clientY});
        if(pan) dragBoard.moved = pan.moved;
        else if(Math.hypot(e2.clientX - dragBoard.sx, e2.clientY - dragBoard.sy) > 4) dragBoard.moved = true;
        const nextViewport = pan?.viewport || {x:dragBoard.ox + e2.clientX - dragBoard.sx, y:dragBoard.oy + e2.clientY - dragBoard.sy, scale:viewport.scale};
        if(!ensureCanvasViewportController().set(nextViewport)) viewport = nextViewport;
        applyViewport();
    }, onEnd:e2 => {
        const shouldClearSelection = dragBoard?.clearSelectionOnClick && !dragBoard.moved && selected.size;
        if(shouldClearSelection){
            if(!clearCanvasRuntimeSelection()) selected.clear();
            refreshSelectionVisuals();
        }
        endDrag(e2);
    }});
    return true;
}

board.onmousedown = e => {
    if(!canvas) return;
    if(e.button === 1){
        startBoardPan(e);
        return;
    }
    if(e.button !== 0) return;
    if(startKnifeDrag(e)) return;
    // Dismiss any open native select dropdown
    if(document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    if(e.target !== board && e.target !== world && e.target !== nodesEl && e.target !== linksEl) return;
    closeCreateMenu();
    if(isRKeyDown){
        e.preventDefault();
        startSelection(e);
        return;
    }
    if(e.ctrlKey || e.metaKey){
        e.preventDefault();
        startSelection(e);
        return;
    }
    startBoardPan(e, {clearSelectionOnClick:true});
};
board.addEventListener('mousemove', e => {
    const point = screenToWorld(e.clientX, e.clientY);
    lastMouseBoard = point;
    updateConnectionHoverFromMouse(e);
    if(canvas && knifeActive && !isEditableTarget(e.target) && !dragNode && !dragBoard && !resizeNode && !tempLink){
        continueKnifeDrag(e);
    } else if(!e.shiftKey) {
        setKnifeMode(false);
    }
});
board.addEventListener('mouseleave', () => setHoveredConnection(''));
board.ondblclick = null;
board.oncontextmenu = e => {
    if(!canvas) return;
    if((e.ctrlKey || e.metaKey) || isRKeyDown){
        e.preventDefault();
        e.stopPropagation();
        return;
    }
    if(e.target !== board && e.target !== world && e.target !== nodesEl && e.target !== linksEl) return;
    e.preventDefault();
    e.stopPropagation();
    openCreateMenu(e.clientX, e.clientY);
};
board.addEventListener('mousedown', e => {
    if(e.target.closest?.('#createMenu, #linkCreateMenu, #nodeInputMenu, #nodeOutputMenu, #imageNodeMenu')) return;
    closeCreateMenu();
});
board.onwheel = e => {
    if(!canvas) return;
    e.preventDefault();
    const rect = board.getBoundingClientRect();
    const sharedNextScale = canvasUnifiedRuntimeEnabled
        ? window.WorkbenchCanvasRuntime?.viewportScaleForWheel?.(viewport, e.deltaY, {strategy:'step', outFactor:.92, inFactor:1.08})
        : null;
    const nextScale = sharedNextScale || safeViewportScale(viewport.scale * (e.deltaY > 0 ? .92 : 1.08));
    if(!ensureCanvasViewportController().zoomAt({x:e.clientX - rect.left, y:e.clientY - rect.top}, nextScale)) {
        const before = screenToWorld(e.clientX, e.clientY);
        viewport.scale = nextScale;
        viewport.x = e.clientX - rect.left - before.x * viewport.scale;
        viewport.y = e.clientY - rect.top - before.y * viewport.scale;
    }
    applyViewport();
    renderLinks();
    renderSelectionHub();
    scheduleViewportSave();
};
board.addEventListener('dragover', e => {
    if(e.target.closest?.('.image-node')){
        dropOverlay.classList.remove('active');
        return;
    }
    if(isCanvasInputDrag(e.dataTransfer)){
        dropOverlay.classList.remove('active');
        return;
    }
    if(hasImageDropData(e.dataTransfer) || hasOutputImageDrag(e.dataTransfer)){
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        dropOverlay.classList.add('active');
    }
});
board.addEventListener('dragleave', e => {
    if(e.target === board || !board.contains(e.relatedTarget)) dropOverlay.classList.remove('active');
});
board.addEventListener('drop', async e => {
    e.preventDefault();
    dropOverlay.classList.remove('active');
    if(e.target.closest?.('.image-node')) return;
    if(hasOutputImageDrag(e.dataTransfer)) {
        createImageCardFromOutput(e.dataTransfer.getData('application/x-canvas-output-image'), screenToWorld(e.clientX, e.clientY));
        return;
    }
    if(Array.from(e.dataTransfer?.types || []).includes('application/x-canvas-asset')){
        try {
            const payload = JSON.parse(e.dataTransfer.getData('application/x-canvas-asset') || '{}');
            if(payload?.url) {
                if(String(payload.kind || '').toLowerCase() === 'workflow') await importWorkflowAssetUrl(payload.url, payload.name || 'workflow');
                else createImageCardFromUrl(payload.url, screenToWorld(e.clientX, e.clientY), payload.name || 'asset');
            }
        } catch(err) {}
        return;
    }
    if(isCanvasInputDrag(e.dataTransfer)) {
        internalDrag = false;
        return;
    }
    const payload = await resolveImageDropPayload(e.dataTransfer);
    if(payload.type === 'none') return;
    try {
        await applyImageDropPayloadToBoard(payload, screenToWorld(e.clientX, e.clientY));
    } catch(err) {
        setStatus('Ready');
        showErrorModal(err.message || (langIsEn() ? 'Image import failed' : '导入图片失败'), langIsEn() ? 'Image import failed' : '导入图片失败');
    }
});
window.addEventListener('dragend', () => dropOverlay.classList.remove('active'));
window.addEventListener('drop', () => dropOverlay.classList.remove('active'));
window.addEventListener('paste', e => {
    if(!canvas) return;
    const files = [...(e.clipboardData?.items || [])].filter(x => x.kind === 'file' && /^(image|video|audio)\//.test(String(x.type || ''))).map(x => x.getAsFile());
    if(!files.length) return;
    e.preventDefault();
    lastImagePasteAt = Date.now();
    const blank = [...selected].map(id => nodes.find(n => n.id === id)).find(n => n?.type === 'image' && !n.url);
    if(blank) fillImageNode(blank.id, files);
    else if(files.length > 1) uploadImageGroup(files);
    else uploadImages(files);
});
const canvasKeyboardRuntime = window.WorkbenchInteractionController.createKeyboardRuntime({windowRef: window});
canvasKeyboardRuntime.register(e => {
    // keyup: knife/rectangle-mode release
    if(e.type === 'keyup'){
        if(String(e.key || '').toLowerCase() === 'r') isRKeyDown = false;
        if(e.key === 'Shift') setKnifeMode(false);
        return false;
    }
    if(!canvas) return false;
    const key = String(e.key || '').toLowerCase();
    if(key === 'r' && !isEditableTarget(e.target)) isRKeyDown = true;
    if(e.key === 'Shift' && !e.altKey && !isEditableTarget(document.activeElement)) setKnifeMode(true);
    if(e.key === 'Escape' && document.getElementById('imageEditModal').classList.contains('open')) { closeImageEditor(); return; }
    if(e.key === 'Escape' && promptTemplateModal?.classList.contains('open')) { closePromptTemplateModal(); return; }
    if(outputLightbox.classList.contains('open') && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')){
        if(navigateOutputLightbox(e.key === 'ArrowRight' ? 1 : -1)){
            e.preventDefault();
            e.stopPropagation();
        }
        return;
    }
    if(e.key === 'Escape' && outputLightbox.classList.contains('open')) { closeOutputLightbox(); return; }
    if(!e.ctrlKey && !e.metaKey && !e.altKey && key === 'z' && !isEditableTarget(e.target)
        && !document.getElementById('imageEditModal')?.classList.contains('open')
        && !promptTemplateModal?.classList.contains('open')
        && !outputLightbox.classList.contains('open')
        && !assetManagerModal?.classList.contains('open')
        && !workflowTransferModal?.classList.contains('open')
        && !logModal?.classList.contains('open')){
        if(e.repeat) return;
        e.preventDefault();
        toggleZoomPreview();
        return;
    }
    if((e.ctrlKey || e.metaKey) && key === 'g') { e.preventDefault(); groupSelectedImages(); }
    if((e.ctrlKey || e.metaKey) && key === 'c') {
        // 在输入框/可编辑元素里时，让浏览器原生 Ctrl+C 工作
        const tag = document.activeElement?.tagName;
        if(tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;
        // 用户在页面任意位置选中了文本时，也不要拦截
        const sel = window.getSelection && window.getSelection();
        if(sel && sel.toString().length > 0) return;
        e.preventDefault();
        copySelectedNodes();
    }
    if((e.ctrlKey || e.metaKey) && key === 'v') {
        const tag = document.activeElement?.tagName;
        if(tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;
        if(clipboardNodeCount()) {
            const pasteRequestedAt = Date.now();
            setTimeout(() => {
                if(!canvas) return;
                if(lastImagePasteAt >= pasteRequestedAt) return;
                pasteNodes();
            }, 90);
        }
    }
    if((e.ctrlKey || e.metaKey) && key === 'z') {
        const tag = document.activeElement?.tagName;
        if(tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;
        e.preventDefault(); performUndo();
    }
    if(e.key === 'Delete' || e.key === 'Backspace') {
        const tag = document.activeElement?.tagName;
        if(tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;
        if(selected.size === 0) return;
        e.preventDefault();
        deleteSelectedNodes();
    }
    return false;
});
window.addEventListener('blur', () => {
    isRKeyDown = false;
    setKnifeMode(false);
    if(selectDrag){
        selectionBox.style.display = 'none';
        selectDrag = null;
        document.body.classList.remove('canvas-selecting');
        ensureInteractionController().end();
    }
    if(dragNode || resizeNode || llmPaneDrag || dragBoard || minimapDrag || knifeActive) endDrag();
});
function deleteSelectedNodes(){
    if(!canvas || selected.size === 0) return;
    pushUndo();
    const toDelete = window.WorkbenchCanvasGraphFragment.expandNodeIds({
        nodes,
        initialIds:[...selected],
        childIds:node => (node.type === 'group' || node.type === 'promptGroup') ? node.items || [] : [],
    });
    const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:toDelete});
    nodes = remaining.nodes;
    connections = remaining.connections;
    selected.clear();
    render();
    scheduleSave();
}
function hasImageFiles(items){
    return [...(items || [])].some(item => {
        const entry = dataTransferItemEntry(item);
        return entry?.isDirectory || (item.kind === 'file' && (/^(image|video|audio)\//.test(String(item.type || '')) || isSupportedUploadFile(item.getAsFile?.())));
    });
}
function isCanvasInputDrag(dataTransfer){
    return internalDrag || [...(dataTransfer?.types || [])].includes('application/x-canvas-input');
}
function hasImageDropData(dataTransfer){ return ensureClassicAssetRuntime().hasImageDropData(dataTransfer); }
function hasOutputImageDrag(dataTransfer){ return [...(dataTransfer?.types || [])].includes('application/x-canvas-output-image'); }
function escapeHtml(str){ return String(str == null ? '' : str).replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s])); }
function escapeAttr(str){ return escapeHtml(str); }
