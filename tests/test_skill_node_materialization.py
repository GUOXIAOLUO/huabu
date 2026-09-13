import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillNodeMaterializationTests(unittest.TestCase):
    def test_materializer_delegates_canonical_skill_creation_command(self):
        module = ROOT / "static/js/workbench/canvas/skill-node-materializer.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const calls=[]; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const definition={{id:'common.summary',version:'1.2.0'}};
const api=sandbox.window.WorkbenchSkillNodeMaterializer.create({{createNode:command=>{{calls.push(command); return {{node:{{kind:'skill',definition_ref:command.definition_ref}}}};}}}});
const result=api.materialize({{definition,binding:{{skill_id:'common.summary',version:'1.2.0',parameters:{{tone:'brief'}}}},request_id:'req-1',actor_id:'user-1',project_id:'project-1',canvas_id:'canvas-1',position:{{x:12,y:24}},expected_revision:3,title:'Summary node'}});
console.log(JSON.stringify({{result,calls}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        command = payload["calls"][0]
        self.assertEqual(command["source"], "skill_library_drag")
        self.assertEqual(command["definition_ref"], {"type": "skill", "id": "common.summary", "version": "1.2.0"})
        self.assertEqual(command["initial_config"]["skill_binding"]["parameters"], {"tone": "brief"})
        self.assertEqual(payload["result"]["node"]["kind"], "skill")

    def test_skill_node_renderer_is_optional_generic_and_renders_binding_and_ports(self):
        renderer = ROOT / "static/js/workbench/canvas/skill-node-renderer.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tagName:tag,children:[],dataset:{{}},append(...items){{this.children.push(...items)}},replaceChildren(...items){{this.children=[...items]}},remove(){{this.removed=true}}}}; }}
const documentRef={{createElement:element}}; const host=element('section'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(renderer))},'utf8'),sandbox);
const node={{kind:'skill',title:'Summary node',definition_ref:{{type:'skill',id:'common.summary',version:'1.2.0'}},config:{{skill_binding:{{skill_id:'common.summary',version:'1.2.0'}}}},ports:{{inputs:[{{id:'source'}}],outputs:[{{id:'result'}}]}}}};
const api=sandbox.window.WorkbenchSkillNodeRenderer; const mounted=api.mount({{contentHost:host}},node,{{document:documentRef}});
console.log(JSON.stringify({{can:api.canRender(node),wrong:api.canRender({{kind:'task',definition_ref:node.definition_ref}}),root:mounted.element.className,definition:mounted.element.children[1].dataset,binding:mounted.element.children[2].textContent,inputs:mounted.element.children[3].children.length,outputs:mounted.element.children[4].children.length}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["can"])
        self.assertFalse(payload["wrong"])
        self.assertEqual(payload["root"], "workbench-skill-node-renderer")
        self.assertEqual(payload["definition"], {"definitionId": "common.summary", "definitionVersion": "1.2.0"})
        self.assertIn("common.summary", payload["binding"])
        self.assertEqual(payload["inputs"], 2)
        self.assertEqual(payload["outputs"], 2)

    def test_skill_node_wiring_uses_shared_renderer_registry_and_keeps_binding_embedded(self):
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        materializer = (ROOT / "static/js/workbench/canvas/skill-node-materializer.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchSkillNodeRenderer.canRender(node)", host)
        self.assertIn("id: 'skill-node', version: '1'", host)
        self.assertIn("skill-node-materializer.js", page)
        self.assertIn("skill-node-renderer.js", page)
        self.assertIn("settings.createNode(command(request))", materializer)
        self.assertNotIn("nodes.push", materializer)
        self.assertNotIn("fetch(", materializer)


if __name__ == "__main__":
    unittest.main()
