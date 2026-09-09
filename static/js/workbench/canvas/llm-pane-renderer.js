/* Neutral markup renderer for the compatibility LLM panes. */
(function exposeLlmPaneRenderer(global) {
    'use strict';
    function state(options = {}) {
        const connectedInput = String(options.connectedInput || '');
        const readonly = connectedInput.length > 0;
        return Object.freeze({
            readonly,
            inputValue: connectedInput || String(options.userInput || ''),
            inputHeight: Math.max(70, Number(options.inputHeight) || 110),
            outputHeight: Math.max(70, Number(options.outputHeight) || 150),
        });
    }
    function chatState(options = {}) {
        return Object.freeze({
            messages: Array.isArray(options.messages) ? options.messages : [],
            input: String(options.input || ''),
            running: Boolean(options.running),
            sendLabel: options.running ? String(options.sendingLabel || '') : String(options.sendLabel || ''),
        });
    }
    function paneMarkup(options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const input = e(options.inputValue || '');
        const output = e(options.outputText || '');
        const inputLabel = options.readonly ? 'Input <span style="font-size:9px;opacity:.5;font-weight:600;text-transform:none;letter-spacing:0">(来自连接)</span>' : 'Input';
        return `<div class="llm-pane-label">${inputLabel}</div><textarea class="llm-input-area llm-input-output" style="height:${options.inputHeight}px; flex:0 0 ${options.inputHeight}px;" ${options.readonly ? 'readonly' : ''} placeholder="${e(options.inputPlaceholder || '')}">${input}</textarea><div class="llm-pane-resizer" title="${e(options.resizeLabel || '')}"></div><div class="llm-pane-label">Output</div><div class="llm-output-wrap" style="height:${options.outputHeight}px; flex:0 0 ${options.outputHeight}px;"><button class="llm-copy-btn llm-output-copy" type="button" title="复制"><i data-lucide="copy" class="w-3.5 h-3.5"></i></button><div class="llm-output llm-result-output">${output}</div></div><div class="gen-run-row mt-2"><button class="llm-run ${options.running ? 'running' : ''}" ${options.running ? 'disabled' : ''}><i data-lucide="play" class="w-4 h-4"></i>${e(options.runLabel || '')}</button>${options.cascadeMarkup || ''}</div>${options.retryMarkup || ''}`;
    }
    function chatMarkup(options = {}) {
        const e = options.escapeHtml || (value => String(value ?? ''));
        const messages = Array.isArray(options.messages) ? options.messages : [];
        const log = messages.length ? messages.map((msg, index) => `<div class="llm-bubble ${msg.role === 'user' ? 'user' : 'assistant'}" data-msg-idx="${index}">${e(msg.content || '')}${msg.role === 'assistant' ? '<button class="llm-bubble-copy" type="button" title="复制"><i data-lucide="copy" style="width:11px;height:11px;display:inline-block;vertical-align:middle"></i></button>' : ''}</div>`).join('') : `<div class="text-[11px] text-gray-300">${e(options.emptyLabel || '')}</div>`;
        return `<div class="llm-chat-log">${log}</div><textarea class="llm-chat-input mt-2" rows="2" placeholder="${e(options.placeholder || '')}">${e(options.input || '')}</textarea><button class="llm-run mt-2" ${options.running ? 'disabled' : ''}><i data-lucide="send" class="w-4 h-4"></i>${e(options.sendLabel || '')}</button>`;
    }
    global.WorkbenchCanvasLlmPaneRenderer = Object.freeze({state, chatState, paneMarkup, chatMarkup});
}(window));
