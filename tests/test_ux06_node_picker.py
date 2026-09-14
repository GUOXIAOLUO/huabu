import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/node-picker.js"
CATALOG = ROOT / "static/js/workbench/canvas/command-registry.js"
STATE = ROOT / "static/js/workbench/canvas/canvas-app-state.js"


class UX06NodePickerTests(unittest.TestCase):
    def test_filter_searches_catalog_metadata_and_respects_category(self):
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
const entries=[
  {{id:'image',definition_ref:{{id:'image',type:'legacy-node',version:'0'}},order:1,metadata:{{title:'上传节点',description:'图片资源',category:'资源',keywords:['图片','上传'],capabilities:['asset'],package:{{id:'core',version:'builtin'}}}}}},
  {{id:'llm',definition_ref:{{id:'llm',type:'legacy-node',version:'0'}},order:2,metadata:{{title:'LLM 节点',description:'处理文本',category:'AI',keywords:['语言模型'],capabilities:['text'],package:{{id:'core',version:'builtin'}}}}}}
].map(sandbox.window.WorkbenchNodePicker.normalize);
const all=sandbox.window.WorkbenchNodePicker.filterEntries(entries,{{query:'语言',category:'all'}}).map(item=>item.id);
const byCapability=sandbox.window.WorkbenchNodePicker.filterEntries(entries,{{query:'asset',category:'资源'}}).map(item=>item.id);
const none=sandbox.window.WorkbenchNodePicker.filterEntries(entries,{{query:'语言',category:'资源'}}).map(item=>item.id);
console.log(JSON.stringify({{all,byCapability,none}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"all": ["llm"], "byCapability": ["image"], "none": []})

    def test_picker_projects_catalog_entries_and_emits_selected_definition(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
const makeClassList=()=>({{add(){{}},remove(){{}},toggle(){{}}}});
const makeElement=tag=>({{tagName:tag,children:[],dataset:{{}},style:{{}},classList:makeClassList(),listeners:{{}},textContent:'',appendChild(child){{this.children.push(child);}},replaceChildren(){{this.children=[];}},setAttribute(name,value){{this[name]=value;}},addEventListener(type,cb){{this.listeners[type]=cb;}}}});
const documentRef={{createElement:tag=>makeElement(tag)}}; const container=makeElement('div'); let selected=null; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
const picker=sandbox.window.WorkbenchNodePicker;
const entry={{id:'canvas.create.prompt',definition_ref:{{id:'prompt',type:'legacy-node',version:'0'}},order:1,metadata:{{title:'提示词',description:'编写提示词',category:'AI',keywords:['prompt'],capabilities:['text'],package:{{id:'core',version:'builtin'}}}}}};
const instance=picker.create({{document:documentRef,container,entries:[entry],onSelect:item=>{{selected=item.id;}}}});
const result=instance.open({{x:12,y:24}}); const panel=container.children[0]; const item=panel.children[2].children[0]; item.listeners.click({{preventDefault(){{}}}});
console.log(JSON.stringify({{result,selected,itemLabel:item['aria-label']}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"]["visible"], ["canvas.create.prompt"])
        self.assertEqual(payload["selected"], "canvas.create.prompt")
        self.assertEqual(payload["itemLabel"], "提示词")

    def test_catalog_exposes_picker_metadata_without_new_creation_owner(self):
        source = CATALOG.read_text(encoding="utf-8")
        picker_source = MODULE.read_text(encoding="utf-8")
        state_source = STATE.read_text(encoding="utf-8")
        for field in ("title", "description", "keywords", "category", "capabilities", "package"):
            self.assertIn(field, source)
            self.assertIn(field, picker_source)
        records_source = (ROOT / "static/js/workbench/canvas/canvas-app-records.js").read_text(encoding="utf-8")
        media_editor_source = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("createClassicMenuNode", media_editor_source)
        self.assertIn("nodePickerCatalogFor('classic')", records_source)
        revision_block = state_source[state_source.index("function currentCanvasRevision"):state_source.index("function adoptCanvasRevision")]
        self.assertIn("canvasNodeRevision", revision_block)
        self.assertNotIn("ensureCanvasSession().adoptRevision", state_source[state_source.index("function adoptCanvasRevision"):state_source.index("let models")])
        self.assertIn("canvasNodeRevision = Number(record?.updated_at", (ROOT / "static/js/workbench/canvas/canvas-app-records.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
