"""Focused tests for the R8-16 Result Tray runtime.

The DoD is "Run outputs appear in tray without polluting Canvas", so these
tests drive the seam in a vm sandbox and prove both halves: execution outputs
are staged with their run/attempt linkage, and there is no path from the tray
to a Canvas node or to the graph.
"""

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/result-tray-runtime.js"

# DoD: staging a result must not create a Canvas node or mutate the graph.
FORBIDDEN_CANVAS_MUTATION_MARKERS = (
    "createNode",
    "create_node",
    "NodeCreation",
    "node-creation-client",
    "addNode",
    "insertNode",
    "materializeNode",
    "graphMutation",
    "graph_mutation",
    "GraphMutationService",
    "/api/canvas-nodes",
)
# The host integration files legitimately name shell factories (createNodeShell),
# so they are scanned for concrete materialization dependencies instead.
FORBIDDEN_MATERIALIZATION_MARKERS = (
    "NodeCreationService",
    "WorkbenchNodeCreation",
    "node-creation-client",
    "materializeNode",
    "promoteToCanvas",
    "graphMutation",
    "graph_mutation",
    "GraphMutationService",
    "/api/canvas-nodes",
)
# A staging seam owns no transport and no client persistence.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")


def run_module(body: str) -> dict:
    """Run one sandbox program against the tray module and return its JSON output."""
    script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
const api=sandbox.window.WorkbenchCanvasResultTray;
{body}
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class ResultTrayRuntimeTests(unittest.TestCase):
    def test_stages_run_outputs_as_linked_non_materialized_items(self):
        payload = run_module("""
const controller=api.create({projectId:'project-1',taskId:'task-1',runId:'run-1',attemptId:'attempt-1'});
controller.ingest({runId:'run-1',attemptId:'attempt-1',outputs:[
  {name:'text',value:'a caption'},
  {name:'poster',value:{kind:'image',url:'https://files.example.test/a.png'}},
]});
console.log(JSON.stringify({snapshot:controller.snapshot(),summary:controller.summary()}));
""")
        snapshot = payload["snapshot"]
        self.assertEqual(snapshot["session_id"], "project-1:task-1:run-1")
        self.assertEqual([item["output_name"] for item in snapshot["items"]], ["text", "poster"])
        self.assertEqual([item["kind"] for item in snapshot["items"]], ["text", "image"])
        self.assertEqual(snapshot["items"][0]["value"], "a caption")
        self.assertEqual(snapshot["items"][1]["value"]["url"], "https://files.example.test/a.png")
        # Linkage to the run/attempt that produced the output.
        self.assertEqual(
            [(item["run_id"], item["attempt_id"], item["ordinal"]) for item in snapshot["items"]],
            [("run-1", "attempt-1", 0), ("run-1", "attempt-1", 0)],
        )
        # DoD: staged by default, nothing materialized.
        self.assertFalse(snapshot["materialized"])
        self.assertEqual([item["materialized"] for item in snapshot["items"]], [False, False])
        self.assertEqual(payload["summary"], {
            "session_id": "project-1:task-1:run-1", "run_id": "run-1", "attempt_id": "attempt-1",
            "item_count": 2, "materialized": False,
        })

    def test_re_ingesting_the_same_attempt_outputs_is_idempotent(self):
        payload = run_module("""
const controller=api.create({runId:'run-1',attemptId:'attempt-1'});
const batch={runId:'run-1',attemptId:'attempt-1',outputs:[
  {name:'shot',value:'/one.png'},{name:'shot',value:'/two.png'},
]};
const first=controller.ingest(batch).length;
const second=controller.ingest(batch).length;
const other=controller.ingest({runId:'run-1',attemptId:'attempt-2',outputs:[{name:'shot',value:'/three.png'}]}).length;
console.log(JSON.stringify({first,second,other,items:controller.snapshot().items.map(item=>item.item_id)}));
""")
        self.assertEqual(payload["first"], 2)
        self.assertEqual(payload["second"], 0)
        self.assertEqual(payload["other"], 1)
        self.assertEqual(payload["items"], [
            "attempt-1:shot:0", "attempt-1:shot:1", "attempt-2:shot:0",
        ])

    def test_cards_are_generic_descriptors_with_declared_kinds_and_previews(self):
        payload = run_module("""
const session=api.createSession({runId:'run-1',attemptId:'attempt-1'});
api.ingest(session,{attemptId:'attempt-1',outputs:[
  {name:'caption',value:'hello'},
  {name:'poster',value:{kind:'image',url:'/a.png'}},
  {name:'clip',value:{kind:'video',uri:'/b.mp4'}},
  {name:'blob',value:{kind:'file',file:'/c.zip'}},
  {name:'payload',value:{items:[]}},
  {name:'empty',value:{kind:'image'}},
]});
console.log(JSON.stringify({cards:api.cards(session),kinds:api.KINDS}));
""")
        cards = payload["cards"]
        self.assertEqual([card["kind"] for card in cards], ["text", "image", "video", "file", "json", "image"])
        self.assertEqual([card["previewable"] for card in cards], [False, True, True, False, False, False])
        self.assertEqual(cards[0]["title"], "caption")
        self.assertEqual(cards[0]["subtitle"], "text · attempt-1")
        self.assertEqual(cards[1]["preview_url"], "/a.png")
        self.assertEqual(cards[2]["preview_url"], "/b.mp4")
        self.assertEqual(cards[3]["preview_url"], "/c.zip")
        self.assertEqual(cards[4]["preview_url"], "")
        self.assertEqual(cards[1]["source"], {"run_id": "run-1", "attempt_id": "attempt-1", "output_name": "poster", "ordinal": 0})
        self.assertEqual([card["materialized"] for card in cards], [False] * 6)
        self.assertIn("image", payload["kinds"])

    def test_mount_renders_staged_cards_into_the_host(self):
        payload = run_module("""
const host={innerHTML:'',attrs:{},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const changes=[];
const controller=api.create({runId:'run-1',attemptId:'attempt-1',onChange:state=>changes.push(state.items.length)});
controller.ingest({attemptId:'attempt-1',outputs:[{name:'poster',value:{kind:'image',url:'/a.png'}}]});
const mounted=controller.mount(host);
const keys=Object.keys(controller);
console.log(JSON.stringify({html:host.innerHTML,tray:host.attrs['data-result-tray'],changes,keys,hasMaterialize:keys.some(k=>/material|createNode|promote|node/i.test(k))}));
""")
        self.assertIn("data-result-item=\"attempt-1:poster:0\"", payload["html"])
        self.assertIn("data-result-kind=\"image\"", payload["html"])
        self.assertIn("1 staged", payload["html"])
        self.assertEqual(payload["tray"], "run-1")
        self.assertEqual(payload["changes"], [1])
        # No materialization entry point exists on the tray controller.
        self.assertFalse(payload["hasMaterialize"])

    def test_snapshot_is_a_copy_so_the_tray_owns_its_staging_state(self):
        payload = run_module("""
const controller=api.create({runId:'run-1',attemptId:'attempt-1'});
controller.ingest({attemptId:'attempt-1',outputs:[{name:'caption',value:'hello'}]});
const snapshot=controller.snapshot();
snapshot.items.push({item_id:'injected'});
snapshot.items[0].materialized=true;
console.log(JSON.stringify({items:controller.snapshot().items.map(item=>({id:item.item_id,materialized:item.materialized}))}));
""")
        self.assertEqual(payload["items"], [{"id": "attempt-1:caption:0", "materialized": False}])

    def test_seam_has_no_canvas_mutation_or_transport_dependency(self):
        source = MODULE.read_text(encoding="utf-8")
        for marker in FORBIDDEN_CANVAS_MUTATION_MARKERS:
            self.assertNotIn(marker, source, msg=f"tray must not reference {marker}")
        for marker in FORBIDDEN_TRANSPORT_MARKERS:
            self.assertNotIn(marker, source, msg=f"tray must not reference {marker}")

    def test_canvas_page_loads_the_tray_runtime_before_the_app_bootstrap(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-tray-runtime.js"), 1)
        self.assertLess(
            page.index("workbench/canvas/result-tray-runtime.js"),
            page.index("workbench/canvas/canvas-app-bootstrap.js"),
        )

    def test_task_rich_node_mounts_the_tray_and_stages_run_outputs(self):
        task_module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(task_module))},'utf8'),sandbox);
