/* Optional Skill-node materialization command. Persistence and graph mutation
   stay behind the injected canonical NodeCreationService/client callback. */
(function exposeWorkbenchSkillNodeMaterializer(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

    function definitionRef(definition) {
        if (!definition || !text(definition.id) || !text(definition.version)) throw new TypeError('Skill materialization requires a versioned SkillDefinition');
        return Object.freeze({type: 'skill', id: text(definition.id), version: text(definition.version)});
    }

    function command(options) {
        const settings = options || {};
        const ref = definitionRef(settings.definition || settings.definition_ref);
        if (!text(settings.request_id) || !text(settings.actor_id) || !text(settings.project_id) || !text(settings.canvas_id)) {
            throw new TypeError('Skill materialization requires request, actor, project, and canvas identifiers');
        }
        if (!settings.position || !Number.isFinite(Number(settings.position.x)) || !Number.isFinite(Number(settings.position.y))) {
            throw new TypeError('Skill materialization requires a finite position');
        }
        const binding = settings.binding && typeof settings.binding === 'object' ? clone(settings.binding) : null;
        return Object.freeze({
            request_id: text(settings.request_id), actor_id: text(settings.actor_id),
            project_id: text(settings.project_id), canvas_id: text(settings.canvas_id),
            source: 'skill_library_drag', definition_ref: ref,
            position: {x: Number(settings.position.x), y: Number(settings.position.y)},
            expected_revision: settings.expected_revision == null ? null : Number(settings.expected_revision),
            title: settings.title == null ? null : text(settings.title),
            initial_config: binding ? {skill_binding: binding} : {},
        });
    }

    function create(options) {
        const settings = options || {};
        if (typeof settings.createNode !== 'function') throw new TypeError('Skill materializer requires the canonical createNode callback');
        function materialize(request) { return settings.createNode(command(request)); }
        return Object.freeze({materialize, command});
    }

    global.WorkbenchSkillNodeMaterializer = Object.freeze({create, command, definitionRef});
}(window));
