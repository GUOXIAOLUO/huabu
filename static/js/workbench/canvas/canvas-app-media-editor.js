const classicVersionedConnectedNodeCreators = Object.freeze({
    group: createVersionedLinkedGroup,
    image: createVersionedLinkedImage,
    prompt: createVersionedLinkedPrompt,
    loop: createVersionedLinkedLoop,
});
function createVersionedClassicConnectedNode(command, state, origin){
    const versionedCreator = classicVersionedConnectedNodeCreators[command?.createType];
    if(!versionedCreator || !canUseVersionedImageCreation() || !window.WorkbenchCanvasCommands?.usesVersionedConnectedCreation(command, 'classic')) return false;
    void versionedCreator(state, origin);
    return true;
}
function createLinkedNode(type){
    const state = linkCreateState;
    closeLinkCreateMenu();
    if(!state) return;
    const origin = nodes.find(n => n.id === state.originId);
    if(!origin) return;
    const command = window.WorkbenchCanvasCommands?.createCommand(type, 'classic');
    if(!command) return;
    if(createVersionedClassicConnectedNode(command, state, origin)) return;
    pushUndo();
    const created = createNodeByType(command.createType, state.point);
    if(!created) return;
    const fromId = state.originKind === 'out' ? origin.id : created.id;
    const toId = state.originKind === 'out' ? created.id : origin.id;
    if(canConnect(fromId, toId) && !connections.some(c => c.from === fromId && c.to === toId)){
        connections.push({id:uid('c'), from:fromId, to:toId});
        syncLatestGeneratedOutputToConnection(fromId, toId);
        syncGeneratorInputs();
        scheduleSave();
        render();
    }
}
async function createVersionedLinkedGroup(state, origin){
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    const edgeId = uid('c');
    try {
        const result = await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id, {
            request_id:`${CLIENT_ID}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            project_id:canvas.project, source:'context_menu',
            definition_ref:{type:'legacy', id:'group', version:'0'}, position:{x:state.point.x, y:state.point.y},
            expected_revision:currentCanvasRevision(), title:'Group',
            existing_node_id:origin.id, edge_id:edgeId,
            direction:state.originKind === 'out' ? 'from_existing' : 'to_existing',
        }, CLIENT_ID);
        window.WorkbenchNodeClient.applyGraphCreationResult(result, {
            nodes, connections, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
            projectNode:created => ({id:created.id, type:'group', x:state.point.x, y:state.point.y, w:300, h:220, items:[]}),
            projectEdge:edge => ({id:edge.id, from:edge.from.node_id, to:edge.to.node_id}),
            onRevision:revision => { adoptCanvasRevision(revision); },
            onAfterCommit:(_node, edge) => {
                syncLatestGeneratedOutputToConnection(edge.from, edge.to);
                syncGeneratorInputs();
            },
        });
        render();
    } catch(error) {
        console.error('Versioned Group creation failed', error);
        setStatus('Create failed');
    }
}
async function createVersionedLinkedImage(state, origin){
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    const edgeId = uid('c');
    try {
        const result = await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id, {
            request_id:`${CLIENT_ID}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            project_id:canvas.project, source:'context_menu',
            definition_ref:{type:'legacy', id:'image', version:'0'}, position:{x:state.point.x, y:state.point.y},
            expected_revision:currentCanvasRevision(), title:'Image',
            existing_node_id:origin.id, edge_id:edgeId,
            direction:state.originKind === 'out' ? 'from_existing' : 'to_existing',
        }, CLIENT_ID);
        window.WorkbenchNodeClient.applyGraphCreationResult(result, {
            nodes, connections, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas,
            projectNode:created => ({id:created.id, type:'image', x:state.point.x, y:state.point.y, name:created.title || 'Image', mediaKind:'image'}),
            projectEdge:edge => ({id:edge.id, from:edge.from.node_id, to:edge.to.node_id}),
            onRevision:revision => { adoptCanvasRevision(revision); },
            onAfterCommit:(_node, edge) => {
                syncLatestGeneratedOutputToConnection(edge.from, edge.to);
                syncGeneratorInputs();
            },
        });
        render();
    } catch(error) {
        console.error('Versioned Image creation failed', error);
        setStatus('Create failed');
    }
}
async function createVersionedLinkedPrompt(state, origin){
    return createVersionedLinkedClassicNode(state, origin, {definitionId:'prompt', title:'Prompt', projectNode:created => ({id:created.id, type:'prompt', x:state.point.x, y:state.point.y, text:''})});
}
async function createVersionedLinkedLoop(state, origin){
    return createVersionedLinkedClassicNode(state, origin, {definitionId:'loop', title:'Loop', projectNode:created => ({id:created.id, type:'loop', x:state.point.x, y:state.point.y, count:3, mode:'serial', showPrompt:false, imageInput:false, videoInput:false, loopStart:1, imageBatchSize:1, videoBatchSize:1, variablePrompt:'', fixedPrompt:''})});
}
async function createVersionedLinkedClassicNode(state, origin, definition){
    const undoSnapshot = {nodes:JSON.parse(JSON.stringify(serializableCanvasNodes())), connections:JSON.parse(JSON.stringify(connections))};
    try {
        const result = await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id, {
            request_id:`${CLIENT_ID}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            project_id:canvas.project, source:'context_menu', definition_ref:{type:'legacy', id:definition.definitionId, version:'0'},
            position:{x:state.point.x, y:state.point.y}, expected_revision:currentCanvasRevision(), title:definition.title,
            initial_config:definition.definitionId === 'prompt' ? {text:''} : undefined,
            existing_node_id:origin.id, edge_id:uid('c'), direction:state.originKind === 'out' ? 'from_existing' : 'to_existing',
        }, CLIENT_ID);
        window.WorkbenchNodeClient.applyGraphCreationResult(result, {
            nodes, connections, undoStack, undoSnapshot, undoLimit:UNDO_MAX, canvas, projectNode:definition.projectNode,
            projectEdge:edge => ({id:edge.id, from:edge.from.node_id, to:edge.to.node_id}), onRevision:revision => { adoptCanvasRevision(revision); },
            onAfterCommit:(_node, edge) => { syncLatestGeneratedOutputToConnection(edge.from, edge.to); syncGeneratorInputs(); },
        });
        render();
    } catch(error) { console.error(`Versioned ${definition.definitionId} creation failed`, error); setStatus('Create failed'); }
}
function createNodeByType(type, point){
    if(type === 'image') return addImageNode(point);
    if(type === 'prompt') return addPromptNode(point);
    if(type === 'loop') return addLoopNode(point);
    if(type === 'group') return addGroupNode(point);
    if(type === 'llm') return addLLMNode(point);
    if(type === 'generator') return ensureClassicNodeFactories().addGenerator({point});
    if(type === 'midjourney') return ensureClassicNodeFactories().addMidjourney({point});
    if(type === 'msgen') return ensureClassicNodeFactories().addMsGen({point});
    if(type === 'video') return ensureClassicNodeFactories().addVideo({point});
    if(type === 'minimax') return ensureClassicMiniMaxControls().addNode({point});
    if(type === 'rh') return ensureClassicRunningHubControls().addNode({point});
    if(type === 'comfy') return ensureClassicComfyControls().addNode({point});
    if(type === 'ltxDirector') return ensureClassicLtxControls().addNode({point});
    if(type === 'output') return ensureClassicNodeFactories().addOutput({point});
    return null;
}
const classicVersionedBlankNodeCreators = Object.freeze({
    image: addVersionedBlankImageNode,
    prompt: addVersionedBlankPromptNode,
    loop: addVersionedBlankLoopNode,
    group: addVersionedBlankGroupNode,
    output: addVersionedBlankOutputNode,
});
function createClassicMenuNode(command, point){
    const versionedCreator = classicVersionedBlankNodeCreators[command?.createType];
    if(versionedCreator && canUseVersionedImageCreation() && window.WorkbenchCanvasCommands?.usesVersionedBlankCreation(command, 'classic')) {
        void versionedCreator(point);
        return null;
    }
    return createNodeByType(command?.createType, point);
}
function menuAdd(type){
    const command = window.WorkbenchCanvasCommands?.createCommand(type, 'classic');
    if(!command) return;
    closeCreateMenu();
    return createClassicMenuNode(command, menuPoint);
}
function quickAdd(type){
    const command = window.WorkbenchCanvasCommands?.createCommand(type, 'classic');
    if(!command) return null;
    const point = defaultPoint(0, 0);
    return createClassicMenuNode(command, point);
}
function mediaKindForUpload(file){ return ensureClassicAssetRuntime().mediaKindForUpload(file); }
function isSupportedUploadFile(file){ return ensureClassicAssetRuntime().isSupportedUploadFile(file); }
function dataTransferItemEntry(item){
    return window.WorkbenchCanvasMediaDrop.entryForItem(item);
}
async function filesFromEntry(entry){
    return window.WorkbenchCanvasMediaDrop.filesFromEntry(entry);
}
async function uploadFilesFromDataTransfer(dataTransfer){ return ensureClassicAssetRuntime().uploadFilesFromDataTransfer(dataTransfer); }
function isAudioUrl(url){
    return window.WorkbenchCanvasMediaKind.isKindForUrl(canvasOriginalMediaUrl(url), 'audio');
}
function isTextUrl(url){
    return window.WorkbenchCanvasMediaKind.isKindForUrl(canvasOriginalMediaUrl(url), 'text');
}
function mediaKindForRef(ref){
    return window.WorkbenchCanvasMediaKind.kindForItem(ref, {
        originalUrl:item => canvasOriginalMediaUrl(item?.url || item),
        includeFlv:true,
    });
}
function imageRefsOnly(refs){
    return WorkbenchCanvasMediaReferences.refsOfKind(refs, 'image', {kindOf:mediaKindForRef, limit:CANVAS_REFERENCE_IMAGE_MAX});
}
function videoRefsOnly(refs){
    return WorkbenchCanvasMediaReferences.refsOfKind(refs, 'video', {kindOf:mediaKindForRef});
}
function isRemoteVideoReferenceUrl(url){
    return WorkbenchCanvasMediaReferences.isRemoteVideoReferenceUrl(url);
}
function tempShUploadedUrlForNode(node, url){ return ensureClassicAssetRuntime().tempShUploadedUrlForNode(node, url); }
function applyUploadedUrlToRefs(refs, node){ return ensureClassicAssetRuntime().applyUploadedUrlToRefs(refs, node); }
function manualVideoUrlForNode(node){
    return (node?.manualVideoUrls || []).find(Boolean) || '';
}
function currentCanvasMediaLinks(node){
    const refs = orderedSources(node, generatorSources(node)).flatMap(src => src.refs || [])
        .filter(ref => ref?.url && ['image','video'].includes(mediaKindForRef(ref)));
    return refs.map(ref => {
        const uploaded = tempShUploadedUrlForNode(node, ref.url);
        return uploaded && uploaded !== ref.url ? uploaded : '';
    }).filter(Boolean);
}
function clearManualVideoUrlForNode(node){
    if(!node) return;
    node.manualVideoUrls = [];
    node.tempShLinks = (node.tempShLinks || []).filter(item => item?.manual !== true);
}
function applyTempShUrlToCanvasRef(ref, uploadedUrl){
    if(!ref?.url || !uploadedUrl) return false;
    const source = nodes.find(n => n.id === ref.nodeId);
    if(!source) return false;
    const kind = mediaKindForRef(ref);
    if(source.type === 'image' && source.url === ref.url){
        source.originalLocalUrl = source.originalLocalUrl || source.url;
        source.url = uploadedUrl;
        source.mediaKind = kind;
        return true;
    }
    if(source.type === 'output' && Array.isArray(source.images)){
        const item = Number.isFinite(Number(ref.outputIndex))
            ? source.images[Number(ref.outputIndex)]
            : source.images.find(img => outputUrlValue(img) === ref.url);
        if(item && typeof item === 'object'){
            item.originalLocalUrl = item.originalLocalUrl || outputUrlValue(item);
            item.url = uploadedUrl;
            item.kind = kind;
            return true;
        }
    }
    if(Array.isArray(source.generatedOutputs)){
        const item = source.generatedOutputs.find(img => outputUrlValue(img) === ref.url);
        if(item && typeof item === 'object'){
            item.originalLocalUrl = item.originalLocalUrl || outputUrlValue(item);
            item.url = uploadedUrl;
            item.kind = kind;
            return true;
        }
    }
    return false;
}
async function uploadCanvasMediaRefToCloud(node, ref){ return ensureClassicAssetRuntime().uploadCanvasMediaRefToCloud(node, ref); }
async function uploadCanvasVideosToCloud(nodeId){ return ensureClassicAssetRuntime().uploadCanvasVideosToCloud(nodeId); }
function applyManualVideoUrlToCanvasRef(node, ref, manualUrl){
    clearManualVideoUrlForNode(node);
    node.manualVideoUrls = [manualUrl];
    if(ref?.url) node.tempShLinks = [...(node.tempShLinks || []), {source:ref.url, url:manualUrl, manual:true}];
}
async function setCanvasManualVideoUrl(nodeId){
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return '';
    const refs = orderedSources(node, generatorSources(node)).flatMap(src => src.refs || [])
        .filter(ref => ref?.url && ['image','video'].includes(mediaKindForRef(ref)));
    const firstLocal = refs.find(ref => ref?.url && !isRemoteVideoReferenceUrl(ref.url));
    const firstAny = firstLocal || refs[0] || null;
    const current = manualVideoUrlForNode(node) || currentCanvasMediaLinks(node)[0] || (firstAny ? tempShUploadedUrlForNode(node, firstAny.url) : '');
    const value = prompt('输入媒体网址 / 火山素材 URI', isRemoteVideoReferenceUrl(current) ? current : '');
    if(value === null) return '';
    const url = String(value || '').trim();
    if(!url){
        clearManualVideoUrlForNode(node);
        refreshNodes([node.id]);
        scheduleSave();
        showErrorModal('已清除手动网址。', '输入网址');
        return '';
    }
    if(!isRemoteVideoReferenceUrl(url)){
        showErrorModal('请输入 http/https 媒体网址或 asset:// 火山素材 URI', '输入网址');
        return '';
    }
    applyManualVideoUrlToCanvasRef(node, firstAny, url);
    refreshNodes([node.id, firstAny?.nodeId].filter(Boolean));
    scheduleSave();
    showErrorModal('已设置视频网址。', '输入网址');
    return url;
}
function audioRefsOnly(refs){
    return WorkbenchCanvasMediaReferences.refsOfKind(refs, 'audio', {kindOf:mediaKindForRef});
}
function mediaKindForNode(node){
    return window.WorkbenchCanvasMediaKind.kindForNode(node, {
        originalUrl:item => canvasOriginalMediaUrl(item?.url || item),
        includeFlv:true,
    });
}
function nodeTitleForMedia(node){
    return WorkbenchCanvasNodePresentation.mediaTitle(mediaKindForNode(node));
}
const IMAGE_DROP_EXT_RE = /\.(png|jpe?g|webp|gif)$/i;
const IMAGE_DROP_TEXT_TYPES = [
    'text/uri-list',
    'text/plain',
    'text/html',
    'DownloadURL',
    'text/x-moz-url',
    'text/x-file-url',
    'public.file-url',
    'public.url',
    'UniformResourceLocator',
    'FileName',
    'FileNameW'
];
const IMAGE_DROP_TYPE_HINT_RE = /^(?:files?|image\/.+|text\/(?:uri-list|html|plain|x-moz-url|x-file-url)|downloadurl|public\.(?:file-url|url)|uniformresourcelocator|filenamew?)$|application\/x-qt-(?:windows-mime|image)|application\/x-moz-file|com\.eagle/i;
function dropDataTypes(dataTransfer){ return ensureClassicAssetRuntime().dropDataTypes(dataTransfer); }
function dropTextCandidates(dataTransfer){ return ensureClassicAssetRuntime().dropTextCandidates(dataTransfer); }
function isRemoteImageDropValue(value){ return ensureClassicAssetRuntime().isRemoteImageDropValue(value); }
function isLocalImageDropValue(value){ return ensureClassicAssetRuntime().isLocalImageDropValue(value); }
function imageDropPayload(dataTransfer){ return ensureClassicAssetRuntime().imageDropPayload(dataTransfer); }
async function resolveImageDropPayload(dataTransfer){ return ensureClassicAssetRuntime().resolveImageDropPayload(dataTransfer); }
async function importLocalImages(paths){ return ensureClassicAssetRuntime().importLocalImages(paths); }
function layoutUploadedMediaNodes(created, base){ return ensureClassicAssetRuntime().layoutUploadedMediaNodes(created, base); }
function createGroupForUploadedNodes(created, point){ return ensureClassicAssetRuntime().createGroupForUploadedNodes(created, point); }
async function uploadMediaFiles(files, point, onlyImages=false, opts={}){ return ensureClassicAssetRuntime().uploadMediaFiles(files, point, onlyImages, opts); }
async function uploadImages(files, point){ return ensureClassicAssetRuntime().uploadImages(files, point); }
async function uploadImageGroup(files, point){ return ensureClassicAssetRuntime().uploadImageGroup(files, point); }
function createImageCardFromUrl(url, point, name='image'){
    if(!ensureCanvas() || !url) return;
    const p = point || defaultPoint(0, 0);
    const mediaKind = isVideoUrl(url) ? 'video' : isAudioUrl(url) ? 'audio' : 'image';
    nodes.push({id:uid('img'), type:'image', x:p.x, y:p.y, url, name:name || outputImageName(url), mediaKind});
    render();
    scheduleSave();
}
async function createImageCardsFromLocalPaths(paths, point){
    if(!ensureCanvas()) return [];
    setStatus(langIsEn() ? 'Importing images...' : '导入图片...');
    try {
        const files = await importLocalImages((paths || []).slice(0, CANVAS_UPLOAD_MAX));
        const base = point || screenToWorld(window.innerWidth / 2, window.innerHeight / 2);
        const created = [];
        files.forEach((file, i) => {
            const node = {id:uid('img'), type:'image', x:base.x + i * 36, y:base.y + i * 36, url:file.url, name:file.name, mediaKind:'image'};
            nodes.push(node);
            created.push(node);
        });
        render();
        scheduleSave();
        setStatus('Ready');
        return created;
    } catch(err) {
        setStatus('Ready');
        throw err;
    }
}
async function applyImageDropPayloadToBoard(payload, point){ return ensureClassicAssetRuntime().applyImageDropPayloadToBoard(payload, point); }
async function applyImageDropPayloadToNode(nodeId, payload){ return ensureClassicAssetRuntime().applyImageDropPayloadToNode(nodeId, payload); }
function allowImageNodeDropEvent(e, highlightEl){ return ensureClassicAssetRuntime().allowImageNodeDropEvent(e, highlightEl); }
function clearImageNodeDropState(e, highlightEl){ return ensureClassicAssetRuntime().clearImageNodeDropState(e, highlightEl); }
async function handleImageNodeDropEvent(e, nodeId, highlightEl){ return ensureClassicAssetRuntime().handleImageNodeDropEvent(e, nodeId, highlightEl); }
async function fillImageNode(nodeId, files, opts={}){
    if(!ensureCanvas()) return;
    const imgs = [...files].filter(file => ['image','video','audio'].includes(mediaKindForUpload(file))).slice(0, CANVAS_UPLOAD_MAX);
    if(!imgs.length) return;
    if(opts.group && imgs.length > 1){
        const source = nodes.find(n => n.id === nodeId);
        pushUndo();
        const point = source ? {x:Number(source.x || 0), y:Number(source.y || 0)} : defaultPoint(0, 0);
        const outgoing = connections.filter(c => c.from === source?.id).map(c => c.to);
        const incoming = connections.filter(c => c.to === source?.id).map(c => c.from);
        const created = await uploadImageGroup(imgs, point);
        const group = created?.group;
        if(source && created?.length > 1){
            const remaining = window.WorkbenchCanvasGraphFragment.removeGraphRecords({nodes, connections, removeIds:[source.id]});
            nodes = remaining.nodes;
            connections = remaining.connections;
            if(group){
                outgoing.forEach(toId => {
                    if(canConnect(group.id, toId) && !connections.some(c => c.from === group.id && c.to === toId)){
                        connections.push({id:uid('c'), from:group.id, to:toId});
                    }
                });
                incoming.forEach(fromId => {
                    if(canConnect(fromId, group.id) && !connections.some(c => c.from === fromId && c.to === group.id)){
                        connections.push({id:uid('c'), from:fromId, to:group.id});
                    }
                });
            }
            selected.delete(source.id);
            render();
            scheduleSave();
        }
        return;
    }
    const form = new FormData();
    form.append('files', imgs[0]);
    const data = await fetch('/api/ai/upload', {method:'POST', body:form}).then(r=>r.json());
    const file = data.files?.[0];
    const node = nodes.find(n => n.id === nodeId);
    if(file && node){
        node.url = file.url;
        node.name = file.name;
        node.mediaKind = file.kind || mediaKindForUpload(imgs[0]);
        render();
        scheduleSave();
    }
}
function setImageNodeFromOutput(nodeId, url){
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'image' || !url || isVideoUrl(url) || isAudioUrl(url)) return;
    pushUndo();
    node.url = url;
    node.name = outputImageName(url);
    node.mediaKind = 'image';
    render();
    scheduleSave();
}
function clearImageNode(nodeId, event=null){
    if(event){
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
    }
    const node = nodes.find(n => n.id === nodeId);
    if(!node || node.type !== 'image') return;
    pushUndo();
    node.url = '';
    node.mediaKind = 'image';
    node.name = '空白图片';
    render();
    scheduleSave();
}
function pickImageForNode(nodeId){
    pickMediaForNode(nodeId);
}
function cropBounds(){
    const img = document.getElementById('cropImage');
    return {w:img.clientWidth || 1, h:img.clientHeight || 1};
}
function editDrawCanvas(){
    return document.getElementById('editDrawCanvas');
}
function editTextCanvas(){
    return document.getElementById('editTextCanvas');
}
function editTextContext(){
    return editTextCanvas()?.getContext('2d') || null;
}
function selectedEditTextItem(){
    return editTextItems.find(item => item.id === editTextSelectedId) || null;
}
function defaultEditTextText(){
    return langIsEn() ? 'Double-click to edit' : '双击编辑';
}
function editTextSizeFromBrush(){
    return WorkbenchCanvasMediaTextOverlay.sizeOf({size:editBrushSize() * 2}, 14);
}
function createEditTextItem(text, point, preset={}){
    return WorkbenchCanvasMediaTextOverlay.create(text, point, {createId:()=>uid('txt'), defaultText:defaultEditTextText, brushSize:editBrushSize(), size:preset.size, color:preset.color || brushColor()});
}
function textItemFont(item){
    return WorkbenchCanvasMediaTextOverlay.font(item);
}
function measureEditTextItem(item, ctx=editTextContext()){
    return WorkbenchCanvasMediaTextOverlay.measure(item, ctx);
}
function hitEditTextItem(point){
    const ctx = editTextContext();
    return WorkbenchCanvasMediaTextOverlay.hit(editTextItems, point, ctx);
}
function renderEditTextCanvas(){
    const canvasEl = editTextCanvas();
    const ctx = editTextContext();
    if(!canvasEl || !ctx) return;
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    editTextItems.forEach(item => {
        if(!item?.text) return;
        const selected = item.id === editTextSelectedId;
        const box = measureEditTextItem(item, ctx);
        ctx.save();
        ctx.font = textItemFont(item);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = item.color || brushColor();
        ctx.strokeStyle = 'rgba(255,255,255,.92)';
        ctx.lineWidth = Math.max(2, (Number(item.size) || 28) / 8);
        ctx.strokeText(String(item.text || ''), item.x, item.y);
        ctx.fillText(String(item.text || ''), item.x, item.y);
        if(selected){
            ctx.setLineDash([7, 5]);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = 'rgba(15,23,42,.72)';
            ctx.strokeRect(box.x, box.y, box.w, box.h);
            ctx.setLineDash([]);
            ctx.fillStyle = 'rgba(15,23,42,.92)';
            ctx.beginPath();
            ctx.arc(item.x + box.w / 2 - box.pad, item.y - box.h / 2 + box.pad, 3.5, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    });
    positionEditTextInlineEditor();
}
function syncTextToolState(force=false){
    const selected = selectedEditTextItem();
    const cropCanvasEl = document.getElementById('cropCanvas');
    cropCanvasEl?.classList.toggle('text-mode', imageEditMode === 'brush' && brushTool === 'text');
}
function syncSelectedEditTextStyleFromBrush(){
    if(imageEditMode !== 'brush' || brushTool !== 'text' || editTextInlineEditor) return;
    const item = selectedEditTextItem();
    if(!item) return;
    const nextSize = editTextSizeFromBrush();
    const nextColor = brushColor();
    if(item.size === nextSize && item.color === nextColor) return;
    beginTextEditChange();
    item.size = nextSize;
    item.color = nextColor;
    renderEditTextCanvas();
    syncTextToolState(true);
}
function beginTextEditChange(){
    if(editTextDirty) return;
    pushEditDrawHistory();
    editTextDirty = true;
}
function setSelectedEditTextItem(id){
    editTextSelectedId = id || '';
    renderEditTextCanvas();
    syncTextToolState(true);
}
function confirmSelectedEditTextItem(){
    const selected = selectedEditTextItem();
    if(!selected) return false;
    if(!String(selected.text || '').trim()){
        editTextItems = editTextItems.filter(item => item.id !== selected.id);
    }
    editTextSelectedId = '';
    editTextDrag = null;
    editTextDirty = false;
    renderEditTextCanvas();
    syncTextToolState(true);
    return true;
}
function editTextCanvasScale(){
    const canvasEl = editTextCanvas();
    const rect = canvasEl?.getBoundingClientRect?.();
    return {
        x:(rect?.width || canvasEl?.width || 1) / Math.max(1, canvasEl?.width || 1),
        y:(rect?.height || canvasEl?.height || 1) / Math.max(1, canvasEl?.height || 1),
        rect
    };
}
function selectInlineEditorText(el){
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}
function inlineEditorText(){
    return String(editTextInlineEditor?.el?.innerText || editTextInlineEditor?.el?.textContent || '').replace(/\u00a0/g, ' ');
}
function autosizeEditTextInlineEditor(){
    const editor = editTextInlineEditor;
    if(!editor?.el) return;
    const el = editor.el;
    el.style.width = 'auto';
    el.style.height = 'auto';
    const minW = Number(editor.minW || 48);
    const minH = Number(editor.minH || 28);
    el.style.width = `${Math.max(minW, el.scrollWidth + 10)}px`;
    el.style.height = `${Math.max(minH, el.scrollHeight + 4)}px`;
}
function positionEditTextInlineEditor(){
    const editor = editTextInlineEditor;
    if(!editor?.el) return;
    const item = editTextItems.find(x => x.id === editor.itemId);
    const canvasEl = editTextCanvas();
    const cropCanvasEl = document.getElementById('cropCanvas');
    if(!item || !canvasEl || !cropCanvasEl) return;
    const ctx = editTextContext();
    const box = measureEditTextItem(item, ctx);
    const scale = editTextCanvasScale();
    const hostRect = cropCanvasEl.getBoundingClientRect();
    const canvasRect = scale.rect || canvasEl.getBoundingClientRect();
    const left = canvasRect.left - hostRect.left + box.x * scale.x;
    const top = canvasRect.top - hostRect.top + box.y * scale.y;
    const w = Math.max(48, box.w * scale.x);
    const h = Math.max(28, box.h * scale.y);
    editor.minW = w;
    editor.minH = h;
    editor.el.style.left = `${left}px`;
    editor.el.style.top = `${top}px`;
    editor.el.style.minWidth = `${w}px`;
    editor.el.style.minHeight = `${h}px`;
    editor.el.style.font = `900 ${Math.max(10, (Number(item.size) || 28) * scale.y)}px Arial, sans-serif`;
    editor.el.style.color = item.color || brushColor();
    autosizeEditTextInlineEditor();
}
function removeEditTextInlineEditor(commit=true){
    const editor = editTextInlineEditor;
    if(!editor) return;
    const item = editTextItems.find(x => x.id === editor.itemId);
    const next = inlineEditorText().trim();
    editTextInlineEditor = null;
    editor.el.remove();
    if(!item) return;
    if(commit){
        if(next !== String(editor.before || '')){
            beginTextEditChange();
            if(next){
                item.text = next;
            } else {
                editTextItems = editTextItems.filter(x => x.id !== item.id);
                editTextSelectedId = '';
            }
        }
    } else {
        item.text = editor.before || item.text || defaultEditTextText();
    }
    editTextDirty = false;
    renderEditTextCanvas();
    syncTextToolState(true);
}
function beginEditTextInline(item){
    if(!item) return;
    removeEditTextInlineEditor(true);
    editTextSelectedId = item.id;
    const host = document.getElementById('cropCanvas');
    if(!host) return;
    const el = document.createElement('div');
    el.className = 'edit-text-inline';
    el.contentEditable = 'true';
    el.spellcheck = false;
    el.textContent = item.text || defaultEditTextText();
    host.appendChild(el);
    editTextInlineEditor = {el, itemId:item.id, before:item.text || ''};
    positionEditTextInlineEditor();
    el.addEventListener('input', autosizeEditTextInlineEditor);
    el.addEventListener('keydown', event => {
        if(event.key === 'Enter' && !event.shiftKey){
            event.preventDefault();
            removeEditTextInlineEditor(true);
        } else if(event.key === 'Escape'){
            event.preventDefault();
            removeEditTextInlineEditor(false);
        }
    });
    el.addEventListener('blur', () => removeEditTextInlineEditor(true));
    requestAnimationFrame(() => {
        el.focus();
        selectInlineEditorText(el);
    });
    renderEditTextCanvas();
    syncTextToolState(true);
}
function editTextPoint(event){
    return editDrawPoint(event);
}
function beginEditText(event){
    if(imageEditMode !== 'brush' || brushTool !== 'text') return;
    event.preventDefault();
    event.stopPropagation();
    removeEditTextInlineEditor(true);
    const canvasEl = editTextCanvas();
    const point = editTextPoint(event);
    const hit = hitEditTextItem(point);
    if(hit){
        editTextSelectedId = hit.id;
        editTextDrag = {
            id: hit.id,
            pointerId: event.pointerId,
            startX: hit.x,
            startY: hit.y,
            sx: event.clientX,
            sy: event.clientY,
            moved: false,
            hasHistory: false
        };
        canvasEl.setPointerCapture?.(event.pointerId);
        canvasEl.style.cursor = 'grabbing';
        syncTextToolState(true);
        renderEditTextCanvas();
        return;
    }
    if(selectedEditTextItem()){
        confirmSelectedEditTextItem();
        return;
    }
    beginTextEditChange();
    const item = createEditTextItem(defaultEditTextText(), point, {color:brushColor(), size:editTextSizeFromBrush()});
    editTextItems.push(item);
    editTextSelectedId = item.id;
    canvasEl.style.cursor = 'text';
    renderEditTextCanvas();
    syncTextToolState(true);
}
function updateEditTextCursor(event){
    const canvasEl = editTextCanvas();
    if(!canvasEl || imageEditMode !== 'brush' || brushTool !== 'text') return;
    const hit = hitEditTextItem(editTextPoint(event));
    canvasEl.style.cursor = hit ? 'move' : 'text';
}
function moveEditText(event){
    if(!editTextDrag){
        updateEditTextCursor(event);
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    const item = editTextItems.find(x => x.id === editTextDrag.id);
    if(!item) return;
    const dx = event.clientX - editTextDrag.sx;
    const dy = event.clientY - editTextDrag.sy;
    if(!editTextDrag.moved && Math.abs(dx) + Math.abs(dy) < 2) return;
    editTextDrag.moved = true;
    if(!editTextDrag.hasHistory){
        beginTextEditChange();
        editTextDrag.hasHistory = true;
    }
    const canvasEl = editTextCanvas();
    const rect = canvasEl?.getBoundingClientRect?.();
    const scaleX = canvasEl ? canvasEl.width / Math.max(1, rect?.width || canvasEl.width) : 1;
    const scaleY = canvasEl ? canvasEl.height / Math.max(1, rect?.height || canvasEl.height) : 1;
    item.x = editTextDrag.startX + dx * scaleX;
    item.y = editTextDrag.startY + dy * scaleY;
    renderEditTextCanvas();
}
function endEditText(event){
    if(editTextDrag && event?.pointerId != null) editTextCanvas()?.releasePointerCapture?.(event.pointerId);
    editTextDrag = null;
    editTextDirty = false;
    renderEditTextCanvas();
    syncTextToolState(true);
    if(event) updateEditTextCursor(event);
}
function editTextHasContent(){
    return editTextItems.some(item => String(item?.text || '').trim().length > 0);
}
function resizeEditTextCanvas(){
    const img = document.getElementById('cropImage');
    const canvasEl = editTextCanvas();
    if(!img || !canvasEl) return;
    const projection = WorkbenchCanvasMediaTools.editorCanvasProjection(img.naturalWidth, img.naturalHeight, img.clientWidth, img.clientHeight);
    if(canvasEl.width !== projection.width) canvasEl.width = projection.width;
    if(canvasEl.height !== projection.height) canvasEl.height = projection.height;
    canvasEl.style.width = `${projection.cssWidth}px`;
    canvasEl.style.height = `${projection.cssHeight}px`;
    renderEditTextCanvas();
}
function resizeEditDrawCanvas(){
    const img = document.getElementById('cropImage');
    const canvasEl = editDrawCanvas();
    const projection = WorkbenchCanvasMediaTools.editorCanvasProjection(img.naturalWidth, img.naturalHeight, img.clientWidth, img.clientHeight);
    if(canvasEl.width !== projection.width || canvasEl.height !== projection.height){
        canvasEl.width = projection.width;
        canvasEl.height = projection.height;
    }
    canvasEl.style.width = `${projection.cssWidth}px`;
    canvasEl.style.height = `${projection.cssHeight}px`;
    resizeEditTextCanvas();
    if(imageEditMode === 'grid') refreshGridSplitPreview();
}
function setImageEditMode(mode, userTouched=false){
    if(userTouched) imageEditModeTouched = true;
    const prevImageEditMode = imageEditMode;
    if(mode !== 'brush') removeEditTextInlineEditor(true);
    const projection = window.WorkbenchCanvasMediaEditorState.uiProjection(mode, prevImageEditMode);
    const presentation = window.WorkbenchCanvasMediaEditorState.presentation(projection.mode);
    imageEditMode = projection.mode;
    const isPreview = projection.preview;
    const cropCanvasEl = document.getElementById('cropCanvas');
    cropCanvasEl.classList.toggle('preview-mode', isPreview);
    cropCanvasEl.classList.toggle('mask-mode', projection.activeModes.mask);
    cropCanvasEl.classList.toggle('brush-mode', projection.activeModes.brush);
    cropCanvasEl.classList.toggle('resize-mode', projection.activeModes.resize);
    cropCanvasEl.classList.toggle('grid-mode', projection.activeModes.grid);
    cropCanvasEl.classList.toggle('outpaint-mode', projection.activeModes.outpaint);
    _syncGridCustomCursor();
    document.querySelectorAll('[data-image-edit-mode]').forEach(btn => btn.classList.toggle('active', btn.dataset.imageEditMode === imageEditMode));
    document.getElementById('imageCropTools')?.classList.toggle('active', projection.activeModes.crop);
    document.getElementById('imageMaskTools').classList.toggle('active', projection.activeModes.mask);
    document.getElementById('imageBrushTools').classList.toggle('active', projection.activeModes.brush);
    document.getElementById('imageResizeTools')?.classList.toggle('active', projection.activeModes.resize);
    document.getElementById('imageGridTools').classList.toggle('active', projection.activeModes.grid);
    syncGridGapValue();
    syncImageResizeControls();
    const title = document.getElementById('imageEditTitle');
    const sub = document.getElementById('imageEditSub');
    const apply = document.getElementById('imageEditApplyBtn');
    if(isPreview){
        apply.style.display = 'none';
        title.textContent = tr('canvas.previewImage');
        sub.textContent = tr('canvas.previewHint');
    } else {
        apply.style.display = projection.applyVisible ? '' : 'none';
        if(imageEditMode === 'resize'){
            title.textContent = '缩放图片';
            sub.textContent = '选择缩小倍数，应用会替换当前原图';
            apply.innerHTML = `<i data-lucide="minimize-2" class="w-4 h-4"></i><span>应用缩放</span>`;
        } else {
            title.textContent = tr(projection.titleKey);
            sub.textContent = tr(projection.subKey);
            apply.innerHTML = `<i data-lucide="${presentation.icon}" class="w-4 h-4"></i><span>${tr(presentation.labelKey)}</span>`;
        }
    }
    resizeEditDrawCanvas();
    if(isPreview) clearEditDrawing(true);
    else if(projection.refreshGrid) refreshGridSplitPreview();
    else if(projection.resetOutpaint) resetOutpaintBox();
    else if(projection.clearDrawing) clearEditDrawing(true);
    syncEditDrawingHistoryButtons();
    syncBrushToolButtons();
    syncTextToolState(true);
    refreshIcons();
}
function editDrawSnapshot(){
    const canvasEl = editDrawCanvas();
    return {
        imageData: canvasEl.getContext('2d').getImageData(0, 0, canvasEl.width, canvasEl.height),
        labelCounter: brushLabelCounter,
        textItems: editTextItems.map(item => ({...item})),
        textSelectedId: editTextSelectedId || '',
    };
}
function restoreEditDrawSnapshot(snapshot){
    if(!snapshot) return;
    removeEditTextInlineEditor(false);
    const canvasEl = editDrawCanvas();
    const imageData = snapshot.imageData || snapshot;
    canvasEl.getContext('2d').putImageData(imageData, 0, 0);
    if(snapshot.labelCounter) brushLabelCounter = snapshot.labelCounter;
    editTextItems = (snapshot.textItems || []).map(item => ({...item}));
    editTextSelectedId = snapshot.textSelectedId || '';
    renderEditTextCanvas();
    syncTextToolState(true);
}
function pushEditDrawHistory(){
    editDrawUndoStack.push(editDrawSnapshot());
    if(editDrawUndoStack.length > EDIT_DRAW_HISTORY_MAX) editDrawUndoStack.shift();
    editDrawRedoStack = [];
    syncEditDrawingHistoryButtons();
}
function syncEditDrawingHistoryButtons(){
    ['maskUndoBtn','brushUndoBtn'].forEach(id => {
        const btn = document.getElementById(id);
        if(btn){ btn.disabled = !editDrawUndoStack.length; btn.style.opacity = editDrawUndoStack.length ? '1' : '.42'; }
    });
    ['maskRedoBtn','brushRedoBtn'].forEach(id => {
        const btn = document.getElementById(id);
        if(btn){ btn.disabled = !editDrawRedoStack.length; btn.style.opacity = editDrawRedoStack.length ? '1' : '.42'; }
    });
}
function undoEditDrawing(){
    if(!editDrawUndoStack.length) return;
    editDrawRedoStack.push(editDrawSnapshot());
    restoreEditDrawSnapshot(editDrawUndoStack.pop());
    syncEditDrawingHistoryButtons();
}
function redoEditDrawing(){
    if(!editDrawRedoStack.length) return;
    editDrawUndoStack.push(editDrawSnapshot());
    restoreEditDrawSnapshot(editDrawRedoStack.pop());
    syncEditDrawingHistoryButtons();
}
function clearEditDrawing(silent=false){
    removeEditTextInlineEditor(false);
    const canvasEl = editDrawCanvas();
    if(!silent && editCanvasHasPixels()) pushEditDrawHistory();
    canvasEl.getContext('2d').clearRect(0, 0, canvasEl.width, canvasEl.height);
    const textCanvasEl = editTextCanvas();
    textCanvasEl?.getContext('2d')?.clearRect(0, 0, textCanvasEl.width, textCanvasEl.height);
    editTextItems = [];
    editTextSelectedId = '';
    editTextDrag = null;
    editTextDirty = false;
    brushLabelCounter = 1;
    syncTextToolState(true);
    syncEditDrawingHistoryButtons();
}
function resetEditDrawingHistory(){
    removeEditTextInlineEditor(false);
    editDrawUndoStack = [];
    editDrawRedoStack = [];
    brushLabelCounter = 1;
    editTextItems = [];
    editTextSelectedId = '';
    editTextDrag = null;
    editTextDirty = false;
    renderEditTextCanvas();
    syncTextToolState(true);
    syncEditDrawingHistoryButtons();
}
function setBrushTool(tool){
    if(tool !== 'text') removeEditTextInlineEditor(true);
    const projection = window.WorkbenchCanvasMediaEditorState.brushToolProjection(tool, imageEditMode);
    brushTool = projection.tool;
    syncBrushToolButtons();
    syncTextToolState(true);
}
function syncBrushToolButtons(){
    document.querySelectorAll('[data-brush-tool]').forEach(btn => {
        const active = btn.dataset.brushTool === brushTool;
        btn.classList.toggle('primary', active);
        btn.classList.toggle('secondary', !active);
    });
    const cropCanvasEl = document.getElementById('cropCanvas');
    cropCanvasEl?.classList.toggle('text-mode', window.WorkbenchCanvasMediaEditorState.brushToolProjection(brushTool, imageEditMode).textMode);
}
function editDrawPoint(event){
    const canvasEl = editDrawCanvas();
    const rect = canvasEl.getBoundingClientRect();
    return WorkbenchCanvasMediaTools.canvasPoint(event.clientX, event.clientY, rect.left, rect.top, rect.width, rect.height, canvasEl.width, canvasEl.height);
}
function gridCustomLineHit(point){
    const canvasEl = editDrawCanvas();
    return WorkbenchCanvasMediaTools.customLineHit(gridCustomLines, point, canvasEl.width, canvasEl.height);
}
function setGridCustomLinePos(index, point){
    const canvasEl = editDrawCanvas();
    WorkbenchCanvasMediaTools.setCustomLinePosition(gridCustomLines[index], point, canvasEl.width, canvasEl.height);
}
function editBrushSize(){
    const projection = WorkbenchCanvasMediaTools.brushControlProjection(
        imageEditMode,
        document.getElementById('maskBrushSize')?.value,
        document.getElementById('paintBrushSize')?.value,
        document.getElementById('paintBrushColor')?.value,
        MASK_BRUSH_ALPHA,
    );
    return projection.size;
}
function brushColor(){
    return WorkbenchCanvasMediaTools.brushControlProjection(
        imageEditMode,
        document.getElementById('maskBrushSize')?.value,
        document.getElementById('paintBrushSize')?.value,
        document.getElementById('paintBrushColor')?.value,
        MASK_BRUSH_ALPHA,
    ).color;
}
const MASK_BRUSH_ALPHA = 115;
const MASK_BRUSH_COLOR = `rgba(255,255,255,${MASK_BRUSH_ALPHA / 255})`;
function setupDrawStyle(ctx){
    Object.assign(ctx, WorkbenchCanvasMediaTools.brushStyle(imageEditMode, editBrushSize(), brushColor(), MASK_BRUSH_ALPHA));
}
function normalizeMaskPreviewCanvas(canvasEl=editDrawCanvas()){
    if(imageEditMode !== 'mask' || !canvasEl?.width || !canvasEl?.height) return;
    const ctx = canvasEl.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvasEl.width, canvasEl.height);
    const data = imageData.data;
    let changed = false;
    for(let i = 0; i < data.length; i += 4){
        if(data[i + 3] <= 0) continue;
        data[i] = 255;
        data[i + 1] = 255;
        data[i + 2] = 255;
        if(data[i + 3] > MASK_BRUSH_ALPHA) data[i + 3] = MASK_BRUSH_ALPHA;
        changed = true;
    }
    if(changed) ctx.putImageData(imageData, 0, 0);
}
function circledNumber(n){
    return window.WorkbenchCanvasMediaTools.circledNumber(n);
}
function drawBrushShape(ctx, start, end, preview=false){
    setupDrawStyle(ctx);
    const x = Math.min(start.x, end.x);
    const y = Math.min(start.y, end.y);
    const w = Math.abs(end.x - start.x);
    const h = Math.abs(end.y - start.y);
    if(brushTool === 'rect'){
        ctx.strokeRect(x, y, w, h);
    } else if(brushTool === 'ellipse'){
        ctx.beginPath();
        ctx.ellipse(x + w / 2, y + h / 2, Math.max(1, w / 2), Math.max(1, h / 2), 0, 0, Math.PI * 2);
        ctx.stroke();
    }
}
function drawNumberLabel(point){
    const canvasEl = editDrawCanvas();
    const ctx = canvasEl.getContext('2d');
    const size = Math.max(18, editBrushSize() * 2.2);
    const text = circledNumber(brushLabelCounter++);
    const style = WorkbenchCanvasMediaTools.labelStyle(size, brushColor());
    setupDrawStyle(ctx);
    ctx.save();
    ctx.font = style.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineWidth = style.lineWidth;
    ctx.strokeStyle = style.strokeStyle;
    ctx.strokeText(text, point.x, point.y);
    ctx.fillStyle = style.fillStyle;
    ctx.fillText(text, point.x, point.y);
    ctx.restore();
}
function beginEditDraw(event){
    if(imageEditMode === 'crop') return;
    if(imageEditMode === 'grid'){
        if(!gridCustomMode) return;
        // 自定义模式：拖动已有线，或点击空白处放置新线
        event.preventDefault();
        event.stopPropagation();
        const canvasEl = editDrawCanvas();
        canvasEl.setPointerCapture?.(event.pointerId);
        const point = editDrawPoint(event);
        const hitIndex = gridCustomLineHit(point);
        gridCustomHistory.push([...gridCustomLines.map(line => ({...line}))]);
        if(hitIndex >= 0){
            gridCustomDrag = {index: hitIndex, pointerId: event.pointerId};
            setGridCustomLinePos(hitIndex, point);
            refreshGridSplitPreview();
            _syncGridCustomUndoBtn();
            return;
        }
        const rect = canvasEl.getBoundingClientRect();
        const fracX = Math.max(0.001, Math.min(0.999, (event.clientX - rect.left) / rect.width));
        const fracY = Math.max(0.001, Math.min(0.999, (event.clientY - rect.top) / rect.height));
        gridCustomLines.push({type: gridCustomOrientation, pos: gridCustomOrientation === 'h' ? fracY : fracX});
        gridCustomDrag = {index: gridCustomLines.length - 1, pointerId: event.pointerId};
        _syncGridCustomUndoBtn();
        refreshGridSplitPreview();
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    const canvasEl = editDrawCanvas();
    canvasEl.setPointerCapture?.(event.pointerId);
    const ctx = canvasEl.getContext('2d');
    const p = editDrawPoint(event);
    pushEditDrawHistory();
    if(imageEditMode === 'brush' && brushTool === 'label'){
        drawNumberLabel(p);
        editDrawState = null;
        canvasEl.releasePointerCapture?.(event.pointerId);
        syncEditDrawingHistoryButtons();
        return;
    }
    editDrawState = {x:p.x, y:p.y, sx:p.x, sy:p.y, pointerId:event.pointerId, snapshot:(imageEditMode === 'brush' && brushTool !== 'free') ? editDrawSnapshot() : null};
    setupDrawStyle(ctx);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x + 0.01, p.y + 0.01);
    if(imageEditMode === 'mask' || brushTool === 'free') ctx.stroke();
    normalizeMaskPreviewCanvas(canvasEl);
}
function moveEditDraw(event){
    if(imageEditMode === 'grid' && gridCustomMode && gridCustomDrag){
        event.preventDefault();
        event.stopPropagation();
        setGridCustomLinePos(gridCustomDrag.index, editDrawPoint(event));
        refreshGridSplitPreview();
        return;
    }
    if(!editDrawState || imageEditMode === 'crop' || imageEditMode === 'grid') return;
    event.preventDefault();
    event.stopPropagation();
    const ctx = editDrawCanvas().getContext('2d');
    const p = editDrawPoint(event);
    if(imageEditMode === 'brush' && brushTool !== 'free'){
        restoreEditDrawSnapshot(editDrawState.snapshot);
        drawBrushShape(ctx, {x:editDrawState.sx, y:editDrawState.sy}, p, true);
        return;
    }
    setupDrawStyle(ctx);
    ctx.beginPath();
    ctx.moveTo(editDrawState.x, editDrawState.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    editDrawState.x = p.x;
    editDrawState.y = p.y;
    normalizeMaskPreviewCanvas();
}
function endEditDraw(event){
    if(editDrawState && event?.pointerId != null) editDrawCanvas().releasePointerCapture?.(event.pointerId);
    if(gridCustomDrag && event?.pointerId != null) editDrawCanvas().releasePointerCapture?.(event.pointerId);
    editDrawState = null;
    gridCustomDrag = null;
    syncEditDrawingHistoryButtons();
}
function editCanvasHasPixels(){
    if(editTextHasContent()) return true;
    return WorkbenchCanvasMediaTools.canvasHasPixels(editDrawCanvas());
}
function syncGridGapValue(){
    const input = document.getElementById('gridGapSize');
    const value = Math.max(0, Math.min(240, Number(input?.value || 0)));
    if(input) input.value = value;
    const label = document.getElementById('gridGapValue');
    if(label) label.textContent = String(value);
    return value;
}
function gridSplitSettings(){
    const settings = WorkbenchCanvasMediaTools.normalizeGridSettings(
        document.getElementById('gridHorizontalLines')?.value,
        document.getElementById('gridVerticalLines')?.value,
        syncGridGapValue(),
    );
    return settings;
}
function gridSplitRects(width, height){
    if(gridCustomMode) return gridSplitRectsCustom(width, height);
    const {rows, cols, gap} = gridSplitSettings();
    return window.WorkbenchCanvasMediaTools.gridSplitRects(width, height, rows, cols, gap);
}
function gridSplitRectsCustom(width, height){
    const gap = Math.max(0, Math.min(240, Number(document.getElementById('gridGapSize')?.value || 0)));
    return window.WorkbenchCanvasMediaTools.customGridRects(width, height, gridCustomLines, gap);
}
function gridLayoutFromRects(rects){
    return window.WorkbenchCanvasMediaTools.gridLayout(rects, uid('grid'));
}
function applyGridPreset(rows, cols){
    gridCustomMode = false;
    gridCustomLines = [];
    gridCustomHistory = [];
    gridCustomDrag = null;
    const h = document.getElementById('gridHorizontalLines');
    const v = document.getElementById('gridVerticalLines');
    if(h){ h.disabled = false; h.value = String(Math.max(0, Number(rows || 1) - 1)); }
    if(v){ v.disabled = false; v.value = String(Math.max(0, Number(cols || 1) - 1)); }
    const toggle = document.getElementById('gridCustomToggle');
    const custom = document.getElementById('gridCustomControls');
    const regular = document.getElementById('gridRegularControls');
    if(toggle){
        toggle.classList.remove('primary');
        toggle.classList.add('secondary');
    }
    if(custom) custom.style.display = 'none';
    if(regular) regular.style.display = 'contents';
    _syncGridCustomCursor();
    _syncGridCustomUndoBtn();
    refreshGridSplitPreview();
}
// ——— 自定义宫格辅助函数 ———
function toggleGridCustomMode(){
    gridCustomMode = !gridCustomMode;
    if(gridCustomMode){ gridCustomLines = []; gridCustomHistory = []; } // 进入自定义时清空旧线及历史
    gridCustomDrag = null;
    const toggle = document.getElementById('gridCustomToggle');
    const regular = document.getElementById('gridRegularControls');
    const custom = document.getElementById('gridCustomControls');
    toggle.classList.toggle('primary', gridCustomMode);
    toggle.classList.toggle('secondary', !gridCustomMode);
    // 禁用/启用常规输入
    ['gridHorizontalLines','gridVerticalLines'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.disabled = gridCustomMode;
    });
    if(custom) custom.style.display = gridCustomMode ? 'flex' : 'none';
    _syncGridCustomCursor();
    _syncGridCustomUndoBtn();
    refreshGridSplitPreview();
}
function setGridCustomOrientation(orient){
    gridCustomOrientation = orient;
    document.getElementById('gridOrientH').classList.toggle('primary', orient === 'h');
    document.getElementById('gridOrientH').classList.toggle('secondary', orient !== 'h');
    document.getElementById('gridOrientV').classList.toggle('primary', orient === 'v');
    document.getElementById('gridOrientV').classList.toggle('secondary', orient !== 'v');
    _syncGridCustomCursor();
}
function clearGridCustomLines(){
    gridCustomHistory = [];
    gridCustomLines = [];
    gridCustomDrag = null;
    _syncGridCustomUndoBtn();
    refreshGridSplitPreview();
}
function undoGridCustomLine(){
    if(!gridCustomHistory.length) return;
    gridCustomLines = gridCustomHistory.pop();
    gridCustomDrag = null;
    _syncGridCustomUndoBtn();
    refreshGridSplitPreview();
}
function _syncGridCustomUndoBtn(){
    const btn = document.getElementById('gridUndoBtn');
    if(!btn) return;
    btn.disabled = gridCustomHistory.length === 0;
    btn.style.opacity = gridCustomHistory.length === 0 ? '0.4' : '1';
}
function clampImageResizeScale(value){
    return window.WorkbenchCanvasMediaTools.clampResizeScale(value);
}
function imageResizeDimensions(){
    const img = document.getElementById('cropImage');
    return window.WorkbenchCanvasMediaTools.resizeControlProjection(img?.naturalWidth, img?.naturalHeight, imageResizeScale);
}
function syncImageResizeControls(){
    imageResizeScale = clampImageResizeScale(imageResizeScale);
    const range = document.getElementById('imageResizeScaleRange');
    const input = document.getElementById('imageResizeScaleInput');
    const label = document.getElementById('imageResizeResolution');
    const overlay = document.getElementById('resizeResolutionOverlay');
    const dims = imageResizeDimensions();
    const text = dims.text;
    if(range && Number(range.value) !== dims.scale) range.value = String(dims.scale);
    if(input && Number(input.value) !== dims.scale) input.value = String(dims.scale);
    if(label) label.textContent = text;
    if(overlay) overlay.textContent = text;
}
function setImageResizeScale(value){
    imageResizeScale = clampImageResizeScale(value);
    syncImageResizeControls();
}
async function resizedImageBlobFromEditor(){
    const img = document.getElementById('cropImage');
    if(!img?.naturalWidth || !img?.naturalHeight) return null;
    const dims = imageResizeDimensions();
    return WorkbenchCanvasMediaTools.resizedImageBlob(img, dims, document);
}
// ——— 图片缩放 ———
function applyImageEditZoom(){
    if(!imageEditBaseW) return;
    const img = document.getElementById('cropImage');
    const oldW = img.clientWidth;
    img.style.maxWidth = 'none';
    img.style.maxHeight = 'none';
    const zoomProjection = WorkbenchCanvasMediaTools.editorZoomProjection(imageEditBaseW, imageEditBaseH, imageEditZoom);
    img.style.width = `${zoomProjection.width}px`;
    img.style.height = `${zoomProjection.height}px`;
    resizeEditDrawCanvas();
    // 按比例同步裁剪框位置
    if(cropState && oldW > 0){
        const scale = img.clientWidth / oldW;
        Object.assign(cropState, WorkbenchCanvasMediaTools.scaleCropRect(cropState, scale));
        clampCrop();
        renderCropBox();
    }
    if(imageEditMode === 'grid') refreshGridSplitPreview();
    syncImageResizeControls();
    syncImageEditOverflow();
    _updateZoomLabel();
}
function syncImageEditOverflow(){
    const stage = document.getElementById('imageEditStage');
    const crop = document.getElementById('cropCanvas');
    if(!stage || !crop) return;
    const rect = crop.getBoundingClientRect();
    const pad = 36;
    const projection = WorkbenchCanvasMediaTools.editorOverflowProjection(rect.width, rect.height, stage.clientWidth, stage.clientHeight, pad);
    stage.classList.toggle('overflowing', projection.overflowing);
    stage.classList.toggle('overflow-x', projection.overflowX);
    stage.classList.toggle('overflow-y', projection.overflowY);
}
function resetImageEditZoom(){
    const stage = document.getElementById('imageEditStage');
    imageEditZoom = 1.0;
    applyImageEditZoom();
    if(stage){ stage.scrollLeft = 0; stage.scrollTop = 0; }
}
function _updateZoomLabel(){
    const el = document.getElementById('imageEditZoomLabel');
    if(el) el.textContent = WorkbenchCanvasMediaTools.editorZoomProjection(0, 0, imageEditZoom).label;
}
function _syncGridCustomCursor(){
    const cropCanvasEl = document.getElementById('cropCanvas');
    cropCanvasEl.classList.toggle('grid-custom-h', imageEditMode === 'grid' && gridCustomMode && gridCustomOrientation === 'h');
    cropCanvasEl.classList.toggle('grid-custom-v', imageEditMode === 'grid' && gridCustomMode && gridCustomOrientation === 'v');
}
function refreshGridSplitPreview(){
    const canvasEl = editDrawCanvas();
    const ctx = canvasEl.getContext('2d');
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    if(imageEditMode !== 'grid') return;
    const countEl = document.getElementById('gridSplitCount');
    const lineWidth = Math.max(2, Math.round(Math.min(canvasEl.width, canvasEl.height) / 320));
    const drawGuideLine = (x1, y1, x2, y2) => {
        ctx.save();
        ctx.lineWidth = lineWidth + 2;
        ctx.strokeStyle = 'rgba(2,6,23,0.72)';
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = 'rgba(255,255,255,0.92)';
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        ctx.restore();
    };
    if(gridCustomMode){
        // 自定义模式：按已放置线渲染（包含空心范围预览）
        const gap = Math.max(0, Math.min(240, Number(document.getElementById('gridGapSize')?.value || 0)));
        const hLines = gridCustomLines.filter(l => l.type === 'h');
        const vLines = gridCustomLines.filter(l => l.type === 'v');
        if(countEl) countEl.textContent = tr('canvas.gridWillOutput').replace('{n}', (hLines.length + 1) * (vLines.length + 1));
        ctx.save();
        hLines.forEach(l => {
            const y = l.pos * canvasEl.height;
            if(gap > 0){
                drawGuideLine(0, y - gap / 2, canvasEl.width, y - gap / 2);
                drawGuideLine(0, y + gap / 2, canvasEl.width, y + gap / 2);
            } else {
                drawGuideLine(0, y, canvasEl.width, y);
            }
        });
        vLines.forEach(l => {
            const x = l.pos * canvasEl.width;
            if(gap > 0){
                drawGuideLine(x - gap / 2, 0, x - gap / 2, canvasEl.height);
                drawGuideLine(x + gap / 2, 0, x + gap / 2, canvasEl.height);
            } else {
                drawGuideLine(x, 0, x, canvasEl.height);
            }
        });
        ctx.restore();
        return;
    }
    // 常规模式
    const {rows, cols, gap} = gridSplitSettings();
    if(countEl) countEl.textContent = tr('canvas.gridWillOutput').replace('{n}', rows * cols);
    ctx.save();
    const scaleX = canvasEl.width;
    const scaleY = canvasEl.height;
    for(let i = 1; i < cols; i++){
        const x = i * scaleX / cols;
        if(gap > 0){
            drawGuideLine(x - gap / 2, 0, x - gap / 2, scaleY);
            drawGuideLine(x + gap / 2, 0, x + gap / 2, scaleY);
        } else {
            drawGuideLine(x, 0, x, scaleY);
        }
    }
    for(let i = 1; i < rows; i++){
        const y = i * scaleY / rows;
        if(gap > 0){
            drawGuideLine(0, y - gap / 2, scaleX, y - gap / 2);
            drawGuideLine(0, y + gap / 2, scaleX, y + gap / 2);
        } else {
            drawGuideLine(0, y, scaleX, y);
        }
    }
    ctx.restore();
}
function imageEditorOutputPoint(node, offsetY=0){
    return window.WorkbenchCanvasMediaTools.outputPoint(node, offsetY);
}
function imageEditorOutputNode(sourceNode){
    let out = WorkbenchCanvasMediaTools.findOutputNodeForSource(sourceNode.id, connections, nodes);
    if(!out){
        const p = imageEditorOutputPoint(sourceNode, 0);
        out = WorkbenchCanvasMediaTools.outputNodeProjection(p, uid);
        nodes.push(out);
    }
    return out;
}
function addGeneratedImageNode(file, sourceNode, suffix, offsetY=0, extra={}){
    const p = imageEditorOutputPoint(sourceNode, offsetY);
    const next = WorkbenchCanvasMediaTools.generatedImageNodeProjection(file, p, uid, suffix, extra);
    if(!next) return null;
    nodes.push(next);
    selected.clear();
    selected.add(next.id);
    return next;
}
function renderCropBox(){
    if(!cropState) return;
    const cropCanvasEl = document.getElementById('cropCanvas');
    const img = document.getElementById('cropImage');
    const draw = editDrawCanvas();
    const textCanvas = editTextCanvas();
    const projection = WorkbenchCanvasMediaTools.cropBoxProjection(cropState, imageEditMode);
    let boxX = projection.boxX;
    let boxY = projection.boxY;
    if(imageEditMode === 'outpaint' && cropCanvasEl && img){
        cropCanvasEl.style.width = `${Math.round(projection.boxWidth)}px`;
        cropCanvasEl.style.height = `${Math.round(projection.boxHeight)}px`;
        img.style.left = `${Math.round(projection.imageLeft)}px`;
        img.style.top = `${Math.round(projection.imageTop)}px`;
        if(draw){
            draw.style.left = img.style.left;
            draw.style.top = img.style.top;
        }
        if(textCanvas){
            textCanvas.style.left = img.style.left;
            textCanvas.style.top = img.style.top;
        }
        updateOutpaintResolutionLabel();
    } else if(cropCanvasEl && img){
        cropCanvasEl.style.width = '';
        cropCanvasEl.style.height = '';
        img.style.left = '';
        img.style.top = '';
        if(draw){
            draw.style.left = '';
            draw.style.top = '';
        }
        if(textCanvas){
            textCanvas.style.left = '';
            textCanvas.style.top = '';
        }
    }
    const box = document.getElementById('cropBox');
    box.style.left = `${boxX}px`;
    box.style.top = `${boxY}px`;
    box.style.width = `${projection.boxWidth}px`;
    box.style.height = `${projection.boxHeight}px`;
    const outpaintFrame = document.getElementById('outpaintFrame');
    if(outpaintFrame){
        outpaintFrame.style.left = `${projection.frameLeft}px`;
        outpaintFrame.style.top = `${projection.frameTop}px`;
        outpaintFrame.style.width = `${projection.frameWidth}px`;
        outpaintFrame.style.height = `${projection.frameHeight}px`;
    }
}
function outpaintNaturalSize(){
    const img = document.getElementById('cropImage');
    if(!img || !cropState) return {w:1, h:1};
    return WorkbenchCanvasMediaTools.outpaintNaturalSize(cropState, img.naturalWidth, img.naturalHeight, img.clientWidth, img.clientHeight);
}
function updateOutpaintResolutionLabel(){
    const label = document.getElementById('outpaintResolution');
    const cropCanvasEl = document.getElementById('cropCanvas');
    if(!label || !cropState) return;
    const size = outpaintNaturalSize();
    cropCanvasEl?.classList.toggle('outpaint-warning', exceedsFourKStandard(size.w, size.h));
    label.textContent = `${Math.round(size.w)} x ${Math.round(size.h)}`;
}
function clampOutpaint(){
    if(!cropState) return;
    const {w, h} = cropBounds();
    WorkbenchCanvasMediaTools.clampOutpaintState(cropState, w, h);
}
function resetOutpaintBox(){
    if(!cropState) return;
    const {w, h} = cropBounds();
    WorkbenchCanvasMediaTools.resetOutpaintState(cropState, w, h);
    renderCropBox();
}
function cropRatioFromPreset(preset){
    const bounds = cropBounds();
    return window.WorkbenchCanvasMediaTools.parseCropRatio(preset, bounds.w > 0 && bounds.h > 0 ? bounds.w / bounds.h : null);
}
function syncCropRatioButtons(){
    document.querySelectorAll('[data-crop-ratio]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.cropRatio === cropAspectPreset);
    });
}
function fitCropRectToAspect(ratio, sourceRect=null){
    const {w:boundsW, h:boundsH} = cropBounds();
    const rect = sourceRect || cropState || {x:0, y:0, w:boundsW, h:boundsH};
    const next = window.WorkbenchCanvasMediaTools.fitCropRectToAspect(ratio, boundsW, boundsH, rect);
    cropState.w = next.w;
    cropState.h = next.h;
    cropState.x = next.x;
    cropState.y = next.y;
    clampCrop();
}
function setCropAspectPreset(preset='free'){
    cropAspectPreset = preset || 'free';
    cropAspectRatio = cropRatioFromPreset(cropAspectPreset);
    syncCropRatioButtons();
    if(cropState && imageEditMode === 'crop' && cropAspectRatio){
        fitCropRectToAspect(cropAspectRatio);
        renderCropBox();
    }
}
function resetCropBox(){
    if(!cropState) return;
    if(imageEditMode === 'outpaint') return resetOutpaintBox();
    const {w, h} = cropBounds();
    const rect = WorkbenchCanvasMediaTools.initialCropRect(w, h);
    Object.assign(cropState, rect);
    if(cropAspectRatio) fitCropRectToAspect(cropAspectRatio, rect);
    renderCropBox();
}
function openImageEditor(nodeId, initialMode='crop'){
    const node = nodes.find(n => n.id === nodeId);
    if(!node?.url) return;
    if(mediaKindForNode(node) !== 'image') return;
    if(!['preview','crop','outpaint','mask','brush','resize','grid'].includes(initialMode)) initialMode = 'crop';
    cropState = {nodeId, x:0, y:0, w:0, h:0};
    // 重置自定义宫格状态
    gridCustomMode = false;
    gridCustomLines = [];
    gridCustomHistory = [];
    gridCustomDrag = null;
    gridCustomOrientation = 'h';
    imageEditZoom = 1.0;
    imageEditBaseW = 0;
    imageEditBaseH = 0;
    imageResizeScale = 0.5;
    imageEditModeTouched = false;
    cropAspectPreset = 'free';
    cropAspectRatio = null;
    syncCropRatioButtons();
    editTextItems = [];
    editTextSelectedId = '';
    editTextDrag = null;
    editTextDirty = false;
    const toggle = document.getElementById('gridCustomToggle');
    if(toggle){ toggle.classList.add('secondary'); toggle.classList.remove('primary'); }
    const custom = document.getElementById('gridCustomControls');
    if(custom) custom.style.display = 'none';
    ['gridHorizontalLines','gridVerticalLines'].forEach(id => { const el = document.getElementById(id); if(el) el.disabled = false; });
    const orientH = document.getElementById('gridOrientH');
    const orientV = document.getElementById('gridOrientV');
    if(orientH){ orientH.classList.add('primary'); orientH.classList.remove('secondary'); }
    if(orientV){ orientV.classList.add('secondary'); orientV.classList.remove('primary'); }
    _syncGridCustomUndoBtn();
    _updateZoomLabel();
    const modal = document.getElementById('imageEditModal');
    const img = document.getElementById('cropImage');
    img.style.width = '';
    img.style.height = '';
    img.style.maxWidth = '';
    img.style.maxHeight = '';
    modal.classList.add('open');
    const editorSrcToken = `${nodeId}:${Date.now()}`;
    img.dataset.editorSrcToken = editorSrcToken;
    img.onload = () => {
        // 记录 zoom=1 时的基础显示尺寸
        imageEditBaseW = img.clientWidth;
        imageEditBaseH = img.clientHeight;
        _updateZoomLabel();
        syncImageResizeControls();
        resizeEditDrawCanvas();
        resetEditDrawingHistory();
        clearEditDrawing(true);
        resetCropBox();
        if(!imageEditModeTouched) setImageEditMode(initialMode);
        syncImageEditOverflow();
        refreshIcons();
    };
    img.crossOrigin = 'anonymous';
    const fullEditorSrc = canvasDisplayMediaUrl(node.url, node.name || '');
    const quickEditorSrc = canvasMediaPreviewUrl(node.url, initialMode === 'preview' ? 1536 : 2048);
    if(quickEditorSrc && quickEditorSrc !== fullEditorSrc){
        img.src = quickEditorSrc;
        requestAnimationFrame(() => {
            setTimeout(() => {
                if(!cropState || cropState.nodeId !== nodeId) return;
                if(!modal.classList.contains('open') || img.dataset.editorSrcToken !== editorSrcToken) return;
                if(img.getAttribute('src') !== fullEditorSrc) img.src = fullEditorSrc;
            }, initialMode === 'preview' ? 120 : 60);
        });
    } else {
        img.src = fullEditorSrc;
    }
    setImageEditMode(initialMode);
    refreshIcons();
}
function closeImageEditor(){
    document.getElementById('imageEditModal').classList.remove('open');
    const img = document.getElementById('cropImage');
    img.onload = null;
    delete img.dataset.editorSrcToken;
    img.removeAttribute('src');
    img.style.width = '';
    img.style.height = '';
    img.style.maxWidth = '';
    img.style.maxHeight = '';
    clearEditDrawing(true);
    cropState = null;
    cropDrag = null;
    editDrawState = null;
    resetEditDrawingHistory();
    gridCustomDrag = null;
    imageEditZoom = 1.0;
    imageEditBaseW = 0;
    imageEditBaseH = 0;
    imageResizeScale = 0.5;
    imageEditModeTouched = false;
    cropAspectPreset = 'free';
    cropAspectRatio = null;
    syncCropRatioButtons();
    document.getElementById('imageEditStage')?.classList.remove('overflowing', 'overflow-x', 'overflow-y');
    const cropCanvasEl = document.getElementById('cropCanvas');
    cropCanvasEl.classList.remove('grid-custom-h', 'grid-custom-v', 'outpaint-mode', 'outpaint-warning', 'dragging-image', 'text-mode', 'resize-mode');
    cropCanvasEl.style.width = '';
    cropCanvasEl.style.height = '';
    const textCanvas = editTextCanvas();
    if(textCanvas){
        textCanvas.style.left = '';
        textCanvas.style.top = '';
    }
}
function clampCrop(){
    if(!cropState) return;
    if(imageEditMode === 'outpaint') return clampOutpaint();
    const {w, h} = cropBounds();
    Object.assign(cropState, WorkbenchCanvasMediaTools.clampCropRect(cropState, w, h));
}
function beginCropDrag(event, mode){
    if(!cropState) return;
    event.preventDefault();
    event.stopPropagation();
    if(imageEditMode === 'outpaint' && mode === 'move') return;
    cropDrag = WorkbenchCanvasMediaTools.createCropDrag(mode, event.clientX, event.clientY, cropState);
}
function resizeOutpaintFromDrag(dx, dy){
    const start = cropDrag?.start;
    if(!start) return;
    const {w, h} = cropBounds();
    Object.assign(cropState, WorkbenchCanvasMediaTools.resizeOutpaintRect(start, cropDrag.mode, dx, dy, w, h));
    clampOutpaint();
}
function clampAspectCropToBounds(anchorX, anchorY, movingX, movingY, ratio, handle){
    const {w:boundsW, h:boundsH} = cropBounds();
    return window.WorkbenchCanvasMediaTools.aspectCropToBounds(anchorX, anchorY, movingX, movingY, ratio, handle, boundsW, boundsH);
}
function resizeCropFromDrag(dx, dy){
    const start = cropDrag?.start;
    if(!start) return;
    const handle = String(cropDrag.mode || 'resize').replace(/^crop-/, '') || 'se';
    if(!cropAspectRatio){
        Object.assign(cropState, WorkbenchCanvasMediaTools.resizeFreeCropRect(start, handle, dx, dy));
        return;
    }
    const {w:boundsW, h:boundsH} = cropBounds();
    Object.assign(cropState, WorkbenchCanvasMediaTools.resizeAspectCropRect(start, handle, dx, dy, cropAspectRatio, boundsW, boundsH));
}
window.addEventListener('mousemove', event => {
    if(!cropDrag || !cropState) return;
    const {dx, dy} = WorkbenchCanvasMediaTools.pointerDelta(cropDrag.sx, cropDrag.sy, event.clientX, event.clientY);
    if(cropDrag.mode === 'move'){
        cropState.x = cropDrag.start.x + dx;
        cropState.y = cropDrag.start.y + dy;
    } else if(cropDrag.mode === 'image'){
        cropState.x = cropDrag.start.x + dx;
        cropState.y = cropDrag.start.y + dy;
    } else if(String(cropDrag.mode || '').startsWith('outpaint-')){
        resizeOutpaintFromDrag(dx, dy);
    } else {
        resizeCropFromDrag(dx, dy);
    }
    clampCrop();
    renderCropBox();
});
window.addEventListener('mouseup', () => { cropDrag = null; document.getElementById('cropCanvas')?.classList.remove('dragging-image'); });
async function uploadCroppedBlob(blob, name){ return ensureClassicAssetRuntime().uploadCroppedBlob(blob, name); }
async function uploadImageBlobs(blobs){ return ensureClassicAssetRuntime().uploadImageBlobs(blobs); }
async function applyImageCrop(){
    if(!cropState) return;
    const node = nodes.find(n => n.id === cropState.nodeId);
    const img = document.getElementById('cropImage');
    if(!node || !img.naturalWidth || !img.naturalHeight) return;
    const cropRect = WorkbenchCanvasMediaTools.cropRectFromDisplay(cropState, img.naturalWidth, img.naturalHeight, img.clientWidth, img.clientHeight);
    const {x:sx, y:sy, w:sw, h:sh} = cropRect;
    const blob = await WorkbenchCanvasMediaTools.cropImageBlob(img, {x:sx, y:sy, w:sw, h:sh}, document);
    if(!blob) return;
    const base = WorkbenchCanvasMediaTools.baseNameWithoutExtension(node.name);
    const file = await uploadCroppedBlob(blob, WorkbenchCanvasMediaTools.outputFileName(base, '_crop'));
    if(file){
        node.url = file.url;
        node.name = file.name;
        closeImageEditor();
        render();
        scheduleSave();
    }
}
async function applyImageOutpaint(){
    if(!cropState) return;
    const node = nodes.find(n => n.id === cropState.nodeId);
    const img = document.getElementById('cropImage');
    if(!node || !img.naturalWidth || !img.naturalHeight) return;
    clampOutpaint();
    const outpaintRect = WorkbenchCanvasMediaTools.outpaintRectFromDisplay(cropState, img.naturalWidth, img.naturalHeight, img.clientWidth, img.clientHeight);
    const {x:dx, y:dy, w:outW, h:outH} = outpaintRect;
    const blob = await WorkbenchCanvasMediaTools.outpaintImageBlob(img, outpaintRect, document);
    if(!blob) return;
    const base = WorkbenchCanvasMediaTools.baseNameWithoutExtension(node.name);
    const file = await uploadCroppedBlob(blob, WorkbenchCanvasMediaTools.outputFileName(base, '_outpaint'));
    if(file){
        node.url = file.url;
        node.name = file.name;
        node.mediaKind = 'image';
        node.natural_w = outW;
        node.natural_h = outH;
        closeImageEditor();
        render();
        scheduleSave();
    }
}
async function applyImageMask(){
    if(!cropState) return;
    const node = nodes.find(n => n.id === cropState.nodeId);
    if(!node || !editCanvasHasPixels()) return;
    const mask = maskCanvasFromDrawCanvas(editDrawCanvas());
    const blob = await WorkbenchCanvasMediaTools.toPngBlob(mask);
    if(!blob) return;
    const base = WorkbenchCanvasMediaTools.baseNameWithoutExtension(node.name);
    const file = await uploadCroppedBlob(blob, WorkbenchCanvasMediaTools.outputFileName(base, '_mask'));
    if(file){
        addGeneratedImageNode(file, node, 'mask', 28, {role:'mask'});
        closeImageEditor();
        render();
        scheduleSave();
    }
}
function maskCanvasFromDrawCanvas(src){
    return WorkbenchCanvasMediaTools.maskFromCanvas(src);
}
async function applyImageBrush(){
    if(!cropState) return;
    removeEditTextInlineEditor(true);
    const node = nodes.find(n => n.id === cropState.nodeId);
    const img = document.getElementById('cropImage');
    if(!node || !img.naturalWidth || !img.naturalHeight || !editCanvasHasPixels()) return;
    const canvasEl = WorkbenchCanvasMediaTools.composeBrushCanvas(img, editDrawCanvas(), editTextCanvas(), document);
    if(!canvasEl) return;
    const ctx = canvasEl.getContext('2d');
    const blob = await WorkbenchCanvasMediaTools.toPngBlob(canvasEl);
    if(!blob) return;
    const base = WorkbenchCanvasMediaTools.baseNameWithoutExtension(node.name);
    const file = await uploadCroppedBlob(blob, WorkbenchCanvasMediaTools.outputFileName(base, '_paint'));
    if(file){
        node.url = file.url;
        node.name = file.name;
        closeImageEditor();
        render();
        scheduleSave();
    }
}
async function applyImageGridSplit(){
    if(!cropState) return;
    const node = nodes.find(n => n.id === cropState.nodeId);
    const img = document.getElementById('cropImage');
    if(!node || !img.naturalWidth || !img.naturalHeight) return;
    const rects = gridSplitRects(img.naturalWidth, img.naturalHeight);
    if(!rects.length) return;
    const base = WorkbenchCanvasMediaTools.baseNameWithoutExtension(node.name);
    const blobs = (await WorkbenchCanvasMediaTools.splitImageBlobs(img, rects, document)).map(item => ({
        blob:item.blob,
        name:WorkbenchCanvasMediaTools.outputFileName(base, `_r${item.row + 1}_c${item.col + 1}`),
    }));
    if(!blobs.length) return;
    const files = await uploadImageBlobs(blobs);
    if(files.length){
        const out = imageEditorOutputNode(node);
        const urls = files.map(file => file.url).filter(Boolean);
        const layout = gridLayoutFromRects(rects);
        appendOutputImages(out, urls, {url:node.url, name:node.name || 'source image'}, urls.map((url, i) => ({
            runMs:0,
            run:{prompt:'宫格切分', refs:[{url:node.url, name:node.name || 'source image'}]},
            grid:{...layout, row:rects[i]?.row || 0, col:rects[i]?.col || 0, w:rects[i]?.w || 1, h:rects[i]?.h || 1}
        })), layout);
        closeImageEditor();
        render();
        scheduleSave();
    }
}
async function applyImageResize(){
    if(!cropState) return;
    const node = nodes.find(n => n.id === cropState.nodeId);
    if(!node) return;
    let resized = null;
    try {
        resized = await resizedImageBlobFromEditor();
    } catch(err) {
        alert('缩放失败：当前图片无法写入画布，请换成本地图片或重新上传后再试。');
        return;
    }
    if(!resized?.blob) return;
    const base = (node.name || 'image').replace(/\.[^.]+$/, '');
    const suffix = `${Math.round(resized.scale * 100)}pct`;
    const file = await uploadCroppedBlob(resized.blob, WorkbenchCanvasMediaTools.outputFileName(base, `_resize_${suffix}`));
    if(!file) return;
    node.url = file.url;
    node.name = file.name;
    node.mediaKind = 'image';
    node.natural_w = resized.targetW;
    node.natural_h = resized.targetH;
    closeImageEditor();
    render();
    scheduleSave();
}
function applyImageEdit(){
    return window.WorkbenchCanvasMediaEditorState.dispatch(imageEditMode, {applyImageOutpaint, applyImageMask, applyImageBrush, applyImageResize, applyImageGridSplit, applyImageCrop});
}

function nodeHasLiveMedia(node){
    return node?.type === 'image' && node.url && ['video','audio'].includes(mediaKindForNode(node));
}
function captureMediaPlaybackState(media){
    return WorkbenchCanvasMediaPlaybackState.capture(media);
}
function restoreMediaPlaybackState(media, state){
    WorkbenchCanvasMediaPlaybackState.restore(media, state);
}
function mediaSignatureFromElement(el){
    const media = el?.querySelector?.('video,audio');
    return WorkbenchCanvasMediaPlaybackState.signature(media);
}
function transplantNodeMediaElement(oldNodeEl, newNodeEl){
    const oldMedia = oldNodeEl?.querySelector?.('video,audio');
    const newMedia = newNodeEl?.querySelector?.('video,audio');
    if(!oldMedia || !newMedia) return;
    const oldSignature = mediaSignatureFromElement(oldNodeEl);
    const newSignature = mediaSignatureFromElement(newNodeEl);
    if(!oldSignature || oldSignature !== newSignature) return;
    const state = captureMediaPlaybackState(oldMedia);
    newMedia.replaceWith(oldMedia);
    restoreMediaPlaybackState(oldMedia, state);
    requestAnimationFrame(() => restoreMediaPlaybackState(oldMedia, state));
}
function captureMediaPlaybackStates(){
    return WorkbenchCanvasMediaPlaybackState.captureAll(nodesEl, {exclude:'.node-shell-mounted'});
}
function restoreMediaPlaybackStates(states){
    WorkbenchCanvasMediaPlaybackState.restoreAll(nodesEl, states, {exclude:'.node-shell-mounted'});
}
function measureCanvasOriginalImageNodes(root=nodesEl){
    root.querySelectorAll?.('.image-node img[data-original-src]').forEach(imgEl => {
        if(imgEl.dataset.previewKind === 'video') return;
        const nodeEl = imgEl.closest('.image-node');
        const node = nodes.find(n => n.id === nodeEl?.dataset.id);
        if(!node || node.type !== 'image' || !node.url || node.natural_w || node.natural_h || node._naturalSizeLoading) return;
        const original = imgEl.dataset.originalSrc || node.url;
        if(!original) return;
        node._naturalSizeLoading = true;
        loadCanvasOriginalImageDimensions(original).then(size => {
            node._naturalSizeLoading = false;
            if(!size || node.natural_w || node.natural_h) return;
            node.natural_w = size.w;
            node.natural_h = size.h;
            scheduleSave();
        });
    });
}

let canvasRenderSweep = null;
function ensureCanvasRenderSweep(){
    if(!canvasRenderSweep){
        canvasRenderSweep = window.WorkbenchCanvasRenderSweep.create({
            container: nodesEl,
            runtime: ensureRenderRuntime(),
            getNodes: () => nodes,
            renderNode,
            isLiveMedia: nodeHasLiveMedia,
            transplantMedia: transplantNodeMediaElement,
            applyViewport,
            captureState: mode => mode === 'render'
                ? {outputScrolls:captureOutputScrolls(), mediaStates:captureMediaPlaybackStates()}
                : {outputScrolls:captureOutputScrolls()},
            restoreState: (mode, state) => {
                if(mode === 'render') restoreMediaPlaybackStates(state?.mediaStates);
                restoreOutputScrolls(state?.outputScrolls);
            },
            afterRender: mode => {
                refreshGeometry();
                refreshGeometryAfterLayout();
                refreshIcons();
                bindCanvasPreviewImageFallbacks(nodesEl);
                syncCanvasSelectedImageResolution(nodesEl);
                measureCanvasOriginalImageNodes(nodesEl);
                refreshOutputTimer();
                if(mode === 'render') applyCanvasNodeShellSemanticZoom();
                scheduleMinimapRender();
            },
            refreshFastPath: node => node.type === 'output' && ensureClassicOutputGrid().refreshOutputNodeContent({node}),
        });
    }
    return canvasRenderSweep;
}
function render(){
    return ensureCanvasRenderSweep().run();
}
function refreshNodes(ids=[]){
    return ensureCanvasRenderSweep().refresh(ids);
}
function refreshRunNodes(node, out=null){ return ensureClassicExecutorRuntime().refreshRunNodes(node, out); }
function normalizedPendingPreviewSize(size){
    const w = Number(size?.w ?? size?.width ?? 0);
    const h = Number(size?.h ?? size?.height ?? 0);
    if(w > 0 && h > 0) return {w:Math.round(w), h:Math.round(h)};
    return null;
}
function pendingPreviewSizeFromSizeString(sizeStr){
    const parsed = parseSizeValue(sizeStr);
    return parsed ? normalizedPendingPreviewSize(parsed) : null;
}
function pendingPreviewSizeFromNode(node){
    if(!node) return null;
    const natural = normalizedPendingPreviewSize({w:node.natural_w || node.width, h:node.natural_h || node.height});
    if(natural) return natural;
    if(node.type === 'image'){
        const img = nodesEl?.querySelector?.(`.image-node[data-id="${CSS.escape(node.id)}"] img`);
        if(isCanvasPreviewImage(img)) return null;
        const domSize = normalizedPendingPreviewSize({w:img?.naturalWidth, h:img?.naturalHeight});
        if(domSize) return domSize;
    }
    if(node.type === 'output'){
        const item = [...(node.images || [])].reverse().find(outputUrlValue);
        const meta = item && typeof item === 'object' ? item : {};
        return normalizedPendingPreviewSize(meta);
    }
    return null;
}
function pendingPreviewSizeFromRefs(refs=[]){
    for(const ref of refs || []){
        const direct = normalizedPendingPreviewSize(ref);
        if(direct) return direct;
        const url = ref?.url;
        if(!url) continue;
        const node = nodes.find(n =>
            (n.type === 'image' && n.url === url) ||
            (n.type === 'output' && (n.images || []).some(item => outputUrlValue(item) === url))
        );
        const nodeSize = pendingPreviewSizeFromNode(node);
        if(nodeSize) return nodeSize;
        const media = nodesEl?.querySelector?.(`[data-url="${CSS.escape(url)}"], [data-output-url="${CSS.escape(url)}"] img, img[src="${CSS.escape(url)}"]`);
        if(isCanvasPreviewImage(media)) continue;
        const domSize = normalizedPendingPreviewSize({w:media?.naturalWidth || media?.videoWidth, h:media?.naturalHeight || media?.videoHeight});
        if(domSize) return domSize;
    }
    return null;
}
function pendingPreviewSizeForRun(node, options={}){
    const requestSize = normalizedPendingPreviewSize(options.requestSize) || pendingPreviewSizeFromSizeString(options.requestSize);
    if(requestSize) return requestSize;
    if(node?.type === 'comfy' && (node.mode || 'text') === 'text'){
        return normalizedPendingPreviewSize({w:Number(node.width || 1024), h:Number(node.height || 1024)});
    }
    if(node?.type === 'minimax'){
        const [w, h] = miniMaxAspectValue(node.aspectRatio || '16:9').split(':').map(Number);
        return normalizedPendingPreviewSize({w:w || 16, h:h || 9});
    }
    return pendingPreviewSizeFromRefs(options.refs || []);
}
function pendingOutputStyle(pending){
    const size = normalizedPendingPreviewSize(pending?.previewSize);
    if(!size) return '';
    return ` style="aspect-ratio:${Math.max(1, size.w)}/${Math.max(1, size.h)}"`;
}
function renderPendingOutput(pending){
    if(pending?.failed){
        const taskId = pending.recoverTaskId || '';
        const querying = Boolean(pending.querying);
        const msg = pending.error || tr('canvas.generationFailed');
        const sub = taskId ? `任务 ID：${escapeHtml(taskId)}` : '没有任务 ID，无法查询';
        return `<div class="output-img-wrap loading-wrap recoverable" data-pending-id="${escapeAttr(pending.id)}"${pendingOutputStyle(pending)}>
            <span class="output-time-pill failed">失败</span>
            <div class="output-recover-state">
                <i data-lucide="refresh-cw" class="${querying ? 'spinning' : ''}"></i>
                <div class="output-recover-title">${querying ? '查询中' : '任务未丢失'}</div>
                <div class="output-recover-sub" title="${escapeAttr(msg)}">${sub}</div>
                <button class="output-recover-query" type="button" ${taskId && !querying ? '' : 'disabled'}>${querying ? '查询中...' : '查询结果'}</button>
            </div>
            <button class="output-del" title="${tr('common.delete')}">×</button>
        </div>`;
    }
    return `<div class="output-img-wrap loading-wrap" data-pending-id="${escapeAttr(pending.id)}"${pendingOutputStyle(pending)}><span class="output-time-pill running">${formatRunDuration(nowMs() - Number(pending.startedAt || nowMs()))}</span><div class="output-spinner"></div><button class="output-del" title="${tr('common.delete')}">×</button></div>`;
}
function captureOutputScrolls(){
    const state = new Map();
    // output 节点滚动位置
    nodesEl.querySelectorAll('.output-node').forEach(el => {
        const body = el.querySelector('.node-body');
        if(body) state.set('out:' + el.dataset.id, { top:body.scrollTop, left:body.scrollLeft });
    });
    // LLM 聊天日志滚动位置（记录是否在底部，以便恢复时保持底部）
    nodesEl.querySelectorAll('.llm-node').forEach(el => {
        const log = el.querySelector('.llm-chat-log');
        if(!log) return;
        const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 12;
        state.set('llm:' + el.dataset.id, { top:log.scrollTop, atBottom });
    });
    return state;
}
function restoreOutputScrolls(state){
    requestAnimationFrame(() => {
        state.forEach((pos, key) => {
            if(key.startsWith('out:')){
                const id = key.slice(4);
                const body = nodesEl.querySelector(`.output-node[data-id="${CSS.escape(id)}"] .node-body`);
                if(body){ body.scrollTop = pos.top || 0; body.scrollLeft = pos.left || 0; }
            } else if(key.startsWith('llm:')){
                const id = key.slice(4);
                const log = nodesEl.querySelector(`.llm-node[data-id="${CSS.escape(id)}"] .llm-chat-log`);
                if(log){
                    // 之前在底部 → 保持底部（显示最新消息）；否则恢复原位
                    log.scrollTop = pos.atBottom ? log.scrollHeight : (pos.top || 0);
                }
            }
        });
    });
}
function isNodeControl(target){
    return !!target.closest('textarea, input, select, option, button, audio, video, [contenteditable="true"], .seg, .gen-btn, .comfy-run, .input-item, .blank-image, .mode-tabs, .ms-model-tabs, .llm-provider, .llm-output, .llm-chat-log, .llm-bubble, .llm-pane-resizer, .loop-preview, .ltx-director-timeline-host, .minimax-canvas-workbench, .pr-wrapper, .pr-toolbar, .pr-viewport, .pr-canvas, .pr-player-controls, .pr-prompt-area');
}
function isNodeDragSurface(target){
    return !isNodeControl(target) && !target.closest('.port, .resize-handle, .output-img-wrap');
}
function canUseCanvasMediaRenderer(node){
    if(!window.WorkbenchNodeClient?.isLoopback?.() || !window.WorkbenchMediaRenderer) return false;
    if(node?.type === 'image') return Boolean(node.url);
    return node?.type === 'group' && (node.items || []).some(id => {
        const item = nodes.find(candidate => candidate.id === id);
        return item?.type === 'image' && item.url;
    });
}
function canvasNodeShellBaseEnabled(){
    return window.WorkbenchNodeClient?.isLoopback?.()
        && window.WorkbenchNodeShell
        && window.WorkbenchUnifiedRenderHost;
}
function canvasNodeShellEnabled(){
    return canvasNodeShellBaseEnabled()
        && window.WorkbenchMediaRenderer;
}
function canvasLegacyRendererEnabled(){
    return canvasNodeShellBaseEnabled()
        && window.WorkbenchLegacyRenderer;
}
function canUseCanvasNodeShellForMedia(node){
    // A group is a graph container even while it has no media members.  Mount it
    // through the same shell so it keeps the common input/output port contract.
    return canvasNodeShellEnabled() && (canUseCanvasMediaRenderer(node) || node?.type === 'group');
}
function canUseCanvasNodeShellForLegacy(node){
    // Form/task nodes keep their source-owned body while the shared host owns
    // chrome, menu, resize, and their declared connection ports.
    return window.WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}, node);
}
function canvasLegacyNodeShellPorts(node){
    if(node?.type === 'prompt') return {input:false, output:true};
    // A Loop can be connected before its input mode is configured. Keeping its
    // input port visible makes connection creation independent of that setting.
    if(node?.type === 'loop') return {input:true, output:true};
    // Output nodes are still valid sources for downstream composition in the
    // existing Canvas contract, so their two Legacy ports stay visible.
    if(node?.type === 'output') return {input:true, output:true};
    // LLM nodes retain their established graph contract: upstream context in,
    // generated text out.
    if(node?.type === 'llm') return {input:true, output:true};
    // Generator nodes keep their input/reference and result-output contract;
    // provider configuration and execution remain owned by the Legacy body.
    if(node?.type === 'generator') return {input:true, output:true};
    // Midjourney keeps the same graph contract while its mode, version, and
    // task-continuation controls remain in the Legacy body.
    if(node?.type === 'midjourney') return {input:true, output:true};
    // ModelScope Generation keeps its model tabs and parameter form in the
    // Legacy body while retaining the established graph ports.
    if(node?.type === 'msgen') return {input:true, output:true};
    // Video Generation keeps media controls and provider configuration in its
    // Legacy body while retaining the established graph ports.
    if(node?.type === 'video') return {input:true, output:true};
    // Comfy workflow selection, field schemas, and execution remain owned by
    // the Legacy body while the shared shell preserves its graph ports.
    if(node?.type === 'comfy') return {input:true, output:true};
    // RunningHub entry selection, parameter schemas, and execution remain
    // Legacy-owned while the shared shell preserves its graph ports.
    if(node?.type === 'rh') return {input:true, output:true};
    // LTX Director keeps its timeline editor, parameter controls, and run
    // behavior in the Legacy body while the shared shell preserves its ports.
    if(node?.type === 'ltxDirector') return {input:true, output:true};
    // MiniMax keeps its timeline, media library, clip settings, and execution
    // in the Legacy body while the shared shell preserves its graph ports.
    if(node?.type === 'minimax') return {input:true, output:true};
    // Prompt Groups retain the existing output-only aggregation contract; their
    // member membership and summarized text remain owned by the Legacy body.
    if(node?.type === 'promptGroup') return {input:false, output:true};
    return {input:true, output:true};
}
function canvasShellPointer(detail={}){
    return {
        button:0,
        clientX:Number(detail.clientX) || 0,
        clientY:Number(detail.clientY) || 0,
        altKey:Boolean(detail.altKey),
        shiftKey:Boolean(detail.shiftKey),
        ctrlKey:Boolean(detail.ctrlKey),
        metaKey:Boolean(detail.metaKey),
        preventDefault(){},
        stopPropagation(){},
    };
}
function selectCanvasNodeFromShell(nodeId){
    if(!nodes.some(node => node.id === nodeId)) return;
    // NodeShell is a Unified surface: its selection command enters
    // CanvasRuntime rather than maintaining a second Classic-only transition.
    if(!applyCanvasRuntimeSelection([nodeId])) {
        selected.clear();
        selected.add(nodeId);
    }
    refreshSelectionVisuals();
}
const canvasNodeShellIntentAdapter = window.WorkbenchUnifiedRenderHost.createIntentAdapter({
    select:intent => selectCanvasNodeFromShell(intent.nodeId),
    focus:intent => selectCanvasNodeFromShell(intent.nodeId),
    menu:intent => selectCanvasNodeFromShell(intent.nodeId),
    delete:intent => deleteNodeFromButton(intent.nodeId),
    drag_start:intent => {
        const node = nodes.find(item => item.id === intent.nodeId);
        if(node) startNodeDrag(canvasShellPointer(intent.detail), node);
    },
    resize_start:intent => {
        const node = nodes.find(item => item.id === intent.nodeId);
        if(node) startNodeResize(canvasShellPointer(intent.detail), node);
    },
    connect_start:intent => {
        const node = nodes.find(item => item.id === intent.nodeId);
        if(node) startLink(canvasShellPointer(intent.detail), node.id, intent.detail?.direction === 'input' ? 'in' : 'out');
    },
});
function handleCanvasNodeShellIntent(intent){ canvasNodeShellIntentAdapter(intent); }
function canvasMediaRecord(node){
    const record = window.WorkbenchCanvas.legacyNodeView(node, {projectId:canvas?.project, canvasId:canvas?.id});
    if(node?.type === 'group') {
        record.output_refs = (node.items || []).map(id => nodes.find(candidate => candidate.id === id))
            .filter(item => item?.type === 'image' && item.url)
            .map(item => ({url:item.url, name:item.name || 'Media', type:mediaKindForNode(item)}));
    }
    return record;
}
const CANVAS_PROVIDER_SHELL_TYPES = Object.freeze(['llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax']);
const CANVAS_NODE_SHELL_LEGACY_CONTROLS = Object.freeze({
    firstSelectors:Object.freeze(['.node-head']),
    selectors:Object.freeze([':scope > .port, :scope > .resize-handle']),
});
let renderRuntime = null;
let interactionController = null;
let canvasViewportController = null;
function ensureInteractionController(){
    if(!interactionController){
        interactionController = window.WorkbenchInteractionController.create({windowRef: window});
    }
    return interactionController;
}
let creationController = null;
function ensureCreationController(){
    if(!creationController){
        creationController = window.WorkbenchInteractionController.createCreationController({
            create: (canvasId, command, clientId) => window.WorkbenchNodeClient.create(canvasId, command, clientId),
            applyResult: (result, apply) => window.WorkbenchNodeClient.applyCreationResult(result, apply),
            requestId: () => `${CLIENT_ID}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        });
    }
    return creationController;
}
let nodeDragSessionFactory = null;
function ensureNodeDragSessionFactory(){
    if(!nodeDragSessionFactory){
        nodeDragSessionFactory = window.WorkbenchInteractionController.createNodeDragSessionFactory({});
    }
    return nodeDragSessionFactory;
}
let nodeResizeSessionFactory = null;
function ensureNodeResizeSessionFactory(){
    if(!nodeResizeSessionFactory){
        nodeResizeSessionFactory = window.WorkbenchInteractionController.createNodeResizeSessionFactory({});
    }
    return nodeResizeSessionFactory;
}
function ensureCanvasViewportController(){
    if(!canvasViewportController){
        canvasViewportController = window.WorkbenchInteractionController.createViewportController({
            getKernel: ensureCanvasUnifiedRuntime,
            applyViewport: nextViewport => { viewport = {...nextViewport}; },
        });
    }
    return canvasViewportController;
}
function ensureRenderRuntime(){
    if(!renderRuntime){
        renderRuntime = window.WorkbenchRenderRuntime.create({
            mount: request => window.WorkbenchUnifiedRenderHost.mountAdapterCard(request),
            mediaState: {
                capture: element => window.WorkbenchCanvasMediaPlaybackState.captureAll(element),
                restore: (element, states) => window.WorkbenchCanvasMediaPlaybackState.restoreAll(element, states),
            },
        });
    }
    return renderRuntime;
}
function mountCanvasNodeShellForMedia(node, body, el){
    if(!canUseCanvasNodeShellForMedia(node)) return false;
    if(node.type === 'group') return mountCanvasGroupShell(node, body, el);
    const record = canvasMediaRecord(node);
    if(!window.WorkbenchMediaRenderer.canRender(record)) return false;
    const mounted = ensureRenderRuntime().mount({
        document, node:record, card:el, contentHost:body,
        preserveLegacyContent:false,
        legacyContentClassName:'canvas-node-shell-legacy-content',
        controlSettings:CANVAS_NODE_SHELL_LEGACY_CONTROLS,
        cardClasses:['node-shell-mounted', 'media-renderer-mounted'],
        ...window.WorkbenchUnifiedRenderHost.cardShellView({selected:selected.has(node.id), onIntent:handleCanvasNodeShellIntent}),
    });
    // Legacy Canvas keeps link anchors on the outer card. The shared host
    // preserves that geometry while NodeShell remains the interaction owner.
    return Boolean(mounted.shell);
}
function mountCanvasGroupShell(node, body, el){
    const memberImages = (node.items || []).map(id => nodes.find(candidate => candidate.id === id))
        .filter(item => item?.type === 'image' && item.url)
        .map(item => ({url:item.url, name:item.name || 'Media', type:mediaKindForNode(item)}));
    ensureRenderRuntime().mountGroupCard({
        document, node, card:el, contentHost:body,
        context:{projectId:canvas?.project, canvasId:canvas?.id},
        memberImages,
        selected:selected.has(node.id),
        onIntent:handleCanvasNodeShellIntent,
        legacyContentClassName:'canvas-node-shell-legacy-content',
        controlSettings:CANVAS_NODE_SHELL_LEGACY_CONTROLS,
        cardClasses:({hasRenderableMedia}) => ['node-shell-mounted', hasRenderableMedia && 'media-renderer-mounted'],
        mountEmptyState: handle => {
            const itemCount = (node.items || []).length;
            const empty = document.createElement('div');
            empty.className = 'workbench-node-shell__group-empty';
            empty.textContent = itemCount ? `${itemCount} ${tr('canvas.grouped')}` : tr('canvas.groupEmpty');
            handle.shell.contentHost.replaceChildren(empty);
        },
    });
    return true;
}
function mountCanvasNodeShellForLegacy(node, body, el){
    if(!canUseCanvasNodeShellForLegacy(node)) return false;
    const record = canvasMediaRecord(node);
    // Migrated generic families receive renderer-owned DOM through the
    // registry; state and page services stay behind rendererOptions callbacks.
    const rendererOptions = node.type === 'prompt' ? {
        templateActive: Boolean(promptTemplateModal?.classList.contains('open') && promptTemplateNodeId === node.id),
        maxLength: PROMPT_TEXT_MAX_LENGTH,
        textLength: promptTextLength,
        bindTextElement: bindScrollableText,
        onPromptInput: text => {
            node.text = text;
            scheduleSave();
            scheduleGeneratorInputSync();
        },
        onOpenTemplate: openPromptTemplateModal,
    } : (CANVAS_PROVIDER_SHELL_TYPES.includes(node.type) ? {
        // Provider-card cleanup flows through the mounted-handle lifecycle.
        onCardDestroy: payloadNode => ensureClassicLtxControls().destroyEditor({node: payloadNode}),
    } : null);
    const mounted = ensureRenderRuntime().mount({
        document, node:record, card:el, contentHost:body,
        preserveLegacyContent: node.type !== 'prompt',
        legacyContentClassName:'canvas-node-shell-legacy-content',
        controlSettings:CANVAS_NODE_SHELL_LEGACY_CONTROLS,
        ...(rendererOptions ? {rendererOptions} : {}),
        cardClasses:['node-shell-mounted', 'legacy-renderer-mounted'],
        ...window.WorkbenchUnifiedRenderHost.cardShellView({selected:selected.has(node.id), onIntent:handleCanvasNodeShellIntent, ports:canvasLegacyNodeShellPorts(node)}),
    });
    const nodeShell = mounted.shell;
    return true;
}
function mountCanvasMediaRenderer(node, body, el){
    if(!canUseCanvasMediaRenderer(node)) return false;
    const record = canvasMediaRecord(node);
    if(!window.WorkbenchMediaRenderer.canRender(record)) return false;
    window.WorkbenchUnifiedRenderHost.mountAdapterContent({
        document, node:record, card:el, contentHost:body,
        cardClasses:['media-renderer-mounted'],
    });
    return true;
}
function renderNode(node){
    normalizeApiNodeLayout(node);
    if(node.type === 'rh' && Number(node.h) === 560) delete node.h;
    const el = document.createElement('div');
    const size = defaultNodeSize(node.type);
    const dimensions = window.WorkbenchCanvasNodePresentation.dimensions(node, size);
    const position = window.WorkbenchCanvasNodePresentation.position(node);
    const hasFixedSize = window.WorkbenchCanvasNodePresentation.isFixedSize(node, size);
    el.className = window.WorkbenchCanvasNodePresentation.className(node, selected.has(node.id), hasFixedSize);
    el.style.left = `${position.left}px`;
    el.style.top = `${position.top}px`;
    el.style.width = `${dimensions.width}px`;
    if(dimensions.height) el.style.height = `${dimensions.height}px`;
    el.dataset.id = node.id;
    el.onclick = (e) => {
        e.stopPropagation();
        if(isNodeControl(e.target)) return;
        if(canvasUnifiedRuntimeEnabled) {
            if(e.ctrlKey || e.metaKey) applyCanvasRuntimeSelection([], node.id);
            else applyCanvasRuntimeSelection([node.id]);
        } else if(e.ctrlKey || e.metaKey) selected.has(node.id) ? selected.delete(node.id) : selected.add(node.id);
        else if(!selected.has(node.id)) { selected.clear(); selected.add(node.id); }
        refreshSelectionVisuals();
    };
    el.oncontextmenu = e => {
    if(!CANVAS_GENERATOR_TYPES.includes(node.type) && node.type !== 'output') return;
        e.preventDefault();
        e.stopPropagation();
        if(node.type === 'output') openOutputNodeMenu(node.id, e.clientX, e.clientY);
        else openGeneratorNodeMenu(node.id, e.clientX, e.clientY);
    };
    const title = window.WorkbenchCanvasNodePresentation.title(node, tr);
    const displayTitle = window.WorkbenchCanvasNodePresentation.displayTitle(node, title, nodeTitleForMedia(node));
    // 失败徽章只在一键运行模式中显示，单节点失败已通过 alert 提示
    const statusHtml = window.WorkbenchCanvasNodePresentation.statusMarkup(node, escapeHtml);
    el.innerHTML = `<div class="node-head"><span class="node-title">${displayTitle}</span><div style="display:flex;align-items:center;gap:8px">${statusHtml}<button onclick="deleteNodeFromButton('${node.id}', event)" class="text-gray-300 hover:text-red-500"><i data-lucide="x" class="w-4 h-4"></i></button></div></div>`;
    const body = document.createElement('div');
    body.className = 'node-body';
    if(node.type === 'image') {
        if(node.url) {
            const missing = isMissingAssetUrl(node.url);
            const mediaKind = mediaKindForNode(node);
            const isEditableImage = mediaKind === 'image' && !missing;
            body.innerHTML = `<div class="image-preview-wrap">${missing ? missingAssetHtml(node.url) : canvasPreviewImgHtml(node.url, 768, 'draggable="false"')}</div><div class="image-caption text-[11px] text-gray-400 truncate">${escapeHtml(node.name || 'image')}${missing ? ` · ${langIsEn() ? 'missing' : '文件缺失'}` : ''}</div>`;
            if(!missing && mediaKind !== 'image'){
                const mediaHtml = mediaKind === 'video'
                    ? `<div class="media-card video-card">${canvasVideoPreviewHtml(node.url, 768, 'draggable="false" data-video-fallback-attrs="controls"')}<button class="canvas-video-play" type="button" title="播放"><i data-lucide="play"></i></button></div>`
                    : `<div class="media-card audio-card"><i data-lucide="file-audio" class="w-8 h-8"></i><div class="audio-title">${escapeHtml(node.name || 'Audio')}</div><div class="audio-sub">AUDIO</div><audio src="${escapeAttr(node.url)}" data-url="${escapeAttr(node.url)}" controls preload="metadata"></audio></div>`;
                body.innerHTML = `<div class="image-preview-wrap">${mediaHtml}</div><div class="image-caption text-[11px] text-gray-400 truncate">${escapeHtml(node.name || nodeTitleForMedia(node))}</div>`;
            }
            const previewWrap = body.querySelector('.image-preview-wrap');
            const loadedImg = body.querySelector('img');
            const videoPlayBtn = body.querySelector('.canvas-video-play');
            const openPreview = e => {
                if(!node.url || missing) return;
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                if(isEditableImage) openImageEditor(node.id, (e.shiftKey || e.altKey) ? 'crop' : 'preview');
                else openImageNodePreview(node.id);
            };
            body.onmousedown = e => {
                if(e.target.closest('video,audio')) return;
                if(e.detail >= 2){
                    openPreview(e);
                    return;
                }
                startNodeDrag(e, node);
            };
            body.ondragover = e => allowImageNodeDropEvent(e, previewWrap);
            body.ondragleave = e => {
                e.stopPropagation();
                previewWrap.classList.remove('drag-over');
            };
            body.ondrop = e => handleImageNodeDropEvent(e, node.id, previewWrap);
            body.oncontextmenu = e => {
                e.preventDefault();
                e.stopPropagation();
                openImageNodeMenu(node.id, e.clientX, e.clientY);
            };
            if(loadedImg && isEditableImage){
                loadedImg.addEventListener('mousedown', e => {
                    if(e.detail >= 2) openPreview(e);
                }, true);
                loadedImg.addEventListener('dblclick', openPreview, true);
            }
            if(loadedImg && mediaKind === 'video'){
                loadedImg.addEventListener('mousedown', e => {
                    if(e.button !== 0) return;
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }, true);
                loadedImg.addEventListener('click', e => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    canvasActivateVideoPreview(e.currentTarget || loadedImg);
                }, true);
            }
            if(videoPlayBtn && loadedImg && mediaKind === 'video'){
                videoPlayBtn.addEventListener('mousedown', e => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }, true);
                videoPlayBtn.addEventListener('click', e => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    canvasActivateVideoPreview(videoPlayBtn.closest('.media-card,.image-preview-wrap') || loadedImg);
                }, true);
            }
            body.addEventListener('dblclick', openPreview, true);
            if(loadedImg && loadedImg.complete && loadedImg.naturalHeight > 0){
                requestAnimationFrame(refreshGeometry);
            } else if(loadedImg) {
                loadedImg.onload = () => refreshGeometryAfterLayout();
            }
        } else {
        body.innerHTML = `<div class="blank-image"><i data-lucide="image-plus" class="w-7 h-7"></i><div class="text-[11px] font-bold">${tr('canvas.clickDragPasteImage')}</div></div>`;
            const blank = body.querySelector('.blank-image');
            blank.onclick = () => pickImageForNode(node.id);
            blank.ondragover = e => allowImageNodeDropEvent(e, blank);
            blank.ondragleave = e => { e.stopPropagation(); blank.classList.remove('drag-over'); };
            blank.ondrop = e => handleImageNodeDropEvent(e, node.id, blank);
        }
    }
    if(node.type === 'prompt' && !canUseCanvasNodeShellForLegacy(node)) {
        // Renderer-owned path: the prompt-card renderer builds this DOM inside
        // NodeShell; this pre-rendered markup remains the flags-off fallback.
        const templateActive = promptTemplateModal?.classList.contains('open') && promptTemplateNodeId === node.id;
        body.innerHTML = `<div class="prompt-editor"><div class="prompt-toolbar"><button class="prompt-template-btn ${templateActive ? 'active' : ''}" type="button" data-prompt-template-open data-prompt-template-node-id="${escapeAttr(node.id)}" aria-pressed="${templateActive ? 'true' : 'false'}" title="${escapeAttr(tr('canvas.promptTemplateLibrary'))}"><i data-lucide="library"></i><span>${escapeHtml(tr('canvas.promptTemplateShort'))}</span></button>${promptCounterHtml(node.text || '')}</div><textarea placeholder="${tr('canvas.promptPlaceholder')}">${escapeHtml(node.text || '')}</textarea></div>`;
        const textarea = body.querySelector('textarea');
        const templateBtn = body.querySelector('[data-prompt-template-open]');
        templateBtn.onclick = e => {
            e.preventDefault();
            e.stopPropagation();
            openPromptTemplateModal(node.id);
        };
        bindScrollableText(textarea);
        textarea.oninput = e => {
            node.text = e.target.value;
            refreshPromptCounter(body, node.text);
            scheduleSave();
            scheduleGeneratorInputSync();
        };
    }
    if(node.type === 'loop') body.appendChild(renderLoopBody(node));
    if(node.type === 'group') {
        const items = (node.items || []).map(id => nodes.find(n => n.id === id)).filter(Boolean);
        const imgCount = items.filter(n => n.type === 'image').length;
        const promptCount = items.filter(n => n.type === 'prompt').length;
        const parts = [];
        if(imgCount) parts.push(`${imgCount} ${tr('canvas.imageCount')}`);
        if(promptCount) parts.push(`${promptCount} ${tr('canvas.promptCount')}`);
        const text = parts.length ? `${parts.join(' · ')} ${tr('canvas.grouped')}` : tr('canvas.groupEmpty');
        body.innerHTML = `<div class="text-[11px] text-gray-400">${text}</div>`;
        const previewItems = groupImageItems(node);
        if(previewItems.length){
            const openGroupPreview = e => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation?.();
                openGroupLightbox(node.id);
            };
            body.style.cursor = 'zoom-in';
            body.onmousedown = e => {
                if(e.button !== 0) return;
                if(e.target.closest('video,audio')) return;
                if(e.detail >= 2){
                    openGroupPreview(e);
                    return;
                }
                startNodeDrag(e, node);
            };
            body.ondblclick = openGroupPreview;
        }
    }
    if(node.type === 'promptGroup') {
        const promptNodes = (node.items || []).map(id => nodes.find(n => n.id === id)).filter(Boolean);
        body.innerHTML = `<div class="text-[11px] text-gray-400">${promptNodes.length} ${tr('canvas.promptCount')} ${tr('canvas.grouped')}</div>`;
    }
    const cardBody = ensureClassicCardBodyRenderer();
    const comfy = ensureClassicComfyControls();
    const rh = ensureClassicRunningHubControls();
    const mmx = ensureClassicMiniMaxControls();
    const ltx = ensureClassicLtxControls();
    const videoBody = ensureClassicVideoCardBody();
    if(node.type === 'llm') body.appendChild(cardBody.renderLLM({node}));
    if(node.type === 'generator') body.appendChild(cardBody.renderGenerator({node}));
    if(node.type === 'midjourney') body.appendChild(cardBody.renderMidjourney({node}));
    if(node.type === 'msgen') body.appendChild(cardBody.renderMsGen({node}));
    if(node.type === 'video') body.appendChild(videoBody.renderBody({node}));
    if(node.type === 'minimax') body.appendChild(mmx.renderBody({node}));
    if(node.type === 'rh') body.appendChild(ensureClassicRunningHubControls().renderBody({node}));
    if(node.type === 'comfy') body.appendChild(comfy.renderBody({node}));
    if(node.type === 'ltxDirector') body.appendChild(ltx.renderBody({node}));
    const outputGrid = ensureClassicOutputGrid();
    if(node.type === 'output') {
        const pendingHtml = (node._pending || []).map(p =>
            renderPendingOutput(p)
        ).join('');
        body.innerHTML = outputGrid.renderOutputGrid({node, pendingHtml});
        body.onwheel = e => {
            e.stopPropagation();
        };
        body.querySelectorAll('.output-img-wrap').forEach(wrap => outputGrid.bindOutputWrap({wrap, node}));
    }
    if(!canUseCanvasNodeShellForMedia(node)) mountCanvasMediaRenderer(node, body, el);
    el.appendChild(body);
    el.querySelectorAll('button, select, textarea, input').forEach(control => {
        control.addEventListener('mousedown', e => e.stopPropagation(), true);
        control.addEventListener('click', e => e.stopPropagation());
    });
    el.onmousedown = e => {
        if(e.button !== 0 || !isNodeDragSurface(e.target)) return;
        startNodeDrag(e, node);
    };
    const canInput = ['generator','midjourney','comfy','ltxDirector','output','llm','msgen','video','rh','minimax'].includes(node.type) || (node.type === 'loop' && (node.imageInput || node.showPrompt));
    const canOutput = ['image','prompt','loop','group','promptGroup','generator','midjourney','comfy','ltxDirector','llm','msgen','video','rh','minimax','output'].includes(node.type);
    if(canInput) el.insertAdjacentHTML('beforeend', `<div class="port in" title="${tr('canvas.connectHere')}"></div>`);
    if(canOutput) el.insertAdjacentHTML('beforeend', `<div class="port out" title="${tr('canvas.dragConnect')}"></div>`);
    el.insertAdjacentHTML('beforeend', `<div class="resize-handle" title="${tr('canvas.resize')}"></div>`);
    el.querySelector('.node-head').onmousedown = e => {
        if(e.button !== 0) return;
        if(isNodeControl(e.target)) return;
        if(node.type === 'group' && e.detail >= 2 && groupImageItems(node).length){
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation?.();
            openGroupLightbox(node.id);
            return;
        }
        startNodeDrag(e, node);
    };
    el.querySelector('.resize-handle').onmousedown = e => { if(e.button === 0 && !e.shiftKey) startNodeResize(e, node); };
    el.ondragstart = e => { e.preventDefault(); e.stopPropagation(); };
    const out = el.querySelector('.port.out');
    if(out) out.onmousedown = e => { if(e.button === 0 && !e.shiftKey) startLink(e, node.id, 'out'); };
    const inp = el.querySelector('.port.in');
    if(inp) inp.onmousedown = e => { if(e.button === 0 && !e.shiftKey) startLink(e, node.id, 'in'); };
    if(!mountCanvasNodeShellForMedia(node, body, el)) mountCanvasNodeShellForLegacy(node, body, el);
    return el;
}
function outputDomKeyForItem(item){
    return WorkbenchCanvasMediaTools.outputDomKeyForItem(item);
}
function outputDomKeyForPending(pending){
    return WorkbenchCanvasMediaTools.outputDomKeyForPending(pending);
}
function defaultNodeSize(type){
    return WorkbenchCanvasNodePresentation.defaultSize(type);
}
function loopCount(node){
    return WorkbenchCanvasLoopPromptRenderer.count(node?.count);
}
function splitPromptIntoItems(text){
    return WorkbenchCanvasLoopPromptRenderer.splitItems(text);
}
const loopPromptVisiting = new Set();
function loopInputPromptItems(node){
    if(loopPromptVisiting.has(node?.id)) return [];
    loopPromptVisiting.add(node?.id);
    try { return WorkbenchCanvasLoopInputProjection.promptItems(node, connections, nodes, renderLoopPrompt); }
    finally { loopPromptVisiting.delete(node?.id); }
}
function loopInputPrompt(node, ctx=loopContext){
    const items = loopInputPromptItems(node);
    return WorkbenchCanvasLoopInputProjection.select(items, node?.loopStart, ctx?.index);
}
function renderLoopPrompt(node, ctx=loopContext){
    const context = WorkbenchCanvasLoopPromptRenderer.contextProjection(node, ctx, loopCount);
    const selected = loopInputPrompt(node, ctx);
    return WorkbenchCanvasLoopPromptRenderer.render({showPrompt:node?.showPrompt, index:context.index, total:context.total, selected, variable:context.variable, tokens:{counter:tr('canvas.counterToken'), total:tr('canvas.totalToken'), progress:tr('canvas.progressToken')}});
}
function imageRefsFromNode(node){
    return WorkbenchCanvasLoopInputProjection.nodeMediaRefs(node, 'image', {nodes, mediaKindForNode, outputValue:outputUrlValue, kindOfOutput:mediaKindForOutputItem, nameForUrl:outputImageName, generatedTypes:CANVAS_IMAGE_OUTPUT_TYPES, generatedRefs:generatedImageRefs, excludeUrl:url => isVideoUrl(url) || isAudioUrl(url)});
}
function loopInputImageRefs(node, ctx=loopContext){
    return WorkbenchCanvasLoopInputProjection.connectedBatch(node, connections, id => imageRefsFromNode(nodes.find(n => n.id === id)), node?.loopStart, node?.imageBatchSize, ctx?.index, node?.imageInput);
}
function videoRefsFromNode(node){
    return WorkbenchCanvasLoopInputProjection.nodeMediaRefs(node, 'video', {nodes, mediaKindForNode, outputValue:outputUrlValue, kindOfOutput:mediaKindForOutputItem, nameForUrl:outputImageName, generatedTypes:CANVAS_MEDIA_OUTPUT_TYPES, generatedRefs:generatedImageRefs});
}
function loopInputVideoRefs(node, ctx=loopContext){
    return WorkbenchCanvasLoopInputProjection.connectedBatch(node, connections, id => videoRefsFromNode(nodes.find(n => n.id === id)), node?.loopStart, node?.videoBatchSize, ctx?.index, node?.videoInput);
}
function loopTokenLabel(token){
    return WorkbenchCanvasLoopPromptRenderer.tokenLabel(token, {
        '《计数》':tr('canvas.counterToken'),
        '《总数》':tr('canvas.totalToken'),
        '《进度》':tr('canvas.progressToken'),
    });
}
function autoSizeLoopNode(node, opening){
    if(!node) return;
    const size = WorkbenchCanvasLoopLayoutProjection.nodeSize(node, opening);
    node.w = size.width;
    if(size.height == null) delete node.h;
    else node.h = size.height;
}
function autoSizeLoopForPanels(node){
    if(!node) return;
    const size = WorkbenchCanvasLoopLayoutProjection.panelSize(node);
    node.w = size.width;
    if(size.height == null) delete node.h;
    else node.h = size.height;
}
function loopTokenChipHtml(token){
    return WorkbenchCanvasLoopPromptRenderer.tokenChip(token, {escapeHtml, escapeAttr, label:loopTokenLabel(token), deleteLabel:tr('common.delete')});
}
function loopVariableHtml(text){
    return WorkbenchCanvasLoopPromptRenderer.variableMarkup(text, {escapeHtml, token:'《计数》', tokenChip:loopTokenChipHtml});
}
function loopEditorText(editor){
    return WorkbenchCanvasLoopPromptRenderer.editorText(editor);
}
function insertLoopToken(editor, token){
    return WorkbenchCanvasLoopPromptRenderer.insertToken(editor, token, {document, selection:window.getSelection(), chipMarkup:loopTokenChipHtml(token)});
}
function promptTextLength(text){
    return WorkbenchCanvasLoopPromptRenderer.textLength(text);
}
function promptCounterHtml(text){
    return WorkbenchCanvasLoopPromptRenderer.counterMarkup(text, PROMPT_TEXT_MAX_LENGTH).markup;
}
function refreshPromptCounter(container, text){
    const counter = container?.querySelector('.prompt-counter');
    if(!counter) return;
    const count = promptTextLength(text);
    counter.classList.toggle('over', count > PROMPT_TEXT_MAX_LENGTH);
    counter.innerHTML = `<span>${count.toLocaleString()}</span><span>/ ${PROMPT_TEXT_MAX_LENGTH.toLocaleString()}</span>`;
}
function canvasAssetLibraries(){ return ensureClassicAssetRuntime().canvasAssetLibraries(); }
function localCanvasAssetFolderCategories(){ return ensureClassicAssetRuntime().localCanvasAssetFolderCategories(); }
function canvasAssetLibraryIsLocal(){ return ensureClassicAssetRuntime().canvasAssetLibraryIsLocal(); }
function canvasAssetSourceLibraries(){ return ensureClassicAssetRuntime().canvasAssetSourceLibraries(); }
function activeCanvasAssetLibrary(){ return ensureClassicAssetRuntime().activeCanvasAssetLibrary(); }
function canvasAssetCategories(){ return ensureClassicAssetRuntime().canvasAssetCategories(); }
function canvasMediaCategories(){
    return (activeCanvasAssetLibrary()?.categories || canvasAssetLibrary.categories || []).filter(cat => {
        const type = String(cat.type || 'image').toLowerCase();
        return type === 'image' || type === 'media';
    });
}
function activeCanvasAssetCategory(){ return ensureClassicAssetRuntime().activeCanvasAssetCategory(); }
function activeCanvasMediaCategory(){
    const cats = canvasMediaCategories();
    return cats.find(cat => cat.id === activeCanvasAssetCategoryId) || cats[0] || null;
}
function canvasWorkflowCategories(){
    return (activeCanvasAssetLibrary()?.categories || canvasAssetLibrary.categories || []).filter(cat => String(cat.type || '').toLowerCase() === 'workflow');
}
function activeCanvasWorkflowCategory(){
    const cats = canvasWorkflowCategories();
    return cats.find(cat => cat.id === activeCanvasWorkflowCategoryId) || cats[0] || null;
}
function currentCanvasAssetItem(itemId){ return ensureClassicAssetRuntime().currentCanvasAssetItem(itemId); }
function canvasAssetItemKind(item){ return ensureClassicAssetRuntime().canvasAssetItemKind(item); }
function canvasAssetThumbHtml(item){ return ensureClassicAssetRuntime().canvasAssetThumbHtml(item); }
function positionCanvasAssetHoverPreview(event){ return ensureClassicAssetRuntime().positionCanvasAssetHoverPreview(event); }
function showCanvasAssetHoverPreview(event, item){ return ensureClassicAssetRuntime().showCanvasAssetHoverPreview(event, item); }
function hideCanvasAssetHoverPreview(){ return ensureClassicAssetRuntime().hideCanvasAssetHoverPreview(); }
async function renameCanvasAssetItem(itemId){ return ensureClassicAssetRuntime().renameCanvasAssetItem(itemId); }
async function deleteCanvasAssetItem(itemId){ return ensureClassicAssetRuntime().deleteCanvasAssetItem(itemId); }
async function loadCanvasAssetLibrary({renderPanel=true}={}){ return ensureClassicAssetRuntime().loadCanvasAssetLibrary({renderPanel}); }
function renderCanvasAssetLibrary(){ return ensureClassicAssetRuntime().renderCanvasAssetLibrary(); }
function toggleCanvasAssetLibrary(open=!canvasAssetLibraryOpen){ return ensureClassicAssetRuntime().toggleCanvasAssetLibrary(open); }
async function addUrlToCanvasAssetLibrary(url, name=''){ return ensureClassicAssetRuntime().addUrlToCanvasAssetLibrary(url, name); }
async function uploadFilesToLibrary(files, libraryId, categoryId){ return ensureClassicAssetRuntime().uploadFilesToLibrary(files, libraryId, categoryId); }
function openAssetManager(){ return ensureClassicAssetRuntime().openAssetManager(); }
function closeAssetManager(){ return ensureClassicAssetRuntime().closeAssetManager(); }
window.closeAssetManager = closeAssetManager;
function renderAssetManager(){ return ensureClassicAssetRuntime().renderAssetManager(); }
function renderImageAssetManager(){ return ensureClassicAssetRuntime().renderImageAssetManager(); }
function workflowAssetThumbHtml(item){ return ensureClassicAssetRuntime().workflowAssetThumbHtml(item); }
function renderWorkflowAssetManager(){ return ensureClassicAssetRuntime().renderWorkflowAssetManager(); }
function renderPromptAssetManager(){ return ensureClassicAssetRuntime().renderPromptAssetManager(); }
async function loadCanvasPromptTemplates(){
    if(canvasPromptTemplatesLoaded) return canvasPromptTemplates;
    try {
        loadCanvasPromptTemplateGroups();
        loadCanvasPromptTemplateOverrides();
        const data = await fetch('/api/prompt-libraries').then(r => r.ok ? r.json() : {library:{libraries:[]}});
        canvasPromptLibraries = Array.isArray(data.library?.libraries) ? data.library.libraries : [];
        if(!canvasPromptLibraries.some(lib => lib.id === activePromptLibraryId)) {
            activePromptLibraryId = canvasPromptLibraries.some(lib => lib.id === 'system') ? 'system' : (canvasPromptLibraries[0]?.id || 'system');
        }
        canvasPromptTemplates = activeCanvasPromptLibraryItems();
    } catch(e) {
        canvasPromptTemplates = [];
        canvasPromptLibraries = [];
    }
    canvasPromptTemplatesLoaded = true;
    return canvasPromptTemplates;
}
function activeCanvasPromptLibrary(){ return ensureClassicAssetRuntime().activeCanvasPromptLibrary(); }
function defaultCanvasPromptTemplateGroups(){
    return [
        {id:'view', name:tr('smart.tplCatView')},
        {id:'storyboard', name:tr('smart.tplCatStoryboard')},
        {id:'character', name:tr('smart.tplCatCharacter')},
        {id:'product', name:tr('smart.tplCatProduct')},
        {id:'lighting', name:tr('smart.tplCatLighting')},
        // “我的”分组在后端/智能画布里用的分类 id 是 custom，这里保持一致，否则后端 custom 条目在普通画布看不到。
        {id:'custom', name:tr('smart.tplCatMine')}
    ];
}
function loadCanvasPromptTemplateGroups(){
    try {
        const list = JSON.parse(localStorage.getItem(CANVAS_PROMPT_TEMPLATE_GROUPS_KEY) || '[]');
        const valid = Array.isArray(list) ? list.filter(g => g?.id && g?.name) : [];
        const defaults = defaultCanvasPromptTemplateGroups();
        promptTemplateGroups = defaults.map(group => valid.find(g => g.id === group.id) || group);
        valid.filter(g => !promptTemplateGroups.some(x => x.id === g.id)).forEach(g => promptTemplateGroups.push(g));
    } catch(e) {
        promptTemplateGroups = defaultCanvasPromptTemplateGroups();
    }
}
function saveCanvasPromptTemplateGroups(){
    localStorage.setItem(CANVAS_PROMPT_TEMPLATE_GROUPS_KEY, JSON.stringify(promptTemplateGroups));
}
function loadCanvasPromptTemplateOverrides(){
    try {
        const data = JSON.parse(localStorage.getItem(CANVAS_PROMPT_TEMPLATE_OVERRIDES_KEY) || '{}');
        canvasPromptTemplateOverrides = {
            hiddenBuiltinIds:Array.isArray(data.hiddenBuiltinIds) ? data.hiddenBuiltinIds : [],
            editedBuiltins:data.editedBuiltins && typeof data.editedBuiltins === 'object' ? data.editedBuiltins : {}
        };
    } catch(e) {
        canvasPromptTemplateOverrides = {hiddenBuiltinIds:[], editedBuiltins:{}};
    }
}
function saveCanvasPromptTemplateOverrides(){
    localStorage.setItem(CANVAS_PROMPT_TEMPLATE_OVERRIDES_KEY, JSON.stringify(canvasPromptTemplateOverrides));
}
function activeCanvasPromptLibraryItems(){ return ensureClassicAssetRuntime().activeCanvasPromptLibraryItems(); }
function refreshCanvasPromptTemplatesFromLibraries(){
    canvasPromptTemplatesLoaded = true;
    canvasPromptTemplates = activeCanvasPromptLibraryItems();
    renderCanvasPromptLibrarySelect();
}
function renderCanvasPromptLibrarySelect(){ return ensureClassicAssetRuntime().renderCanvasPromptLibrarySelect(); }
function activeCanvasPromptTemplateGroups(){
    const lib = activeCanvasPromptLibrary();
    if(!lib || lib.id === 'system') return promptTemplateGroups;
    return Array.isArray(lib.categories) ? lib.categories.filter(c => c?.id && c?.name) : [];
}
function canvasPromptTemplateCategoryLabel(category){
    const lib = activeCanvasPromptLibrary();
    return window.WorkbenchCanvasPromptTemplateData.categoryLabel(category, {
        allLabel:tr('smart.tplAll'),
        remote:Boolean(lib && lib.id !== 'system'),
        libraryGroups:activeCanvasPromptTemplateGroups(),
        fallbackGroups:promptTemplateGroups,
        builtinLabels:{
        view:tr('smart.tplCatView'),
        storyboard:tr('smart.tplCatStoryboard'),
        character:tr('smart.tplCatCharacter'),
        product:tr('smart.tplCatProduct'),
        lighting:tr('smart.tplCatLighting'),
        custom:tr('smart.tplCatMine'),
        mine:tr('smart.tplCatMine')
        },
    });
}
function canvasPromptTemplateName(template){
    return window.WorkbenchCanvasPromptTemplateData.name(template, langIsEn());
}
function canvasPromptTemplateScene(template){
    return window.WorkbenchCanvasPromptTemplateData.scene(template, langIsEn());
}
function canvasPromptTemplateDisplayScene(template){
    return window.WorkbenchCanvasPromptTemplateData.displayScene(template, langIsEn());
}
function canvasPromptTemplateText(template, mode='positive'){
    return window.WorkbenchCanvasPromptTemplateData.text(template, mode);
}
function canvasPromptTemplateNegativeText(template){
    return window.WorkbenchCanvasPromptTemplateData.negativeText(template);
}
function canvasPromptTemplatePositiveText(template){
    return window.WorkbenchCanvasPromptTemplateData.positiveText(template);
}
function canvasPromptTemplatePreview(template){
    return window.WorkbenchCanvasPromptTemplateData.preview(template);
}
function canvasPromptTemplateItemCard(item, selectedId){
    return window.WorkbenchCanvasPromptTemplateData.itemCard(item, selectedId, {
        english:langIsEn(), escapeHtml, escapeAttr,
        categoryLabel:category => canvasPromptTemplateCategoryLabel(category),
        sourceLabels:{builtin:tr('smart.tplBuiltin'), mine:tr('smart.tplMine')},
    });
}
function canvasPromptTemplateEmptyState(){
    return window.WorkbenchCanvasPromptTemplateData.emptyState(tr('smart.tplNoMatches'), escapeHtml);
}
function canvasPromptTemplateDetailEmptyState(){
    return window.WorkbenchCanvasPromptTemplateData.detailEmptyState(tr('smart.tplPickOrCreate'), escapeHtml);
}
function canvasPromptTemplateSearchText(template){
    return window.WorkbenchCanvasPromptTemplateData.searchText(template);
}
function canvasPromptTemplateVisibleItems(){
    const query = String(promptTemplateSearch?.value || promptTemplateQuery || '').trim().toLowerCase();
    return window.WorkbenchCanvasPromptTemplateData.visibleItems({
        items:canvasPromptTemplates, category:promptTemplateCategory, query,
    });
}
function currentCanvasPromptTemplateLibraryEditable(){ return ensureClassicAssetRuntime().currentCanvasPromptTemplateLibraryEditable(); }
function currentCanvasPromptTemplateNodeText(){
    return window.WorkbenchCanvasPromptTemplateData.nodeText(nodes, promptTemplateNodeId);
}
function syncCanvasPromptTemplateButtons(){
    WorkbenchCanvasPromptTemplateInteraction.syncOpenButtons(document, promptTemplateModal, promptTemplateNodeId);
}
function canvasPromptTemplateDefaultName(text){
    return window.WorkbenchCanvasPromptTemplateData.defaultName(text);
}
function canvasPromptTemplateParamsText(template){
    return window.WorkbenchCanvasPromptTemplateData.paramsText(template);
}
function canvasPromptTemplateSourceLabel(template){
    return window.WorkbenchCanvasPromptTemplateData.sourceLabel(template, {builtin:tr('smart.tplBuiltin'), mine:tr('smart.tplMine')});
}
function canvasPromptTemplateDetailSourceLabel(template){
    return window.WorkbenchCanvasPromptTemplateData.detailSourceLabel(template, {builtin:tr('smart.tplBuiltinTemplate'), mine:tr('smart.tplMineTemplate')});
}
function selectedCanvasPromptTemplate(){
    return window.WorkbenchCanvasPromptTemplateData.selectedItem(canvasPromptTemplates, promptTemplateSelectedId);
}
function syncCanvasPromptTemplateMutation(data, fallbackSelectedId=''){
    canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
    refreshCanvasPromptTemplatesFromLibraries();
    promptTemplateSelectedId = data.item?.id || fallbackSelectedId || promptTemplateSelectedId;
    const selected = selectedCanvasPromptTemplate();
    promptTemplateCategory = selected?.category || promptTemplateCategory || 'all';
}
async function saveCurrentCanvasPromptAsTemplate(){
    const lib = activeCanvasPromptLibrary();
    if(!currentCanvasPromptTemplateLibraryEditable()){ setStatus('请选择可编辑的提示词库'); return; }
    const text = currentCanvasPromptTemplateNodeText();
    if(!text){ setStatus('当前提示词为空'); return; }
    try {
        const data = await fetch('/api/prompt-libraries/items', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                library_id:lib.id,
                name:canvasPromptTemplateDefaultName(text),
                category:promptTemplateCategory === 'all' ? 'custom' : promptTemplateCategory,
                positive:text,
                scene:'我的提示词预设'
            })
        }).then(async r => {
            if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '保存失败');
            return r.json();
        });
        activePromptLibraryId = lib.id;
        syncCanvasPromptTemplateMutation(data, data.item?.id || '');
        promptTemplateEditing = true;
        renderPromptTemplateModal();
    } catch(err) {
        setStatus(err.message || '保存失败');
    }
}
async function createBlankCanvasPromptTemplate(){
    const lib = activeCanvasPromptLibrary();
    if(!currentCanvasPromptTemplateLibraryEditable()){ setStatus('请选择可编辑的提示词库'); return; }
    const category = promptTemplateCategory && promptTemplateCategory !== 'all' ? promptTemplateCategory : 'custom';
    try {
        const data = await fetch('/api/prompt-libraries/items', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({library_id:lib.id, name:'新模板', category, positive:'新提示词', scene:'我的提示词预设'})
        }).then(async r => {
            if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '创建失败');
            return r.json();
        });
        activePromptLibraryId = lib.id;
        promptTemplateCategory = category;
        syncCanvasPromptTemplateMutation(data, data.item?.id || '');
        promptTemplateEditing = true;
        renderPromptTemplateModal();
    } catch(err) {
        setStatus(err.message || '创建失败');
    }
}
async function saveCanvasPromptTemplateEdit(){
    const lib = activeCanvasPromptLibrary();
    const item = selectedCanvasPromptTemplate();
    if(!item) return;
    const name = promptTemplatePanel.querySelector('[data-template-edit-name]')?.value?.trim() || '';
    const positive = promptTemplatePanel.querySelector('[data-template-edit-text]')?.value?.trim() || '';
    const category = promptTemplatePanel.querySelector('[data-template-edit-category]')?.value || 'mine';
    if(!name || !positive){ setStatus(tr('smart.tplRequired')); return; }
    try {
        // 仅当模板不是后端项（非 remote）时才退回本地覆盖；系统库现在是 remote，走下面的后端 PATCH 同步。
        if(item.builtin && !item.remote){
            canvasPromptTemplateOverrides.editedBuiltins = canvasPromptTemplateOverrides.editedBuiltins || {};
            canvasPromptTemplateOverrides.editedBuiltins[item.sourceId || item.id] = {
                ...(canvasPromptTemplateOverrides.editedBuiltins[item.sourceId || item.id] || {}),
                name,
                category,
                positive
            };
            saveCanvasPromptTemplateOverrides();
            promptTemplateEditing = false;
            refreshCanvasPromptTemplatesFromLibraries();
            renderPromptTemplateModal();
            return;
        }
        const data = await fetch(`/api/prompt-libraries/items/${encodeURIComponent(item.id)}`, {
            method:'PATCH',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({library_id:item.libraryId || lib.id, name, category, scene:item.scene || '', positive, negative:item.negative || ''})
        }).then(async r => {
            if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '保存失败');
            return r.json();
        });
        // 迁移：清掉这条系统模板的旧本地覆盖，避免它盖住刚同步到后端的最新内容。
        const legacyKey = item.sourceId || item.id;
        if(canvasPromptTemplateOverrides.editedBuiltins && canvasPromptTemplateOverrides.editedBuiltins[legacyKey]){
            delete canvasPromptTemplateOverrides.editedBuiltins[legacyKey];
            saveCanvasPromptTemplateOverrides();
        }
        syncCanvasPromptTemplateMutation(data, item.id);
        promptTemplateEditing = false;
        renderPromptTemplateModal();
    } catch(err) {
        setStatus(err.message || '保存失败');
    }
}
async function deleteCanvasPromptTemplate(){
    const item = selectedCanvasPromptTemplate();
    if(!item) return;
    if(!window.confirm(`删除提示词「${canvasPromptTemplateName(item) || '提示词'}」？`)) return;
    try {
        // 系统库现在是 remote，删除走后端 DELETE 并同步；仅非 remote 的内置项才退回本地隐藏。
        if(item.builtin && !item.remote){
            canvasPromptTemplateOverrides.hiddenBuiltinIds = [...new Set([...(canvasPromptTemplateOverrides.hiddenBuiltinIds || []), item.sourceId || item.id])];
            saveCanvasPromptTemplateOverrides();
            promptTemplateSelectedId = '';
            promptTemplateEditing = false;
            refreshCanvasPromptTemplatesFromLibraries();
            renderPromptTemplateModal();
            return;
        }
        const data = await fetch(`/api/prompt-libraries/items/${encodeURIComponent(item.id)}`, {method:'DELETE'}).then(async r => {
            if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '删除失败');
            return r.json();
        });
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        refreshCanvasPromptTemplatesFromLibraries();
        promptTemplateSelectedId = '';
        promptTemplateEditing = false;
        renderPromptTemplateModal();
    } catch(err) {
        setStatus(err.message || '删除失败');
    }
}
function promptTemplateScrollSnapshot(){
    return WorkbenchCanvasPromptTemplateInteraction.snapshot(promptTemplatePanel);
}
function restorePromptTemplateScroll(snapshot){
    WorkbenchCanvasPromptTemplateInteraction.restore(promptTemplatePanel, snapshot, requestAnimationFrame);
}
async function createCanvasPromptTemplateGroup(){
    const name = window.prompt(tr('smart.tplNewGroupPrompt'), tr('smart.tplNewGroupDefault'));
    if(!String(name || '').trim()) return;
    const lib = activeCanvasPromptLibrary();
    if(lib && lib.id !== 'system'){
        try {
            const data = await fetch('/api/prompt-libraries/categories', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({name:String(name).trim().slice(0, 24), library_id:lib.id})
            }).then(async r => { if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '新增分组失败'); return r.json(); });
            canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
            promptTemplateCategory = data.category?.id || promptTemplateCategory;
            refreshCanvasPromptTemplatesFromLibraries();
            renderPromptTemplateModal();
        } catch(err){ setStatus(err.message || '新增分组失败'); }
        return;
    }
    const group = {id:uid('tpl_group'), name:String(name).trim().slice(0, 24)};
    promptTemplateGroups.push(group);
    saveCanvasPromptTemplateGroups();
    promptTemplateCategory = group.id;
    renderPromptTemplateModal();
}
async function renameCanvasPromptTemplateGroup(groupId){
    const lib = activeCanvasPromptLibrary();
    const group = activeCanvasPromptTemplateGroups().find(g => g.id === groupId);
    if(!group) return;
    const name = window.prompt(tr('smart.tplGroupNamePrompt'), group.name || '');
    if(!String(name || '').trim()) return;
    if(lib && lib.id !== 'system'){
        try {
            const data = await fetch(`/api/prompt-libraries/categories/${encodeURIComponent(groupId)}`, {
                method:'PATCH', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({name:String(name).trim().slice(0, 24), library_id:lib.id})
            }).then(async r => { if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '重命名失败'); return r.json(); });
            canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
            refreshCanvasPromptTemplatesFromLibraries();
            renderPromptTemplateModal();
        } catch(err){ setStatus(err.message || '重命名失败'); }
        return;
    }
    group.name = String(name).trim().slice(0, 24);
    saveCanvasPromptTemplateGroups();
    renderPromptTemplateModal();
}
async function deleteCanvasPromptTemplateGroup(groupId){
    const lib = activeCanvasPromptLibrary();
    if(lib && lib.id !== 'system'){
        if(!window.confirm(tr('smart.tplDeleteGroupConfirm'))) return;
        try {
            const data = await fetch(`/api/prompt-libraries/categories/${encodeURIComponent(groupId)}`, {method:'DELETE'})
                .then(async r => { if(!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '删除失败'); return r.json(); });
            canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
            if(promptTemplateCategory === groupId) promptTemplateCategory = 'all';
            refreshCanvasPromptTemplatesFromLibraries();
            renderPromptTemplateModal();
        } catch(err){ setStatus(err.message || '删除失败'); }
        return;
    }
    if(['view','storyboard','character','product','lighting','mine'].includes(groupId)){
        renameCanvasPromptTemplateGroup(groupId);
        return;
    }
    if(!window.confirm(tr('smart.tplDeleteGroupConfirm'))) return;
    promptTemplateGroups = promptTemplateGroups.filter(g => g.id !== groupId);
    Object.entries(canvasPromptTemplateOverrides.editedBuiltins || {}).forEach(([id, item]) => {
        if(item?.category === groupId) canvasPromptTemplateOverrides.editedBuiltins[id] = {...item, category:'mine'};
    });
    canvasPromptLibraries = canvasPromptLibraries.map(lib => ({
        ...lib,
        items:(lib.items || []).map(item => item.category === groupId ? {...item, category:'mine'} : item)
    }));
    if(promptTemplateCategory === groupId) promptTemplateCategory = 'all';
    saveCanvasPromptTemplateGroups();
    saveCanvasPromptTemplateOverrides();
    refreshCanvasPromptTemplatesFromLibraries();
    renderPromptTemplateModal();
}
function renderPromptTemplateModal(){
    if(!promptTemplateModal || !promptTemplatePanel || !promptTemplateCats || !promptTemplateBody) return;
    canvasPromptTemplates = activeCanvasPromptLibraryItems();
    renderCanvasPromptLibrarySelect();
    const scrollSnapshot = promptTemplateScrollSnapshot();
    const activeGroups = activeCanvasPromptTemplateGroups();
    const categories = [{id:'all', name:tr('smart.tplAll')}, ...activeGroups.map(group => ({...group, name:canvasPromptTemplateCategoryLabel(group.id)}))];
    const counts = window.WorkbenchCanvasPromptTemplateData.categoryCounts(canvasPromptTemplates);
    const items = canvasPromptTemplateVisibleItems();
    promptTemplateSelectedId = window.WorkbenchCanvasPromptTemplateData.selectedId(items, promptTemplateSelectedId);
    const selected = window.WorkbenchCanvasPromptTemplateData.selectedItem(items, promptTemplateSelectedId);
    const rendered = window.WorkbenchCanvasPromptTemplateRenderer.render({
        groups:activeGroups, categories, counts, category:promptTemplateCategory, groupEdit:promptTemplateGroupEditMode,
        items, selected, editable:currentCanvasPromptTemplateLibraryEditable(), editMode:Boolean(promptTemplateEditing && selected), promptGroups,
        tr, escapeHtml, escapeAttr, name:canvasPromptTemplateName, scene:canvasPromptTemplateDisplayScene,
        categoryLabel:canvasPromptTemplateCategoryLabel, sourceLabel:canvasPromptTemplateSourceLabel,
        positiveText:canvasPromptTemplatePositiveText, negativeText:canvasPromptTemplateNegativeText,
        paramsText:canvasPromptTemplateParamsText,
    });
    promptTemplateCats.innerHTML = rendered.categories;
    promptTemplateBody.innerHTML = rendered.body;
    refreshIcons();
    restorePromptTemplateScroll(scrollSnapshot);
    return;
}
async function openPromptTemplateModal(nodeId){
    promptTemplateNodeId = nodeId || '';
    promptTemplateQuery = '';
    promptTemplateEditing = false;
    if(promptTemplateSearch) promptTemplateSearch.value = '';
    await loadCanvasPromptTemplates();
    if(!promptTemplateCategory) promptTemplateCategory = 'all';
    if(!promptTemplateSelectedId) promptTemplateSelectedId = canvasPromptTemplates[0]?.id || '';
    renderPromptTemplateModal();
    promptTemplateModal?.classList.add('open');
    syncCanvasPromptTemplateButtons();
    promptTemplateSearch?.focus();
}
function closePromptTemplateModal(){
    promptTemplateModal?.classList.remove('open');
    promptTemplateNodeId = '';
    promptTemplateEditing = false;
    syncCanvasPromptTemplateButtons();
}
function applyPromptTemplateToPromptNode(mode='positive'){
    const template = canvasPromptTemplates.find(item => item.id === promptTemplateSelectedId);
    const node = nodes.find(n => n.id === promptTemplateNodeId && n.type === 'prompt');
    const applied = window.WorkbenchCanvasPromptTemplateApplication.apply({
        template,
        node,
        mode,
        textFor:canvasPromptTemplateText,
        close:closePromptTemplateModal,
    });
    if(!applied) return;
    scheduleSave();
    syncGeneratorInputs();
    refreshGeneratorInputViews();
    render();
}
function renderLoopBody(node){
    const wrap = document.createElement('div');
    wrap.className = 'loop-body';
    Object.assign(node, WorkbenchCanvasLoopInputProjection.config(node, loopCount));
    const imageInputCount = loopInputImageRefs(node, {index:node.loopStart}).length;
    const promptItemCount = node.showPrompt ? loopInputPromptItems(node).length : 0;
    const bodyState = WorkbenchCanvasLoopLayoutProjection.bodyState(node, imageInputCount, promptItemCount);
    const loopSummary = WorkbenchCanvasLoopInputProjection.summary(bodyState.imageInputCount, bodyState.promptItemCount);
    const hasUpstreamPrompt = bodyState.hasUpstreamPrompt;
    const loopTargetId = findLoopCascadeTarget(node.id);
    const loopTargetOrder = loopTargetId ? ensureClassicCascadeOrchestrator().computeCascadeOrder(loopTargetId) : [];
    const cascade = loopTargetId ? ensureClassicCascadeOrchestrator() : null;
    const loopRunState = WorkbenchCanvasLoopLayoutProjection.runState({
        targetId: loopTargetId,
        orderLength: loopTargetOrder.length,
        active: cascade ? cascade.isCascadeActive(loopTargetId) : false,
        stopping: cascade ? cascade.isCascadeStopping(loopTargetId) : false,
        count: node.count,
    });
    const loopRunHtml = loopRunState.hasTarget ? (loopRunState.active
        ? `<div class="gen-run-row"><button class="gen-cascade-btn gen-cascade-stop" type="button" data-loop-cascade-stop="${loopRunState.targetId}" ${loopRunState.stopping ? 'disabled' : ''}><i data-lucide="square" class="w-4 h-4"></i><span>${loopRunState.stopping ? '停止中…' : '停止运行'}</span></button></div>`
        : `<div class="gen-run-row"><button class="gen-cascade-btn" type="button" data-loop-cascade="${loopRunState.targetId}" title="从当前循环节点启动整条工作流"><i data-lucide="play-circle" class="w-4 h-4"></i><span>开始 ${loopRunState.orderLength || 1} 个节点 × ${loopRunState.count} ${tr('canvas.loopRounds')}</span></button></div>`)
        : '';
    wrap.innerHTML = `
        <div class="loop-count-row">
            <div class="loop-run-row">
                <div class="loop-count-group">
                    <span class="loop-count-label">${tr('canvas.loopCount')}</span>
                    <input class="loop-count-input" type="number" min="1" max="100" step="1" value="${node.count}">
                </div>
                <div class="seg loop-mode">
                    <button type="button" data-loop-mode="serial" class="${node.mode !== 'parallel' ? 'active' : ''}">${tr('canvas.loopSerial')}</button>
                    <button type="button" data-loop-mode="parallel" class="${node.mode === 'parallel' ? 'active' : ''}">${tr('canvas.loopParallel')}</button>
                </div>
            </div>
            <div class="loop-toggle-row">
                <button class="loop-toggle loop-image-toggle ${node.imageInput ? 'active' : ''}" type="button"><i data-lucide="image" class="w-3.5 h-3.5"></i>${tr('canvas.loopImageToggle')}</button>
                <button class="loop-toggle loop-prompt-toggle ${node.showPrompt ? 'active' : ''}" type="button"><i data-lucide="text-cursor-input" class="w-3.5 h-3.5"></i>${tr('canvas.loopPromptToggle')}</button>
            </div>
        </div>
        ${node.imageInput ? `<div class="loop-image-panel">
            <div class="loop-image-row">
                <span class="loop-count-label">${tr('canvas.loopImageStart')}</span>
                <input class="loop-count-input loop-image-start-input" type="number" min="1" max="9999" step="1" value="${node.loopStart}">
                <span class="loop-count-label">${tr('canvas.loopBatchSize')}</span>
                <input class="loop-count-input loop-batch-input" type="number" min="1" max="100" step="1" value="${node.imageBatchSize}">
            </div>
            <div class="loop-image-hint loop-image-hint-only">${loopSummary.imageInputCount ? trf('canvas.loopImageWillOutput', {n:loopSummary.imageInputCount}) : tr('canvas.loopImageEmpty')}</div>
        </div>` : ''}
        ${node.showPrompt ? `<div class="loop-prompt-panel ${hasUpstreamPrompt ? 'has-upstream' : ''}">
            <div class="loop-field">
                <div class="loop-variable-editor ${hasUpstreamPrompt ? 'is-disabled' : ''}" contenteditable="${hasUpstreamPrompt ? 'false' : 'true'}" data-placeholder="${escapeAttr(tr('canvas.loopVariablePlaceholder'))}">${loopVariableHtml(node.variablePrompt || '')}</div>
            </div>
            ${hasUpstreamPrompt ? `<div class="loop-prompt-hint">已识别 ${loopSummary.promptItemCount} 条提示词，按计数轮流输出</div>` : ''}
            <div class="loop-start-row">
                <button class="loop-token-btn loop-counter-token-btn" type="button" data-token="《计数》">${tr('canvas.counterToken')}</button>
                <span class="loop-count-label">${tr('canvas.loopStart')}</span>
                <input class="loop-count-input loop-start-input" type="number" min="1" max="9999" step="1" value="${node.loopStart}">
            </div>
        </div>` : ''}
        ${loopRunHtml}
    `;
    const countInput = wrap.querySelector('.loop-count-input');
    const variable = wrap.querySelector('.loop-variable-editor');
    const toggle = wrap.querySelector('.loop-prompt-toggle');
    const imageToggle = wrap.querySelector('.loop-image-toggle');
    if(variable) {
        variable.onmousedown = e => e.stopPropagation();
        variable.onclick = e => e.stopPropagation();
        variable.onwheel = e => e.stopPropagation();
    }
    const refreshPreview = () => {
        const preview = wrap.querySelector('.loop-preview:last-child');
        if(preview) preview.textContent = renderLoopPrompt(node, {index:1, total:loopCount(node)}) || tr('canvas.noPromptMeta');
    };
    const refreshImageHint = () => {
        const hint = wrap.querySelector('.loop-image-hint-only');
        if(!hint) return;
        const count = loopInputImageRefs(node, {index:node.loopStart}).length;
        hint.textContent = count ? trf('canvas.loopImageWillOutput', {n:count}) : tr('canvas.loopImageEmpty');
    };
    const syncStartInputs = source => {
        wrap.querySelectorAll('.loop-image-start-input, .loop-start-input').forEach(input => {
            if(input !== source && input.value !== String(node.loopStart)) input.value = node.loopStart;
        });
    };
    countInput.oninput = e => {
        node.count = loopCount({count:e.target.value});
        e.target.value = node.count;
        refreshPreview();
        /* 同步底部级联按钮上的轮数文字，避免输入循环次数后下游"× N 轮"残留旧值
           不直接 render() 是为了不破坏当前正在输入的 input 焦点 */
        const loopCascadeBtn = wrap.querySelector('[data-loop-cascade]');
        if(loopCascadeBtn){
            const span = loopCascadeBtn.querySelector('span');
            if(span) span.textContent = `开始 ${loopTargetOrder.length || 1} 个节点 × ${node.count} ${tr('canvas.loopRounds')}`;
        }
        if(loopTargetId){
            const targetEl = document.querySelector(`.node[data-id="${loopTargetId}"]`);
            const targetCascadeBtn = targetEl?.querySelector('[data-cascade]');
            if(targetCascadeBtn){
                const span = targetCascadeBtn.querySelector('span');
                if(span){
                    const targetOrder = ensureClassicCascadeOrchestrator().computeCascadeOrder(loopTargetId);
                    span.textContent = `一键运行 ${targetOrder.length} 个节点 × ${node.count} ${tr('canvas.loopRounds')}`;
                }
            }
        }
        scheduleSave();
    };
    const startInput = wrap.querySelector('.loop-start-input');
    if(startInput){
        startInput.onmousedown = e => e.stopPropagation();
        startInput.onclick = e => e.stopPropagation();
        startInput.oninput = e => {
            node.loopStart = Math.max(1, Number(e.target.value) || 1);
            refreshImageHint();
            syncStartInputs(e.target);
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
    }
    const imageStartInput = wrap.querySelector('.loop-image-start-input');
    if(imageStartInput){
        imageStartInput.onmousedown = e => e.stopPropagation();
        imageStartInput.onclick = e => e.stopPropagation();
        imageStartInput.oninput = e => {
            node.loopStart = Math.max(1, Number(e.target.value) || 1);
            refreshImageHint();
            syncStartInputs(e.target);
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
    }
    const batchInput = wrap.querySelector('.loop-batch-input');
    if(batchInput){
        batchInput.onmousedown = e => e.stopPropagation();
        batchInput.onclick = e => e.stopPropagation();
        batchInput.oninput = e => {
            node.imageBatchSize = Math.max(1, Math.min(100, Number(e.target.value) || 1));
            e.target.value = node.imageBatchSize;
            refreshImageHint();
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
    }
    wrap.querySelectorAll('[data-loop-mode]').forEach(btn => {
        btn.onclick = e => {
            e.stopPropagation();
            node.mode = btn.dataset.loopMode === 'parallel' ? 'parallel' : 'serial';
            render();
            scheduleSave();
        };
    });
    toggle.onclick = e => {
        e.stopPropagation();
        const opening = !node.showPrompt;
        node.showPrompt = opening;
        autoSizeLoopNode(node, opening);
        autoSizeLoopForPanels(node);
        if(!opening){
            connections = connections.filter(c => c.to !== node.id || canConnect(c.from, node.id));
        }
        render();
        scheduleSave();
        syncGeneratorInputs();
        refreshGeneratorInputViews();
    };
    if(variable) {
        variable.oninput = e => {
            node.variablePrompt = loopEditorText(variable);
            refreshPreview();
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
        variable.addEventListener('click', e => {
            const btn = e.target.closest('.loop-token-chip button');
            if(!btn) return;
            e.preventDefault();
            e.stopPropagation();
            btn.closest('.loop-token-chip')?.remove();
            node.variablePrompt = loopEditorText(variable);
            refreshPreview();
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        });
    }
    wrap.querySelectorAll('[data-token]').forEach(btn => {
        btn.onclick = e => {
            e.stopPropagation();
            const token = btn.dataset.token || '';
            if(!variable) return;
            insertLoopToken(variable, token);
            node.variablePrompt = loopEditorText(variable);
            variable.focus();
            refreshPreview();
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
    });
    if(imageToggle){
        imageToggle.onclick = e => {
            e.stopPropagation();
            node.imageInput = !node.imageInput;
            if(node.imageInput){
                node.loopStart = Math.max(1, Number(node.loopStart) || 1);
                node.imageBatchSize = Math.max(1, Math.min(100, Number(node.imageBatchSize) || 1));
            } else {
                connections = connections.filter(c => c.to !== node.id || canConnect(c.from, node.id));
            }
            autoSizeLoopForPanels(node);
            render();
            scheduleSave();
            syncGeneratorInputs();
            refreshGeneratorInputViews();
        };
    }
    wrap.querySelectorAll('[data-loop-cascade]').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = e => {
            e.stopPropagation();
            ensureClassicCascadeOrchestrator().runNodeCascade({nodeId: btn.dataset.loopCascade});
        };
    });
    wrap.querySelectorAll('[data-loop-cascade-stop]').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = e => {
            e.stopPropagation();
            ensureClassicCascadeOrchestrator().requestCascadeStop({targetId: btn.dataset.loopCascadeStop, reason: ""});
        };
    });
    return wrap;
}
