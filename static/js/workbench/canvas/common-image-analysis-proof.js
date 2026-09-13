/* Minimal configuration proof for the generic image-analysis Skill. It only
   registers declarative metadata and persists Task configuration. */
(function exposeCommonImageAnalysisConfiguration(global) {
    'use strict';

    const DEFINITION = Object.freeze({
        id: 'common.image-analysis', version: '1.0.0', title: 'Image analysis',
        input_schema: Object.freeze({type: 'object', properties: Object.freeze({image: Object.freeze({type: 'asset_version'})}), required: Object.freeze(['image'])}),
        output_schema: Object.freeze({type: 'object', properties: Object.freeze({observations: Object.freeze({type: 'array'})})}),
        parameter_schema: Object.freeze({type: 'object', properties: Object.freeze({detail: Object.freeze({type: 'string', default: 'high'})})}),
        ports: Object.freeze({inputs: Object.freeze([{id: 'image', accepts: Object.freeze(['asset.image']), required: true}]), outputs: Object.freeze([{id: 'observations', produces: Object.freeze(['artifact.file'])}])}),
        capability_requirements: Object.freeze([{id: 'vision.analysis', version: '1'}]),
        prompt: Object.freeze({prompt_id: 'common.image-analysis.prompt', version: 1}),
    });

    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

    function refOf(definition) {
        return Object.freeze({type: 'skill', id: definition.id, version: definition.version});
    }

    function register(registry) {
        if (!registry || typeof registry.register !== 'function') throw new TypeError('Image-analysis proof requires a Skill registry');
        const existing = typeof registry.resolve === 'function' ? registry.resolve(DEFINITION.id, DEFINITION.version) : null;
        if (!existing) registry.register(clone(DEFINITION));
        return DEFINITION;
    }

    function create(options) {
        const settings = options || {};
        const registry = settings.registry;
        const task = settings.task;
        if (!task || typeof task.update !== 'function' || typeof task.snapshot !== 'function') throw new TypeError('Image-analysis proof requires a Task Rich Node');
        const definition = register(registry);

        function snapshot() {
            const fields = task.snapshot().fields || {};
            const inputs = Array.isArray(fields.inputs) ? fields.inputs : [];
            const image = inputs.find(input => input && (input.port_id === 'image' || input.port === 'image'));
            return Object.freeze({
                definition_ref: refOf(definition),
                asset: image?.value || image?.asset || null,
                binding: fields.skillBinding || null,
            });
        }

        function configure(options = {}) {
            const asset = options.asset;
            const prompt = options.prompt;
            if (!asset || asset.type !== 'asset_version' || !String(asset.id || '').trim()) throw new TypeError('Image-analysis proof requires an AssetVersion reference');
            if (!prompt || !String(prompt.prompt_id || '').trim() || !Number.isInteger(Number(prompt.version)) || Number(prompt.version) < 1) throw new TypeError('Image-analysis proof requires a versioned Prompt reference');
            task.update({
                definition: clone(definition), skill: definition.id,
                inputs: [{port_id: 'image', value: clone(asset)}],
                skillBinding: {skill_id: definition.id, version: definition.version, enabled: true, parameters: {detail: 'high'}, prompt_override: clone(prompt), execution_profile_ref: null},
            });
            return snapshot();
        }

        return Object.freeze({definition, snapshot, configure});
    }

    global.WorkbenchCommonImageAnalysisConfiguration = Object.freeze({create, definition: DEFINITION});
}(window));
