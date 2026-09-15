/* Compact Workbench projection for a version-pinned ComfyUI workflow.
   The Comfy executor owns execution; this module only renders the mapped
   contract and delegates Run to the existing host callback. */
(function exposeWorkbenchComfyWorkflowPresentation(global) {
    'use strict';

    function normalize(definition) {
        const source = definition && typeof definition === 'object' ? definition : {};
        const id = String(source.id || source.workflow_id || '').trim();
        const version = Number(source.version);
        if (!id || !Number.isInteger(version) || version < 1) return null;
        const inputs = Array.isArray(source.input_bindings) ? source.input_bindings : [];
        const outputs = Array.isArray(source.output_mappings) ? source.output_mappings : [];
        return Object.freeze({
            id, version, ref: `${id}@${version}`,
            title: String(source.title || id).trim() || id,
            inputs: Object.freeze(inputs.map(item => Object.freeze({
                role: String(item.role || '').trim(), nodeId: String(item.node_id || '').trim(),
                inputName: String(item.input_name || '').trim(), required: item.required !== false,
            })).filter(item => item.role && item.nodeId && item.inputName)),
            outputs: Object.freeze(outputs.map(item => Object.freeze({
                role: String(item.role || '').trim(), nodeId: String(item.node_id || '').trim(),
                outputName: String(item.output_name || 'output').trim() || 'output',
                kind: String(item.kind || 'image').trim() || 'image',
            })).filter(item => item.role && item.nodeId)),
        });
    }

    function create(options = {}) {
        const documentRef = options.document || global.document;
        const container = options.container;
        const model = normalize(options.definition);
        if (!documentRef || !container || !model) throw new TypeError('Comfy workflow presentation requires a versioned definition');
        const root = documentRef.createElement('section');
        root.className = 'workbench-comfy-workflow-presentation';
        root.dataset.comfyWorkflowPresentation = '';
        const title = documentRef.createElement('strong');
        title.className = 'workbench-comfy-workflow-presentation__title';
        title.textContent = model.title;
        const ref = documentRef.createElement('span');
        ref.className = 'workbench-comfy-workflow-presentation__ref';
        ref.textContent = model.ref;
        const inputs = documentRef.createElement('div');
        inputs.className = 'workbench-comfy-workflow-presentation__inputs';
        const outputs = documentRef.createElement('div');
        outputs.className = 'workbench-comfy-workflow-presentation__outputs';
        root.append(title, ref, inputs, outputs);
        model.inputs.forEach(item => {
            const chip = documentRef.createElement('span');
            chip.className = 'workbench-comfy-workflow-presentation__chip';
            chip.dataset.comfyInputRole = item.role;
            chip.textContent = `${item.role}${item.required ? ' · 必填' : ''}`;
            inputs.append(chip);
        });
        model.outputs.forEach(item => {
            const chip = documentRef.createElement('span');
            chip.className = 'workbench-comfy-workflow-presentation__chip';
            chip.dataset.comfyOutputRole = item.role;
            chip.textContent = `${item.role} · ${item.kind}`;
            outputs.append(chip);
        });
        if (typeof options.onRun === 'function') {
            const run = documentRef.createElement('button');
            run.type = 'button'; run.className = 'workbench-comfy-workflow-presentation__run';
            run.textContent = '运行工作流'; run.addEventListener('click', options.onRun);
            root.append(run);
        }
        container.prepend(root);
        return Object.freeze({root, model});
    }

    global.WorkbenchComfyWorkflowPresentation = Object.freeze({normalize, create});
}(window));
