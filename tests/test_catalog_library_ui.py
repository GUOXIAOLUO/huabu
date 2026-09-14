import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/catalog-library.js"
PAGE = ROOT / "static/js/asset-manager.js"
HTML = ROOT / "static/asset-manager.html"


class CatalogLibraryUiTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_catalog_presentation_filters_attributes_and_builds_reference_drag_payload(self):
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))}, 'utf8'), sandbox);
const C = sandbox.window.WorkbenchCatalogLibrary;
const catalog = {{id:'catalog-1', name:'通用目录', scope:'workspace', item_ids:['item-1'], schema:{{attributes:[{{key:'sku', label:'SKU', value_type:'text'}}]}}}};
const item = {{id:'item-1', catalog_id:'catalog-1', title:'Chair', version_ids:['version-1'], current_version_id:'version-1', attributes:{{sku:'C-1'}}}};
const version = {{id:'version-1', item_id:'item-1', ordinal:1, attributes:{{sku:'C-1'}}, media_refs:[]}};
const esc = value => String(value ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const html = C.render({{catalogs:[catalog], items:[item], versions:[version], query:'chair', attributeKey:'sku', selectedCatalogId:'catalog-1', selectedItemId:'item-1', selectedItem:item, selectedVersionId:'version-1', selectedVersion:version}}, {{escapeHtml:esc}});
console.log(JSON.stringify({{matches:C.filterItems([item], 'chair', 'sku').length, noMatch:C.filterItems([item], 'table', '').length, payload:C.dragPayload(catalog,item,version), hasCatalog:html.includes('通用目录'), hasItem:html.includes('Chair'), hasFilter:html.includes('data-catalog-attribute-filter=\"sku\"'), draggable:html.includes('draggable=\"true\"')}}));
"""
        actual = self.run_node(script)
        self.assertEqual(actual["matches"], 1)
        self.assertEqual(actual["noMatch"], 0)
        self.assertEqual(actual["payload"]["type"], "catalog_item_version")
        self.assertTrue(actual["payload"]["reference_only"])
        self.assertEqual(actual["payload"]["version_id"], "version-1")
        self.assertTrue(actual["hasCatalog"])
        self.assertTrue(actual["hasItem"])
        self.assertTrue(actual["hasFilter"])
        self.assertTrue(actual["draggable"])

    def test_resource_page_registers_catalog_surface_and_wires_canonical_api(self):
        page = PAGE.read_text(encoding="utf-8")
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("id:'catalogs', kind:'catalog', label:'目录', surface:'library'", page)
        self.assertIn("searchId:'catalogSearch'", page)
        self.assertIn("/api/v1/catalogs?workspace_id=local", page)
        self.assertIn("/api/v1/catalogs/${encodeURIComponent(catalogId)}/items", page)
        self.assertIn("catalog-item-version+json", page)
        self.assertIn("catalog-library.js", html)
        self.assertLess(html.index("catalog-library.js"), html.index("asset-manager.js"))


if __name__ == "__main__":
    unittest.main()
