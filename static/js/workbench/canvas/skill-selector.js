/* Generic Task Skill selector. Discovery is injected; Task owns the binding
   state and this module never executes or resolves a provider. */
(function exposeWorkbenchSkillSelector(global) {
    'use strict';

    function text(value, fallback = '') {
        const normalized = String(value ?? '').trim();
        return normalized || fallback;
    }

    function clone(value) {
        return value == null ? value : JSON.parse(JSON.stringify(value));
    }

    function registrationOf(value) {
        const registration = value?.skill && typeof value.skill === 'object' ? value : {skill: value};
        const skill = registration.skill;
        if (!skill || !text(skill.id) || !text(skill.version)) throw new TypeError('SkillSelector requires a versioned Skill');
        return {registration, skill};
    }

    function refOf(skill) {
        if (skill && typeof skill === 'object' && text(skill.skill_id) && text(skill.version)) {
            return {skill_id: text(skill.skill_id), version: text(skill.version)};
        }
        const {skill: definition} = registrationOf(skill);
        return {skill_id: text(definition.id), version: text(definition.version)};
    }

    function create(options) {
        const settings = options || {};
        const registry = settings.registry;
        if (!registry || typeof registry.discover !== 'function') throw new TypeError('SkillSelector requires a discovery registry');
        const task = settings.task || null;
        let recent = Array.isArray(settings.recent) ? settings.recent.map(refOf) : [];
        const recommended = Array.isArray(settings.recommended) ? settings.recommended.map(refOf) : [];

        function key(ref) { return `${ref.skill_id}@${ref.version}`; }
        function uniqueRefs(refs) {
            const seen = new Set();
            return refs.filter(ref => !seen.has(key(ref)) && seen.add(key(ref))).map(clone);
        }
        function discover(query = '') {
            return registry.discover({query: text(query)}).map(registrationOf).map(item => item.registration);
        }
        function all() { return discover(''); }
        function resolveRefs(refs) {
            const byKey = new Map(all().map(item => { const ref = refOf(item); return [key(ref), item]; }));
            return uniqueRefs(refs).map(ref => byKey.get(key(ref))).filter(Boolean);
        }
        function packs() {
            if (typeof registry.list_packs !== 'function') return [];
            return registry.list_packs({enabled: true}).map(pack => clone(pack));
        }
        function snapshot(query = '') {
            return Object.freeze({
                query: text(query),
                results: Object.freeze(discover(query)),
                recent: Object.freeze(resolveRefs(recent)),
                recommended: Object.freeze(resolveRefs(recommended)),
                packs: Object.freeze(packs()),
            });
        }
        function select(skill, overrides = {}) {
            const {skill: definition} = registrationOf(skill);
            const binding = {
                skill_id: text(definition.id), version: text(definition.version),
                enabled: overrides.enabled !== false,
                parameters: clone(overrides.parameters || {}),
                prompt_override: clone(overrides.prompt_override || null),
                execution_profile_ref: overrides.execution_profile_ref == null ? null : text(overrides.execution_profile_ref),
            };
            recent = uniqueRefs([binding, ...recent]).slice(0, Number(settings.recentLimit) > 0 ? Number(settings.recentLimit) : 8);
            if (typeof settings.persistRecent === 'function') settings.persistRecent(clone(recent));
            if (task && typeof task.update === 'function') task.update({skillBinding: clone(binding)});
            if (typeof settings.onSelect === 'function') settings.onSelect(clone(binding), definition);
            return Object.freeze(clone(binding));
        }
        function mount(host, mountOptions = {}) {
            if (!host || typeof host.replaceChildren !== 'function') throw new TypeError('SkillSelector requires a host');
            const documentRef = mountOptions.document || host.ownerDocument || global.document;
            if (!documentRef || typeof documentRef.createElement !== 'function') throw new TypeError('SkillSelector requires a document');
            const root = documentRef.createElement('section');
            root.className = 'workbench-skill-selector';
            const search = documentRef.createElement('input');
            search.type = 'search'; search.className = 'workbench-skill-selector__search';
            search.placeholder = mountOptions.searchLabel || 'Search skills';
            const results = documentRef.createElement('div');
            results.className = 'workbench-skill-selector__results';
            function group(name, items, renderItem) {
                if (!items.length) return;
                const section = documentRef.createElement('section');
                section.className = `workbench-skill-selector__group workbench-skill-selector__group--${name}`;
                const heading = documentRef.createElement('h4'); heading.textContent = name;
                section.append(heading);
                items.forEach(item => section.append(renderItem(item)));
                results.append(section);
            }
            function skillButton(registration) {
                const {skill} = registrationOf(registration);
                const button = documentRef.createElement('button'); button.type = 'button';
                button.className = 'workbench-skill-selector__skill';
                button.dataset.skillId = text(skill.id); button.dataset.skillVersion = text(skill.version);
                button.textContent = `${text(skill.title, skill.id)} · ${text(skill.version)}`;
                button.addEventListener('click', event => { event.preventDefault(); select(registration); render(); });
                return button;
            }
            function render() {
                const view = snapshot(search.value || '');
                results.replaceChildren();
                group('results', view.results, skillButton);
                group('recent', view.recent, skillButton);
                group('recommended', view.recommended, skillButton);
                group('packs', view.packs, pack => {
                    const item = documentRef.createElement('div'); item.className = 'workbench-skill-selector__pack';
                    item.textContent = `${text(pack.pack?.title, pack.title || pack.id)} · ${text(pack.pack?.version, pack.version || '')}`;
                    return item;
                });
            }
            search.addEventListener('input', render);
            root.append(search, results); host.replaceChildren(root); render();
            return Object.freeze({element: root, destroy: () => root.remove()});
        }
        return Object.freeze({snapshot, discover, packs, select, mount, recent: () => Object.freeze(clone(recent.map(refOf)))});
    }

    global.WorkbenchSkillSelector = Object.freeze({create, refOf});
}(window));
