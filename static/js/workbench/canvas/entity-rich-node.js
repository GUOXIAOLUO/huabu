/* Generic Entity Rich Node presentation. Entity definitions and version truth
   come from the Workbench services; this module only renders and emits edit
   intents, so it never persists entity data or embeds industry fields. */
(function exposeWorkbenchEntityRichNode(global) {
    'use strict';

    const PRESENTATIONS = Object.freeze(['card', 'expanded', 'workspace', 'inspector']);

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function entityOf(node) {
        return node?.entity_record || node?.entity || node?.record || node?.config?.entity || node || {};
    }

    function definitionOf(node) {
        const entity = entityOf(node);
        return node?.entity_definition || node?.definition || entity?.definition || node?.definition_snapshot || null;
    }

    function propertiesOf(entity) {
        const version = entity?.current_version || entity?.currentVersion || entity?.version || {};
        const payload = version.payload || {};
        const properties = entity?.properties || payload.properties || {};
        return properties && typeof properties === 'object' ? properties : {};
    }

    function fieldDefinitions(definition) {
        const schema = definition?.schema || {};
        const properties = schema.properties || definition?.properties || [];
        if (Array.isArray(properties)) return properties.filter(item => item && typeof item === 'object');
        if (!properties || typeof properties !== 'object') return [];
        return Object.keys(properties).sort().map(key => ({key, ...properties[key]}));
    }

    function currentVersionId(entity) {
        const version = entity?.current_version || entity?.currentVersion || entity?.version || {};
        return text(entity?.current_version_id || entity?.currentVersionId || version.id);
    }

    function compatible(node) {
        return Boolean(node && typeof node === 'object' && (node.kind === 'entity' || node.type === 'entity'));
    }

    function formatValue(value) {
        if (value == null || value === '') return '—';
        if (typeof value === 'object') {
            try { return JSON.stringify(value); } catch (_) { return '[复杂值]'; }
        }
        return String(value);
    }

    function create(options) {
        const settings = options || {};
        const node = settings.node;
        if (!compatible(node)) throw new TypeError('EntityRichNode requires an entity NodeRecord');
        const entity = entityOf(node);
        const definition = definitionOf(node) || {};
        const presentation = settings.presentation || global.WorkbenchPresentationState?.create({
            initial: settings.presentationState,
            storage: settings.storage,
            storageKey: settings.storageKey || `workbench.entity.presentation:${text(node.id, 'unknown')}`,
            onChange: settings.onChange,
        });
        if (!presentation || typeof presentation.state !== 'function' || typeof presentation.transition !== 'function') {
            throw new Error('EntityRichNode requires WorkbenchPresentationState');
        }
        const fields = Object.freeze(fieldDefinitions(definition).map(field => Object.freeze({
            key: text(field.key || field.id || field.name),
            label: text(field.label || field.title || field.name || field.key || field.id, 'Field'),
            type: text(field.type || field.value_type, 'string'),
        })).filter(field => field.key));
        const relations = Object.freeze((Array.isArray(node.relations) ? node.relations : []).map(relation => Object.freeze({
            id: text(relation.id, 'relation'),
            type: text(relation.relation_type || relation.type, 'relation'),
            target: text(relation.to?.resource_id || relation.from?.resource_id || relation.target_id, '—'),
        })));
        function snapshot() {
            return Object.freeze({
                nodeId: text(node.id), title: text(node.title || entity.name, 'Entity'),
                definitionId: text(definition.id || definition.definition_id),
                definitionVersion: text(definition.version), presentation: presentation.state(),
                versionId: currentVersionId(entity), fields, properties: propertiesOf(entity), relations,
            });
        }
        function edit(key, value) {
            const snap = snapshot();
            const detail = Object.freeze({
                entityId: text(entity.id || node.entity_id || node.id),
                baseVersionId: snap.versionId || null,
                definitionId: snap.definitionId || null,
                definitionVersion: snap.definitionVersion || null,
                property: text(key), value,
            });
            if (typeof settings.onEdit === 'function') settings.onEdit(detail);
            return detail;
        }
        return Object.freeze({
            presentations: PRESENTATIONS, snapshot, state: presentation.state,
            canTransition: presentation.canTransition,
            transition: next => { presentation.transition(next); return snapshot(); }, edit,
        });
    }

    function mount(shell, node, options) {
        if (!shell?.contentHost || !compatible(node)) throw new TypeError('EntityRichNode requires a shell content host');
        const settings = options || {};
        const rich = settings.richNode || create({node, ...settings, presentation: settings.presentation || shell.entityRichNode});
        const documentRef = settings.document || shell.contentHost.ownerDocument || global.document;
        const root = documentRef.createElement('section');
        root.className = 'workbench-entity-rich-node';
        const render = () => {
            root.replaceChildren();
            const snap = rich.snapshot();
            root.dataset.presentation = snap.presentation;
            root.dataset.definitionId = snap.definitionId;
            root.dataset.versionId = snap.versionId;
            const identity = documentRef.createElement('div');
            identity.className = 'workbench-entity-rich-node__identity';
            identity.textContent = `${snap.definitionId || 'Entity'}${snap.definitionVersion ? ` · ${snap.definitionVersion}` : ''}${snap.versionId ? ` · 版本 ${snap.versionId}` : ''}`;
            root.append(identity);
            const fields = documentRef.createElement('dl');
            fields.className = 'workbench-entity-rich-node__fields';
            snap.fields.forEach(field => {
                const label = documentRef.createElement('dt'); label.textContent = field.label; label.dataset.fieldKey = field.key;
                const value = documentRef.createElement('dd'); value.dataset.fieldKey = field.key;
                if (snap.presentation === 'inspector') {
                    const input = documentRef.createElement('input'); input.type = field.type === 'number' ? 'number' : 'text';
                    input.value = formatValue(snap.properties[field.key] ?? ''); input.dataset.fieldKey = field.key;
                    input.addEventListener('change', event => rich.edit(field.key, event.target.value)); value.append(input);
                } else value.textContent = formatValue(snap.properties[field.key]);
                fields.append(label, value);
            });
            root.append(fields);
            if (snap.relations.length) {
                const relationSection = documentRef.createElement('section'); relationSection.className = 'workbench-entity-rich-node__relations';
                const heading = documentRef.createElement('h4'); heading.textContent = '关系'; relationSection.append(heading);
                const list = documentRef.createElement('ul'); snap.relations.forEach(relation => { const item = documentRef.createElement('li'); item.textContent = `${relation.type} · ${relation.target}`; item.dataset.relationId = relation.id; list.append(item); });
                relationSection.append(list); root.append(relationSection);
            }
            const editButton = documentRef.createElement('button'); editButton.type = 'button'; editButton.textContent = snap.presentation === 'inspector' ? '完成编辑' : '编辑实体'; editButton.dataset.intent = 'edit-entity';
            editButton.addEventListener('click', event => { event.stopPropagation(); rich.transition(snap.presentation === 'inspector' ? 'card' : 'inspector'); render(); }); root.append(editButton);
        };
        render(); shell.contentHost.replaceChildren(root);
        return Object.freeze({element: root, richNode: rich, destroy: () => root.remove()});
    }

    global.WorkbenchEntityRichNode = Object.freeze({PRESENTATIONS, entityOf, definitionOf, fieldDefinitions, compatible, create, mount});
}(window));
