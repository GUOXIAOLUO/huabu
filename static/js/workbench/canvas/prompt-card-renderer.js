/* Generic-family renderer: owns the Classic prompt card DOM. The page keeps
   state ownership (prompt text payload, save scheduling, template modal) and
   supplies behavior through rendererOptions; the registry resolves this
   renderer for legacy prompt records, so migrated cards no longer depend on
   pre-rendered page DOM. */
(function exposeWorkbenchPromptCardRenderer(global) {
    'use strict';

    if (!global.WorkbenchNodeCardHost || !global.WorkbenchNodeCardHost.registry) {
        throw new Error('PromptCardRenderer requires NodeCardHost with a registry');
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, ch => (
            {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]
        ));
    }
    const escapeAttr = escapeHtml;
    function tr(key) {
        return global.StudioI18n?.t ? global.StudioI18n.t(key) : key;
    }
    function defaultTextLength(value) {
        return Array.from(String(value || '')).length;
    }

    const promptCardRenderer = {
        id: 'prompt-card',
        version: '1',
        priority: 10,
        canRender: node => node?.definition_ref?.type === 'legacy' && node?.definition_ref?.id === 'prompt',
        mount(shell, node, options) {
            const settings = options || {};
            const contentHost = shell.contentHost;
            if (!contentHost) throw new TypeError('PromptCardRenderer requires a shell content host');
            const documentRef = settings.document || contentHost.ownerDocument || global.document;
            const payload = node.extensions?.legacy?.payload || {};
            const text = String(payload.text ?? '');
            const maxLength = Number(settings.maxLength) || 20000;
            const textLength = typeof settings.textLength === 'function' ? settings.textLength : defaultTextLength;

            const editor = documentRef.createElement('div');
            editor.className = 'prompt-editor';

            const toolbar = documentRef.createElement('div');
            toolbar.className = 'prompt-toolbar';
            const templateButton = documentRef.createElement('button');
            templateButton.type = 'button';
            templateButton.className = `prompt-template-btn${settings.templateActive ? ' active' : ''}`;
            templateButton.dataset.promptTemplateOpen = 'true';
            templateButton.dataset.promptTemplateNodeId = String(node.id || '');
            templateButton.setAttribute('aria-pressed', settings.templateActive ? 'true' : 'false');
            templateButton.title = tr('canvas.promptTemplateLibrary');
            const icon = documentRef.createElement('i');
            icon.dataset.lucide = 'library';
            const label = documentRef.createElement('span');
            label.textContent = tr('canvas.promptTemplateShort');
            templateButton.append(icon, label);
            templateButton.addEventListener('click', event => {
                event.preventDefault();
                event.stopPropagation();
                settings.onOpenTemplate?.(node.id);
            });

            const count = textLength(text);
            const counter = documentRef.createElement('div');
            counter.className = `prompt-counter${count > maxLength ? ' over' : ''}`;
            const countSpan = documentRef.createElement('span');
            countSpan.textContent = count.toLocaleString();
            const maxSpan = documentRef.createElement('span');
            maxSpan.textContent = `/ ${maxLength.toLocaleString()}`;
            counter.append(countSpan, maxSpan);

            toolbar.append(templateButton, counter);

            const textarea = documentRef.createElement('textarea');
            textarea.placeholder = tr('canvas.promptPlaceholder');
            textarea.value = text;
            textarea.addEventListener('input', event => {
                const value = event.target.value;
                const nextCount = textLength(value);
                countSpan.textContent = nextCount.toLocaleString();
                counter.className = `prompt-counter${nextCount > maxLength ? ' over' : ''}`;
                settings.onPromptInput?.(value);
            });

            editor.append(toolbar, textarea);
            contentHost.replaceChildren(editor);
            if (typeof settings.bindTextElement === 'function') settings.bindTextElement(textarea);

            return Object.freeze({
                element: editor,
                destroy() {},
            });
        },
    };

    global.WorkbenchNodeCardHost.registry.register(promptCardRenderer);
}(window));
