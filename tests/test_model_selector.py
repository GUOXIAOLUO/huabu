import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ModelSelectorTests(unittest.TestCase):
    def test_task_model_selector_is_wired_through_the_production_node_card_boundary(self):
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        task = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("modelSelectorOptions", host)
        self.assertIn("modelAvailabilities", host)
        self.assertIn("capabilityRequirements", host)
        self.assertIn("data-task-model-selector-host", shell)
        self.assertIn("mountModelSelector", shell)
        self.assertIn("modelSelection", task)
        self.assertIn("/static/js/workbench/canvas/model-selector.js", page)

    def test_selector_exposes_auto_resolved_route_and_explicit_unavailable_reasons(self):
        selector = ROOT / "static/js/workbench/canvas/model-selector.js"
        task = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tagName:tag,children:[],dataset:{{}},append(...items){{this.children.push(...items)}},replaceChildren(...items){{this.children=[...items]}},addEventListener(name,fn){{this[name]=fn}},remove(){{this.removed=true}},setAttribute(){{}}}}; }}
const values={{}}; const storage={{getItem:key=>values[key]||null,setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(selector))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(task))},'utf8'),sandbox);
const node=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}},storage}});
const routes=[
  {{id:'runtime-route',model_ref:'model-x',route_type:'runtime',route_ref:'codex',executor_type:'codex_harness',normalized_capabilities:['vision','reasoning'],enabled:true,status:'available'}},
  {{id:'disabled-route',model_ref:'model-x',route_type:'provider',route_ref:'api',executor_type:'model_api',normalized_capabilities:['vision'],enabled:false,status:'available'}}
];
const picker=sandbox.window.WorkbenchModelSelector.create({{task:{{update:patch=>node.update(patch)}},requirements:[{{id:'vision'}},'reasoning'],availabilities:routes}});
const initial=picker.snapshot(); const explicit=picker.select('runtime-route'); const host=element('section');
const mounted=picker.mount(host,{{document:{{createElement:element}}}});
console.log(JSON.stringify({{auto:initial.resolved.id,disabled:initial.entries[1].reasons,explicit:explicit.selection,task:node.snapshot().fields.modelSelection,resolved:explicit.resolved.id,root:mounted.element.className,options:mounted.element.children[0].children[0].children.length}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["auto"], "runtime-route")
        self.assertIn("route_disabled", payload["disabled"])
        self.assertEqual(payload["explicit"], {"mode": "explicit", "availabilityId": "runtime-route"})
        self.assertEqual(payload["task"]["selection"]["availabilityId"], "runtime-route")
        self.assertEqual(payload["resolved"], "runtime-route")
        self.assertEqual(payload["root"], "workbench-model-selector")
        self.assertEqual(payload["options"], 3)

    def test_selector_does_not_render_credentials_or_change_skill_binding(self):
        selector = ROOT / "static/js/workbench/canvas/model-selector.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(selector))},'utf8'),sandbox);
const picker=sandbox.window.WorkbenchModelSelector.create({{requirements:['text'],availabilities:[{{id:'a',model_ref:'m',route_type:'provider',route_ref:'r',executor_type:'api',normalized_capabilities:['text'],status:'available',native_metadata:{{apiKey:'hidden'}}}}]}});
const view=picker.snapshot(); console.log(JSON.stringify({{resolved:view.resolved,serialized:JSON.stringify(view),hasCredential:Object.prototype.hasOwnProperty.call(view,'credential_ref')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["resolved"]["id"], "a")
        self.assertNotIn("credential_ref", payload["serialized"])
        self.assertNotIn("hidden", payload["serialized"])
        self.assertFalse(payload["hasCredential"])


if __name__ == "__main__":
    unittest.main()
