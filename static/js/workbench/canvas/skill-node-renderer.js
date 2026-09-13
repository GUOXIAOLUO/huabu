/* Optional, renderer-only view for a materialized generic Skill Node. It does
   not execute Skills or own definition/binding persistence. */
(function exposeWorkbenchSkillNodeRenderer(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function canRender(node) {
        return Boolean(node && node.kind === 'skill' && node.definition_ref
            && node.definition_ref.type === 'skill');
    }

    function bindingOf(node) {
        const config = node?.config && typeof node.config === 'object' ? node.config : {};
        return config.skill_binding && typeof config.skill_binding === 'object' ? config.skill_binding : null;
    }

    function mount(shell, node, options) {
        if (!shell?.contentHost || !canRender(node)) throw new TypeError('SkillNodeRenderer requires a generic Skill Node and content host');
        const documentRef = options?.document || shell.contentHost.ownerDocument || global.document;
        if (!documentRef?.createElement) throw new TypeError('SkillNodeRenderer requires a document');
        const root = documentRef.createElement('section'); root.className = 'workbench-skill-node-renderer';
        const heading = documentRef.createElement('h3'); heading.textContent = text(node.title, node.definition_ref.id); root.append(heading);
        const ref = documentRef.createElement('div'); ref.className = 'workbench-skill-node-renderer__definition';
        ref.dataset.definitionId = node.definition_ref.id; ref.dataset.definitionVersion = node.definition_ref.version;
        ref.textContent = `Skill · ${node.definition_ref.id} · ${node.definition_ref.version}`; root.append(ref);
        const binding = bindingOf(node);
        if (binding) {
            const detail = documentRef.createElement('div'); detail.className = 'workbench-skill-node-renderer__binding';
            detail.textContent = `Binding · ${text(binding.skill_id, node.definition_ref.id)} · ${text(binding.version, node.definition_ref.version)}`; root.append(detail);
        }
        function ports(direction, title, values) {
            if (!values.length) return;
            const section = documentRef.createElement('section'); section.className = `workbench-skill-node-renderer__ports workbench-skill-node-renderer__ports--${direction}`;
            const label = documentRef.createElement('h4'); label.textContent = title; section.append(label);
            values.forEach(port => { const item = documentRef.createElement('div'); item.dataset.portId = text(port.id, direction); item.textContent = text(port.id, direction); section.append(item); });
            root.append(section);
        }
        ports('input', 'Inputs', Array.isArray(node.ports?.inputs) ? node.ports.inputs : []);
        ports('output', 'Outputs', Array.isArray(node.ports?.outputs) ? node.ports.outputs : []);
        shell.contentHost.replaceChildren(root);
        return Object.freeze({element: root, destroy: () => root.remove()});
    }

    global.WorkbenchSkillNodeRenderer = Object.freeze({canRender, bindingOf, mount});
}(window));
