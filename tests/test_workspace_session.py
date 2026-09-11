import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkspaceSessionTests(unittest.TestCase):
    def test_session_lifecycle_context_and_dirty_save_discard(self):
        module = ROOT / "static/js/workbench/canvas/workspace-session.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const W=sandbox.window.WorkbenchWorkspaceSession;
const events=[], saved=[], discarded=[];
const session=W.create({{onChange:value=>events.push(value), onSave:context=>saved.push(context.nodeId), onDiscard:context=>discarded.push(context.nodeId)}});
const selection=['node-1'];
let cleanClose=session.open({{nodeId:'node-1', selection}});
selection.push('node-2');
session.markDirty();
let blocked=false; try {{ session.close(); }} catch(e) {{ blocked=e.message==='workspace has unsaved changes'; }}
const savedState=session.save();
const closed=session.close();
const reopened=session.open({{nodeId:'node-2', selection:['node-2']}});
session.markDirty();
const discardedState=session.close({{discard:true}});
console.log(JSON.stringify({{states:W.STATES,cleanClose,blocked,savedState,closed,reopened,discardedState,saved,discarded,events:events.map(event=>[event.state,event.dirty,event.context&&event.context.nodeId])}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["states"], ["closed", "open"])
        self.assertEqual(payload["cleanClose"]["context"]["nodeId"], "node-1")
        self.assertEqual(payload["cleanClose"]["context"]["selection"], ["node-1"])
        self.assertTrue(payload["blocked"])
        self.assertFalse(payload["savedState"]["dirty"])
        self.assertEqual(payload["saved"], ["node-1"])
        self.assertEqual(payload["closed"]["state"], "closed")
        self.assertEqual(payload["reopened"]["context"]["nodeId"], "node-2")
        self.assertEqual(payload["discardedState"]["state"], "closed")
        self.assertEqual(payload["discarded"], ["node-2"])

    def test_workspace_registry_is_generic_and_rejects_duplicate_ids(self):
        module = ROOT / "static/js/workbench/canvas/workspace-session.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const registry=sandbox.window.WorkbenchWorkspaceSession.createRegistry();
const definition=registry.register({{id:'generic', open:context=>context}});
let duplicate=false; try {{ registry.register({{id:'generic', open:()=>null}}); }} catch(e) {{ duplicate=e.message==='workspace already registered: generic'; }}
console.log(JSON.stringify({{id:definition.id, resolved:registry.resolve('generic').id, count:registry.list().length, duplicate, removed:registry.unregister('generic'), missing:registry.resolve('generic')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "id": "generic", "resolved": "generic", "count": 1,
            "duplicate": True, "removed": True, "missing": None,
        })

    def test_canvas_adapter_projects_current_selection_and_canvas_context(self):
        runtime = ROOT / "static/js/workbench/canvas/workspace-session.js"
        adapter = ROOT / "static/js/workbench/canvas/canvas-workspace-session.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(adapter))},'utf8'),sandbox);
let selection=['node-1','node-2'];
const canvas={{id:'canvas-1', project:'project-1'}};
const session=sandbox.window.WorkbenchCanvasWorkspaceSession.create({{getSelection:()=>selection, getCanvas:()=>canvas}});
const opened=session.openFromSelection('node-1');
selection.push('node-3');
console.log(JSON.stringify({{opened, retained:session.context(), state:session.state()}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "open")
        self.assertEqual(payload["opened"]["context"], {
            "nodeId": "node-1", "selection": ["node-1", "node-2"],
            "canvasId": "canvas-1", "projectId": "project-1",
        })
        self.assertEqual(payload["retained"]["selection"], ["node-1", "node-2"])


if __name__ == "__main__":
    unittest.main()
