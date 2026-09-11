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
        const taskRichNode = global.WorkbenchTaskRichNode?.compatible(node)
            ? global.WorkbenchTaskRichNode.create({node, presentationController})
            : null;
        const artifactRichNode = global.WorkbenchArtifactRichNode?.compatible(node)
            ? global.WorkbenchArtifactRichNode.create({node, presentation: presentationController})
            : null;
        const collectionRichNode = global.WorkbenchCollectionRichNode?.isCompatible(node)
            ? global.WorkbenchCollectionRichNode.create({node, presentation: presentationController})
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
            presentationState: () => assetRichNode?.state() || taskRichNode?.state().presentation || artifactRichNode?.state() || collectionRichNode?.state() || root.dataset.presentationState || 'card',
            assetRichNode,
            taskRichNode,
            artifactRichNode,
            collectionRichNode,
            transitionPresentation, update, destroy: () => root.remove(),
        });
    }

    global.WorkbenchNodeShell = Object.freeze({create: createNodeShell});
}(window));
