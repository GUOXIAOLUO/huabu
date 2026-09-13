import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommonImageAnalysisConfigurationProofTests(unittest.TestCase):
    def test_asset_task_skill_binding_and_prompt_survive_task_restart(self):
        module = ROOT / "static/js/workbench/canvas/common-image-analysis-proof.js"
        task_module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const values={{}};
const storage={{getItem:key=>values[key]||null,setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(task_module))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const registry={{registered:[],register(definition){{this.registered.push(definition);}},resolve(id,version){{return this.registered.find(item=>item.id===id&&item.version===version)||null;}}}};
const node={{id:'task-1',kind:'task',title:'Image analysis'}};
const firstTask=sandbox.window.WorkbenchTaskRichNode.create({{node,storage}});
const first=sandbox.window.WorkbenchCommonImageAnalysisConfiguration.create({{registry,task:firstTask}});
const configured=first.configure({{asset:{{type:'asset_version',id:'asset-v1'}},prompt:{{prompt_id:'common.image-analysis.prompt',version:2}}}});
const restartedTask=sandbox.window.WorkbenchTaskRichNode.create({{node,storage}});
const reloaded=sandbox.window.WorkbenchCommonImageAnalysisConfiguration.create({{registry,task:restartedTask}}).snapshot();
console.log(JSON.stringify({{registered:registry.registered.map(item=>({{id:item.id,version:item.version}})),configured,reloaded,stored:values['workbench.task.state:task-1']}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["registered"], [{"id": "common.image-analysis", "version": "1.0.0"}])
        for state in (payload["configured"], payload["reloaded"]):
            self.assertEqual(state["definition_ref"], {"type": "skill", "id": "common.image-analysis", "version": "1.0.0"})
            self.assertEqual(state["asset"], {"type": "asset_version", "id": "asset-v1"})
            self.assertEqual(state["binding"]["skill_id"], "common.image-analysis")
            self.assertEqual(state["binding"]["version"], "1.0.0")
            self.assertEqual(state["binding"]["prompt_override"], {"prompt_id": "common.image-analysis.prompt", "version": 2})
        self.assertEqual(payload["configured"], payload["reloaded"])

    def test_configuration_proof_has_no_execution_or_wholehouse_ownership(self):
        module = (ROOT / "static/js/workbench/canvas/common-image-analysis-proof.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("common-image-analysis-proof.js", page)
        self.assertNotIn("execute", module.lower())
        self.assertNotIn("wholehouse", module.lower())
        self.assertIn("skillBinding", module)


if __name__ == "__main__":
    unittest.main()
