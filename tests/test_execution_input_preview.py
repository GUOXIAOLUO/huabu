import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/execution-input-preview.js"


class ExecutionInputPreviewTests(unittest.TestCase):
    def run_node(self, expression):
        script = f"const fs=require('fs');const vm=require('vm');const sandbox={{window:{{}}}};vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);{expression}"
        return subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True).stdout.strip()

    def test_normalizes_items_missing_inputs_and_blocks_invalid_projection(self):
        output = self.run_node("""
const api=sandbox.window.WorkbenchExecutionInputPreview;
const view=api.normalize({valid:false,inputs:[],errors:[{code:'resolver_unavailable',binding_id:'asset-2',message:'asset missing'}]}, {mode:'batch',concurrency:2});
console.log(JSON.stringify({count:view.items.length,missing:view.missing[0].binding_id,executable:view.executable,summary:view.policy.mode}));
""")
        self.assertEqual(json.loads(output), {"count": 1, "missing": "asset-2", "executable": False, "summary": "batch"})

    def test_policy_edits_are_safe_and_single_mode_is_bounded(self):
        output = self.run_node("""
const api=sandbox.window.WorkbenchExecutionInputPreview;
const preview=api.create({projection:{valid:true,inputs:[{input_id:'one',binding_id:'one',role:'prompt',target:'task.input',source_type:'literal',source_ref:'hello',value:'hello'}],errors:[]},policy:{mode:'single'}});
const batch=preview.updatePolicy({mode:'batch',concurrency:2,start_index:0});
const single=preview.updatePolicy({mode:'single',concurrency:9});
console.log(JSON.stringify({batch:batch.policy.mode,concurrency:batch.policy.concurrency,executable:batch.executable,forced:single.policy.concurrency}));
""")
        self.assertEqual(json.loads(output), {"batch": "batch", "concurrency": 2, "executable": True, "forced": 1})

    def test_page_loads_preview_before_shell_and_task_exposes_mount_seam(self):
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        task = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertLess(page.index("execution-input-preview.js"), page.index("node-shell.js"))
        self.assertIn("mountExecutionInputPreview", task)
        self.assertIn("executionInputPreviewOptions", shell)

    def test_task_mount_derives_preview_options_from_the_node_record(self):
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("node.executionInputProjection", host)
        self.assertIn("node.executionPolicy", host)
        self.assertIn("'task'", editor)
        self.assertIn("node?.type === 'task'", editor)


if __name__ == "__main__":
    unittest.main()
