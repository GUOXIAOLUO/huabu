/* Reusable node-card composition boundary. A Canvas page supplies a NodeRecord
   and receives intents; this host owns shell creation and renderer selection. */
(function exposeWorkbenchNodeCardHost(global) {
    'use strict';

    if (!global.WorkbenchRendererRegistry || !global.WorkbenchNodeShell) {
        throw new Error('NodeCardHost requires RendererRegistry and NodeShell');
    }

    const registry = global.WorkbenchRendererRegistry.create();
    function hasRenderer(id, version) {
        return registry.all().some(renderer => renderer.id === id && renderer.version === version);
    }

    function registerBuiltIns() {
        if (global.WorkbenchSkillNodeRenderer && !hasRenderer('skill-node', '1')) {
            registry.register({
                id: 'skill-node', version: '1', priority: 130,
                canRender: node => global.WorkbenchSkillNodeRenderer.canRender(node),
                mount: (shell, node, options) => global.WorkbenchSkillNodeRenderer.mount(shell, node, options),
            });
        }
        if (global.WorkbenchCollectionRichNode && !hasRenderer('collection-gallery', '1')) {
            registry.register({
                id: 'collection-gallery', version: '1', priority: 120,
                canRender: node => global.WorkbenchCollectionRichNode.isCompatible(node),
                mount: (shell, node, options) => global.WorkbenchCollectionRichNode.mount(shell, node, {
                    ...(options || {}), richNode: shell.collectionRichNode,
                }),
            });
        }
        if (global.WorkbenchEntityRichNode && !hasRenderer('entity-rich', '1')) {
            registry.register({
                id: 'entity-rich', version: '1', priority: 125,
                canRender: node => global.WorkbenchEntityRichNode.compatible(node),
                mount: (shell, node, options) => global.WorkbenchEntityRichNode.mount(shell, node, {
                    ...(options || {}), richNode: shell.entityRichNode,
                }),
            });
        }
        if (global.WorkbenchMediaRenderer && !hasRenderer('media', '1')) {
            registry.register({
                id: 'media',
                version: '1',
                priority: 100,
                canRender: node => global.WorkbenchMediaRenderer.canRender(node),
                mount: (shell, node, options) => global.WorkbenchMediaRenderer.mount(shell, node, options),
            });
        }
        if (global.WorkbenchLegacyRenderer && !hasRenderer('source-payload', '1')) {
            registry.register({
                id: 'source-payload',
                version: '1',
                priority: 0,
                canRender: node => global.WorkbenchLegacyRenderer.canRender(node),
                mount: (shell, node, options) => global.WorkbenchLegacyRenderer.mount(shell, node, options),
            });
        }
    }

    registerBuiltIns();

    function resolveRenderer(settings) {
        const node = settings.node;
        if (!node) throw new TypeError('NodeCardHost requires a NodeRecord');
        registerBuiltIns();
        return registry.require(node, settings);
    }

    function rendererOptions(settings) {
        return settings.rendererOptions || settings;
    }

    function mount(options) {
        const settings = options || {};
        const node = settings.node;
        const renderer = resolveRenderer(settings);
        const resolvedRendererOptions = rendererOptions(settings);
        // Legacy compatibility records retain the original Task node in
        // rendererOptions so the shared Task presentation can still mount.
        const taskCandidate = resolvedRendererOptions.taskNode || node;
        const isTask = taskCandidate.kind === 'task' || taskCandidate.type === 'task';
        const modelSelectorOptions = isTask
            ? {
                ...(resolvedRendererOptions.modelSelectorOptions || {}),
                availabilities: resolvedRendererOptions.modelAvailabilities || resolvedRendererOptions.modelSelectorOptions?.availabilities || [],
                requirements: resolvedRendererOptions.capabilityRequirements || resolvedRendererOptions.modelSelectorOptions?.requirements || [],
            }
            : null;
        const executionInputPreviewOptions = isTask
            ? {
                projection: resolvedRendererOptions.executionInputProjection
                    || node.executionInputProjection
                    || node.execution_input_projection
                    || {valid: node.executionValid !== false, inputs: Array.isArray(node.inputs) ? node.inputs : [], errors: Array.isArray(node.inputErrors) ? node.inputErrors : []},
                policy: resolvedRendererOptions.executionPolicy || node.executionPolicy || node.execution_policy || {},
                ...(resolvedRendererOptions.executionInputPreviewOptions || {}),
            }
            : null;
        const taskPresentationOptions = isTask && resolvedRendererOptions.taskPresentationOptions
            ? {
                ...resolvedRendererOptions.taskPresentationOptions,
                // The compact card owns the visible selector hosts. These
                // options still flow through the canonical selector modules;
                // no provider or credential data is copied into the node.
                modelSelectorOptions,
                ...(resolvedRendererOptions.skillSelectorOptions
                    ? {skillSelectorOptions: resolvedRendererOptions.skillSelectorOptions}
                    : {}),
            }
            : resolvedRendererOptions.taskPresentationOptions;
        const resultAssetOptions = resolvedRendererOptions.resultAssetMaterializationOptions;
        const resultSelectionOptions = resolvedRendererOptions.resultSelectionOptions || resultAssetOptions
            ? {...(resolvedRendererOptions.resultSelectionOptions || {})}
            : null;
        if (resultSelectionOptions && resultAssetOptions && !resultSelectionOptions.onSaveAsAsset
            && global.WorkbenchResultAssetMaterializationApiClient?.createHandler) {
            resultSelectionOptions.onSaveAsAsset = global.WorkbenchResultAssetMaterializationApiClient.createHandler(resultAssetOptions);
        }
        const entityRichNodeOptions = node.kind === 'entity' || node.type === 'entity'
            ? {
                ...resolvedRendererOptions,
                onEdit: detail => {
                    resolvedRendererOptions.onEdit?.(detail);
                    if (typeof settings.onIntent === 'function') {
                        settings.onIntent({type: 'entity_edit', nodeId: node.id, detail});
                    }
                },
            }
            : resolvedRendererOptions;
        const shell = global.WorkbenchNodeShell.create({
            document: settings.document || global.document,
            node,
            viewState: settings.viewState || {},
            onIntent: settings.onIntent,
            showDelete: settings.showDelete,
            ports: settings.ports,
            taskNode: resolvedRendererOptions.taskNode,
            taskRichNodeOptions: resolvedRendererOptions.taskRichNodeOptions,
            taskPresentationOptions,
            deferTaskPresentation: isTask && Boolean(resolvedRendererOptions.taskPresentationOptions),
            collectionRichNodeOptions: resolvedRendererOptions,
            skillSelectorOptions: resolvedRendererOptions.skillSelectorOptions,
            skillPresentationOptions: resolvedRendererOptions.skillPresentationOptions,
            skillInspectorOptions: resolvedRendererOptions.skillInspectorOptions,
            modelSelectorOptions,
            executionInputPreviewOptions,
            resultSelectionOptions,
            resultWorkspaceOptions: resolvedRendererOptions.resultWorkspaceOptions,
            entityRichNodeOptions,
        });
        const mountedRenderer = renderer.mount(shell, node, {
            ...resolvedRendererOptions,
            contentFirst: renderer.id === 'media' || resolvedRendererOptions.contentFirst === true,
        });
        const mountedTaskPresentation = isTask && taskPresentationOptions && shell.taskRichNode
            ? shell.taskRichNode.mountTaskPresentation(shell.contentHost, taskPresentationOptions)
            : null;
        let mountedResultWorkspace = null;
        if (isTask && resolvedRendererOptions.resultWorkspaceOptions && shell.taskRichNode) {
            const workspaceHost = (settings.document || global.document).createElement('section');
            workspaceHost.setAttribute('data-result-workspace-host', '');
            shell.contentHost.append(workspaceHost);
            mountedResultWorkspace = shell.taskRichNode.mountResultWorkspace(workspaceHost, resolvedRendererOptions.resultWorkspaceOptions);
        }
        shell.element.dataset.rendererId = renderer.id;
        shell.element.dataset.rendererVersion = renderer.version;
        return Object.freeze({
            element: shell.element,
            shell,
            renderer,
            mountedRenderer,
            mountedTaskPresentation,
            mountedResultWorkspace,
            destroy() {
                mountedRenderer && mountedRenderer.destroy && mountedRenderer.destroy();
                mountedResultWorkspace?.destroy?.();
                shell.destroy();
            },
        });
    }

    function mountContent(options) {
        const settings = options || {};
        const node = settings.node;
        const contentHost = settings.contentHost;
        if (!contentHost) throw new TypeError('NodeCardHost requires a content host');
        const renderer = resolveRenderer(settings);
        const mountedRenderer = renderer.mount({contentHost}, node, rendererOptions(settings));
        return Object.freeze({
            element: mountedRenderer?.element || contentHost,
            renderer,
            mountedRenderer,
            destroy() { mountedRenderer && mountedRenderer.destroy && mountedRenderer.destroy(); },
        });
    }

    global.WorkbenchNodeCardHost = Object.freeze({mount, mountContent, registry, registerBuiltIns});
}(window));
