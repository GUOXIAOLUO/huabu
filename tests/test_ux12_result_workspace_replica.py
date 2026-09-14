import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "static/js/workbench/canvas/result-workspace-runtime.js"


class UX12ResultWorkspaceReplicaTests(unittest.TestCase):
    def test_one_workspace_composes_preview_compare_and_selection_without_copying_result_state(self):
        modules = [
            ROOT / "static/js/workbench/canvas/result-preview-runtime.js",
            ROOT / "static/js/workbench/canvas/result-compare-runtime.js",
            ROOT / "static/js/workbench/canvas/result-selection-runtime.js",
            WORKSPACE,
        ]
        loaders = "".join(
            f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))},'utf8'),sandbox);\n"
            for path in modules
        )
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',textContent:'',innerHTML:'',
  append(...items){{this.children.push(...items);}},replaceChildren(...items){{this.children=items; }},setAttribute(name,value){{this.dataset[name]=String(value);}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{}} }}; }}
const documentRef={{createElement:element}},sandbox={{window:{{document:documentRef}},document:documentRef}};
{loaders}
const items=[{{item_id:'result-1',kind:'image',title:'Option A',preview_url:'/a.png',value:{{kind:'image',url:'/a.png'}}}},{{item_id:'result-2',kind:'text',title:'Option B',preview_url:'',value:'caption'}}];
const controller=sandbox.window.WorkbenchCanvasResultWorkspace.create({{document:documentRef,items,compare:{{candidates:items}},selection:{{records:[{{id:'sel-1',attempt_id:'a',output_name:'out',ordinal:0,selected:true,favorite:false,rating:4,comment:'good',revision:1}}]}}}});
const host=element('section'); const mounted=controller.mount(host); const initial=host.children[0];
mounted.setView('preview'); const preview=host.children[0];
mounted.next(); const afterNext=controller.snapshot(); mounted.setView('preview'); const textPreview=host.children[0]; const previewHtml=textPreview.children[1].children[2].innerHTML; mounted.setView('compare'); const compare=host.children[0];
console.log(JSON.stringify({{sameItems:controller.snapshot().itemCount===items.length,initialView:initial.dataset.view,previewView:preview.dataset.view,previewHasText:previewHtml.includes('caption'),afterNext:afterNext.activeItem.item_id,compareView:compare.dataset.view,compareTabs:compare.children[0].children[2].children.map(button=>button.dataset.view),hasCompare:compare.children[1].children.length>0,selectionChild:mounted.children.selection!==null}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "sameItems": True,
            "initialView": "grid",
            "previewView": "preview",
            "previewHasText": True,
            "afterNext": "result-2",
            "compareView": "compare",
            "compareTabs": ["grid", "preview", "compare", "selection", "collection", "materialization"],
            "hasCompare": True,
            "selectionChild": True,
        })

    def test_task_and_canvas_load_the_workspace_through_the_shared_task_shell(self):
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        task = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-workspace-runtime.js"), 1)
        self.assertLess(page.index("result-workspace-runtime.js"), page.index("canvas-app-bootstrap.js"))
        self.assertIn("mountResultWorkspace", task)
        self.assertIn("settings.resultWorkspaceOptions", shell)
        self.assertIn("taskRichNode.mountResultWorkspace(resultWorkspaceHost, settings.resultWorkspaceOptions)", shell)
        self.assertIn("resultWorkspaceOptions: resolvedRendererOptions.resultWorkspaceOptions", host)


if __name__ == "__main__":
    unittest.main()
