const canvasAppBootstrap = window.WorkbenchCanvasAppBootstrap.create({
    initializeTheme: () => applyTheme(localStorage.getItem('studio_theme') || localStorage.getItem(CANVAS_THEME_KEY) || 'light'),
    initializeToolbar: applyQuickToolbarState,
    applyTranslations: () => { if(window.StudioI18n) StudioI18n.apply(); },
    updateDocumentTitle: () => { document.title = tr('canvas.title'); },
    initializeOutputCompare: initOutputCompareEvents,
    initializeOutputPreview: initOutputPreviewZoomEvents,
    applyViewport,
    // This must remain inside the load callback: the asset seam captures
    // page-owned bindings initialized by the complete canvas.js evaluation.
    revealAssetControls: revealCanvasAssetControls,
    loadConfiguration: loadConfig,
    pruneConfiguration: pruneMissingComfyWorkflows,
    openCanvas,
    canvasListUrl: () => canvasListUrlForProject(rememberedCanvasListProject()),
    navigate: url => window.location.replace(url),
});
Object.assign(window, {
    applyGridPreset,
    applyImageEdit,
    clearEditDrawing,
    clearGridCustomLines,
    closeAssetManager,
    closeCanvasLog,
    closeErrorModal,
    closeImageEditor,
    closeOutputLightbox,
    closePromptTemplateModal,
    closeWorkflowTransferModal,
    copyErrorMessage,
    deleteNodeFromButton,
    exportSelectedWorkflow,
    exportSelectedWorkflowToLibrary,
    groupSelectedImages,
    menuAdd,
    openCanvasLog,
    quickAdd,
    redoEditDrawing,
    resetCropBox,
    setBrushTool,
    setGridCustomOrientation,
    toggleGridCustomMode,
    toggleQuickToolbar,
    undoEditDrawing,
    undoGridCustomLine,
});
const startCanvasApp = () => canvasAppBootstrap.start({search: window.location.search});
if(document.readyState === 'loading') window.addEventListener('load', startCanvasApp, {once:true});
else startCanvasApp();
