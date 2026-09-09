/* Prompt-template modal event routing. The page supplies state callbacks. */
(function exposePromptTemplateInteraction(global) {
    'use strict';
    function create(options = {}) {
        const callbacks = options.callbacks || {};
        const search = options.search;
        const library = options.library;
        const close = options.close;
        const panel = options.panel;
        const call = (name, ...args) => typeof callbacks[name] === 'function' ? callbacks[name](...args) : undefined;
        search?.addEventListener('input', event => call('queryChanged', event.target.value || ''));
        library?.addEventListener('change', event => call('libraryChanged', event.target.value || 'system'));
        if (close) close.onclick = () => call('close');
        ['pointerdown', 'mousedown'].forEach(type => panel?.addEventListener(type, event => event.stopPropagation()));
        panel?.addEventListener('wheel', event => event.stopPropagation(), {passive: false});
        panel?.addEventListener('click', event => {
            event.stopPropagation();
            const target = event.target.closest?.('[data-template-apply],[data-prompt-template-apply]');
            if (target) return call('apply', target.dataset.templateApply || target.dataset.promptTemplateApply || 'positive');
            if (event.target.closest?.('[data-template-save-current],[data-prompt-template-save-current]')) return call('saveCurrent');
            if (event.target.closest?.('[data-template-new],[data-prompt-template-new]')) return call('create');
            if (event.target.closest?.('[data-template-edit],[data-prompt-template-edit]')) return call('edit');
            if (event.target.closest?.('[data-template-edit-cancel],[data-prompt-template-edit-cancel]')) return call('cancelEdit');
            if (event.target.closest?.('[data-template-edit-save],[data-prompt-template-edit-save]')) return call('saveEdit');
            if (event.target.closest?.('[data-template-delete],[data-prompt-template-delete]')) return call('delete');
            const category = event.target.closest?.('[data-template-cat],[data-prompt-template-cat]');
            if (category) return call('category', category.dataset.templateCat || category.dataset.promptTemplateCat || 'all');
            const categoryEdit = event.target.closest?.('[data-template-cat-edit]');
            if (categoryEdit) return call('editCategory', categoryEdit.dataset.templateCatEdit || '');
            const categoryDelete = event.target.closest?.('[data-template-cat-delete]');
            if (categoryDelete) return call('deleteCategory', categoryDelete.dataset.templateCatDelete || '');
            if (event.target.closest?.('[data-template-group-edit]')) return call('toggleGroups');
            if (event.target.closest?.('[data-template-cat-new]')) return call('createCategory');
            const item = event.target.closest?.('[data-template-id],[data-prompt-template-id]');
            if (item) return call('select', item.dataset.templateId || item.dataset.promptTemplateId || '');
        });
        return Object.freeze({});
    }
    function snapshot(panel) {
        if (!panel) return null;
        return {
            panelTop: panel.scrollTop || 0,
            tabLeft: panel.querySelector?.('.prompt-template-tabs')?.scrollLeft || 0,
            listTop: panel.querySelector?.('.prompt-template-list')?.scrollTop || 0,
            detailTop: panel.querySelector?.('.prompt-template-preview-content')?.scrollTop || 0,
        };
    }
    function restore(panel, value, requestFrame = global.requestAnimationFrame) {
        if (!panel || !value) return;
        const apply = () => {
            panel.scrollTop = value.panelTop || 0;
            const tabs = panel.querySelector?.('.prompt-template-tabs');
            const list = panel.querySelector?.('.prompt-template-list');
            const detail = panel.querySelector?.('.prompt-template-preview-content');
            if (tabs) tabs.scrollLeft = value.tabLeft || 0;
            if (list) list.scrollTop = value.listTop || 0;
            if (detail) detail.scrollTop = value.detailTop || 0;
        };
        if (typeof requestFrame === 'function') requestFrame(apply); else apply();
    }
    function syncOpenButtons(documentRef, modal, nodeId) {
        const activeId = modal?.classList?.contains?.('open') ? String(nodeId || '') : '';
        documentRef?.querySelectorAll?.('[data-prompt-template-open]')?.forEach?.(button => {
            const active = Boolean(activeId && button.dataset.promptTemplateNodeId === activeId);
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }
    global.WorkbenchCanvasPromptTemplateInteraction = Object.freeze({create, snapshot, restore, syncOpenButtons});
}(window));
