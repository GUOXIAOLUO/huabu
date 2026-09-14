/* Shared DOM shell for migrated nodes. Rendering and persistence stay outside this module. */
(function exposeWorkbenchNodeShell(global) {
    'use strict';

    const VALID_STATES = new Set((global.WorkbenchCanvas && global.WorkbenchCanvas.STATES) || []);

    function text(value, fallback) {
        const normalized = String(value == null ? '' : value).trim();
        return normalized || fallback;
    }

    function emit(onIntent, type, node, detail) {
        if (typeof onIntent === 'function') onIntent({type, nodeId: node.id, detail: detail || {}});
    }

    function createButton(documentRef, className, label, onClick) {
        const button = documentRef.createElement('button');
        button.type = 'button';
        button.className = className;
        button.setAttribute('aria-label', label);
        button.textContent = label;
        button.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            onClick(event);
        });
        return button;
    }

    function createNodeShell(options) {
        const settings = options || {};
        const documentRef = settings.document || global.document;
        const node = settings.node;
        if (!documentRef || !node || !text(node.id, '')) throw new TypeError('NodeShell requires a document and a node with an id');

        const onIntent = settings.onIntent;
        const portVisibility = settings.ports || {};
        const presentationController = global.WorkbenchPresentationState
            ? global.WorkbenchPresentationState.create({initial: settings.viewState && settings.viewState.presentation})
            : null;
        const assetRichNode = global.WorkbenchAssetRichNode?.isCompatible(node)
            ? global.WorkbenchAssetRichNode.create({node, presentation: presentationController})
            : null;
        // Keep the original call shape documented for compatibility tests:
        // WorkbenchTaskRichNode.create({node, presentationController})
        const taskNode = settings.taskNode && global.WorkbenchTaskRichNode?.compatible(settings.taskNode) ? settings.taskNode : node;
        const taskRichNode = global.WorkbenchTaskRichNode?.compatible(taskNode)
            ? global.WorkbenchTaskRichNode.create({node: taskNode, presentationController, ...(settings.taskRichNodeOptions || {})})
            : null;
        const artifactRichNode = global.WorkbenchArtifactRichNode?.compatible(node)
            ? global.WorkbenchArtifactRichNode.create({node, presentation: presentationController})
            : null;
        const collectionRichNodeOptions = settings.collectionRichNodeOptions && typeof settings.collectionRichNodeOptions === 'object'
            ? settings.collectionRichNodeOptions
            : {};
        const collectionRichNode = global.WorkbenchCollectionRichNode?.isCompatible(node)
            ? global.WorkbenchCollectionRichNode.create({...collectionRichNodeOptions, node, presentation: presentationController})
            : null;
        const entityRichNodeOptions = settings.entityRichNodeOptions && typeof settings.entityRichNodeOptions === 'object'
            ? settings.entityRichNodeOptions : {};
        const entityRichNode = global.WorkbenchEntityRichNode?.compatible(node)
            ? global.WorkbenchEntityRichNode.create({...entityRichNodeOptions, node, presentation: presentationController})
            : null;
        let selectedState = Boolean(settings.viewState && settings.viewState.selected);
        const root = documentRef.createElement('article');
        root.className = 'workbench-node-shell';
        root.dataset.nodeId = node.id;
        root.setAttribute('role', 'group');
        root.tabIndex = 0;

        const header = documentRef.createElement('header');
        header.className = 'workbench-node-shell__header';
        const title = documentRef.createElement('span');
        title.className = 'workbench-node-shell__title';
        const status = documentRef.createElement('span');
        status.className = 'workbench-node-shell__status';
        status.setAttribute('aria-live', 'polite');
        const actions = documentRef.createElement('div');
        actions.className = 'workbench-node-shell__actions';
        const menu = createButton(documentRef, 'workbench-node-shell__menu', 'Node menu', () => emit(onIntent, 'menu', node));
        actions.append(menu);
        if (settings.showDelete) {
            const remove = createButton(documentRef, 'workbench-node-shell__delete', 'Delete node', () => emit(onIntent, 'delete', node));
            actions.append(remove);
        }
        header.append(title, status, actions);

        function createPort(className, label, direction) {
            const port = createButton(documentRef, className, label, () => {});
            port.dataset.port = direction === 'input' ? 'in' : 'out';
            port.addEventListener('mousedown', event => {
                if (event.button !== 0) return;
                event.preventDefault();
                event.stopPropagation();
                emit(onIntent, 'connect_start', node, {
                    direction, clientX: event.clientX, clientY: event.clientY,
                });
            });
            return port;
        }
        const inputPort = createPort('workbench-node-shell__port workbench-node-shell__port--input', 'Input port', 'input');
        const outputPort = createPort('workbench-node-shell__port workbench-node-shell__port--output', 'Output port', 'output');
        const content = documentRef.createElement('section');
        content.className = 'workbench-node-shell__content';
        content.setAttribute('data-node-shell-content', '');
        const taskPresentationHost = taskRichNode && settings.taskPresentationOptions ? documentRef.createElement('section') : null;
        // Inline Task presentation owns its selector controls. Keep the
        // standalone hosts only for legacy/expanded callers without the card.
        const inlineTaskPresentation = Boolean(taskRichNode && settings.taskPresentationOptions);
        const skillSelectorHost = taskRichNode && settings.skillSelectorOptions && !inlineTaskPresentation ? documentRef.createElement('section') : null;
        const skillPresentationHost = taskRichNode && settings.skillPresentationOptions ? documentRef.createElement('section') : null;
        const skillInspectorHost = taskRichNode && settings.skillInspectorOptions ? documentRef.createElement('section') : null;
        const modelSelectorHost = taskRichNode && settings.modelSelectorOptions && !inlineTaskPresentation ? documentRef.createElement('section') : null;
        const executionInputPreviewHost = taskRichNode && settings.executionInputPreviewOptions ? documentRef.createElement('section') : null;
        const resultTrayHost = taskRichNode && settings.resultTrayOptions ? documentRef.createElement('section') : null;
        const resultCompareHost = taskRichNode && settings.resultCompareOptions ? documentRef.createElement('section') : null;
        const resultSelectionHost = taskRichNode && settings.resultSelectionOptions && !settings.resultWorkspaceOptions ? documentRef.createElement('section') : null;
        const executionBranchHost = taskRichNode && settings.executionBranchOptions ? documentRef.createElement('section') : null;
        const resultCollectionHost = taskRichNode && settings.resultCollectionOptions ? documentRef.createElement('section') : null;
        const resultMaterializationHost = taskRichNode && settings.resultMaterializationOptions ? documentRef.createElement('section') : null;
        const resultWorkspaceHost = taskRichNode && settings.resultWorkspaceOptions ? documentRef.createElement('section') : null;
        skillSelectorHost?.setAttribute('data-task-skill-selector-host', '');
        taskPresentationHost?.setAttribute('data-task-card-presentation-host', '');
        skillPresentationHost?.setAttribute('data-task-skill-presentation-host', '');
        skillInspectorHost?.setAttribute('data-task-skill-inspector-host', '');
        modelSelectorHost?.setAttribute('data-task-model-selector-host', '');
        executionInputPreviewHost?.setAttribute('data-execution-input-preview-host', '');
        resultTrayHost?.setAttribute('data-result-tray-host', '');
        resultCompareHost?.setAttribute('data-result-compare-host', '');
        resultSelectionHost?.setAttribute('data-result-selection-host', '');
        executionBranchHost?.setAttribute('data-execution-branch-host', '');
        resultCollectionHost?.setAttribute('data-result-collection-host', '');
        resultMaterializationHost?.setAttribute('data-result-materialization-host', '');
        resultWorkspaceHost?.setAttribute('data-result-workspace-host', '');
        content.append(...[taskPresentationHost, skillSelectorHost, skillPresentationHost, skillInspectorHost, modelSelectorHost, executionInputPreviewHost, resultWorkspaceHost, resultTrayHost, resultCompareHost, resultSelectionHost, executionBranchHost, resultCollectionHost, resultMaterializationHost].filter(Boolean));
        const toolbar = documentRef.createElement('div');
        toolbar.className = 'workbench-node-shell__toolbar';
        toolbar.setAttribute('data-node-shell-toolbar', '');
        const footer = documentRef.createElement('footer');
        footer.className = 'workbench-node-shell__footer';
        const resize = createButton(documentRef, 'workbench-node-shell__resize', 'Resize node', () => {});
        resize.addEventListener('mousedown', event => {
            if (event.button !== 0) return;
            event.preventDefault();
            event.stopPropagation();
            emit(onIntent, 'resize_start', node, {
                clientX: event.clientX, clientY: event.clientY,
            });
        });
        footer.append(resize);

        const mountedSkillSelector = taskRichNode && settings.skillSelectorOptions && !inlineTaskPresentation
            ? taskRichNode.mountSkillSelector(skillSelectorHost, settings.skillSelectorOptions)
            : null;
        let mountedTaskPresentation = taskRichNode && settings.taskPresentationOptions && !settings.deferTaskPresentation
            ? taskRichNode.mountTaskPresentation(taskPresentationHost, settings.taskPresentationOptions)
            : null;
        const mountedSkillPresentation = taskRichNode && settings.skillPresentationOptions
            ? taskRichNode.mountSkillPresentation(skillPresentationHost, settings.skillPresentationOptions)
            : null;
        const mountedSkillInspector = taskRichNode && settings.skillInspectorOptions
            ? taskRichNode.mountSkillInspector(skillInspectorHost, settings.skillInspectorOptions)
            : null;
        const mountedModelSelector = taskRichNode && settings.modelSelectorOptions && !inlineTaskPresentation
            ? taskRichNode.mountModelSelector(modelSelectorHost, settings.modelSelectorOptions)
            : null;
        const mountedExecutionInputPreview = taskRichNode && settings.executionInputPreviewOptions
            ? taskRichNode.mountExecutionInputPreview(executionInputPreviewHost, settings.executionInputPreviewOptions)
            : null;
        const mountedResultTray = taskRichNode && settings.resultTrayOptions
            ? taskRichNode.mountResultTray(resultTrayHost, settings.resultTrayOptions)
            : null;
        const mountedResultCompare = taskRichNode && settings.resultCompareOptions
            ? taskRichNode.mountResultCompare(resultCompareHost, settings.resultCompareOptions)
            : null;
        const mountedResultSelection = taskRichNode && settings.resultSelectionOptions && !settings.resultWorkspaceOptions
            ? taskRichNode.mountResultSelection(resultSelectionHost, settings.resultSelectionOptions)
            : null;
        const mountedExecutionBranch = taskRichNode && settings.executionBranchOptions
            ? taskRichNode.mountExecutionBranch(executionBranchHost, settings.executionBranchOptions)
            : null;
        const mountedResultCollection = taskRichNode && settings.resultCollectionOptions
            ? taskRichNode.mountResultCollection(resultCollectionHost, settings.resultCollectionOptions)
            : null;
        const mountedResultMaterialization = taskRichNode && settings.resultMaterializationOptions
            ? taskRichNode.mountResultMaterialization(resultMaterializationHost, settings.resultMaterializationOptions)
            : null;
        const mountedResultWorkspace = taskRichNode && settings.resultWorkspaceOptions
            ? taskRichNode.mountResultWorkspace(resultWorkspaceHost, settings.resultWorkspaceOptions)
            : null;

        root.append(header);
        if (portVisibility.input !== false) root.append(inputPort);
        root.append(content, toolbar);
        if (portVisibility.output !== false) root.append(outputPort);
        root.append(footer);
        root.addEventListener('focus', () => emit(onIntent, 'focus', node));
        root.addEventListener('click', event => {
            event.stopPropagation();
            emit(onIntent, 'select', node, {
                shiftKey: event.shiftKey, ctrlKey: event.ctrlKey, metaKey: event.metaKey,
            });
        });
        root.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                emit(onIntent, 'select', node);
            }
        });
        header.addEventListener('mousedown', event => {
            if (event.button !== 0) return;
            if (event.target.closest('button')) return;
            event.preventDefault();
            event.stopPropagation();
            emit(onIntent, 'drag_start', node, {
                pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY,
                altKey: event.altKey, shiftKey: event.shiftKey, ctrlKey: event.ctrlKey,
            });
        });

        function update(nextNode, viewState) {
            if (!nextNode || nextNode.id !== node.id) throw new TypeError('NodeShell update requires the same node id');
            const state = VALID_STATES.has(nextNode.state) ? nextNode.state : 'ready';
            if (viewState && Object.prototype.hasOwnProperty.call(viewState, 'selected')) selectedState = Boolean(viewState.selected);
            const selected = selectedState;
            const presentation = presentationController
                ? presentationController.state()
                : (global.WorkbenchPresentationState
                    ? global.WorkbenchPresentationState.normalize(viewState && viewState.presentation)
                    : 'card');
            root.dataset.state = state;
            root.dataset.presentationState = presentation;
            root.classList.remove('is-presentation-card', 'is-presentation-expanded', 'is-presentation-workspace', 'is-presentation-inspector');
            root.classList.add(`is-presentation-${presentation}`);
            root.classList.toggle('is-selected', selected);
            root.setAttribute('aria-label', `${text(nextNode.title, 'Untitled node')}, ${state}`);
            title.textContent = text(nextNode.title, 'Untitled node');
            status.textContent = state;
            footer.dataset.nodeId = nextNode.id;
        }

        function transitionPresentation(next) {
            if (!presentationController) throw new Error('presentation state model is unavailable');
            const state = presentationController.transition(next);
            update(node, {selected: selectedState, presentation: state});
            return state;
        }

        update(node, settings.viewState);
        const slots = Object.freeze({
            header, title, status, ports: Object.freeze({input: inputPort, output: outputPort}),
            content, actions, toolbar, footer, resize,
        });
        return Object.freeze({
            element: root, slots,
            contentHost: content, toolbarHost: toolbar,
            presentationState: () => assetRichNode?.state() || taskRichNode?.state().presentation || artifactRichNode?.state() || collectionRichNode?.state() || entityRichNode?.state() || root.dataset.presentationState || 'card',
            assetRichNode,
            taskRichNode,
            mountedSkillSelector,
            mountedTaskPresentation,
            mountedSkillPresentation,
            mountedSkillInspector,
            mountedModelSelector,
            mountedExecutionInputPreview,
            mountedResultTray,
            mountedResultCompare,
            mountedResultSelection,
            mountedExecutionBranch,
            mountedResultCollection,
            mountedResultMaterialization,
            mountedResultWorkspace,
            artifactRichNode,
            collectionRichNode,
            entityRichNode,
            transitionPresentation, update, destroy: () => { mountedTaskPresentation?.destroy?.(); mountedSkillSelector?.destroy?.(); mountedSkillPresentation?.destroy?.(); mountedSkillInspector?.destroy?.(); mountedModelSelector?.destroy?.(); mountedExecutionInputPreview?.destroy?.(); mountedResultTray?.destroy?.(); mountedResultCompare?.destroy?.(); mountedResultSelection?.destroy?.(); mountedExecutionBranch?.destroy?.(); mountedResultCollection?.destroy?.(); mountedResultMaterialization?.destroy?.(); mountedResultWorkspace?.destroy?.(); root.remove(); },
        });
    }

    global.WorkbenchNodeShell = Object.freeze({create: createNodeShell});
}(window));
