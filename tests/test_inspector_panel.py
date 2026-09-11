import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InspectorPanelTests(unittest.TestCase):
    def test_single_and_multi_selection_render_through_one_panel_owner(self):
        module = ROOT / "static/js/workbench/canvas/inspector-panel.js"
        inspector = ROOT / "static/js/workbench/canvas/node-inspector.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tag, children:[], dataset:{{}}, hidden:false, className:'', textContent:'', append(...items){{this.children.push(...items)}}, replaceChildren(...items){{this.children=[...items]}}, setAttribute(){{}}}}; }}
const documentRef={{createElement:element}}; const root=element('aside');
const sandbox={{window:{{}}, document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(inspector))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const panel=sandbox.window.WorkbenchInspectorPanel.create({{document:documentRef,element:root}});
const single=panel.render([{{id:'n1',title:'Node 1',kind:'prompt',state:'ready'}}], {{connections:[]}});
const singleSections=root.children.slice(1).map(item=>item.dataset.inspectorSection);
const multi=panel.render([{{id:'n1',kind:'prompt'}},{{id:'n2',kind:'image'}}]);
const multiSections=root.children.slice(1).map(item=>item.dataset.inspectorSection);
panel.clear();
console.log(JSON.stringify({{singleTitle:single.title,singleSections,multiTitle:multi.title,multiSections,hidden:root.hidden}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "singleTitle": "Node 1",
            "singleSections": ["metadata", "identity", "geometry", "status", "version", "input-output", "history", "execution"],
            "multiTitle": "已选中 2 个节点",
            "multiSections": ["identity", "status", "history", "version", "execution"],
            "hidden": True,
        })

    def test_canvas_binds_selection_to_inspector_panel_and_loads_single_script(self):
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("id=\"canvasInspectorPanel\"", page)
        self.assertIn("/static/js/workbench/canvas/inspector-panel.js", page)
        runtime = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchInspectorPanel.create", runtime)
        self.assertIn("canvasInspectorPanel.render(selectedNodes, {connections})", runtime)

    def test_generic_renderer_can_contribute_a_valid_inspector_section(self):
        module = ROOT / "static/js/workbench/canvas/inspector-panel.js"
        inspector = ROOT / "static/js/workbench/canvas/node-inspector.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tag, children:[], dataset:{{}}, hidden:false, className:'', textContent:'', append(...items){{this.children.push(...items)}}, replaceChildren(...items){{this.children=[...items]}}, setAttribute(){{}}}}; }}
const documentRef={{createElement:element}}; const root=element('aside');
const sandbox={{window:{{}}, document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(inspector))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
sandbox.window.WorkbenchNodeInspector.registerSectionProvider({{id:'generic',version:'1'}}, 'details', node => ({{id:'details', title:'通用详情', fields:[{{id:'label', label:'标签', value:node.label}}]}}));
const panel=sandbox.window.WorkbenchInspectorPanel.create({{document:documentRef,element:root}});
panel.render([{{id:'n1',kind:'generic',label:'保留',renderer:{{id:'generic',version:'1'}}}}]);
console.log(JSON.stringify({{section:root.children.find(item=>item.dataset.inspectorSection==='details')?.children[0]?.textContent || ''}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["section"], "通用详情")


if __name__ == "__main__":
    unittest.main()
