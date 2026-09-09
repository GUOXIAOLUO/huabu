function renderLLMNodePane(container, node){
    const connectedInput = llmInputText(node);
    const paneState = WorkbenchCanvasLlmPaneRenderer.state({
        connectedInput, userInput: node.userInput,
        inputHeight: node.llmInputHeight, outputHeight: node.llmOutputHeight,
    });
    const inputPlaceholder = langIsEn() ? 'Type input, or connect a Prompt node…' : '直接输入，或连接提示词节点…';
    container.innerHTML = WorkbenchCanvasLlmPaneRenderer.paneMarkup({inputValue:paneState.inputValue, outputText:node.outputText || tr('canvas.llmOutputEmpty'), inputHeight:paneState.inputHeight, outputHeight:paneState.outputHeight, readonly:paneState.readonly, inputPlaceholder, resizeLabel:tr('canvas.resizePanes'), running:node.running, runLabel:node.running ? tr('canvas.running') : 'Run LLM', cascadeMarkup:cascadeBtnHtml(node), retryMarkup:retryBarHtml(node), escapeHtml});
    const isReadonly = paneState.readonly;
    const inputEl = container.querySelector('.llm-input-output');
    bindScrollableText(inputEl);
    if(!isReadonly){
        inputEl.oninput = e => { node.userInput = e.target.value; };
    }
    bindScrollableText(container.querySelector('.llm-result-output'));
    container.querySelector('.llm-pane-resizer').onmousedown = e => startLLMPaneResize(e, node);
    container.querySelector('.llm-run').onclick = e => { e.stopPropagation(); runLLMNode(node.id); };
    bindCascadeButtons(container, node.id);
    const copyBtn = container.querySelector('.llm-output-copy');
    if(copyBtn){
        copyBtn.onmousedown = e => e.stopPropagation();
        copyBtn.onclick = async e => {
            e.stopPropagation();
            const text = node.outputText || '';
            if(!text) return;
            if(await copyTextToClipboard(text)){
                copyBtn.classList.add('copied');
                setTimeout(() => copyBtn.classList.remove('copied'), 1500);
            }
        };
    }
}
function renderLLMChatPane(container, node){
    const chatState = WorkbenchCanvasLlmPaneRenderer.chatState({messages:node.messages, input:node.chatInput, running:node.running, sendingLabel:tr('canvas.sending'), sendLabel:'Send'});
    container.innerHTML = WorkbenchCanvasLlmPaneRenderer.chatMarkup({messages:chatState.messages, input:chatState.input, placeholder:tr('canvas.chatInput'), emptyLabel:tr('canvas.startChat'), running:chatState.running, sendLabel:chatState.sendLabel, escapeHtml});
    bindScrollableText(container.querySelector('.llm-chat-log'));
    bindScrollableText(container.querySelector('.llm-chat-input'));
    const chatInputEl = container.querySelector('.llm-chat-input');
    chatInputEl.oninput = e => { node.chatInput = e.target.value; scheduleSave(); };
    chatInputEl.onkeydown = e => {
        if(e.key === 'Enter' && !e.shiftKey && !e.isComposing){
            e.preventDefault();
            e.stopPropagation();
            runLLMChat(node.id);
        }
    };
    container.querySelector('.llm-run').onclick = e => { e.stopPropagation(); runLLMChat(node.id); };
    container.querySelectorAll('.llm-bubble-copy').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = async e => {
            e.stopPropagation();
            const bubble = btn.closest('.llm-bubble');
            const idx = Number(bubble?.dataset.msgIdx);
            const msg = (node.messages || [])[idx];
            if(!msg) return;
            if(await copyTextToClipboard(msg.content || '')){
                btn.classList.add('copied');
                setTimeout(() => btn.classList.remove('copied'), 1500);
            }
        };
    });
}
function bindScrollableText(el){
    if(!el) return;
    const stop = e => e.stopPropagation();
    const beginSelection = e => {
        e.stopPropagation();
        textSelectionGuard = {
            el,
            scrollTop:el.scrollTop || 0,
            scrollLeft:el.scrollLeft || 0,
            clientY:e.clientY,
            wheelUntil:0,
            active:true
        };
    };
    el.addEventListener('mousedown', beginSelection);
    el.addEventListener('mousemove', e => {
        e.stopPropagation();
        if(textSelectionGuard?.el === el) textSelectionGuard.clientY = e.clientY;
    });
    el.addEventListener('mouseup', e => {
        e.stopPropagation();
        if(textSelectionGuard?.el === el) textSelectionGuard.active = false;
    });
    el.addEventListener('mouseleave', e => {
        e.stopPropagation();
        if(textSelectionGuard?.el === el) {
            el.scrollTop = textSelectionGuard.scrollTop;
            el.scrollLeft = textSelectionGuard.scrollLeft;
        }
    });
    el.addEventListener('scroll', () => {
        const guard = textSelectionGuard;
        if(!guard || guard.el !== el || !guard.active || Date.now() < guard.wheelUntil) {
            if(guard?.el === el) {
                guard.scrollTop = el.scrollTop || 0;
                guard.scrollLeft = el.scrollLeft || 0;
            }
            return;
        }
        const nextTop = el.scrollTop || 0;
        const prevTop = guard.scrollTop || 0;
        const rect = el.getBoundingClientRect();
        const pointerBelow = Number.isFinite(guard.clientY) && guard.clientY > rect.bottom - 10;
        const pointerAbove = Number.isFinite(guard.clientY) && guard.clientY < rect.top + 10;
        const jumpedToTop = prevTop > Math.max(80, el.clientHeight * 0.45) && nextTop < 4 && !pointerAbove;
        const wrongDirectionJump = pointerBelow && nextTop < prevTop - Math.max(40, el.clientHeight * 0.25);
        if(jumpedToTop || wrongDirectionJump) {
            requestAnimationFrame(() => {
                if(textSelectionGuard?.el === el && textSelectionGuard.active) {
                    el.scrollTop = prevTop;
                    el.scrollLeft = guard.scrollLeft || 0;
                }
            });
            return;
        }
        guard.scrollTop = nextTop;
        guard.scrollLeft = el.scrollLeft || 0;
    }, {passive:true});
    el.addEventListener('click', stop);
    el.addEventListener('dblclick', stop);
    el.addEventListener('wheel', e => {
        e.stopPropagation();
        if(textSelectionGuard?.el === el) textSelectionGuard.wheelUntil = Date.now() + 180;
    }, {passive:true});
}
function startLLMPaneResize(e, node){
    e.preventDefault();
    e.stopPropagation();
    llmPaneDrag = {
        node,
        sy:e.clientY,
        inputStart:Math.max(70, node.llmInputHeight || 110),
        outputStart:Math.max(70, node.llmOutputHeight || 150)
    };
    ensureInteractionController().begin({kind:'llm-pane-resize', onMove:onLLMPaneResize, onEnd:endDrag});
}
function onLLMPaneResize(e){
    if(!llmPaneDrag) return;
    const total = llmPaneDrag.inputStart + llmPaneDrag.outputStart;
    const delta = (e.clientY - llmPaneDrag.sy) / viewport.scale;
    const minPane = 70;
    const nextInput = Math.max(minPane, Math.min(total - minPane, llmPaneDrag.inputStart + delta));
    const nextOutput = Math.max(minPane, total - nextInput);
    llmPaneDrag.node.llmInputHeight = Math.round(nextInput);
    llmPaneDrag.node.llmOutputHeight = Math.round(nextOutput);
    const el = nodesEl.querySelector(`.node[data-id="${llmPaneDrag.node.id}"]`);
    if(el){
        const inputEl = el.querySelector('.llm-input-output');
        const outputEl = el.querySelector('.llm-result-output');
        if(inputEl){
            inputEl.style.height = `${llmPaneDrag.node.llmInputHeight}px`;
            inputEl.style.flexBasis = `${llmPaneDrag.node.llmInputHeight}px`;
        }
        if(outputEl){
            outputEl.style.height = `${llmPaneDrag.node.llmOutputHeight}px`;
            outputEl.style.flexBasis = `${llmPaneDrag.node.llmOutputHeight}px`;
        }
    }
}
function llmInputText(node){
    return connections.filter(c => c.to === node.id).map(c => nodes.find(n => n.id === c.from)).filter(Boolean).map(n => {
        if(n.type === 'prompt') return n.text || '';
        if(n.type === 'loop') return renderLoopPrompt(n);
        if(n.type === 'promptGroup') return (n.items || []).map(id => nodes.find(x => x.id === id)).filter(Boolean).map(p => p.text || '').filter(Boolean).join('\n\n');
        if(n.type === 'llm') return n.outputText || '';
        return '';
    }).filter(Boolean).join('\n\n');
}
function llmInputImages(node){
    const urls = [];
    connections.filter(c => c.to === node.id).map(c => nodes.find(n => n.id === c.from)).filter(Boolean).forEach(n => {
        if(n.type === 'image' && n.url && mediaKindForNode(n) === 'image') urls.push(n.url);
        if(n.type === 'output' && (n.images||[]).length){
            const last = [...n.images].reverse().map(outputUrlValue).find(url => url && !isVideoUrl(url) && !isAudioUrl(url));
            if(last) urls.push(last);
        }
        if(n.type === 'group'){
            (n.items || []).map(id => nodes.find(x => x.id === id)).filter(x => x?.type === 'image' && x?.url && mediaKindForNode(x) === 'image').forEach(img => urls.push(img.url));
        }
    });
    return urls;
}
function llmInputVideos(node){
    const urls = [];
    connections.filter(c => c.to === node.id).map(c => nodes.find(n => n.id === c.from)).filter(Boolean).forEach(n => {
        if(n.type === 'image' && n.url && mediaKindForNode(n) === 'video') urls.push(n.url);
        if(n.type === 'output' && (n.images||[]).length){
            const last = [...n.images].reverse().map(outputUrlValue).find(url => url && isVideoUrl(url));
            if(last) urls.push(last);
        }
        if(n.type === 'group'){
            (n.items || []).map(id => nodes.find(x => x.id === id)).filter(x => x?.type === 'image' && x?.url && mediaKindForNode(x) === 'video').forEach(video => urls.push(video.url));
        }
    });
    return urls;
}
function midjourneyModalHtml(node, maskRef){
    if(!node.mjModalTaskId) return '';
    const hasMask = Boolean(maskRef?.url);
    return `<div class="mj-modal-panel"><div class="mj-action-title">局部重绘</div><textarea class="mj-modal-prompt" placeholder="描述要替换的内容">${escapeHtml(node.mjModalPrompt || node.lastPrompt || '')}</textarea><div class="mj-modal-mask ${hasMask ? 'ready' : ''}"><i data-lucide="${hasMask ? 'brush' : 'image-off'}"></i><span>${hasMask ? `遮罩已连接：${escapeHtml(maskRef.name || 'mask')}` : '连接遮罩图片节点后才能提交'}</span></div><button type="button" class="mj-reroll mj-modal-submit" ${hasMask && !node.running ? '' : 'disabled'}><i data-lucide="wand-sparkles"></i>${node.running ? '提交中...' : '提交局部重绘'}</button></div>`;
}
function midjourneyContinuationHtml(node){
    if(!node.lastTaskId || node.mjModalTaskId) return '';
    if(['blend','edit'].includes(node.lastAction)) return '';
    const isSingle = Number(node.lastImageCount || 0) === 1;
    if(!isSingle){
        if(['8.1','8.2'].includes(String(node.version || '')) && node.lastAction !== 'blend' && node.lastAction !== 'edit'){
            return `<div class="mj-actions"><div class="mj-action-title">v8 重塑</div><div class="mj-action-grid">${[1,2,3,4].map(index => `<button type="button" data-mj-action="remix_subtle" data-index="${index}" title="轻微重塑第 ${index} 张">R${index}</button>`).join('')}</div><div class="mj-action-grid">${[1,2,3,4].map(index => `<button type="button" data-mj-action="remix_strong" data-index="${index}" title="强烈重塑第 ${index} 张">R+${index}</button>`).join('')}</div><button class="mj-reroll" type="button" data-mj-action="reroll"><i data-lucide="refresh-cw"></i>重新生成</button></div>`;
        }
        return `<div class="mj-actions"><div class="mj-action-title">选择四宫格图片</div><div class="mj-action-grid">${[1,2,3,4].map(index => `<button type="button" data-mj-action="upscale" data-index="${index}" title="放大第 ${index} 张">U${index}</button>`).join('')}</div><div class="mj-action-grid">${[1,2,3,4].map(index => `<button type="button" data-mj-action="variation" data-index="${index}" title="生成第 ${index} 张的弱变体">V${index}</button>`).join('')}</div><button class="mj-reroll" type="button" data-mj-action="reroll"><i data-lucide="refresh-cw"></i>重新生成</button></div>`;
    }
    return `<div class="mj-actions"><div class="mj-action-title">单图细化</div><div class="mj-text-action-grid"><button type="button" data-mj-action="low_variation" data-index="1">弱变体</button><button type="button" data-mj-action="high_variation" data-index="1">强变体</button><button type="button" data-mj-action="zoom" data-zoom-ratio="1.5">扩图 1.5x</button><button type="button" data-mj-action="zoom" data-zoom-ratio="2">扩图 2x</button></div><div class="mj-pan-grid"><button type="button" data-mj-action="pan" data-direction="left" title="向左扩展"><i data-lucide="arrow-left"></i></button><button type="button" data-mj-action="pan" data-direction="up" title="向上扩展"><i data-lucide="arrow-up"></i></button><button type="button" data-mj-action="inpaint" title="局部重绘"><i data-lucide="brush"></i></button><button type="button" data-mj-action="pan" data-direction="right" title="向右扩展"><i data-lucide="arrow-right"></i></button></div></div>`;
}
function miniMaxAspectValue(value){
    return WorkbenchCanvasMediaTools.minimaxAspectValue(value);
}
function miniMaxRefsForNode(node){
    const sources = orderedSources(node, generatorSources(node));
    return WorkbenchCanvasMediaTools.minimaxSourceProjection(sources);
}
function miniMaxNormalizeRef(ref){
    return WorkbenchCanvasMediaTools.minimaxNormalizeRef(ref, mediaKindForRef);
}
function miniMaxUniqueRefs(refs=[]){
    return WorkbenchCanvasMediaTools.minimaxUniqueRefs(refs, mediaKindForRef);
}
function miniMaxRefSummary(refs=[]){
    return WorkbenchCanvasMediaTools.minimaxRefSummary(refs, mediaKindForRef);
}
function miniMaxEnsureSegment(node){
    node.minimaxEngine = ensureClassicMiniMaxControls().getEngine({node});
    const config = WorkbenchCanvasMediaTools.minimaxNodeConfig(node, miniMaxAspectValue, 'MiniMax_H3.json', CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID);
    node.workflow = config.workflow;
    node.minimaxRunningHubWorkflowId = config.minimaxRunningHubWorkflowId;
    node.rhPayment = config.rhPayment;
    node.aspectRatio = config.aspectRatio;
    node.megapixels = config.megapixels;
    node.segments = WorkbenchCanvasMediaTools.minimaxSegmentList(node.segments, node.duration || 8, () => uid('seg'));
    node.segments.forEach((seg, index) => {
        const previousEnd = index > 0 ? Number(node.segments[index - 1].start || 0) + Number(node.segments[index - 1].duration || 0) : 0;
        const timing = WorkbenchCanvasMediaTools.minimaxSegmentTiming(seg, previousEnd, node.duration || 8);
        seg.start = timing.start;
        seg.duration = timing.duration;
        seg.prompt = String(seg.prompt || '');
        const visuals = WorkbenchCanvasMediaTools.minimaxSegmentVisuals(seg, node.aspectRatio, node.megapixels, miniMaxAspectValue);
        seg.aspectRatio = visuals.aspectRatio;
        seg.megapixels = visuals.megapixels;
        seg.refs = WorkbenchCanvasMediaTools.minimaxReferenceMigration(seg, mediaKindForRef, CANVAS_MINIMAX_REF_IMAGE_MAX + CANVAS_MINIMAX_REF_VIDEO_MAX + CANVAS_MINIMAX_REF_AUDIO_MAX);
        const outputs = WorkbenchCanvasMediaTools.minimaxOutputProjection(seg, node.materials, outputUrlValue, mediaKindForOutputItem);
        seg.result = outputs.result;
        seg.results = outputs.results;
        seg.trimIn = timing.trimIn;
        seg.trimOut = timing.trimOut;
    });
    const selection = WorkbenchCanvasMediaTools.minimaxSelectionProjection(node.segments, node.selectedSegmentId, node.duration);
    node.selectedSegmentId = selection.selectedId;
    node.duration = selection.duration;
    node.materials = WorkbenchCanvasMediaTools.minimaxOutputProjection({}, node.materials, outputUrlValue, mediaKindForOutputItem).materials;
    return node.segments.find(seg => seg.id === node.selectedSegmentId) || node.segments[0];
}
function miniMaxSelectedSegment(node){
    return miniMaxEnsureSegment(node);
}
function miniMaxTimelineTotal(node){
    miniMaxEnsureSegment(node);
    return WorkbenchCanvasMediaTools.minimaxSelectionProjection(node.segments, node.selectedSegmentId, node.duration).duration;
}
function miniMaxActiveSegmentAt(node, time){
    miniMaxEnsureSegment(node);
    const safeTime = Math.max(0, Number(time || 0));
    return WorkbenchCanvasMediaTools.minimaxActiveSegment(node.segments, safeTime, node.selectedSegmentId);
}
function miniMaxCompactSegments(node){
    if(!node?.segments?.length) return;
    const projection = WorkbenchCanvasMediaTools.minimaxCompactSegments(node.segments, node.playhead);
    node.segments = projection.segments;
    node.duration = projection.duration;
    node.playhead = projection.playhead;
}
function miniMaxExplicitRefsForSegment(seg){
    return miniMaxUniqueRefs(seg?.refs || []);
}
function miniMaxRefsForSegment(node, seg){
    const upstream = miniMaxRefsForNode(node).refs;
    return WorkbenchCanvasMediaTools.minimaxSegmentRefs(seg, upstream, mediaKindForRef, CANVAS_MINIMAX_REF_IMAGE_MAX + CANVAS_MINIMAX_REF_VIDEO_MAX + CANVAS_MINIMAX_REF_AUDIO_MAX);
}
function miniMaxMediaHtml(item, label='Media'){
    return WorkbenchCanvasMediaOutputRenderer.renderLite(item, {
        label, urlValue:outputUrlValue,
        kind:value => mediaKindForOutputItem(value) || mediaKindForRef(value),
        escapeHtml, escapeAttr,
        imagePreview:canvasPreviewImgHtml,
        videoPreview:canvasVideoPreviewHtml,
    });
}
function miniMaxSetSegmentResult(node, seg, item){
    if(!node || !seg) return false;
    const result = WorkbenchCanvasMediaTools.minimaxSegmentResult(item, outputUrlValue);
    if(!result) return false;
    const url = outputUrlValue(result);
    seg.result = result;
    seg.results = WorkbenchCanvasMediaTools.minimaxPrependUnique(seg.results, result, outputUrlValue);
    node.materials = WorkbenchCanvasMediaTools.minimaxPrependUnique(node.materials, {...result, segmentId:seg.id, createdAt:Date.now()}, outputUrlValue);
    return true;
}
function miniMaxDownloadItem(item){
    const download = WorkbenchCanvasMediaTools.minimaxDownloadProjection(item, outputUrlValue, canvasFileNameFromUrl, safeDownloadFileName);
    if(!download) return;
    const link = document.createElement('a');
    link.href = canvasDisplayMediaUrl(download.url, download.name);
    link.download = download.name;
    document.body.appendChild(link);
    link.click();
    link.remove();
}
function miniMaxSegmentRefsByKind(refs, kind){
    return WorkbenchCanvasMediaTools.minimaxSegmentRefsByKind(refs, kind, mediaKindForRef);
}
function miniMaxSetPlayheadDom(wrap, node, time){
    const total = miniMaxTimelineTotal(node);
    const projection = WorkbenchCanvasMediaTools.minimaxTimelineInteraction(node.segments, total, time, node.selectedSegmentId);
    node.playhead = projection.safeTime;
    wrap.querySelectorAll('[data-minimax-playhead]').forEach(head => { head.style.left = `${projection.percent}%`; });
    const label = wrap.querySelector('[data-minimax-time-label]');
    if(label) label.textContent = projection.label;
    return projection.safeTime;
}
function miniMaxApplyTimelineTime(wrap, node, time, play=false){
    const safeTime = miniMaxSetPlayheadDom(wrap, node, time);
    const projection = WorkbenchCanvasMediaTools.minimaxTimelineInteraction(node.segments, miniMaxTimelineTotal(node), safeTime, node.selectedSegmentId);
    const seg = projection.active;
    if(projection.selectionChanged){
        node.selectedSegmentId = projection.selectedId;
        refreshNodes([node.id]);
        scheduleSave();
        return;
    }
    ensureClassicMiniMaxControls().syncPlayerDom({wrap, seg, time: safeTime, play});
}
function miniMaxStartPaneResize(e, node, pane){
    e.preventDefault();
    e.stopPropagation();
    const wrap = e.currentTarget?.closest?.('.minimax-canvas-workbench');
    const startX = e.clientX;
    const startY = e.clientY;
    const startLibrary = Math.max(170, Math.min(520, Number(node.minimaxLibraryW || 190)));
    const startPreview = Math.max(130, Math.min(760, Number(node.minimaxPreviewH || 220)));
    const startVideo = Math.max(48, Math.min(180, Number(node.minimaxVideoTrackH || 74)));
    const startRefLane = Math.max(30, Math.min(130, Number(node.minimaxRefLaneH || 36)));
    const refLanes = Math.max(1, wrap?.querySelectorAll?.('.minimax-ref-lane')?.length || 1);
    document.body.classList.add('canvas-minimax-pane-resize');
    const applyVars = () => {
        if(!wrap) return;
        wrap.querySelector('.minimax-wb-body')?.style.setProperty('--minimax-library-w', `${Math.max(170, Math.min(520, Number(node.minimaxLibraryW || 190)))}px`);
        const main = wrap.querySelector('.minimax-wb-main');
        if(main){
            main.style.setProperty('--minimax-preview-h', `${Math.max(130, Math.min(760, Number(node.minimaxPreviewH || 220)))}px`);
            main.style.setProperty('--minimax-video-h', `${Math.max(48, Math.min(180, Number(node.minimaxVideoTrackH || 74)))}px`);
            main.style.setProperty('--minimax-ref-lane-h', `${Math.max(30, Math.min(130, Number(node.minimaxRefLaneH || 36)))}px`);
            main.style.setProperty('--minimax-ref-h', `${Math.max(78, refLanes * Math.max(30, Math.min(130, Number(node.minimaxRefLaneH || 36))))}px`);
        }
    };
    const onMove = move => {
        move.preventDefault();
        const dx = (move.clientX - startX) / viewport.scale;
        const dy = (move.clientY - startY) / viewport.scale;
        const projection = WorkbenchCanvasMediaTools.minimaxPaneProjection({libraryW:startLibrary, previewH:startPreview, videoTrackH:startVideo, refLaneH:startRefLane}, {x:pane === 'library' ? dx : 0, y:pane === 'library' ? 0 : dy}, 1);
        if(pane === 'library') node.minimaxLibraryW = projection.libraryW;
        if(pane === 'preview') node.minimaxPreviewH = projection.previewH;
        if(pane === 'video') node.minimaxVideoTrackH = projection.videoTrackH;
        if(pane === 'refs') node.minimaxRefLaneH = projection.refLaneH;
        applyVars();
    };
    const onUp = () => {
        document.body.classList.remove('canvas-minimax-pane-resize');
        window.removeEventListener('mousemove', onMove, true);
        window.removeEventListener('mouseup', onUp, true);
        window.removeEventListener('blur', onUp, true);
        scheduleSave();
    };
    window.addEventListener('mousemove', onMove, true);
    window.addEventListener('mouseup', onUp, true);
    window.addEventListener('blur', onUp, true);
}
function renderPromptPreview(container, promptInputs){
    if(!container) return;
    const previewState = WorkbenchCanvasPromptTemplateRenderer.previewState(promptInputs);
    container.innerHTML = WorkbenchCanvasPromptTemplateRenderer.renderPreviewInputs(previewState.items, escapeHtml);
}
function renderImageInputList(list, node, imageInputs, emptyText=null){
    if(!list) return;
    const inputState = WorkbenchCanvasMediaInputRenderer.listState({refs:imageInputs});
    list.innerHTML = inputState.empty ? WorkbenchCanvasMediaInputRenderer.emptyMarkup(emptyText || tr('canvas.inputImagesEmpty'), escapeHtml) : '';
    inputState.refs.forEach((src, i) => {
        const item = document.createElement('div');
        item.className = 'input-item';
        item.draggable = true;
        item.dataset.sourceId = src.id;
        item.innerHTML = WorkbenchCanvasMediaInputRenderer.itemMarkup(src, i, {
            escapeHtml,
            isMissing: isMissingAssetUrl,
            preview: url => canvasPreviewImgHtml(url, 256),
            missing: url => missingAssetHtml(url, true),
        });
        item.ondragstart = e => {
            e.stopPropagation();
            internalDrag = true;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('application/x-canvas-input', src.id);
        };
        item.ondragend = () => { internalDrag = false; };
        item.ondragover = e => { e.preventDefault(); e.stopPropagation(); };
        item.ondrop = e => {
            e.preventDefault();
            e.stopPropagation();
            reorderInput(node, e.dataTransfer.getData('application/x-canvas-input'), src.id);
            internalDrag = false;
        };
        list.appendChild(item);
    });
    refreshIcons();
}
function hasComfyWorkflow(name){
    return WorkbenchCanvasComfyFieldRenderer.hasWorkflow(name, comfyWorkflows);
}
function validComfyWorkflowName(name){
    return WorkbenchCanvasComfyFieldRenderer.workflowName(name, comfyWorkflows);
}
function pruneMissingComfyWorkflows(){
    let changed = false;
    nodes.filter(n => n.type === 'comfy').forEach(node => {
        if(node.comfyWorkflow && !hasComfyWorkflow(node.comfyWorkflow)){
            delete comfyWorkflowCache[node.comfyWorkflow];
            node.comfyWorkflow = '';
            changed = true;
        }
    });
    if(changed) scheduleSave();
}
function currentComfyWorkflow(node){
    const selected = validComfyWorkflowName(node.comfyWorkflow || comfyWorkflows[0]?.name || '');
    return comfyWorkflowCache[selected] || null;
}
async function ensureComfyWorkflow(name){
    return WorkbenchCanvasComfyFieldRenderer.loadWorkflow(name, comfyWorkflows, comfyWorkflowCache,
        workflowName => fetch(`/api/workflows/${encodeURIComponent(workflowName)}`));
}
function validRunningHubWorkflowId(workflowId){
    return String(workflowId || '').trim();
}
async function ensureRunningHubWorkflow(workflowId){
    return WorkbenchCanvasRunningHubFieldRenderer.loadWorkflow(workflowId, runningHubWorkflowCache,
        id => fetch(`/api/runninghub/workflows/${encodeURIComponent(id)}`));
}
const comfyFieldProjection = WorkbenchCanvasComfyFieldRenderer.create({currentWorkflow: currentComfyWorkflow});
const comfyFieldKind = WorkbenchCanvasComfyFieldRenderer.kind;
const comfyFields = comfyFieldProjection.fields;
const comfyParamValue = comfyFieldProjection.paramValue;
const comfyRandomEnabled = comfyFieldProjection.randomEnabled;
const comfyRandomActive = comfyFieldProjection.randomActive;
const comfyRandomValue = comfyFieldProjection.randomValue;
function toggleComfyRandom(nodeId, fieldId){
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return;
    const field = comfyFields(node).find(f => f.id === fieldId);
    if(!comfyRandomEnabled(field)) return;
    node.comfyRandomActive = node.comfyRandomActive || {};
    node.comfyRandomActive = comfyFieldProjection.toggleRandomActive(node.comfyRandomActive, fieldId);
    refreshNodes([node.id]);
    scheduleSave();
}
function renderComfyImages(list, node, imageInputs){
    const inputState = WorkbenchCanvasMediaInputRenderer.listState({refs:imageInputs});
    list.innerHTML = inputState.empty ? WorkbenchCanvasMediaInputRenderer.emptyMarkup(tr('canvas.groupEmpty'), escapeHtml) : '';
    inputState.refs.forEach((src, i) => {
        const item = document.createElement('div');
        item.className = 'input-item';
        item.draggable = true;
        item.dataset.sourceId = src.id;
        const firstRef = (src.refs || [])[0];
        const kind = mediaKindForRef(firstRef || src.preview);
        const icon = kind === 'video' ? 'file-video' : kind === 'audio' ? 'file-audio' : 'image';
        const label = kind === 'image' ? `${tr('canvas.image')} ${i + 1}` : `${nodeTitleForMedia({mediaKind:kind})} ${i + 1}`;
        item.innerHTML = WorkbenchCanvasMediaInputRenderer.itemMarkup({...src, label}, i, {
            escapeHtml,
            isMissing: isMissingAssetUrl,
            preview: url => kind === 'video' ? canvasVideoPreviewHtml(url, 256) : canvasPreviewImgHtml(url, 256),
            missing: url => missingAssetHtml(url, true),
        });
        if(kind === 'audio' || !src.preview) item.innerHTML = WorkbenchCanvasMediaInputRenderer.itemMarkup({...src, label, preview:''}, i, {
            escapeHtml,
            preview: () => `<i data-lucide="${icon}" class="w-6 h-6 text-slate-400"></i>`,
        });
        item.ondragstart = e => {
            e.stopPropagation();
            internalDrag = true;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('application/x-canvas-input', src.id);
        };
        item.ondragend = () => { internalDrag = false; };
        item.ondragover = e => { e.preventDefault(); e.stopPropagation(); };
        item.ondrop = e => {
            e.preventDefault();
            e.stopPropagation();
            reorderInput(node, e.dataTransfer.getData('application/x-canvas-input'), src.id);
            internalDrag = false;
        };
        list.appendChild(item);
    });
}
const RH_KNOWN_FIELD_OPTIONS = {
    aspectRatio:['1:1','16:9','9:16','4:3','3:4','4:5','5:4','3:2','2:3','21:9','9:21'],
    aspect_ratio:['1:1','16:9','9:16','4:3','3:4','4:5','5:4','3:2','2:3','21:9','9:21'],
    ratio:['1:1','16:9','9:16','21:9','9:21','4:3','3:4','4:5','5:4','3:2','2:3'],
    resolution:['1k','2k','4k','8k'],
    size:['512','768','1024','1280','1536','2048'],
    mode:['text2img','img2img'],
    quality:['low','medium','high','best'],
    instanceType:['default','plus','pro'],
    instance_type:['default','plus','pro'],
    precision:['fp16','fp32','bf16'],
    scheduler:['normal','karras','exponential','sgm_uniform','simple','ddim_uniform'],
    sampler:['euler','euler_ancestral','heun','dpm_2','dpm_2_ancestral','lms','dpmpp_2m','dpmpp_sde','ddim','uni_pc']
};
function rhParamKey(nodeId, fieldName){
    return WorkbenchCanvasRunningHubFieldRenderer.paramKey(nodeId, fieldName);
}
function rhFieldKind(field){
    return WorkbenchCanvasRunningHubFieldRenderer.fieldKind(field);
}
function rhFieldRole(field){
    return WorkbenchCanvasRunningHubFieldRenderer.fieldRole(field);
}
function rhExtractFieldOptions(field){
    return WorkbenchCanvasRunningHubFieldRenderer.extractOptions(field, RH_KNOWN_FIELD_OPTIONS);
}
function rhDefaultValue(field){
    return WorkbenchCanvasRunningHubFieldRenderer.defaultValue(field);
}
function rhRandomEnabled(field){
    return WorkbenchCanvasRunningHubFieldRenderer.randomEnabled(field, {kindOf:rhFieldKind});
}
function rhRandomActive(node, key){
    node.rhRandomActive = node.rhRandomActive || {};
    return WorkbenchCanvasRunningHubFieldRenderer.randomActive(node.rhRandomActive, key);
}
function toggleRhRandom(nodeId, key){
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return;
    const field = rhActiveFields(node).find(f => rhParamKey(f.nodeId, f.fieldName) === key);
    if(!rhRandomEnabled(field)) return;
    node.rhRandomActive = node.rhRandomActive || {};
    node.rhRandomActive = WorkbenchCanvasRunningHubFieldRenderer.toggleRandomActive(node.rhRandomActive, key);
    refreshNodes([node.id]);
    scheduleSave();
}
function rhWorkflowNodeInfoList(data){
    return WorkbenchCanvasRunningHubFieldRenderer.workflowNodeInfoList(data, {linkOf:rhIsWorkflowLinkValue});
}
function rhInferWorkflowFieldType(fieldName, fieldValue){
    return WorkbenchCanvasRunningHubFieldRenderer.inferWorkflowFieldType(fieldName, fieldValue);
}
function rhIsWorkflowLinkValue(value){
    return WorkbenchCanvasRunningHubFieldRenderer.isWorkflowLinkValue(value);
}
function runningHubEntries(kind){
    const provider = ensureClassicRunningHubControls().getProvider();
    if(kind === 'model'){
        return uniqueModels(provider?.image_models || []).map(model => ({
            id:model,
            model,
            title:model,
            enabled:true,
            source:'model'
        }));
    }
    const key = kind === 'workflow' ? 'rh_workflows' : 'rh_apps';
    return WorkbenchCanvasRunningHubFieldRenderer.visibleEntries(provider?.[key]);
}
function runningHubEntryId(entry, kind){
    return WorkbenchCanvasRunningHubFieldRenderer.entryId(entry, kind);
}
function runningHubEntryLabel(entry, kind){
    return WorkbenchCanvasRunningHubFieldRenderer.entryLabel(entry, kind);
}
function runningHubEntryKey(kind, id){
    return WorkbenchCanvasRunningHubFieldRenderer.entryKey(kind, id);
}
function parseRunningHubEntryKey(value){
    return WorkbenchCanvasRunningHubFieldRenderer.parseEntryKey(value);
}
function runningHubAllEntries(){
    return WorkbenchCanvasRunningHubFieldRenderer.allEntries({model:runningHubEntries('model'), app:runningHubEntries('app'), workflow:runningHubEntries('workflow')}, {idOf:runningHubEntryId});
}
function rhSelectedEntryRef(node){
    const all = runningHubAllEntries();
    return WorkbenchCanvasRunningHubFieldRenderer.resolveEntryRef({...node, workflowId:validRunningHubWorkflowId(node?.workflowId || '')}, all);
}
function applyRhEntrySelection(node, ref){
    if(!node || !ref) return;
    node.rhConfigKey = runningHubEntryKey(ref.kind, ref.id);
    node.rhMode = ref.kind;
    if(ref.kind === 'workflow') node.workflowId = ref.id;
    else if(ref.kind === 'app') node.webappId = ref.id;
    else if(ref.kind === 'model'){
        node.rhModel = ref.id;
        node.model = ref.id;
        node.apiProvider = 'runninghub';
        node.resolution = node.resolution || defaultApiImageResolution(ref.id);
        node.ratio = node.ratio || 'square';
        node.quality = node.quality || 'auto';
        node.count = Math.max(1, Math.min(8, Number(node.count || 1)));
    }
}
function currentRunningHubAppConfig(node){
    const webappId = String(node?.webappId || '').trim();
    if(!webappId) return null;
    return runningHubEntries('app').find(app => runningHubEntryId(app, 'app') === webappId) || null;
}
function rhEntryFields(entry){
    return WorkbenchCanvasRunningHubFieldRenderer.entryFields(entry);
}
function rhWorkflowEntryHasSavedConfig(entry){
    return WorkbenchCanvasRunningHubFieldRenderer.workflowEntryHasSavedConfig(entry);
}
function rhWorkflowJsonFromSources(...sources){
    return WorkbenchCanvasRunningHubFieldRenderer.firstObjectSource(...sources);
}
function rhCurrentEntry(node){
    return WorkbenchCanvasRunningHubFieldRenderer.currentEntry(rhSelectedEntryRef(node));
}
function rhCurrentKind(node){
    const selected = rhSelectedEntryRef(node)?.kind;
    return WorkbenchCanvasRunningHubFieldRenderer.currentKind(node, selected);
}
function ensureRhNodeSelection(node){
    if(!node || node.type !== 'rh') return null;
    node.rhPayment = node.rhPayment || 'free';
    const all = runningHubAllEntries();
    let ref = rhSelectedEntryRef(node);
    if(!ref && all.length) ref = all[0];
    if(ref){
        applyRhEntrySelection(node, ref);
        return ref.entry;
    }
    return null;
}
function rhEntryOptions(selected){
    const models = runningHubEntries('model');
    const apps = runningHubEntries('app');
    const workflows = runningHubEntries('workflow');
    return WorkbenchCanvasRunningHubFieldRenderer.entryOptions({model:models, app:apps, workflow:workflows}, selected, {
        escapeHtml, escapeAttr,
        idOf: runningHubEntryId,
        labelOf: runningHubEntryLabel,
    });
}
function rhPaymentOptions(node){
    const provider = ensureClassicRunningHubControls().getProvider();
    return WorkbenchCanvasRunningHubFieldRenderer.paymentOptions(node.rhPayment, provider || {});
}
function rhUseWallet(node){ return ensureClassicExecutorRuntime().rhUseWallet(node); }
function rhUsableFields(fields){
    return WorkbenchCanvasRunningHubFieldRenderer.usableFields(fields);
}
function rhActiveFields(node){
    if(rhCurrentKind(node) === 'model') return [];
    const sortFields = fields => WorkbenchCanvasRunningHubFieldRenderer.sortFields(fields, {kindOf:rhFieldKind});
    if(rhCurrentKind(node) === 'workflow') {
        const workflowId = validRunningHubWorkflowId(node.workflowId || '');
        const savedEntry = ensureClassicRunningHubControls().getCurrentWorkflow({node});
        if(Array.isArray(savedEntry?.fields) && savedEntry.fields.length) return sortFields(rhUsableFields(savedEntry.fields));
        const saved = workflowId ? runningHubWorkflowCache[workflowId] : null;
        if(Array.isArray(saved?.fields)) return sortFields(rhUsableFields(saved.fields));
        return sortFields(node.rhWorkflowInfo?.nodeInfoList || []);
    }
    const savedApp = currentRunningHubAppConfig(node);
    if(Array.isArray(savedApp?.fields) && savedApp.fields.length) return sortFields(rhUsableFields(savedApp.fields));
    return sortFields(node.rhAppInfo?.nodeInfoList || []);
}
async function ensureRunningHubWorkflowConfigForNode(node){
    if(rhCurrentKind(node) !== 'workflow') return null;
    const workflowId = validRunningHubWorkflowId(node.workflowId || '');
    if(!workflowId) return null;
    if(!runningHubWorkflowCache[workflowId]){
        try { await ensureRunningHubWorkflow(workflowId); } catch(_) {}
    }
    return ensureClassicRunningHubControls().getCurrentWorkflowConfig({node});
}
function rhMediaSources(node){
    return WorkbenchCanvasRunningHubFieldRenderer.sourceProjection(generatorSources(node), {
        order:sources => orderedSources(node, sources),
        kindOf:mediaKindForRef,
        imageLimit:CANVAS_REFERENCE_IMAGE_MAX,
    });
}
function rhFieldIndexes(fields){
    return WorkbenchCanvasRunningHubFieldRenderer.mediaIndexes(fields, {kindOf:rhFieldKind, keyOf:rhParamKey});
}
function rhFieldValue(node, field, media=null){
    node.rhParams = node.rhParams || {};
    const key = rhParamKey(field.nodeId, field.fieldName);
    const kind = rhFieldKind(field);
    const param = node.rhParams[key];
    if(rhRandomEnabled(field) && rhRandomActive(node, key)){
        node.rhRandomValues = node.rhRandomValues || {};
        if(node.rhRandomValues[key] === undefined){
            node.rhRandomValues[key] = comfyRandomValue({
                input:field.fieldName,
                name:field.label || field.fieldName,
                min:field.min,
                max:field.max,
                step:field.step,
                type:'number'
            });
        }
        return node.rhRandomValues[key];
    }
    const idx = rhFieldIndexes(rhActiveFields(node))[key] || 0;
    const projection = WorkbenchCanvasRunningHubFieldRenderer.fieldValue(field, param, media || rhMediaSources(node), idx, {kindOf:rhFieldKind, roleOf:rhFieldRole, defaultValue:rhDefaultValue});
    if(rhCurrentKind(node) === 'workflow' && ['image','video','audio'].includes(kind) && field.required !== true && !projection.value && param?.sourceFromUpstream !== false) return '';
    return projection.value;
}
function rhRequiredLabel(field){
    return WorkbenchCanvasRunningHubFieldRenderer.fieldLabel(field);
}
function rhPruneWorkflowForMissingFields(workflowJson, missingFields){
    return WorkbenchCanvasRunningHubFieldRenderer.pruneWorkflowForMissingFields(workflowJson, missingFields, {nodeInfoListOf:rhWorkflowNodeInfoList, linkOf:rhIsWorkflowLinkValue});
}
async function rhBuildWorkflowRequestExtras(node, media, nodeInfoList){
    const config = await ensureRunningHubWorkflowConfigForNode(node);
    if(!config || (config.optionalImageMode || 'prune-workflow') !== 'prune-workflow') return {};
    const fields = rhActiveFields(node);
    const indexes = rhFieldIndexes(fields);
    const imageFields = fields.filter(field => rhFieldKind(field) === 'image');
    const mediaState = WorkbenchCanvasRunningHubFieldRenderer.mediaInputState(imageFields, media, {indexes, kindOf:rhFieldKind, keyOf:rhParamKey});
    if(mediaState.missingRequired.length) throw new Error(`RunningHub 工作流缺少必选图片：${rhRequiredLabel(mediaState.missingRequired[0])}`);
    const missingOptional = mediaState.missingOptional;
    if(!missingOptional.length) return {};
    missingOptional.forEach(field => {
        const key = rhParamKey(field.nodeId, field.fieldName);
        const idx = nodeInfoList.findIndex(item => rhParamKey(item.nodeId, item.fieldName) === key);
        if(idx >= 0) nodeInfoList.splice(idx, 1);
    });
    const workflow = rhPruneWorkflowForMissingFields(config.workflowJson || {}, missingOptional);
    return workflow ? {workflow} : {};
}
function miniMaxRunningHubEntry(node=null){
    const workflows = runningHubEntries('workflow');
    const currentId = String(node?.minimaxRunningHubWorkflowId || '').trim();
    return WorkbenchCanvasRunningHubFieldRenderer.selectEntry(workflows, currentId, CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_TITLE, CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID, item => runningHubEntryId(item, 'workflow'));
}
function miniMaxRunningHubFieldText(field){
    return WorkbenchCanvasRunningHubFieldRenderer.fieldText(field);
}
function miniMaxRunningHubFieldMatches(field, patterns=[], fallbackKeys=[]){
    return WorkbenchCanvasRunningHubFieldRenderer.fieldMatches(field, patterns, fallbackKeys, rhParamKey);
}
function miniMaxRunningHubFullAspectField(field){
    return WorkbenchCanvasRunningHubFieldRenderer.isFullAspectField(field, rhDefaultValue);
}
function miniMaxFullAspectLabel(ratio){
    return WorkbenchCanvasRunningHubFieldRenderer.fullAspectLabel(ratio, miniMaxAspectValue);
}
function miniMaxRunningHubValue(field, desired){
    return WorkbenchCanvasRunningHubFieldRenderer.valueForField(field, desired, {normalize:miniMaxAspectValue, defaultValue:rhDefaultValue, extractOptions:rhExtractFieldOptions});
}
function miniMaxSetRunningHubParam(params, fields, patterns, fallbackKeys, desired){
    return WorkbenchCanvasRunningHubFieldRenderer.setParam(params, fields, patterns, fallbackKeys, desired, {keyOf:rhParamKey, normalize:miniMaxAspectValue, defaultValue:rhDefaultValue, extractOptions:rhExtractFieldOptions});
}
function miniMaxCompactJson(value, limit=1800){
    return WorkbenchCanvasRunningHubFieldRenderer.compactJson(value, limit);
}
function miniMaxDetailedError(message, details={}){
    return WorkbenchCanvasRunningHubFieldRenderer.detailedError(message, details);
}
function miniMaxRunningHubPayloadError(stage, data, fallback, extra={}){
    return WorkbenchCanvasRunningHubFieldRenderer.payloadError(stage, data, fallback, extra);
}
function miniMaxReadableError(error, engine='comfyui'){
    return WorkbenchCanvasRunningHubFieldRenderer.readableError(error, engine, tr('canvas.generationFailed'));
}
function miniMaxLogError(error, engine='comfyui'){
    return WorkbenchCanvasRunningHubFieldRenderer.logErrorText(error, engine, tr('canvas.generationFailed'));
}
function rhMediaPreviewHtml(ref, kind){
    const safe = escapeAttr(ref?.url || '');
    if(kind === 'video') return canvasVideoPreviewHtml(ref?.url || '', 256);
    if(kind === 'audio') return `<i data-lucide="file-audio" class="w-6 h-6 text-slate-400"></i>`;
    return safe && !isMissingAssetUrl(safe) ? canvasPreviewImgHtml(safe, 256) : `<i data-lucide="image" class="w-6 h-6 text-slate-400"></i>`;
}
function rhModelSettingsHtml(node){
    const count = Math.max(1, Math.min(8, Number(node.count || 1)));
    return `
        <div class="gen-settings rh-model-settings">
            <div class="gen-settings-row api-size-row">
                <select class="select-lite resolution compact-select" data-rh-model-field="resolution">
                    <option value="auto">自动</option>
                    <option value="1k">1K</option>
                    <option value="2k">2K</option>
                    <option value="4k">4K</option>
                    <option value="custom">${tr('canvas.custom')}</option>
                </select>
                <select class="select-lite ratio compact-select" data-rh-model-field="ratio">
                    <option value="square">1:1</option>
                    <option value="portrait">2:3</option>
                    <option value="landscape">3:2</option>
                    <option value="portrait43">3:4</option>
                    <option value="landscape43">4:3</option>
                    <option value="story">9:16</option>
                    <option value="wide">16:9</option>
                    <option value="ultrawide">21:9</option>
                    <option value="ultratall">9:21</option>
                    <option value="source">${tr('canvas.adaptiveRatio')}</option>
                    <option value="custom">${tr('canvas.custom')}</option>
                </select>
                <select class="select-lite quality-select" data-rh-model-field="quality">
                    <option value="auto">Q auto</option>
                    <option value="low">Q low</option>
                    <option value="medium">Q med</option>
                    <option value="high">Q high</option>
                </select>
                <input class="setting-input rh-model-count-input" data-rh-model-field="count" type="number" min="1" max="8" step="1" value="${count}" style="width:64px">
            </div>
            <div class="gen-settings-row custom-ratio-row" style="display:none">
                <label class="field"><div class="setting-title">${tr('canvas.ratioWidth')}</div><input class="setting-input custom-ratio-w-input" data-rh-model-field="customRatioWidth" type="number" min="1" step="1" value="${escapeHtml(node.customRatioWidth || '')}" placeholder="4"></label>
                <label class="field"><div class="setting-title">${tr('canvas.ratioHeight')}</div><input class="setting-input custom-ratio-h-input" data-rh-model-field="customRatioHeight" type="number" min="1" step="1" value="${escapeHtml(node.customRatioHeight || '')}" placeholder="3"></label>
            </div>
            <div class="gen-settings-row custom-size-row" style="display:none">
                <label class="field"><div class="setting-title">${tr('canvas.width')}</div><input class="setting-input custom-w-input" data-rh-model-field="customWidth" type="number" min="64" step="64" value="${escapeHtml(node.customWidth || '')}" placeholder="Auto"></label>
                <label class="field"><div class="setting-title">${tr('canvas.height')}</div><input class="setting-input custom-h-input" data-rh-model-field="customHeight" type="number" min="64" step="64" value="${escapeHtml(node.customHeight || '')}" placeholder="Auto"></label>
            </div>
        </div>
    `;
}
function bindRhModelControls(wrap, node, media){
    const resolutionSelect = wrap.querySelector('[data-rh-model-field="resolution"]');
    const ratioSelect = wrap.querySelector('[data-rh-model-field="ratio"]');
    const qualitySelect = wrap.querySelector('[data-rh-model-field="quality"]');
    const countInput = wrap.querySelector('[data-rh-model-field="count"]');
    const customRatioRow = wrap.querySelector('.custom-ratio-row');
    const customSizeRow = wrap.querySelector('.custom-size-row');
    const customRatioWInput = wrap.querySelector('[data-rh-model-field="customRatioWidth"]');
    const customRatioHInput = wrap.querySelector('[data-rh-model-field="customRatioHeight"]');
    const customWInput = wrap.querySelector('[data-rh-model-field="customWidth"]');
    const customHInput = wrap.querySelector('[data-rh-model-field="customHeight"]');
    const hydrateCustomParts = () => {
        if((!node.customRatioWidth || !node.customRatioHeight) && node.customRatio) {
            const raw = String(node.customRatio || '');
            if(raw.includes(':')){
                const [w,h] = raw.split(':');
                node.customRatioWidth = node.customRatioWidth || w;
                node.customRatioHeight = node.customRatioHeight || h;
            }
        }
        if((!node.customWidth || !node.customHeight) && node.customSize) {
            const parsed = parseSizeValue(node.customSize);
            node.customWidth = node.customWidth || parsed?.width || '';
            node.customHeight = node.customHeight || parsed?.height || '';
        }
    };
    const sync = () => {
        hydrateCustomParts();
        normalizeApiNodeSizeChoice(node);
        if(resolutionSelect) resolutionSelect.value = node.resolution || defaultApiImageResolution(node.model);
        if(ratioSelect) ratioSelect.value = node.ratio || 'square';
        if(qualitySelect) qualitySelect.value = node.quality || 'auto';
        if(countInput) countInput.value = Math.max(1, Math.min(8, Number(node.count || 1)));
        if(customRatioRow) customRatioRow.style.display = node.ratio === 'custom' ? '' : 'none';
        if(customSizeRow) customSizeRow.style.display = node.resolution === 'custom' ? '' : 'none';
        if(customRatioWInput) customRatioWInput.value = node.customRatioWidth || '';
        if(customRatioHInput) customRatioHInput.value = node.customRatioHeight || '';
        if(customWInput) customWInput.value = node.customWidth || '';
        if(customHInput) customHInput.value = node.customHeight || '';
    };
    wrap.querySelectorAll('[data-rh-model-field]').forEach(control => {
        control.onmousedown = e => e.stopPropagation();
        control.onclick = e => e.stopPropagation();
        control.oninput = control.onchange = e => {
            const field = control.dataset.rhModelField;
            if(field === 'resolution'){
                node.resolution = e.target.value || defaultApiImageResolution(node.model);
                node._apiResolutionUserSet = true;
            } else if(field === 'ratio'){
                node.ratio = e.target.value || 'square';
            } else if(field === 'quality'){
                node.quality = e.target.value || 'auto';
            } else if(field === 'count'){
                node.count = Math.max(1, Math.min(8, Number(e.target.value || 1)));
            } else if(field === 'customRatioWidth' || field === 'customRatioHeight'){
                node[field] = e.target.value;
                node.customRatio = node.customRatioWidth && node.customRatioHeight ? `${node.customRatioWidth}:${node.customRatioHeight}` : '';
            } else if(field === 'customWidth' || field === 'customHeight'){
                node[field] = e.target.value;
                node.customSize = node.customWidth && node.customHeight ? `${node.customWidth}x${node.customHeight}` : '';
            }
            sync();
            scheduleSave();
        };
    });
    sync();
}
function renderRhInputs(list, node, media){
    if(!list) return;
    const inputState = WorkbenchCanvasMediaInputRenderer.listState(media);
    if(inputState.empty){
        list.innerHTML = `<div class="text-[11px] text-gray-300 py-2">${tr('canvas.groupEmpty')}</div>`;
        return;
    }
    list.innerHTML = '';
    inputState.refs.forEach((ref, i) => {
        const kind = mediaKindForRef(ref);
        const item = document.createElement('div');
        item.className = 'input-item rh-input-item';
        item.innerHTML = WorkbenchCanvasMediaInputRenderer.itemMarkup({
            preview: ref?.url,
            label: nodeTitleForMedia({mediaKind:kind}),
        }, i, {
            escapeHtml,
            isMissing: () => false,
            preview: () => rhMediaPreviewHtml(ref, kind),
        });
        list.appendChild(item);
    });
}
function renderRhPromptFields(container, node, fields){
    if(!container) return;
    const prompts = WorkbenchCanvasRunningHubFieldRenderer.promptFields(fields, {
        roleOf: rhFieldRole,
        keyOf: rhParamKey,
        valueOf: field => rhFieldValue(node, field, rhMediaSources(node)),
    });
    if(!prompts.length){
        container.innerHTML = '';
        return;
    }
    container.innerHTML = prompts.map(prompt => WorkbenchCanvasRunningHubFieldRenderer.promptMarkup({escapeHtml, escapeAttr, label:prompt.label, key:prompt.key, value:prompt.value})).join('');
    bindRhParamControls(container, node);
}
function renderRhSettingField(node, field, key, kind, label, value, options, wide=false){
    const descriptor = WorkbenchCanvasRunningHubFieldRenderer.settingField(
        field, key, kind, label, value, options, rhRandomEnabled(field), rhRandomEnabled(field) ? rhRandomActive(node, key) : false,
    );
    return WorkbenchCanvasRunningHubFieldRenderer.render({escapeHtml, escapeAttr, ...descriptor, wide});
}
function bindRhParamControls(container, node){
    container.querySelectorAll('button[data-rh-param]').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = e => {
            e.stopPropagation();
            const key = btn.dataset.rhParam;
            node.rhParams = node.rhParams || {};
            const field = rhActiveFields(node).find(f => rhParamKey(f.nodeId, f.fieldName) === key);
            const cur = node.rhParams[key] || {};
            const on = String(rhFieldValue(node, field)).toLowerCase() === 'true';
            node.rhParams[key] = {...cur, value:String(!on)};
            render();
            scheduleSave();
        };
    });
    container.querySelectorAll('input[data-rh-param], select[data-rh-param], textarea[data-rh-param]').forEach(control => {
        control.onmousedown = e => e.stopPropagation();
        control.onclick = e => e.stopPropagation();
        control.oninput = control.onchange = e => {
            const key = control.dataset.rhParam;
            node.rhParams = node.rhParams || {};
            const cur = node.rhParams[key] || {};
            node.rhParams[key] = {...cur, value:e.target.value};
            const val = control.closest('.field')?.querySelector('.rh-param-val');
            if(val) val.textContent = e.target.value;
            scheduleSave();
        };
    });
    container.querySelectorAll('[data-rh-random]').forEach(btn => {
        btn.onmousedown = e => e.stopPropagation();
        btn.onclick = e => {
            e.stopPropagation();
            toggleRhRandom(node.id, btn.dataset.rhRandom);
        };
    });
}
async function rhFetchAppInfo(nodeId, showAlert=true){
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return;
    if(!String(node.webappId || '').trim()){
        if(showAlert) alert(tr('canvas.rhNeedWebappId'));
        return false;
    }
    node.rhFetching = true;
    refreshNodes([node.id]);
    try {
        const res = await fetch(`/api/runninghub/app-info?webappId=${encodeURIComponent(node.webappId.trim())}`);
        const data = await res.json();
        if(!res.ok || data.success === false) throw new Error(data.detail || data.error || tr('canvas.rhFailed'));
        node.rhAppInfo = data.data || {};
        node.rhParams = node.rhParams || {};
        (node.rhAppInfo.nodeInfoList || []).forEach(field => {
            const key = rhParamKey(field.nodeId, field.fieldName);
            if(!node.rhParams[key]) node.rhParams[key] = {value:rhDefaultValue(field)};
        });
        ensureClassicExecutionHost().setRunStatus(node, '', '');
        scheduleSave();
        return true;
    } catch(err) {
        if(showAlert) alert(err.message || tr('canvas.rhFailed'));
        return false;
    } finally {
        node.rhFetching = false;
        refreshNodes([node.id]);
    }
}
async function rhFetchWorkflowInfo(nodeId, showAlert=true){
    const node = nodes.find(n => n.id === nodeId);
    if(!node) return false;
    if(!String(node.workflowId || '').trim()){
        if(showAlert) alert(tr('canvas.rhNeedWorkflowId'));
        return false;
    }
    node.rhFetching = true;
    refreshNodes([node.id]);
    try {
        const saved = await ensureRunningHubWorkflow(node.workflowId.trim());
        const res = await fetch(`/api/runninghub/workflow-info?workflowId=${encodeURIComponent(node.workflowId.trim())}`);
        const data = await res.json();
        if(!res.ok || data.success === false) throw new Error(data.detail || data.error || tr('canvas.rhFailed'));
        const info = data.data || {};
        const savedFields = Array.isArray(saved?.fields) ? saved.fields : [];
        const mergedFields = savedFields.length
            ? savedFields
            : Array.isArray(info.nodeInfoList) ? info.nodeInfoList : [];
        node.rhWorkflowInfo = {
            workflowId:node.workflowId.trim(),
            nodeInfoList:mergedFields,
            raw:info.raw || null
        };
        node.rhParams = node.rhParams || {};
        (node.rhWorkflowInfo.nodeInfoList || []).forEach(field => {
            const key = rhParamKey(field.nodeId, field.fieldName);
            if(!node.rhParams[key]) node.rhParams[key] = {value:rhDefaultValue(field)};
        });
        ensureClassicExecutionHost().setRunStatus(node, '', '');
        scheduleSave();
        return true;
    } catch(err) {
        if(showAlert) alert(err.message || tr('canvas.rhFailed'));
        return false;
    } finally {
        node.rhFetching = false;
        refreshNodes([node.id]);
    }
}
async function rhImportWorkflowJson(nodeId, file){ return ensureClassicAssetRuntime().rhImportWorkflowJson(nodeId, file); }
async function rhUploadValueIfNeeded(value, node=null){ return ensureClassicAssetRuntime().rhUploadValueIfNeeded(value, node); }
async function rhBuildNodeInfoList(node, media){
    const fields = rhActiveFields(node);
    const result = [];
    const indexes = rhFieldIndexes(fields);
    for(const field of fields){
        const kind = rhFieldKind(field);
        const key = rhParamKey(field.nodeId, field.fieldName);
        if(rhCurrentKind(node) === 'workflow' && field.sourceFromUpstream === false && !['image','video','audio'].includes(kind)) continue;
        if(rhCurrentKind(node) === 'workflow' && kind === 'image'){
            const idx = indexes[key] || 0;
            const hasInput = Boolean(media.image?.[idx]?.url);
            if(field.required !== true && !hasInput) continue;
        }
        let value = rhFieldValue(node, field, media);
        if(['image','video','audio'].includes(kind)) value = await rhUploadValueIfNeeded(value, node);
        if(['number','slider'].includes(kind) && String(value ?? '').trim() !== '' && !Number.isNaN(Number(value))) value = Number(value);
        result.push({nodeId:field.nodeId, fieldName:field.fieldName, fieldValue:value});
    }
    return result;
}
async function runRhNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runRhNode(nodeId, opts); }
async function runRhModelNode(node, opts={}){ return ensureClassicExecutorRuntime().runRhModelNode(node, opts); }
function renderComfyCustomField(node, f){
    const value = comfyParamValue(node, f);
    const label = f.name || f.input;
    const options = {escapeHtml, id:f.id, label, type:f.type, value};
    if(f.type === 'slider') Object.assign(options, {min:f.min ?? 0, max:f.max ?? 10, step:f.step ?? 1});
    if(f.type === 'dropdown') options.options = f.options || [];
    if(comfyRandomEnabled(f)) Object.assign(options, {type:'number', random:true, active:comfyRandomActive(node, f.id)});
    if(f.type === 'boolean') options.active = value;
    return WorkbenchCanvasComfyFieldRenderer.render(options);
}
function hasExplicitOutputConnection(nodeId){
    return connections.some(c => {
        if(c.from !== nodeId) return false;
        const to = nodes.find(n => n.id === c.to);
        return to?.type === 'output';
    });
}
function hasDownstreamGenerator(nodeId){
    return connections.some(c => {
        if(c.from !== nodeId) return false;
        const to = nodes.find(n => n.id === c.to);
        if(!to) return false;
        if(CANVAS_GENERATOR_TYPES.includes(to.type)) return true;
        if(to.type !== 'output') return false;
        return connections.some(cc => {
            if(cc.from !== to.id) return false;
            const next = nodes.find(n => n.id === cc.to);
            return next && CANVAS_GENERATOR_TYPES.includes(next.type);
        });
    });
}
function shouldCreateOutputForNode(node){
    if(!node) return false;
    if(hasExplicitOutputConnection(node.id)) return true;
    return !hasDownstreamGenerator(node.id);
}
function outputForNode(node, dx=460){ return ensureClassicExecutorRuntime().outputForNode(node, dx); }
function outputNodesForSource(nodeId){
    return WorkbenchCanvasMediaTools.outputNodesForSource(nodeId, connections, nodes);
}
function latestGeneratedOutputItem(node){
    return WorkbenchCanvasMediaTools.latestGeneratedOutputItem(node, outputUrlValue);
}
function outputHasUrl(out, url){
    return WorkbenchCanvasMediaTools.outputHasUrl(out, url, outputUrlValue);
}
function appendOutputImagesWithoutDuplicates(out, images, compareRef=null, metas=[], layout=null){
    const next = WorkbenchCanvasMediaTools.appendUniqueOutputRecords(out.images, images, compareRef, metas, layout, outputUrlValue);
    out.images = next.images;
    if(next.outputLayout) out.outputLayout = next.outputLayout;
    else if(out.outputLayout) delete out.outputLayout;
    if(Object.keys(next.imageComparisons).length) out.imageComparisons = {...(out.imageComparisons || {}), ...next.imageComparisons};
    return next.added;
}
function syncLatestGeneratedOutputToConnection(fromId, toId){
    const source = nodes.find(n => n.id === fromId);
    const out = nodes.find(n => n.id === toId);
    if(!source || !out || out.type !== 'output' || !CANVAS_MEDIA_OUTPUT_TYPES.includes(source.type)) return false;
    const latest = latestGeneratedOutputItem(source);
    if(!latest) return false;
    return appendOutputImagesWithoutDuplicates(out, [latest]) > 0;
}
function syncConnectedOutputsFromGenerated(node, outputs){
    if(!node || !CANVAS_MEDIA_OUTPUT_TYPES.includes(node.type)) return;
    const list = WorkbenchCanvasMediaTools.outputItemsWithUrl(outputs, outputUrlValue);
    if(!list.length) return;
    outputNodesForSource(node.id).forEach(out => appendOutputImagesWithoutDuplicates(out, list));
}
function generatedImageRefs(node){
    return WorkbenchCanvasMediaTools.generatedMediaRefs(node, {
        outputUrlValue,
        mediaKindForOutputItem,
        outputImageName,
        mediaOutputTypes:['rh','ltxDirector','video','minimax'],
    });
}
function mediaRefsFromNode(node){
    return WorkbenchCanvasMediaTools.mediaRefsFromNode(node, {
        nodes,
        mediaKindForNode,
        mediaKindForOutputItem,
        outputUrlValue,
        outputImageName,
        generatedImageRefs,
        mediaOutputTypes:CANVAS_MEDIA_OUTPUT_TYPES,
    });
}
function generatorSources(gen){
    return WorkbenchCanvasMediaTools.generatorSourceProjection(gen, connections, nodes, {
        outputUrlValue,
        mediaKindForOutputItem,
        mediaKindForNode,
        generatedImageRefs,
        mediaOutputTypes:CANVAS_MEDIA_OUTPUT_TYPES,
        loopContext,
        renderLoopPrompt,
        loopInputImageRefs,
        loopImageLabel:index => trf('canvas.loopImageLabel', {n:index}),
        loopLabel:node => `${tr('canvas.loopNode')} ${loopCount(node)}x`,
    });
}
function orderedSources(gen, sources){
    return WorkbenchCanvasMediaTools.orderedInputSources(gen, sources);
}
function reorderInput(gen, movedId, targetId){
    if(!movedId || movedId === targetId) return;
    const sources = generatorSources(gen);
    const imageIds = WorkbenchCanvasMediaTools.refSourceIds(sources);
    const next = WorkbenchCanvasMediaTools.reorderInputIds(gen.inputs, movedId, targetId, imageIds);
    if(!next) return;
    gen.inputs = next;
    render();
    scheduleSave();
}
function syncGeneratorInputs(){
    nodes.filter(n => CANVAS_GENERATOR_TYPES.includes(n.type)).forEach(gen => {
        orderedSources(gen, generatorSources(gen));
        if(gen.type === 'ltxDirector') ltxSyncConnectedImagesToTimeline(gen);
    });
}
// 提示词节点每敲一个字都全量重建所有生成器节点的输入/预览 DOM 会卡顿。节点的 text 已即时写入
// （运行时实时读取，不受影响），生成器里的预览只需稍后同步一次即可，这里做防抖。
let generatorInputSyncTimer = 0;
function scheduleGeneratorInputSync(){
    clearTimeout(generatorInputSyncTimer);
    generatorInputSyncTimer = setTimeout(() => {
        syncGeneratorInputs();
        refreshGeneratorInputViews();
    }, 160);
}
function refreshGeneratorInputViews(){
    nodes.filter(n => CANVAS_GENERATOR_TYPES.includes(n.type)).forEach(gen => {
        const el = nodesEl.querySelector(`.node[data-id="${gen.id}"]`);
        if(!el) return;
        const sources = orderedSources(gen, generatorSources(gen));
        const inputProjection = WorkbenchCanvasMediaTools.inputViewProjection(sources, imageRefsOnly);
        const imageInputs = inputProjection.imageInputs;
        renderPromptPreview(el.querySelector('.prompt-list'), inputProjection.promptInputs);
        if(gen.type === 'generator') renderImageInputList(el.querySelector('.input-list'), gen, imageInputs);
        if(gen.type === 'midjourney') renderImageInputList(el.querySelector('.mj-input-list'), gen, imageInputs);
        if(gen.type === 'msgen') renderImageInputList(el.querySelector('.ms-img-list'), gen, imageInputs);
        if(gen.type === 'comfy') renderComfyImages(el.querySelector('.input-list'), gen, imageInputs);
        if(gen.type === 'ltxDirector'){
            ltxSyncConnectedImagesToTimeline(gen);
            renderComfyImages(el.querySelector('.input-list'), gen, imageInputs);
        }
        if(gen.type === 'video') ensureClassicVideoProviderParams().renderVideoImageInputs({list: el.querySelector('.video-img-list'), node: gen, inputs: imageInputs});
        if(gen.type === 'minimax'){
            miniMaxEnsureSegment(gen);
            refreshNodes([gen.id]);
            return;
        }
        if(gen.type === 'rh'){
            const media = rhMediaSources(gen);
            if(rhCurrentKind(gen) === 'model') renderPromptPreview(el.querySelector('.rh-prompt-list'), WorkbenchCanvasMediaTools.inputViewProjection(media.sources, imageRefsOnly).promptInputs);
            else renderRhPromptFields(el.querySelector('.rh-prompt-list'), gen, rhActiveFields(gen));
            renderRhInputs(el.querySelector('.rh-input-list'), gen, media);
            ensureClassicRunningHubControls().renderParams({container: el.querySelector('.rh-param-list'), node: gen, fields: rhActiveFields(gen), media});
        }
    });
}
async function runGenerator(genId, opts={}){ return ensureClassicExecutorRuntime().runGenerator(genId, opts); }
async function midjourneyRequest(path, options={}){ return ensureClassicExecutorRuntime().midjourneyRequest(path, options); }
async function waitMidjourneyTask(providerId, taskId, options={}){ return ensureClassicExecutorRuntime().waitMidjourneyTask(providerId, taskId, options); }
async function completeMidjourneyRun(node, out, run, result, append=false){
    const executionHost = ensureClassicExecutionHost();
    const outputs = result.image_items?.length ? result.image_items : (result.images || []);
    if(!outputs.length) throw new Error('Midjourney 任务没有返回图片');
    run.request = requestMetaFromResult(result);
    run.request.task_id = result.task_id || node.lastTaskId || '';
    appendOutputImages(out, outputs, run.refs?.[0], [{runMs:nowMs() - Number(run.startedAt || nowMs()), run}]);
    mergeGeneratedOutputs(node, outputs, append);
    executionHost.setRunStatus(node, 'done', '');
    executionHost.markRunning(node, false);
    node.lastTaskStatus = 'SUCCESS';
    node.lastImageCount = outputs.length;
    addGenerationLog({run, outputs, runMs:nowMs() - Number(run.startedAt || nowMs())});
    executionHost.render(node, out);
    executionHost.save();
}
async function runMidjourneyNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runMidjourneyNode(nodeId, opts); }
async function runMidjourneyAction(nodeId, action, index=0, extra={}){ return ensureClassicExecutorRuntime().runMidjourneyAction(nodeId, action, index, extra); }
async function runMidjourneyModal(nodeId, maskRef){ return ensureClassicExecutorRuntime().runMidjourneyModal(nodeId, maskRef); }
async function runGeneratorLegacy(genId, opts={}){ return ensureClassicExecutorRuntime().runGeneratorLegacy(genId, opts); }
async function runVideoNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runVideoNode(nodeId, opts); }
async function miniMaxDynamicParams(node, prompt, refs){
    const seg = miniMaxSelectedSegment(node);
    const duration = Math.max(1, Math.min(60, Number(seg?.duration || node.duration || 8) || 8));
    const params = {
        "136":{},
        "115":{aspect_ratio:miniMaxFullAspectLabel(seg?.aspectRatio || node.aspectRatio || '16:9'), megapixels:Number(seg?.megapixels || node.megapixels || 0.4)},
        "132":{value:duration},
        "138":{value:prompt},
        "129":{noise_seed:Math.floor(Math.random() * 4294967295)}
    };
    for(let i = 0; i < CANVAS_MINIMAX_REF_IMAGE_MAX; i++) params["136"][`ref_images.ref_image_${i}`] = null;
    for(let i = 0; i < CANVAS_MINIMAX_REF_VIDEO_MAX; i++) params["136"][`ref_videos.ref_video_${i}`] = null;
    for(let i = 0; i < CANVAS_MINIMAX_REF_AUDIO_MAX; i++) params["136"][`ref_audios.ref_audio_${i}`] = null;
    const images = imageRefsOnly(refs);
    const videos = videoRefsOnly(refs);
    const audios = audioRefsOnly(refs);
    if(images.length > CANVAS_MINIMAX_REF_IMAGE_MAX) throw new Error(`MiniMax H3 最多支持 ${CANVAS_MINIMAX_REF_IMAGE_MAX} 张参考图`);
    if(videos.length > CANVAS_MINIMAX_REF_VIDEO_MAX) throw new Error(`MiniMax H3 最多支持 ${CANVAS_MINIMAX_REF_VIDEO_MAX} 段参考视频`);
    if(audios.length > CANVAS_MINIMAX_REF_AUDIO_MAX) throw new Error(`MiniMax H3 最多支持 ${CANVAS_MINIMAX_REF_AUDIO_MAX} 段参考音频`);
    for(let i = 0; i < images.length; i++){
        const name = await comfyNameForRef(images[i]);
        params[String(9000 + i)] = {class_type:'LoadImage', inputs:{image:name}, _meta:{title:`MiniMax image ${i + 1}`}};
        params["136"][`ref_images.ref_image_${i}`] = [String(9000 + i), 0];
    }
    for(let i = 0; i < videos.length; i++){
        const name = await comfyNameForRef(videos[i]);
        const loadNodeId = String(9040 + i);
        const componentsNodeId = String(9050 + i);
        params[loadNodeId] = {class_type:'LoadVideo', inputs:{file:name}, _meta:{title:`MiniMax video ${i + 1}`}};
        params[componentsNodeId] = {class_type:'GetVideoComponents', inputs:{video:[loadNodeId, 0]}, _meta:{title:`MiniMax video frames ${i + 1}`}};
        params["136"][`ref_videos.ref_video_${i}`] = [componentsNodeId, 0];
    }
    for(let i = 0; i < audios.length; i++){
        const name = await comfyNameForRef(audios[i]);
        params[String(9060 + i)] = {class_type:'LoadAudio', inputs:{audio:name}, _meta:{title:`MiniMax audio ${i + 1}`}};
        params["136"][`ref_audios.ref_audio_${i}`] = [String(9060 + i), 0];
    }
    return params;
}
async function miniMaxRunningHubSettings(node){
    const entry = miniMaxRunningHubEntry(node);
    const workflowId = runningHubEntryId(entry, 'workflow');
    if(!entry || !workflowId) throw new Error(`请先在 API 设置中添加「${CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_TITLE}」`);
    node.minimaxRunningHubWorkflowId = workflowId;
    node.rhPayment = node.rhPayment || 'free';
    const cached = await ensureRunningHubWorkflow(workflowId).catch(() => null);
    const fields = rhUsableFields(
        Array.isArray(entry?.fields) && entry.fields.length ? entry.fields : (cached?.fields || [])
    );
    if(!fields.length) throw new Error(`请先在 API 设置中打开「${runningHubEntryLabel(entry, 'workflow')}」，拉取并保存工作流参数`);
    const rhNode = {
        type:'rh',
        rhMode:'workflow',
        rhConfigKey:runningHubEntryKey('workflow', workflowId),
        workflowId,
        rhPayment:node.rhPayment || 'free',
        rhParams:{},
        rhWorkflowInfo:{workflowId, nodeInfoList:fields},
        rhOptionalImageMode:entry.optionalImageMode || cached?.optionalImageMode || 'prune-workflow'
    };
    return {entry, workflowId, fields, rhNode};
}
function miniMaxApplyRunningHubParams(rhNode, fields, node, prompt){
    const seg = miniMaxSelectedSegment(node);
    const params = rhNode.rhParams || {};
    rhNode.rhParams = WorkbenchCanvasRunningHubFieldRenderer.applyPresetParams(params, fields, [
        {patterns:[/prompt|positive|text|caption|description|关键词|提示词|正向/], fallbackKeys:['138::value'], value:prompt},
        {patterns:[/duration|seconds|时长|秒/], fallbackKeys:['132::value'], value:Math.max(1, Math.min(60, Number(seg?.duration || node.duration || 8) || 8))},
        {patterns:[/aspect[_\s-]?ratio|\bratio\b|画面比例|比例/], fallbackKeys:['115::aspect_ratio'], value:miniMaxAspectValue(seg?.aspectRatio || node.aspectRatio || '16:9')},
        {patterns:[/megapixels?|百万像素/], fallbackKeys:['115::megapixels'], value:Number(seg?.megapixels || node.megapixels || 0.4)},
    ], {keyOf:rhParamKey, normalize:miniMaxAspectValue, defaultValue:rhDefaultValue, extractOptions:rhExtractFieldOptions});
}
async function miniMaxBuildRunningHubNodeInfoList(rhNode, fields, media){
    const result = [];
    const indexes = rhFieldIndexes(fields);
    const mediaState = WorkbenchCanvasRunningHubFieldRenderer.mediaInputState(fields, media, {indexes, kindOf:rhFieldKind, keyOf:rhParamKey});
    if(mediaState.missingRequired.length) throw new Error(`RunningHub 工作流缺少必选素材：${rhRequiredLabel(mediaState.missingRequired[0])}`);
    for(const field of fields){
        const kind = rhFieldKind(field);
        const role = rhFieldRole(field);
        const key = rhParamKey(field.nodeId, field.fieldName);
        if(mediaState.missingOptional.includes(field)) continue;
        let value = '';
        const param = rhNode.rhParams?.[key];
        const projection = WorkbenchCanvasRunningHubFieldRenderer.fieldValue(field, param, media, indexes[key] || 0, {kindOf:rhFieldKind, roleOf:rhFieldRole, defaultValue:rhDefaultValue});
        if(projection.skip) continue;
        value = projection.upload ? await rhUploadValueIfNeeded(projection.value, rhNode) : projection.value;
        result.push({nodeId:field.nodeId, fieldName:field.fieldName, fieldValue:value});
    }
    return result;
}
async function miniMaxBuildRunningHubWorkflowExtras(rhNode, fields, media, nodeInfoList){
    const config = await ensureRunningHubWorkflowConfigForNode(rhNode);
    if(!config || (config.optionalImageMode || 'prune-workflow') !== 'prune-workflow') return {};
    const indexes = rhFieldIndexes(fields);
    const mediaState = WorkbenchCanvasRunningHubFieldRenderer.mediaInputState(fields, media, {indexes, kindOf:rhFieldKind, keyOf:rhParamKey});
    if(mediaState.missingRequired.length) throw new Error(`RunningHub 工作流缺少必选素材：${rhRequiredLabel(mediaState.missingRequired[0])}`);
    const missingOptional = mediaState.missingOptional;
    if(!missingOptional.length) return {};
    missingOptional.forEach(field => {
        const key = rhParamKey(field.nodeId, field.fieldName);
        const idx = nodeInfoList.findIndex(item => rhParamKey(item.nodeId, item.fieldName) === key);
        if(idx >= 0) nodeInfoList.splice(idx, 1);
    });
    const workflow = rhPruneWorkflowForMissingFields(config.workflowJson || {}, missingOptional);
    return workflow ? {workflow} : {};
}
async function runMiniMaxRunningHub(node, media, options={}){ return ensureClassicExecutorRuntime().runMiniMaxRunningHub(node, media, options); }
async function runMiniMaxNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runMiniMaxNode(nodeId, opts); }
async function uploadCanvasUrlToComfy(url){ return ensureClassicExecutorRuntime().uploadCanvasUrlToComfy(url); }
async function comfyNameForRef(ref){
    if(ref.comfy_name) return ref.comfy_name;
    if(!ref.url) throw new Error(langIsEn() ? 'Missing input image' : '缺少输入图片');
    return uploadCanvasUrlToComfy(ref.url);
}
async function runComfyUpscale(imageUrl, resolution, options={}){ return ensureClassicExecutorRuntime().runComfyUpscale(imageUrl, resolution, options); }
function clearStuckGeneratorRunning(node){
    if(!node || !node.running) return;
    const seam = ensureClassicCascadeOrchestrator();
    if(seam.isCascadeActive(node.id) || seam.isCascadeStopping(node.id)) return;
    ensureClassicExecutionHost().markRunning(node, false);
}
async function runComfyNode(nodeId, opts={}){ return ensureClassicExecutorRuntime().runComfyNode(nodeId, opts); }
async function callCanvasLLM(node, message, messages=[], options={}){ return ensureClassicExecutorRuntime().callCanvasLLM(node, message, messages, options); }