const T=sandbox.window.WorkbenchTaskRichNode;
const host={{innerHTML:'',attrs:{{}},setAttribute(k,v){{this.attrs[k]=v;}},removeAttribute(k){{delete this.attrs[k];}}}};
const task=T.create({{node:{{id:'task-1',type:'task',title:'Task'}}}});
const mounted=task.mountResultTray(host,{{runId:'run-1',attemptId:'attempt-1'}});
mounted.ingest({{runId:'run-1',attemptId:'attempt-1',outputs:[{{name:'poster',value:{{kind:'image',url:'/a.png'}}}}]}});
console.log(JSON.stringify({{html:host.innerHTML,tray:host.attrs['data-result-tray'],hasMount:typeof task.mountResultTray==='function'}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["hasMount"])
        self.assertEqual(payload["tray"], "run-1")
        self.assertIn("data-result-item=\"attempt-1:poster:0\"", payload["html"])
        self.assertIn("1 staged", payload["html"])

    def test_task_rich_node_reports_a_missing_tray_instead_of_creating_a_node(self):
        task_module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(task_module))},'utf8'),sandbox);
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',type:'task',title:'Task'}}}});
let message='';
try {{ task.mountResultTray({{}},{{}}); }} catch (error) {{ message=String(error.message); }}
console.log(JSON.stringify({{message}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["message"], "Task result tray is unavailable")

    def test_node_shell_mounts_and_destroys_the_tray_without_touching_the_graph(self):
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("settings.resultTrayOptions", shell)
        self.assertIn("taskRichNode.mountResultTray(resultTrayHost, settings.resultTrayOptions)", shell)
        self.assertIn("resultTrayHost?.setAttribute('data-result-tray-host', '')", shell)
        self.assertIn("mountedResultTray?.destroy?.()", shell)
        task_source = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        self.assertIn("mountResultTray", task_source)
        for marker in FORBIDDEN_MATERIALIZATION_MARKERS:
            self.assertNotIn(marker, task_source, msg=f"task node must not materialize via {marker}")
            self.assertNotIn(marker, shell, msg=f"node shell must not materialize via {marker}")


if __name__ == "__main__":
    unittest.main()
