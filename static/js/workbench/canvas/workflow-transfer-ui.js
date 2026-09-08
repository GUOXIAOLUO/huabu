/* Neutral workflow-transfer modal lifecycle for the Canvas adapter. */
(function exposeWorkflowTransferUi(global) {
    'use strict';

    function create(options = {}) {
        const modal = options.modal;
        const toggle = options.toggle;
        const dropZone = options.dropZone;
        const refreshIcons = typeof options.refreshIcons === 'function' ? options.refreshIcons : () => {};
        const payload = typeof options.payload === 'function' ? options.payload : () => ({nodes: [], connections: []});
        const closeAssetLibrary = typeof options.closeAssetLibrary === 'function' ? options.closeAssetLibrary : () => {};
        const setStatus = typeof options.setStatus === 'function' ? options.setStatus : () => {};
        const meta = options.meta;
        const sub = options.sub;
        return Object.freeze({
            open() {
                if (typeof options.hasCanvas === 'function' && !options.hasCanvas()) {
                    setStatus(options.needCanvasMessage || '需要先打开画布');
                    return false;
                }
                closeAssetLibrary();
                const current = payload();
                const nodeCount = current.nodes.length;
                const connectionCount = current.connections.length;
                if (meta) meta.textContent = nodeCount ? `已选择 ${nodeCount} 个节点，${connectionCount} 条连线` : '未选择节点，请先框选要导出的组件';
                if (sub) sub.textContent = nodeCount ? '导出当前框选内容，或把工作流导入到当前画布' : '请先框选节点再导出；导入会追加到当前画布';
                modal?.classList.add('open');
                toggle?.classList.add('active');
                refreshIcons();
                return true;
            },
            close() {
                modal?.classList.remove('open');
                toggle?.classList.remove('active');
                dropZone?.classList.remove('drag-over');
            },
            update() {
                const current = payload();
                const nodeCount = current.nodes.length;
                const connectionCount = current.connections.length;
                if (meta) meta.textContent = nodeCount ? `已选择 ${nodeCount} 个节点，${connectionCount} 条连线` : '未选择节点，请先框选要导出的组件';
                if (sub) sub.textContent = nodeCount ? '导出当前框选内容，或把工作流导入到当前画布' : '请先框选节点再导出；导入会追加到当前画布';
            },
        });
    }

    global.WorkbenchCanvasWorkflowTransferUi = Object.freeze({create});
}(window));
