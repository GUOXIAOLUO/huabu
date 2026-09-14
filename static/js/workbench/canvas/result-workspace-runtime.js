/* Unified Result Workspace presentation. The child runtimes remain the
   authority for tray, preview, compare, selection, collection, and
   materialization state; this module owns only navigation and composition. */
(function exposeWorkbenchCanvasResultWorkspace(global) {
    'use strict';

    const VIEWS = Object.freeze(['grid', 'preview', 'compare', 'selection', 'collection', 'materialization']);

    function text(value, fallback = '') {
        const result = String(value ?? '').trim();
        return result || fallback;
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        let view = VIEWS.includes(settings.initialView) ? settings.initialView : 'grid';
        let activeIndex = 0;
        let host = null;
        let children = Object.freeze({});
        let mounted = false;

        function items() {
            return Array.isArray(settings.items) ? settings.items : [];
        }

        function activeItem() {
            const values = items();
            return values.length ? values[Math.min(activeIndex, values.length - 1)] : null;
        }

        function snapshot() {
            return Object.freeze({
                view, activeIndex, activeItem: activeItem(), itemCount: items().length,
                availableViews: VIEWS,
            });
        }

        function emitChange() { settings.onChange?.(snapshot()); }

        function setView(next) {
            if (!VIEWS.includes(next)) throw new RangeError(`unknown result workspace view: ${next}`);
            view = next;
            render();
            return snapshot();
        }

        function selectIndex(index) {
            const next = Number(index);
            if (!Number.isInteger(next) || next < 0 || next >= items().length) throw new RangeError('result index is unavailable');
            activeIndex = next;
            settings.onPreview?.(activeItem(), activeIndex);
            render();
            return snapshot();
        }

        function step(delta) {
            const values = items();
            if (!values.length) return snapshot();
            activeIndex = (activeIndex + Number(delta) + values.length) % values.length;
            settings.onPreview?.(activeItem(), activeIndex);
            render();
            return snapshot();
        }

        function childController(name, factory, childOptions) {
            const runtime = global[factory];
            if (!runtime || typeof runtime.create !== 'function' || !childOptions) return null;
            return runtime.create(childOptions);
        }

        function renderPreview(target) {
            const item = activeItem();
            const preview = global.WorkbenchCanvasResultPreview;
            if (!item || !preview) { target.textContent = item ? 'Preview unavailable' : 'No results yet'; return; }
            target.innerHTML = preview.previewHtml(item);
        }

        function render() {
            if (!host) return;
            const documentRef = settings.document || host.ownerDocument || global.document;
            host.replaceChildren();
            const root = documentRef.createElement('section');
            root.className = 'workbench-result-workspace';
            root.dataset.view = view;
            const header = documentRef.createElement('header');
            header.className = 'workbench-result-workspace__header';
            const title = documentRef.createElement('strong'); title.textContent = text(settings.title, 'Results');
            const count = documentRef.createElement('span'); count.textContent = `${items().length} results`;
            header.append(title, count);
            const tabs = documentRef.createElement('nav'); tabs.className = 'workbench-result-workspace__tabs'; tabs.setAttribute('aria-label', 'Result workspace');
            VIEWS.forEach(name => { const button = documentRef.createElement('button'); button.type = 'button'; button.dataset.view = name; button.textContent = name[0].toUpperCase() + name.slice(1); button.setAttribute('aria-pressed', String(view === name)); button.addEventListener('click', () => setView(name)); tabs.append(button); });
            header.append(tabs);
            const body = documentRef.createElement('div'); body.className = 'workbench-result-workspace__body';
            const actionBar = documentRef.createElement('div'); actionBar.className = 'workbench-result-workspace__actions';
            [['preview', 'Preview'], ['compare', 'Compare'], ['selection', 'Select / rate'], ['collection', 'Collect'], ['materialization', 'Materialize']].forEach(([name, label]) => {
                if (name !== 'preview' && !children[name]) return;
                const action = documentRef.createElement('button'); action.type = 'button'; action.dataset.action = name; action.textContent = label;
                action.addEventListener('click', () => setView(name)); actionBar.append(action);
            });
            if (actionBar.children.length) body.append(actionBar);
            if (view === 'preview') {
                const controls = documentRef.createElement('div'); controls.className = 'workbench-result-workspace__preview-controls';
                const previous = documentRef.createElement('button'); previous.type = 'button'; previous.dataset.action = 'previous'; previous.textContent = 'Previous'; previous.addEventListener('click', () => step(-1));
                const next = documentRef.createElement('button'); next.type = 'button'; next.dataset.action = 'next'; next.textContent = 'Next'; next.addEventListener('click', () => step(1));
                controls.append(previous, next); const previewHost = documentRef.createElement('div'); previewHost.className = 'workbench-result-workspace__preview'; renderPreview(previewHost); body.append(controls, previewHost);
            } else if (view === 'grid' && children.tray) {
                const trayHost = documentRef.createElement('div'); trayHost.className = 'workbench-result-workspace__tray'; children.tray.mount(trayHost); body.append(trayHost);
                trayHost.addEventListener('click', event => {
                    const card = event.target.closest?.('[data-result-item]');
                    const index = card ? items().findIndex(item => String(item?.item_id) === String(card.dataset.resultItem)) : -1;
                    if (index >= 0) { selectIndex(index); setView('preview'); }
                });
            } else if (view === 'compare' && children.compare) {
                const compareHost = documentRef.createElement('div'); children.compare.mount(compareHost); body.append(compareHost);
            } else if (view === 'selection' && children.selection) {
                const selectionHost = documentRef.createElement('div'); children.selection.mount(selectionHost); body.append(selectionHost);
            } else if (view === 'collection' && children.collection) {
                const collectionHost = documentRef.createElement('div'); children.collection.mount(collectionHost); body.append(collectionHost);
            } else if (view === 'materialization' && children.materialization) {
                const materializationHost = documentRef.createElement('div'); children.materialization.mount(materializationHost); body.append(materializationHost);
            } else {
                const empty = documentRef.createElement('p'); empty.className = 'is-empty'; empty.textContent = 'This result view is unavailable'; body.append(empty);
            }
            root.append(header, body); host.append(root); emitChange();
        }

        function mount(target) {
            if (!target || typeof target.replaceChildren !== 'function') throw new TypeError('Result workspace requires a host');
            host = target;
            children = Object.freeze({
                tray: childController('tray', 'WorkbenchCanvasResultTray', settings.tray),
                compare: childController('compare', 'WorkbenchCanvasResultCompare', settings.compare),
                selection: childController('selection', 'WorkbenchCanvasResultSelection', settings.selection),
                collection: childController('collection', 'WorkbenchCanvasResultCollection', settings.collection),
                materialization: childController('materialization', 'WorkbenchCanvasResultMaterialization', settings.materialization),
            });
            mounted = true; render();
            return Object.freeze({element: host, snapshot, setView, selectIndex, previous: () => step(-1), next: () => step(1), children, destroy: () => { Object.values(children).forEach(child => child?.destroy?.()); host?.replaceChildren(); host = null; mounted = false; }});
        }

        return Object.freeze({snapshot, setView, selectIndex, previous: () => step(-1), next: () => step(1), mount});
    }

    global.WorkbenchCanvasResultWorkspace = Object.freeze({VIEWS, create});
}(window));
