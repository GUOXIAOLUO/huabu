import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TaskRichNodeTests(unittest.TestCase):
    def test_generic_task_exercises_presentations_and_reloads_generic_state(self):
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const T=sandbox.window.WorkbenchTaskRichNode;
const node={{id:'task-1',type:'task',title:'Draft task',status:'ready',inputs:[{{type:'literal',value:'x'}}],definition_ref:{{id:'legacy-definition'}}}};
const task=T.create({{node,storage}});
const states=['expanded','workspace','inspector','card'].map(p=>task.update({{presentation:p}}).presentation);
task.update({{status:'ready',inputs:[{{type:'literal',value:'saved'}}],definition:{{id:'task-definition',version:'1'}},skill:'placeholder',workspace:'placeholder',inspector:'placeholder'}});
const reload=T.create({{node,storage}}).snapshot();
console.log(JSON.stringify({{compatible:T.compatible(node),presentations:T.PRESENTATIONS,states,reload}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["presentations"], ["card", "expanded", "workspace", "inspector"])
        self.assertEqual(payload["states"], ["expanded", "workspace", "inspector", "card"])
        self.assertTrue(payload["compatible"])
        self.assertEqual(payload["reload"]["fields"]["status"], "ready")
        self.assertEqual(payload["reload"]["fields"]["inputs"], [{"type": "literal", "value": "saved"}])
        self.assertEqual(payload["reload"]["fields"]["skill"], "placeholder")
        self.assertEqual(payload["reload"]["kind"], "task")

    def test_task_skeleton_does_not_claim_skill_or_execution_ownership(self):
        source = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertNotIn("SkillRegistry", source)
        self.assertNotIn("ModelDefinition", source)
        self.assertNotIn("execute", source.lower())
        self.assertIn("/static/js/workbench/canvas/task-rich-node.js", page)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchTaskRichNode.create({node, presentationController})", shell)
        self.assertIn("taskRichNode?.state().presentation", shell)

    def test_task_rich_node_reuses_shared_presentation_owner(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const controller=sandbox.window.WorkbenchPresentationState.create();
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}},presentationController:controller}});
task.update({{presentation:'expanded'}});
const afterTask=controller.state();
controller.transition('inspector');
console.log(JSON.stringify({{afterTask,afterController:task.state().presentation}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"afterTask": "expanded", "afterController": "inspector"})


if __name__ == "__main__":
    unittest.main()
