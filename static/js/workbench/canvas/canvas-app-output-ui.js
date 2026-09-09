function renderOutputMedia(item, useGridLayout=false){
    return WorkbenchCanvasMediaOutputRenderer.render(item, {useGrid:useGridLayout, presentation:value => WorkbenchCanvasMediaTools.outputPresentation(value, {useGrid:useGridLayout, kindOf:mediaKindForOutputItem}), escapeAttr, escapeHtml, formatDuration:formatRunDuration, isMissing:isMissingAssetUrl, missingHtml:missingAssetHtml, videoPreview:canvasVideoPreviewHtml, imagePreview:canvasPreviewImgHtml, tr});
}
function outputGridLayout(node){
    if(node?._pending?.length) return null;
    return WorkbenchCanvasMediaTools.outputGridLayout(node?.images, node?.outputLayout);
}
function outputImageName(url){
    return WorkbenchCanvasMediaTools.outputImageName(url);
}
function setOutputDragPreview(event, img){
    if(!event.dataTransfer || !img) return;
    const wrap = document.createElement('div');
    wrap.className = 'output-drag-preview';
    const clone = img.cloneNode();
    clone.removeAttribute('id');
    wrap.appendChild(clone);
    document.body.appendChild(wrap);
    const rect = img.getBoundingClientRect();
    event.dataTransfer.setDragImage(wrap, Math.min(rect.width / 2, 120), Math.min(rect.height / 2, 120));
    setTimeout(() => wrap.remove(), 0);
}
function appendOutputImages(out, images, compareRef, metas=[], layout=null){
    const list = (images || []).filter(Boolean);
    if(!out || !list.length) return;
    const next = WorkbenchCanvasMediaTools.appendOutputRecords(out.images, list, compareRef, metas, layout);
    out.images = next.images;
    if(next.outputLayout) out.outputLayout = next.outputLayout;
    else if(out.outputLayout) delete out.outputLayout;
    if(Object.keys(next.imageComparisons).length) out.imageComparisons = {...(out.imageComparisons || {}), ...next.imageComparisons};
}
function outputCompareUrlFor(url, out){
    return WorkbenchCanvasMediaTools.outputCompareUrl(url, out?.imageComparisons, out?.images);
}
function markOutputViewed(out, url){
    if(!out || !url || !(out.images || []).length) return;
    const next = WorkbenchCanvasMediaTools.markOutputViewed(out.images, url);
    out.images = next.images;
    if(next.changed){
        render();
        scheduleSave();
    }
}
function outputLightboxItems(out=null){
    const normalize = (item, sourceOut=null) => {
        const url = outputUrlValue(item);
        if(!url || mediaKindForOutputItem(item) !== 'image') return null;
        return {url, outId:sourceOut?.id || ''};
    };
    const sourceOut = out?.id ? nodes.find(n => n.id === out.id) || out : null;
    return WorkbenchCanvasMediaTools.collectLightboxItems({sourceOut, groupItems:groupImageItems, imageKind:mediaKindForNode, outputNodes:nodes.filter(n => n.type === 'output'), logs:canvas?.logs, normalize});
}
function openGroupLightbox(groupId, index=0){
    const group = nodes.find(n => n.id === groupId);
    const items = groupImageItems(group);
    if(!items.length) return;
    const item = items[WorkbenchCanvasMediaTools.clampListIndex(index, items.length)] || items[0];
    openOutputLightbox(item.url, group);
}
function navigateOutputLightbox(direction){
    if(!outputLightbox.classList.contains('open') || !currentOutputLightboxUrl) return false;
    const out = currentOutputLightboxOutId ? nodes.find(n => n.id === currentOutputLightboxOutId) : null;
    const items = outputLightboxItems(out);
    const next = WorkbenchCanvasMediaTools.nextLightboxItem(items, currentOutputLightboxUrl, direction);
    if(!next) return false;
    const nextOut = next.outId ? nodes.find(n => n.id === next.outId) : null;
    openOutputLightbox(next.url, nextOut);
    return true;
}
function createImageCardFromOutput(url, point){
    if(!ensureCanvas() || !url) return;
    if(mediaKindForRef(url) !== 'image') return;
    const node = WorkbenchCanvasMediaTools.outputImageNodeProjection(url, point || defaultPoint(0, 0), uid, outputImageName);
    if(!node) return;
    nodes.push(node);
    render();
    scheduleSave();
}
async function downloadUrl(url, filename){
    const res = await fetch(url);
    if(!res.ok) throw new Error('下载失败');
    const blob = await res.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
function setOutputCompareMode(active){
    outputPreview.classList.toggle('compare-mode', active);
    if(active){
        const styles = WorkbenchCanvasMediaTools.compareModeStyles(active);
        outputCompareOriginalWrap.style.clipPath = styles.clipPath;
        outputCompareSlider.style.left = styles.sliderLeft;
    }
}
function outputResolutionText(text, meta=null){
    outputResolution.innerHTML = WorkbenchCanvasMediaTools.outputResolutionMarkup(text, meta?.runMs, formatRunDuration);
}
function setupOutputPromptPanel(meta){
    currentOutputMeta = meta || null;
    const projection = WorkbenchCanvasMediaTools.outputPromptProjection(meta, tr('canvas.noPromptMeta'));
    const prompt = projection.prompt;
    outputPromptPanel.classList.toggle('open', projection.open);
    outputPromptText.textContent = projection.text;
    outputCopyPromptBtn.onclick = e => {
        e.stopPropagation();
        if(!prompt) return;
        copyTextToClipboard(prompt);
        const span = outputCopyPromptBtn.querySelector('span');
        const oldText = span?.textContent || tr('canvas.copyPrompt');
        outputCopyPromptBtn.classList.add('copied');
        if(span) span.textContent = tr('canvas.copied');
        clearTimeout(outputCopyPromptBtn._copyTimer);
        outputCopyPromptBtn._copyTimer = setTimeout(() => {
            outputCopyPromptBtn.classList.remove('copied');
            if(span) span.textContent = oldText;
        }, 1200);
    };
    outputRerunBtn.disabled = !WorkbenchCanvasMediaTools.outputRerunAvailable(meta);
    outputRerunBtn.onclick = e => {
        e.stopPropagation();
        if (!WorkbenchCanvasMediaTools.outputRerunAvailable(currentOutputMeta)) return;
        rerunFromOutputMeta(currentOutputMeta);
    };
}
window.WorkbenchCanvasPromptTemplateInteraction.create({
    search:promptTemplateSearch, library:promptTemplateLibrarySelect,
    close:promptTemplateClose, panel:promptTemplatePanel,
    callbacks:{
        queryChanged:value => { promptTemplateQuery = value; renderPromptTemplateModal(); },
        libraryChanged:value => { activePromptLibraryId = value || 'system'; canvasPromptTemplates = activeCanvasPromptLibraryItems(); promptTemplateSelectedId = ''; promptTemplateEditing = false; renderPromptTemplateModal(); },
        close:closePromptTemplateModal,
        apply:applyPromptTemplateToPromptNode,
        saveCurrent:saveCurrentCanvasPromptAsTemplate,
        create:createBlankCanvasPromptTemplate,
        edit:() => { promptTemplateEditing = true; renderPromptTemplateModal(); },
        cancelEdit:() => { promptTemplateEditing = false; renderPromptTemplateModal(); },
        saveEdit:saveCanvasPromptTemplateEdit,
        delete:deleteCanvasPromptTemplate,
        category:value => { promptTemplateCategory = value; promptTemplateSelectedId = ''; promptTemplateEditing = false; renderPromptTemplateModal(); },
        editCategory:renameCanvasPromptTemplateGroup,
        deleteCategory:deleteCanvasPromptTemplateGroup,
        toggleGroups:() => { promptTemplateGroupEditMode = !promptTemplateGroupEditMode; renderPromptTemplateModal(); },
        createCategory:createCanvasPromptTemplateGroup,
        select:value => { promptTemplateSelectedId = value; promptTemplateEditing = false; renderPromptTemplateModal(); },
    },
});
canvasAssetToggle?.addEventListener('click', () => toggleCanvasAssetLibrary());
workflowTransferToggle?.addEventListener('click', () => {
    if(workflowTransferModal?.classList.contains('open')) closeWorkflowTransferModal();
    else openWorkflowTransferModal();
});
canvasLogToggle?.addEventListener('click', event => {
    event.preventDefault();
    openCanvasLog();
});
workflowImportInput?.addEventListener('change', event => {
    const file = event.target.files?.[0];
    if(file) importWorkflowFile(file);
    event.target.value = '';
});
workflowImportDropZone?.addEventListener('click', () => workflowImportInput?.click());
workflowImportDropZone?.addEventListener('dragenter', event => {
    event.preventDefault();
    event.stopPropagation();
    workflowImportDropZone.classList.add('drag-over');
});
workflowImportDropZone?.addEventListener('dragover', event => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = 'copy';
    workflowImportDropZone.classList.add('drag-over');
});
workflowImportDropZone?.addEventListener('dragleave', event => {
    event.preventDefault();
    event.stopPropagation();
    if(!workflowImportDropZone.contains(event.relatedTarget)) workflowImportDropZone.classList.remove('drag-over');
});
workflowImportDropZone?.addEventListener('drop', event => {
    event.preventDefault();
    event.stopPropagation();
    workflowImportDropZone.classList.remove('drag-over');
    const file = [...(event.dataTransfer?.files || [])].find(item => /\.(json|zip)$/i.test(item.name || ''));
    if(file) importWorkflowFile(file);
    else setStatus('请拖入 JSON 或 ZIP 工作流文件');
});
canvasAssetCloseBtn?.addEventListener('click', () => toggleCanvasAssetLibrary(false));
canvasAssetLibrarySelect?.addEventListener('change', () => {
    activeCanvasAssetLibraryId = canvasAssetLibrarySelect.value || '';
    activeCanvasAssetCategoryId = '';
    renderCanvasAssetLibrary();
});
canvasAssetCategorySelect?.addEventListener('change', () => {
    activeCanvasAssetCategoryId = canvasAssetCategorySelect.value || '';
    renderCanvasAssetLibrary();
});
canvasAssetAddCategoryBtn?.addEventListener('click', async () => {
    if(canvasAssetLibraryIsLocal()){ setStatus('本地素材请在素材库管理中管理文件夹'); return; }
    const name = window.prompt('新分组名称', '新分组');
    if(!String(name || '').trim()) return;
    const data = await fetch('/api/asset-library/categories', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({library_id:activeCanvasAssetLibraryId, name:String(name).trim(), type:'image'})
    }).then(r => r.json());
    canvasAssetLibrary = data.library || canvasAssetLibrary;
    activeCanvasAssetCategoryId = data.category?.id || activeCanvasAssetCategoryId;
    renderCanvasAssetLibrary();
});
canvasAssetPanel?.addEventListener('wheel', event => {
    event.stopPropagation();
    const scroller = event.target.closest?.('.canvas-asset-grid') || canvasAssetGrid;
    if(!scroller || getComputedStyle(scroller).display === 'none') return;
    const canScroll = scroller.scrollHeight > scroller.clientHeight || scroller.scrollWidth > scroller.clientWidth;
    if(!canScroll) return;
    event.preventDefault();
    scroller.scrollTop += event.deltaY;
    scroller.scrollLeft += event.deltaX;
}, {passive:false, capture:true});
workflowTransferModal?.addEventListener('wheel', event => {
    event.stopPropagation();
}, {passive:true, capture:true});
workflowTransferModal?.addEventListener('dragover', event => {
    event.preventDefault();
    event.stopPropagation();
    if(workflowImportDropZone){
        event.dataTransfer.dropEffect = 'copy';
        workflowImportDropZone.classList.add('drag-over');
    }
});
workflowTransferModal?.addEventListener('dragleave', event => {
    event.preventDefault();
    event.stopPropagation();
    if(!workflowTransferModal.contains(event.relatedTarget)) workflowImportDropZone?.classList.remove('drag-over');
});
workflowTransferModal?.addEventListener('drop', event => {
    event.preventDefault();
    event.stopPropagation();
    workflowImportDropZone?.classList.remove('drag-over');
    const file = [...(event.dataTransfer?.files || [])].find(item => /\.(json|zip)$/i.test(item.name || ''));
    if(file) importWorkflowFile(file);
    else setStatus('请拖入 JSON 或 ZIP 工作流文件');
});
function hasCanvasAssetSaveDrop(dataTransfer){ return ensureClassicAssetRuntime().hasCanvasAssetSaveDrop(dataTransfer); }
canvasAssetDropZone?.addEventListener('dragover', event => {
    if(!hasCanvasAssetSaveDrop(event.dataTransfer)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    canvasAssetDropZone.classList.add('drag-over');
});
canvasAssetDropZone?.addEventListener('dragleave', () => canvasAssetDropZone.classList.remove('drag-over'));
canvasAssetDropZone?.addEventListener('drop', async event => {
    if(!hasCanvasAssetSaveDrop(event.dataTransfer)) return;
    event.preventDefault();
    event.stopPropagation();
    canvasAssetDropZone.classList.remove('drag-over');
    try {
        if(hasOutputImageDrag(event.dataTransfer)){
            await addUrlToCanvasAssetLibrary(event.dataTransfer.getData('application/x-canvas-output-image'), 'output');
            return;
        }
        const payload = await resolveImageDropPayload(event.dataTransfer);
        if(payload.type === 'files'){
            const cat = activeCanvasAssetCategory();
            const data = cat ? await uploadFilesToLibrary(payload.files, activeCanvasAssetLibraryId, cat.id) : null;
            if(data?.library) {
                canvasAssetLibrary = data.library;
                renderCanvasAssetLibrary();
                setStatus('已保存到资产库');
            }
        } else if(payload.type === 'url') {
            await addUrlToCanvasAssetLibrary(payload.url, outputImageName(payload.url));
        }
    } catch(err) {
        showErrorModal(err.message || '保存资产失败', '保存资产失败');
    }
});
gateAssetManagerBtn?.addEventListener('click', openAssetManager);
document.querySelectorAll('[data-manager-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
        assetManagerTab = btn.dataset.managerTab || 'assets';
        renderAssetManager();
    });
});
assetManagerModal?.addEventListener('change', event => {
    let shouldRender = false;
    const assetCheck = event.target.closest?.('[data-manager-asset-check]');
    if(assetCheck){
        if(assetCheck.checked) managerSelectedAssetIds.add(assetCheck.dataset.managerAssetCheck);
        else managerSelectedAssetIds.delete(assetCheck.dataset.managerAssetCheck);
        shouldRender = true;
    }
    const promptCheck = event.target.closest?.('[data-manager-prompt-check]');
    if(promptCheck){
        if(promptCheck.checked) managerSelectedPromptIds.add(promptCheck.dataset.managerPromptCheck);
        else managerSelectedPromptIds.delete(promptCheck.dataset.managerPromptCheck);
        shouldRender = true;
    }
    const workflowCheck = event.target.closest?.('[data-manager-workflow-check]');
    if(workflowCheck){
        if(workflowCheck.checked) managerSelectedWorkflowIds.add(workflowCheck.dataset.managerWorkflowCheck);
        else managerSelectedWorkflowIds.delete(workflowCheck.dataset.managerWorkflowCheck);
        shouldRender = true;
    }
    if(shouldRender) renderAssetManager();
});
assetManagerModal?.addEventListener('click', async event => {
    const assetLib = event.target.closest?.('[data-manager-asset-lib]');
    if(assetLib){ activeCanvasAssetLibraryId = assetLib.dataset.managerAssetLib || ''; activeCanvasAssetCategoryId = ''; managerSelectedAssetIds.clear(); renderAssetManager(); return; }
    const assetCat = event.target.closest?.('[data-manager-asset-cat]');
    if(assetCat){ activeCanvasAssetCategoryId = assetCat.dataset.managerAssetCat || ''; managerSelectedAssetIds.clear(); renderAssetManager(); return; }
    const workflowLib = event.target.closest?.('[data-manager-workflow-lib]');
    if(workflowLib){ activeCanvasAssetLibraryId = workflowLib.dataset.managerWorkflowLib || ''; activeCanvasWorkflowCategoryId = ''; managerSelectedWorkflowIds.clear(); renderAssetManager(); return; }
    const workflowCat = event.target.closest?.('[data-manager-workflow-cat]');
    if(workflowCat){ activeCanvasWorkflowCategoryId = workflowCat.dataset.managerWorkflowCat || ''; managerSelectedWorkflowIds.clear(); renderAssetManager(); return; }
    const promptLib = event.target.closest?.('[data-manager-prompt-lib]');
    if(promptLib){ activePromptLibraryId = promptLib.dataset.managerPromptLib || 'system'; managerSelectedPromptIds.clear(); renderAssetManager(); return; }
    const workflowRename = event.target.closest?.('[data-manager-workflow-rename]');
    if(workflowRename){
        const itemId = workflowRename.dataset.managerWorkflowRename || '';
        const item = (activeCanvasWorkflowCategory()?.items || []).find(entry => entry.id === itemId);
        const name = window.prompt('工作流名称', item?.name || '');
        if(!item || !String(name || '').trim()) return;
        const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    const workflowRemove = event.target.closest?.('[data-manager-workflow-remove]');
    if(workflowRemove){
        const itemId = workflowRemove.dataset.managerWorkflowRemove || '';
        const item = (activeCanvasWorkflowCategory()?.items || []).find(entry => entry.id === itemId);
        if(!item || !window.confirm(`删除工作流「${item.name || 'workflow'}」？`)) return;
        const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        managerSelectedWorkflowIds.delete(item.id);
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    const assetRename = event.target.closest?.('[data-manager-asset-rename]');
    if(assetRename){
        const itemId = assetRename.dataset.managerAssetRename || '';
        const item = (activeCanvasMediaCategory()?.items || []).find(entry => entry.id === itemId);
        const name = window.prompt('资产名称', item?.name || '');
        if(!item || !String(name || '').trim()) return;
        const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    const assetRemove = event.target.closest?.('[data-manager-asset-remove]');
    if(assetRemove){
        const itemId = assetRemove.dataset.managerAssetRemove || '';
        const item = (activeCanvasMediaCategory()?.items || []).find(entry => entry.id === itemId);
        if(!item || !window.confirm(`删除资产「${item.name || 'asset'}」？`)) return;
        const data = await fetch(`/api/asset-library/items/${encodeURIComponent(item.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        managerSelectedAssetIds.delete(item.id);
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    const promptEdit = event.target.closest?.('[data-manager-prompt-edit]');
    if(promptEdit){
        const lib = activeCanvasPromptLibrary();
        if(!lib || lib.readonly) return;
        const itemId = promptEdit.dataset.managerPromptEdit || '';
        const item = (lib.items || []).find(entry => entry.id === itemId);
        if(!item) return;
        const name = window.prompt('提示词名称', item.name || '提示词');
        if(!String(name || '').trim()) return;
        const positive = window.prompt('提示词内容', item.positive || '');
        if(!String(positive || '').trim()) return;
        const data = await fetch(`/api/prompt-libraries/items/${encodeURIComponent(item.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:lib.id, name, positive, negative:item.negative || '', category:item.category || 'mine', scene:item.scene || ''})}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    const promptRemove = event.target.closest?.('[data-manager-prompt-remove]');
    if(promptRemove){
        const lib = activeCanvasPromptLibrary();
        if(!lib || lib.readonly) return;
        const itemId = promptRemove.dataset.managerPromptRemove || '';
        const item = (lib.items || []).find(entry => entry.id === itemId);
        if(!item || !window.confirm(`删除提示词「${item.name || '提示词'}」？`)) return;
        const data = await fetch(`/api/prompt-libraries/items/${encodeURIComponent(item.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        managerSelectedPromptIds.delete(item.id);
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    if(event.target.closest?.('[data-manager-asset-lib-new]')){
        const name = window.prompt('资产库名称', '新资产库');
        if(!String(name || '').trim()) return;
        const data = await fetch('/api/asset-library/libraries', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        activeCanvasAssetLibraryId = data.asset_library?.id || activeCanvasAssetLibraryId;
        activeCanvasAssetCategoryId = '';
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-lib-rename]')){
        const lib = activeCanvasAssetLibrary();
        const name = window.prompt('资产库名称', lib?.name || '');
        if(!lib || !String(name || '').trim()) return;
        const data = await fetch(`/api/asset-library/libraries/${encodeURIComponent(lib.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-lib-delete]')){
        const lib = activeCanvasAssetLibrary();
        if(!lib || !window.confirm(`删除资产库「${lib.name || '资产库'}」？`)) return;
        const data = await fetch(`/api/asset-library/libraries/${encodeURIComponent(lib.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        activeCanvasAssetLibraryId = canvasAssetLibrary.active_library_id || canvasAssetLibraries()[0]?.id || '';
        activeCanvasAssetCategoryId = '';
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-cat-new]')){
        const name = window.prompt('分组名称', '新分组');
        if(!String(name || '').trim()) return;
        const data = await fetch('/api/asset-library/categories', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:activeCanvasAssetLibraryId, name, type:'image'})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        activeCanvasAssetCategoryId = data.category?.id || activeCanvasAssetCategoryId;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-cat-rename]')){
        const cat = activeCanvasMediaCategory();
        const name = window.prompt('分组名称', cat?.name || '');
        if(!cat || !String(name || '').trim()) return;
        const data = await fetch(`/api/asset-library/categories/${encodeURIComponent(cat.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-cat-delete]')){
        const cat = activeCanvasMediaCategory();
        if(!cat || !window.confirm(`删除分组「${cat.name || '分组'}」？`)) return;
        const data = await fetch(`/api/asset-library/categories/${encodeURIComponent(cat.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        activeCanvasAssetCategoryId = canvasMediaCategories()[0]?.id || '';
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-asset-delete]')){
        if(!managerSelectedAssetIds.size) return;
        const data = await fetch('/api/asset-library/items/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:activeCanvasAssetLibraryId, ids:[...managerSelectedAssetIds]})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        managerSelectedAssetIds.clear();
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-workflow-export]')){
        const items = (activeCanvasWorkflowCategory()?.items || []).filter(item => managerSelectedWorkflowIds.has(item.id));
        if(items.length === 1) {
            const item = items[0];
            downloadUrl(item.url, `${item.name || 'workflow'}${String(item.url).toLowerCase().endsWith('.json') ? '.json' : '.zip'}`);
        } else if(items.length > 1) {
            const res = await fetch('/api/canvas-assets/download', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({filename:'workflows.zip', items:items.map(item => ({url:item.url, name:item.name || 'workflow'}))})});
            if(res.ok) window.WorkbenchCanvasWorkflowTransfer.downloadBlob(await res.blob(), 'workflows.zip', {revokeAfterMs:1200});
        }
        return;
    }
    if(event.target.closest?.('[data-manager-workflow-delete]')){
        if(!managerSelectedWorkflowIds.size) return;
        const data = await fetch('/api/asset-library/items/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:activeCanvasAssetLibraryId, ids:[...managerSelectedWorkflowIds]})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        managerSelectedWorkflowIds.clear();
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-workflow-cat-new]')){
        const name = window.prompt('工作流分组名称', '工作流');
        if(!String(name || '').trim()) return;
        const data = await fetch('/api/asset-library/categories', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:activeCanvasAssetLibraryId, name, type:'workflow'})}).then(r => r.json());
        canvasAssetLibrary = data.library || canvasAssetLibrary;
        activeCanvasWorkflowCategoryId = data.category?.id || activeCanvasWorkflowCategoryId;
        renderAssetManager(); renderCanvasAssetLibrary(); return;
    }
    if(event.target.closest?.('[data-manager-prompt-lib-new]')){
        const name = window.prompt('提示词库名称', '新提示词库');
        if(!String(name || '').trim()) return;
        const data = await fetch('/api/prompt-libraries', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        activePromptLibraryId = data.prompt_library?.id || activePromptLibraryId;
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    if(event.target.closest?.('[data-manager-prompt-lib-rename]')){
        const lib = activeCanvasPromptLibrary();
        if(!lib || lib.readonly) return;
        const name = window.prompt('提示词库名称', lib.name || '');
        if(!String(name || '').trim()) return;
        const data = await fetch(`/api/prompt-libraries/${encodeURIComponent(lib.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    if(event.target.closest?.('[data-manager-prompt-lib-delete]')){
        const lib = activeCanvasPromptLibrary();
        if(!lib || lib.readonly || !window.confirm(`删除提示词库「${lib.name || '提示词库'}」？`)) return;
        const data = await fetch(`/api/prompt-libraries/${encodeURIComponent(lib.id)}`, {method:'DELETE'}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        activePromptLibraryId = data.library?.active_library_id || canvasPromptLibraries.find(item => item.id !== 'system')?.id || 'system';
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    if(event.target.closest?.('[data-manager-prompt-new]')){
        const lib = activeCanvasPromptLibrary();
        if(!lib || lib.readonly) return;
        const name = window.prompt('提示词名称', '新提示词');
        if(!String(name || '').trim()) return;
        const positive = window.prompt('提示词内容', '');
        if(!String(positive || '').trim()) return;
        const data = await fetch('/api/prompt-libraries/items', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({library_id:lib.id, name, positive, category:'mine'})}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
    if(event.target.closest?.('[data-manager-prompt-delete]')){
        if(!managerSelectedPromptIds.size) return;
        const data = await fetch('/api/prompt-libraries/items/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ids:[...managerSelectedPromptIds]})}).then(r => r.json());
        canvasPromptLibraries = data.library?.libraries || canvasPromptLibraries;
        managerSelectedPromptIds.clear();
        refreshCanvasPromptTemplatesFromLibraries();
        renderAssetManager(); return;
    }
}, true);
function rerunFromOutputMeta(meta){
    if(!ensureCanvas() || !meta?.run?.nodeType) return;
    const p = defaultPoint(180, 40);
    const projection = WorkbenchCanvasMediaTools.rerunOutputProjection(meta, p, uid);
    if(!projection) return;
    nodes.push(...projection.nodes);
    connections.push(...projection.connections);
    closeOutputLightbox();
    render();
    scheduleSave();
}
function updateOutputCompareSlider(clientX){
    const rect = outputCompareContainer.getBoundingClientRect();
    const projection = WorkbenchCanvasMediaTools.compareSliderProjection(clientX, rect.left, rect.width);
    if(!rect.width) return;
    outputCompareOriginalWrap.style.clipPath = projection.clipPath;
    outputCompareSlider.style.left = `${projection.percent}%`;
}
function applyOutputPreviewZoom(){
    const projection = WorkbenchCanvasMediaTools.previewTransformProjection(outputPreviewZoom, outputPreviewPan);
    [outputLightboxImg, outputCompareResult, outputCompareOriginal].forEach(img => {
        img.style.transform = projection.transform;
        img.style.transformOrigin = '0 0';
    });
    outputPreview.classList.toggle('zoomed', projection.zoomed);
}
let outputGlobalPointerEventsBound = false;
let outputPreviewEventsBound = false;
let outputCompareEventsBound = false;
function bindOutputGlobalPointerEvents(){
    if(outputGlobalPointerEventsBound) return;
    outputGlobalPointerEventsBound = true;
    window.addEventListener('mousemove', e => {
        if(outputPreviewPanDrag){
            outputPreviewPan = WorkbenchCanvasMediaTools.previewPanProjection(outputPreviewPanDrag, e.clientX, e.clientY);
            applyOutputPreviewZoom();
        }
        if(outputCompareDrag) updateOutputCompareSlider(e.clientX);
    });
    window.addEventListener('mouseup', () => {
        outputPreviewPanDrag = null;
        outputPreview.classList.remove('panning');
        outputCompareDrag = false;
    });
}
function resetOutputPreviewZoom(){
    outputPreviewZoom = 1;
    outputPreviewPan = {x: 0, y: 0};
    outputPreviewPanDrag = null;
    outputPreview.classList.remove('panning');
    applyOutputPreviewZoom();
}
function initOutputPreviewZoomEvents(){
    if(outputPreviewEventsBound) return;
    outputPreviewEventsBound = true;
    bindOutputGlobalPointerEvents();
    outputPreview.addEventListener('wheel', e => {
        if(outputLightboxVideo.style.display === 'block') return;
        e.preventDefault();
        e.stopPropagation();
        const rect = outputPreview.getBoundingClientRect();
        const localX = e.clientX - rect.left;
        const localY = e.clientY - rect.top;
        const projection = WorkbenchCanvasMediaTools.previewZoomProjection(outputPreviewZoom, outputPreviewPan, e.deltaY, localX, localY);
        outputPreviewZoom = projection.zoom;
        outputPreviewPan = projection.pan;
        applyOutputPreviewZoom();
    }, {passive:false});
    outputPreview.addEventListener('mousedown', e => {
        if(outputLightboxVideo.style.display === 'block') return;
        if(e.button !== 0 || outputPreviewZoom <= 1.001) return;
        if(e.target.closest('.output-preview-actions, .output-resolution, .output-compare-slider')) return;
        outputPreviewPanDrag = {
            sx:e.clientX,
            sy:e.clientY,
            ox:outputPreviewPan.x,
            oy:outputPreviewPan.y
        };
        outputPreview.classList.add('panning');
        e.preventDefault();
        e.stopPropagation();
    });
}
function initOutputCompareEvents(){
    if(outputCompareEventsBound) return;
    outputCompareEventsBound = true;
    bindOutputGlobalPointerEvents();
    outputCompareContainer.addEventListener('mousedown', e => {
        outputCompareDrag = true;
        updateOutputCompareSlider(e.clientX);
        e.preventDefault();
        e.stopPropagation();
    });
    outputCompareSlider.addEventListener('mousedown', e => {
        outputCompareDrag = true;
        e.preventDefault();
        e.stopPropagation();
    });
    outputCompareContainer.addEventListener('touchstart', e => {
        outputCompareDrag = true;
        updateOutputCompareSlider(e.touches[0].clientX);
        e.preventDefault();
        e.stopPropagation();
    }, {passive:false});
    window.addEventListener('touchmove', e => {
        if(outputCompareDrag) {
            updateOutputCompareSlider(e.touches[0].clientX);
            e.preventDefault();
        }
    }, {passive:false});
    window.addEventListener('touchend', () => { outputCompareDrag = false; });
}
function openOutputLightbox(url, out){
    if(!url) return;
    resetOutputPreviewZoom();
    currentOutputLightboxOutId = out?.id || '';
    currentOutputLightboxUrl = url;
    const meta = outputMetaFor(url, out);
    markOutputViewed(out, url);
    setupOutputPromptPanel(meta);
    outputResolutionText('--', meta);
    currentOutputCompareUrl = outputCompareUrlFor(url, out);
    setOutputCompareMode(false);
    const groupDownloadItems = out?.type === 'group' ? groupImageItems(out) : [];
    const videoMode = mediaKindForOutputItem(meta && Object.keys(meta).length ? {...meta, url} : url) === 'video';
    const projection = WorkbenchCanvasMediaTools.lightboxProjection({
        kind:videoMode ? 'video' : 'image',
        groupCount:groupDownloadItems.length,
        compareUrl:currentOutputCompareUrl,
    });
    if(outputDownloadAllBtn){
        outputDownloadAllBtn.style.display = projection.showDownloadAll ? 'flex' : 'none';
        outputDownloadAllBtn.onclick = e => {
            e.stopPropagation();
            if(currentOutputLightboxOutId) downloadGroupNodeImages(currentOutputLightboxOutId);
        };
    }
    const visibility = projection.visibility;
    outputLightboxImg.style.display = visibility.image ? 'block' : 'none';
    outputLightboxVideo.style.display = visibility.video ? 'block' : 'none';
    outputCompareResult.style.display = visibility.compare ? 'block' : 'none';
    outputCompareOriginal.style.display = visibility.compare ? 'block' : 'none';
    if(videoMode){
        outputLightboxImg.src = '';
        outputCompareResult.src = '';
        outputCompareOriginal.src = '';
        outputLightboxVideo.onloadedmetadata = () => {
            outputResolutionText(outputLightboxVideo.videoWidth && outputLightboxVideo.videoHeight
                ? `${outputLightboxVideo.videoWidth} x ${outputLightboxVideo.videoHeight}`
                : 'Video', meta);
        };
        outputLightboxVideo.src = canvasDisplayMediaUrl(url, outputDownloadName(url));
        outputPreview.ondblclick = null;
        outputDownloadBtn.onclick = e => {
            e.stopPropagation();
            downloadUrl(url, outputDownloadName(url)).catch(err => alert(err.message || '下载失败'));
        };
        outputLightbox.classList.add('open');
        refreshIcons();
        return;
    }
    outputLightboxVideo.pause();
    outputLightboxVideo.src = '';
    outputLightboxImg.draggable = false;
    outputCompareResult.draggable = false;
    outputCompareOriginal.draggable = false;
    outputLightboxImg.onload = () => {
        outputResolutionText(`${outputLightboxImg.naturalWidth} x ${outputLightboxImg.naturalHeight}`, meta);
    };
    outputLightboxImg.src = canvasDisplayMediaUrl(url, outputDownloadName(url));
    outputCompareResult.src = canvasDisplayMediaUrl(url, outputDownloadName(url));
    outputCompareOriginal.src = currentOutputCompareUrl ? canvasDisplayMediaUrl(currentOutputCompareUrl, outputDownloadName(currentOutputCompareUrl)) : '';
    outputPreview.ondblclick = e => {
        e.stopPropagation();
        if(!currentOutputCompareUrl) return;
        setOutputCompareMode(!outputPreview.classList.contains('compare-mode'));
    };
    outputDownloadBtn.onclick = e => {
        e.stopPropagation();
        downloadUrl(url, outputDownloadName(url)).catch(err => alert(err.message || '下载失败'));
    };
    outputLightbox.classList.add('open');
    refreshIcons();
}
function closeOutputLightbox(){
    outputLightbox.classList.remove('open');
    setOutputCompareMode(false);
    outputLightboxImg.src = '';
    outputLightboxVideo.pause();
    outputLightboxVideo.src = '';
    outputLightboxVideo.style.display = 'none';
    outputLightboxImg.style.display = 'block';
    outputCompareResult.style.display = 'block';
    outputCompareOriginal.style.display = 'block';
    outputCompareResult.src = '';
    outputCompareOriginal.src = '';
    outputPreview.ondblclick = null;
    if(outputDownloadAllBtn){
        outputDownloadAllBtn.style.display = 'none';
        outputDownloadAllBtn.onclick = null;
    }
    resetOutputPreviewZoom();
    currentOutputCompareUrl = '';
    currentOutputMeta = null;
    currentOutputLightboxOutId = '';
    currentOutputLightboxUrl = '';
    setupOutputPromptPanel(null);
}
