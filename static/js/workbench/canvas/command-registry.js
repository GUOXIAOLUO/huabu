/* Shared Canvas command catalog. Page adapters own behavior; this module owns
   stable command IDs and which canvas modes may expose them. */
(function exposeWorkbenchCanvasCommands(global) {
    'use strict';

    if (!global.WorkbenchCreationCatalog) throw new Error('WorkbenchCreationCatalog must load before WorkbenchCanvasCommands');

    const creationIcons = Object.freeze({
        image:'image-plus', prompt:'text-cursor-input', loop:'repeat-2', group:'group', minimax:'sparkles',
        llm:'message-square-text', generator:'wand-sparkles', midjourney:'panel-top', msgen:'cloud-lightning',
        video:'clapperboard', rh:'workflow', comfy:'workflow', ltxDirector:'film', output:'circle-dot',
    });

    const compatibilityCreateEntries = [
        // The first six tuple fields retain the established compatibility
        // contract; picker metadata is appended after them.
        // ['canvas.create.prompt', 'prompt', ['classic', 'smart'], 20, ['classic', 'smart'], ['classic', 'smart']]
        // ['canvas.create.loop', 'loop', ['classic', 'smart'], 30, ['classic', 'smart'], ['classic', 'smart']]
        ['canvas.create.image', 'image', ['classic', 'smart'], 10, ['classic', 'smart'], ['classic', 'smart'], '资源', '上传节点', '将图片或视频作为资源节点', ['图片', '视频', '上传', '资源'], ['asset', 'media']],
        ['canvas.create.prompt', 'prompt', ['classic', 'smart'], 20, ['classic', 'smart'], ['classic', 'smart'], 'AI', '提示词', '编写和组织可复用的提示词', ['提示词', '文本', 'prompt', 'AI'], ['prompt', 'text']],
        ['canvas.create.loop', 'loop', ['classic', 'smart'], 30, ['classic', 'smart'], ['classic', 'smart'], '工作流', '循环节点', '对输入内容执行批量处理', ['循环', '批量', '工作流'], ['workflow', 'batch']],
        ['canvas.create.group', 'group', ['classic', 'smart'], 40, ['classic', 'smart'], ['classic', 'smart'], '工作流', '分组', '把相关节点组织到一个视觉组中', ['分组', '组织', '节点'], ['group']],
        ['canvas.create.minimax', 'minimax', ['classic', 'smart'], 50, ['smart'], ['smart'], 'AI', 'MiniMax H3', '使用 MiniMax H3 生成媒体内容', ['MiniMax', '生成', '视频', 'AI'], ['generation', 'media']],
        ['canvas.create.llm', 'llm', ['classic'], 60, [], [], 'AI', 'LLM 节点', '使用语言模型处理文本和上下文', ['LLM', '语言模型', '文本', '聊天'], ['text', 'model']],
        ['canvas.create.generator', 'generator', ['classic'], 70, [], [], 'AI', 'API 生成', '通过已配置的模型路线生成媒体', ['API', '生成', '图片', '视频'], ['generation', 'media']],
        ['canvas.create.midjourney', 'midjourney', ['classic'], 80, [], [], 'AI', 'Midjourney', '创建 Midjourney 图像生成节点', ['Midjourney', '图片', '生成'], ['generation', 'image']],
        ['canvas.create.msgen', 'msgen', ['classic'], 90, [], [], 'AI', 'Modelscope 生成', '创建 Modelscope 媒体生成节点', ['Modelscope', '图片', '视频', '生成'], ['generation', 'media']],
        ['canvas.create.video', 'video', ['classic'], 100, [], [], 'AI', '视频生成', '创建视频生成节点', ['视频', '生成', 'media'], ['generation', 'video']],
        ['canvas.create.rh', 'rh', ['classic'], 110, [], [], '工作流', 'RunningHub 生成', '使用 RunningHub 工作流生成媒体', ['RunningHub', '工作流', '生成'], ['workflow', 'generation']],
        ['canvas.create.comfy', 'comfy', ['classic'], 120, [], [], '工作流', 'ComfyUI 生成', '使用 ComfyUI 工作流生成媒体', ['ComfyUI', '工作流', '生成'], ['workflow', 'generation']],
        ['canvas.create.ltx-director', 'ltxDirector', ['classic'], 130, [], [], '工作流', 'LTX Director', '编排带时间线的视频生成流程', ['LTX', '视频', '时间线', '工作流'], ['workflow', 'video']],
        ['canvas.create.output', 'output', ['classic'], 140, ['classic'], [], '资源', 'Output', '接收和查看执行结果', ['Output', '结果', '资源'], ['artifact', 'result']],
    ].map(([id, createType, canvasKinds, order, versionedBlankCanvasKinds, versionedConnectedCanvasKinds, category, title, description, keywords, capabilities]) => ({
        id,
        definition_ref: {id: createType, type: 'legacy-node', version: '0'},
        order,
        metadata: {
            createType,
            canvasKinds: Object.freeze(canvasKinds),
            versionedBlankCanvasKinds: Object.freeze(versionedBlankCanvasKinds),
            versionedConnectedCanvasKinds: Object.freeze(versionedConnectedCanvasKinds),
            category,
            title,
            description,
            icon:creationIcons[createType] || 'box',
            keywords: Object.freeze(keywords),
            capabilities: Object.freeze(capabilities),
            package: Object.freeze({id:'core', version:'builtin'}),
        },
    }));
    const createCommands = Object.freeze(global.WorkbenchCreationCatalog.create(compatibilityCreateEntries).all().map(entry => Object.freeze({
        id: entry.id,
        createType: entry.metadata.createType,
        canvasKinds: entry.metadata.canvasKinds,
        versionedBlankCanvasKinds: entry.metadata.versionedBlankCanvasKinds,
        versionedConnectedCanvasKinds: entry.metadata.versionedConnectedCanvasKinds,
        order: entry.order,
        definition_ref: entry.definition_ref,
        metadata: entry.metadata,
    })));

    const selectionCommands = Object.freeze([
        Object.freeze({id:'canvas.selection.group', canvasKinds:Object.freeze(['classic', 'smart'])}),
    ]);

    const graphCommands = Object.freeze([
        Object.freeze({id:'canvas.graph.connect', canvasKinds:Object.freeze(['classic', 'smart'])}),
        Object.freeze({id:'canvas.graph.create-connected', canvasKinds:Object.freeze(['classic', 'smart'])}),
        Object.freeze({id:'canvas.group.add-member', canvasKinds:Object.freeze(['classic', 'smart'])}),
    ]);

    const nodeCommands = Object.freeze([
        Object.freeze({id:'canvas.node.inspect', canvasKinds:Object.freeze(['classic', 'smart'])}),
    ]);

    function supports(command, canvasKind) {
        return Boolean(command && command.canvasKinds.includes(canvasKind));
    }

    function createCommand(createType, canvasKind) {
        return createCommands.find(command => command.createType === createType && supports(command, canvasKind)) || null;
    }

    function selectionCommand(commandId, canvasKind) {
        return selectionCommands.find(command => command.id === commandId && supports(command, canvasKind)) || null;
    }

    function graphCommand(commandId, canvasKind) {
        return graphCommands.find(command => command.id === commandId && supports(command, canvasKind)) || null;
    }

    function nodeCommand(commandId, canvasKind) {
        return nodeCommands.find(command => command.id === commandId && supports(command, canvasKind)) || null;
    }

    function createCommandsFor(canvasKind) {
        return Object.freeze(createCommands.filter(command => supports(command, canvasKind)).sort((left, right) => left.order - right.order));
    }

    function creationCatalogFor(canvasKind) {
        return Object.freeze(createCommandsFor(canvasKind).map(command => Object.freeze({
            id: command.id,
            definition_ref: command.definition_ref,
            order: command.order,
        })));
    }

    function nodePickerCatalogFor(canvasKind) {
        return Object.freeze(createCommandsFor(canvasKind).map(command => Object.freeze({
            id: command.id,
            definition_ref: command.definition_ref,
            order: command.order,
            metadata: command.metadata,
        })));
    }

    function usesVersionedBlankCreation(command, canvasKind) {
        return Boolean(command && command.versionedBlankCanvasKinds.includes(canvasKind));
    }

    function usesVersionedConnectedCreation(command, canvasKind) {
        return Boolean(command && command.versionedConnectedCanvasKinds.includes(canvasKind));
    }

    function orderCreateMenuItems(items, catalog) {
        if (!Array.isArray(catalog)) throw new TypeError('catalog must be an array');
        const byId = new Map(Array.from(items || []).map(item => [item.dataset && item.dataset.canvasCommand, item]));
        const allowedIds = new Set(catalog.map(command => command.id));
        byId.forEach((item, id) => { item.hidden = !allowedIds.has(id); });
        return Object.freeze(catalog.map(command => byId.get(command.id)).filter(Boolean));
    }

    global.WorkbenchCanvasCommands = Object.freeze({createCommand, createCommandsFor, creationCatalogFor, graphCommand, nodeCommand, nodePickerCatalogFor, orderCreateMenuItems, selectionCommand, usesVersionedBlankCreation, usesVersionedConnectedCreation});
}(window));
