import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL_MODULE = ROOT / "static/js/workbench/canvas/resource-library-shell.js"
PAGE_JS = ROOT / "static/js/asset-manager.js"
PAGE_HTML = ROOT / "static/asset-manager.html"
STUDIO_HTML = ROOT / "static/index.html"


def page_category_definitions():
    """Read the page's real registry seed so the shell tests are page-driven."""
    source = PAGE_JS.read_text(encoding="utf-8")
    match = re.search(r"const RESOURCE_CATEGORY_DEFINITIONS = (\[.*?\n\]);", source, re.S)
    assert match, "RESOURCE_CATEGORY_DEFINITIONS not found in asset-manager.js"
    return match.group(1)


class ResourceLibraryShellTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_registry_is_extensible_ordered_and_rejects_bad_descriptors(self):
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(SHELL_MODULE))}, 'utf8'), sandbox);
const S = sandbox.window.WorkbenchResourceLibraryShell;
const definitions = {page_category_definitions()};
const registry = S.createRegistry(definitions);
const added = registry.register({{id:'catalog-probe', kind:'catalog', label:'目录探针', surface:'library', tab:'catalog-probe', order:5}});
const failures = [];
function capture(fn) {{ try {{ fn(); return null; }} catch (error) {{ return String(error.message); }} }}
failures.push(capture(() => registry.register({{id:'assets', kind:'asset', label:'dup', surface:'library'}})));
failures.push(capture(() => registry.register({{id:'x', kind:'asset', label:'x', surface:'holo'}})));
failures.push(capture(() => registry.register({{id:'y', kind:'unknown-kind', label:'y', surface:'library'}})));
failures.push(capture(() => registry.register({{id:'z', kind:'asset', surface:'library'}})));
failures.push(capture(() => S.createShell({{registry:{{}}}})));
console.log(JSON.stringify({{
  ids: registry.ids(),
  first: registry.list()[0].id,
  kinds: registry.kinds(),
  added: added.id,
  size: registry.size(),
  library: registry.bySurface('library').map(item => item.id),
  canvas: registry.bySurface('canvas').map(item => item.id),
  get: registry.get('collections'),
  missing: registry.get('nope'),
  failures,
}}));
"""
        actual = self.run_node(script)
        self.assertEqual(actual["ids"][0], "catalog-probe", "registry order must honour descriptor order")
        self.assertEqual(actual["first"], "catalog-probe")
        self.assertEqual(actual["added"], "catalog-probe")
        self.assertEqual(actual["size"], len(actual["ids"]))
        self.assertIn("asset", actual["kinds"])
        self.assertIn("collection", actual["kinds"])
        self.assertIn("prompt", actual["kinds"])
        self.assertIn("skill", actual["kinds"])
        self.assertIn("workflow", actual["kinds"])
        self.assertIn("collections", actual["canvas"])
        self.assertIn("skills", actual["canvas"])
        self.assertIn("assets", actual["library"])
        self.assertEqual(actual["get"]["surface"], "canvas")
        self.assertEqual(actual["get"]["entry"], "canvas-list")
        self.assertIsNone(actual["missing"])
        self.assertIn("already registered", actual["failures"][0])
        self.assertIn("Unsupported resource surface", actual["failures"][1])
        self.assertIn("Unsupported resource kind", actual["failures"][2])
        self.assertIn("Resource category label (z) is required", actual["failures"][3])
        self.assertIn("requires a resource registry", actual["failures"][4])

    def test_shell_renders_category_rail_unified_search_and_kind_filter(self):
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(SHELL_MODULE))}, 'utf8'), sandbox);
const S = sandbox.window.WorkbenchResourceLibraryShell;
const escapeHtml = value => String(value ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const registry = S.createRegistry({page_category_definitions()});
const shell = S.createShell({{registry, escapeHtml, escapeAttr:escapeHtml}});
const beforeSelection = shell.render();
shell.setCategory('prompts');
shell.setQuery('风景');
const html = shell.render();
console.log(JSON.stringify({{
  beforeSelectionHasActive: beforeSelection.includes('resource-cat active'),
  beforeSelectionHasSearch: beforeSelection.includes('id="resourceShellSearch"'),
  hasRail: html.includes('class="resource-shell-rail asset-tabs"'),
  hasSearch: html.includes('id="resourceShellSearch"'),
  hasFilters: html.includes('class="resource-filters"'),
  searchValue: html.includes('value="风景"'),
  searchCategory: html.includes('data-resource-search-category="prompts"'),
  activeCategory: (html.match(/resource-cat active"[^>]*data-resource-category="([^"]+)"/) || [])[1] || null,
  categories: [...html.matchAll(/data-resource-category="([^"]+)"/g)].map(match => match[1]),
  tabs: [...html.matchAll(/data-resource-category="([^"]+)"[^>]*data-tab="([^"]+)"/g)].map(match => match[1]),
  entries: [...html.matchAll(/data-resource-category="([^"]+)"[^>]*data-resource-entry="([^"]+)"/g)].map(match => match[1]),
  entryTargets: [...html.matchAll(/data-resource-category="([^"]+)"[^>]*data-resource-entry="([^"]+)"/g)].map(match => match[2]),
  chips: [...html.matchAll(/data-resource-kind-filter="([^"]+)"/g)].map(match => match[1]),
  chipPressed: html.includes('data-resource-kind-filter="prompt" aria-pressed="false"'),
  escapeApplied: !html.includes('<script'),
}}));
"""
        actual = self.run_node(script)
        self.assertFalse(actual["beforeSelectionHasActive"], "no category may be marked active before the host selects one")
        self.assertFalse(actual["beforeSelectionHasSearch"], "no search control may render before the host selects a category")
        self.assertTrue(actual["hasRail"])
        self.assertTrue(actual["hasSearch"])
        self.assertTrue(actual["hasFilters"])
        self.assertTrue(actual["searchValue"])
        self.assertTrue(actual["searchCategory"])
        self.assertEqual(actual["activeCategory"], "prompts")
        self.assertIn("assets", actual["categories"])
        self.assertIn("collections", actual["categories"])
        self.assertIn("prompts", actual["categories"])
        self.assertIn("skills", actual["categories"])
        self.assertIn("assets", actual["tabs"])
        self.assertIn("prompts", actual["tabs"])
        self.assertNotIn("collections", actual["tabs"], "canvas-surface categories must not be tabs")
        self.assertNotIn("skills", actual["tabs"], "canvas-surface categories must not be tabs")
        self.assertEqual(actual["entries"], ["collections", "skills"])
        self.assertEqual(set(actual["entryTargets"]), {"canvas-list"})
        self.assertIn("asset", actual["chips"])
        self.assertIn("collection", actual["chips"])
        self.assertIn("skill", actual["chips"])
        self.assertTrue(actual["chipPressed"])
        self.assertTrue(actual["escapeApplied"])

    def test_shell_kind_filter_projects_the_category_rail_and_toggles_off(self):
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(SHELL_MODULE))}, 'utf8'), sandbox);
const S = sandbox.window.WorkbenchResourceLibraryShell;
const escapeHtml = value => String(value ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const registry = S.createRegistry({page_category_definitions()});
const shell = S.createShell({{registry, escapeHtml, escapeAttr:escapeHtml}});
const all = shell.visibleCategories().map(item => item.id);
const on = shell.setKindFilter('collection');
const collectionVisible = shell.visibleCategories().map(item => item.id);
const html = shell.render();
/* the active category stays on the rail so the rail cannot contradict the body */
shell.setCategory('prompts');
const pinnedVisible = shell.visibleCategories().map(item => item.id);
const promptsMatches = shell.matches(registry.get('prompts'));
const collectionsMatches = shell.matches(registry.get('collections'));
const pinnedHtml = shell.render();
const off = shell.setKindFilter('collection');
const backToAll = shell.visibleCategories().map(item => item.id);
let unknown = null;
try {{ shell.setKindFilter('nope'); }} catch (error) {{ unknown = String(error.message); }}
let badCategory = null;
try {{ shell.setCategory('nope'); }} catch (error) {{ badCategory = String(error.message); }}
console.log(JSON.stringify({{all, on, collectionVisible, pinnedVisible, promptsMatches, collectionsMatches,
  off, backToAll, unknown, badCategory,
  htmlCategories: [...html.matchAll(/data-resource-category="([^"]+)"/g)].map(match => match[1]),
  pinnedCategories: [...pinnedHtml.matchAll(/data-resource-category="([^"]+)"/g)].map(match => match[1]),
  pinnedSearchCategory: pinnedHtml.includes('data-resource-search-category="prompts"'),
  pressed: html.includes('data-resource-kind-filter="collection" aria-pressed="true"'),
}}));
"""
        actual = self.run_node(script)
        self.assertGreater(len(actual["all"]), 2)
        self.assertEqual(actual["on"], "collection")
        self.assertEqual(actual["collectionVisible"], ["collections"])
        self.assertEqual(actual["htmlCategories"], ["collections"])
        self.assertTrue(actual["pressed"])
        self.assertFalse(actual["promptsMatches"], "matches() must be the pure kind test")
        self.assertTrue(actual["collectionsMatches"])
        self.assertEqual(set(actual["pinnedVisible"]), {"collections", "prompts"})
        self.assertEqual(set(actual["pinnedCategories"]), {"collections", "prompts"})
        self.assertTrue(actual["pinnedSearchCategory"], "the pinned active category keeps its search control")
        self.assertEqual(actual["off"], "")
        self.assertEqual(actual["backToAll"], actual["all"])
        self.assertIn("Unknown resource kind filter", actual["unknown"])
        self.assertIn("Unknown resource category", actual["badCategory"])

    def test_asset_manager_mounts_the_shell_as_the_single_resources_section(self):
        page = PAGE_JS.read_text(encoding="utf-8")
        html = PAGE_HTML.read_text(encoding="utf-8")

        self.assertIn('<div id="resourceLibraryShell" class="resource-shell"', html)
        self.assertNotIn('id="assetTabAssets"', html, "the static tab markup must be replaced by the registry rail")
        self.assertIn("resource-library-shell.js", html)
        self.assertLess(
            html.index("resource-library-shell.js"),
            html.index("asset-manager.js"),
            "the shell module must load before the page script",
        )

        self.assertIn("const resourceShellEl = document.getElementById('resourceLibraryShell');", page)
        self.assertIn("window.WorkbenchResourceLibraryShell.createRegistry(RESOURCE_CATEGORY_DEFINITIONS)", page)
        self.assertIn("window.WorkbenchResourceLibraryShell.createShell({", page)
        for kind in ("kind:'asset'", "kind:'prompt'", "kind:'collection'", "kind:'skill'"):
            self.assertIn(kind, page, f"the four canonical resource kinds must be registered ({kind})")
        self.assertIn("{id:'knowledge', kind:'knowledge'", page)
        self.assertIn("tab:'knowledge', searchId:'knowledgeSearch'", page)
        self.assertIn("/api/v1/knowledge-entries/search?", page)
        self.assertIn("function renderKnowledgeManager()", page)
        self.assertIn("entry.source_refs", page)
        self.assertIn("entry.scope", page)
        self.assertIn("surface:'canvas', entry:'canvas-list'", page)
        self.assertIn("function openResourceCategory(id){", page)
        self.assertIn("function openResourceCanvasSurface(descriptor){", page)
        self.assertIn("function applyResourceShellQuery(value){", page)
        self.assertIn("function syncResourceShell(){", page)
        self.assertIn("syncResourceShell();", page)
        self.assertIn("resourceShellEl?.addEventListener('click'", page)
        self.assertIn("resourceCategory.dataset.resourceSurface === 'canvas'", page)
        self.assertNotIn(
            "document.querySelectorAll('[data-tab]').forEach",
            page,
            "the load-time static tab binding is dead once the rail is registry-rendered",
        )

    def test_resources_stay_under_one_top_level_section_and_canvas_entries_route_out(self):
        page = PAGE_JS.read_text(encoding="utf-8")
        studio = STUDIO_HTML.read_text(encoding="utf-8")

        self.assertIn("window.parent.postMessage({type:'studio-switch-page'", page)
        self.assertIn("event.data.type === 'studio-switch-page'", studio)
        self.assertIn("PAGE_IDS.includes(event.data.page)", studio)
        self.assertIn("switchUI(document.querySelector(`[onclick*=\"'${event.data.page}'\"]`), event.data.page);", studio)

        nav_items = re.findall(r'<div class="nav-item[^"]*" onclick="switchUI\(this, \'([^\']+)\'\)', studio)
        self.assertEqual(
            nav_items,
            ["zimage", "enhance", "klein", "angle", "online", "gpt-chat", "canvas", "asset-manager"],
            "no new top-level navigation entry may be added for resources",
        )
        page_ids = re.search(r"const PAGE_IDS = \[(.*?)\];", studio, re.S).group(1)
        self.assertEqual(
            [item.strip().strip("'") for item in page_ids.split(",")],
            ["zimage", "enhance", "klein", "angle", "online", "gpt-chat", "canvas", "asset-manager", "api-settings", "comfyui-settings"],
        )

    def test_resource_library_shell_script_is_valid_javascript(self):
        for path in (SHELL_MODULE, PAGE_JS):
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
