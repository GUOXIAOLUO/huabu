"""Focused tests for the R8-18 Result Compare workspace.

The DoD is "Users can compare candidates while they remain run results", so
these tests drive the seam in a vm sandbox and prove three things: several
staged candidates can be selected together and compared side by side with their
run/attempt metadata and their preview, the selection is preserved across
candidate updates and re-renders, and comparing never promotes a candidate out
of the run-result state.
"""

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARE = ROOT / "static/js/workbench/canvas/result-compare-runtime.js"
PREVIEW = ROOT / "static/js/workbench/canvas/result-preview-runtime.js"
TRAY = ROOT / "static/js/workbench/canvas/result-tray-runtime.js"

# DoD: comparing a candidate must not create a Canvas node or mutate the graph.
FORBIDDEN_CANVAS_MUTATION_MARKERS = (
    "createNode",
    "create_node",
    "NodeCreation",
    "node-creation-client",
    "addNode",
    "insertNode",
    "materializeNode",
    "promoteToCanvas",
    "graphMutation",
    "graph_mutation",
    "GraphMutationService",
    "/api/canvas-nodes",
)
# A compare seam owns no transport and no client persistence.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
# Out of scope: no domain-specific scoring. The workspace may not compute or
# expose a score, rank, rating or weight for any candidate.
FORBIDDEN_SCORING_MARKERS = ("score(", "score:", "score =", "rank(", "ranking(", "rating", "weight(", "weight:")
# Classification stays with the caller and the shared media-kind classifier: a
# compare column renders the kind it is given instead of re-deriving it from a
# URL or an extension.
FORBIDDEN_CLASSIFIER_MARKERS = (
    ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".mp3", ".wav", ".zip",
    "mediaKindFor", "WorkbenchCanvasMediaKind",
)

# Rendered columns are counted by their full opening tag rather than by the
# substring `result-compare__column`: the wrapper class
# `workbench-result-compare__columns` contains that substring, so a bare
# substring count would report one column too many.
COLUMN_OPEN = '<article class="result-compare__column"'

# `node-shell.js` legitimately defines its own factory named `createNodeShell`,
# which contains the forbidden `createNode` marker as a substring. Scrubbing that
# one known-legitimate token keeps the scan strict about real node creation
# (e.g. a `createNodeFromResult` would still be caught) without a false positive.
NODE_SHELL_LEGITIMATE_TOKENS = ("createNodeShell",)

CANDIDATES = """
const candidates = [
  {item_id:'a1', kind:'image', title:'poster', subtitle:'image · attempt-1', preview_url:'/a.png',
   run_id:'run-1', attempt_id:'attempt-1', output_name:'poster', ordinal:0, value:{kind:'image',url:'/a.png'}},
  {item_id:'a2', kind:'image', title:'poster', subtitle:'image · attempt-2', preview_url:'/b.png',
   run_id:'run-1', attempt_id:'attempt-2', output_name:'poster', ordinal:0, value:{kind:'image',url:'/b.png'}},
  {item_id:'a3', kind:'text', title:'caption', subtitle:'text · attempt-1', preview_url:'',
   run_id:'run-1', attempt_id:'attempt-1', output_name:'caption', ordinal:0, value:'a caption'},
  {item_id:'a4', kind:'video', title:'clip', subtitle:'video · attempt-3', preview_url:'/c.mp4',
   run_id:'run-1', attempt_id:'attempt-3', output_name:'clip', ordinal:0, value:{kind:'video',url:'/c.mp4'}},
  {item_id:'a5', kind:'image', title:'poster', subtitle:'image · attempt-4', preview_url:'/d.png',
   run_id:'run-1', attempt_id:'attempt-4', output_name:'poster', ordinal:0, value:{kind:'image',url:'/d.png'}},
];
"""


def _scrub_legitimate_tokens(source: str) -> str:
    """Remove identifiers that merely contain a forbidden marker as a substring."""
    scrubbed = source
    for token in NODE_SHELL_LEGITIMATE_TOKENS:
        scrubbed = scrubbed.replace(token, "")
    return scrubbed


def run_program(body: str, *modules: Path) -> dict:
    """Run one sandbox program with the given modules loaded, in order."""
    loaders = "".join(
        f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))},'utf8'),sandbox);\n"
        for path in modules
    )
    script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
{loaders}
{body}
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class ResultCompareRuntimeTests(unittest.TestCase):
    def test_multi_select_is_order_preserving_and_bounded(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const controller=api.create({{candidates}});
const results=[];
['a3','a1','a2','a4','a5'].forEach(id=>results.push(controller.toggle(id)));
console.log(JSON.stringify({{
  results,
  selection:controller.selection(),
  state:controller.snapshot().state,
  limit:controller.snapshot().max_candidates,
}}));
""", COMPARE)
        # Selection order is the user's order, and the fifth is refused at capacity.
        self.assertEqual(payload["selection"], ["a3", "a1", "a2", "a4"])
        self.assertEqual(payload["limit"], 4)
        self.assertEqual(
            [entry["reason"] for entry in payload["results"]],
            ["selected", "selected", "selected", "selected", "at_capacity"],
        )
        self.assertEqual(payload["results"][4]["selected"], False)
        self.assertEqual(payload["state"], "ready")

    def test_toggling_off_and_unknown_candidates_are_reported(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const controller=api.create({{candidates}});
const on=controller.toggle('a1');
const off=controller.toggle('a1');
const unknown=controller.toggle('nope');
console.log(JSON.stringify({{on,off,unknown,selection:controller.selection(),has:controller.has('a1')}}));
""", COMPARE)
        self.assertEqual(payload["on"]["reason"], "selected")
        self.assertEqual(payload["off"]["reason"], "deselected")
        self.assertEqual(payload["off"]["selected"], False)
        self.assertEqual(payload["unknown"]["reason"], "unknown_candidate")
        self.assertEqual(payload["selection"], [])
        self.assertFalse(payload["has"])

    def test_state_transitions_through_empty_incomplete_and_ready(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const controller=api.create({{candidates}});
const states=[controller.snapshot().state];
controller.toggle('a1'); states.push(controller.snapshot().state);
controller.toggle('a2'); states.push(controller.snapshot().state);
controller.clear(); states.push(controller.snapshot().state);
console.log(JSON.stringify({{states,compareStates:api.STATES,min:api.MIN_CANDIDATES,max:api.MAX_CANDIDATES}}));
""", COMPARE)
        self.assertEqual(payload["states"], ["empty", "incomplete", "ready", "empty"])
        self.assertEqual(payload["compareStates"], ["empty", "incomplete", "ready"])
        self.assertEqual(payload["min"], 2)
        self.assertEqual(payload["max"], 4)

    def test_selection_is_preserved_across_candidate_updates(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const controller=api.create({{candidates}});
controller.select(['a1','a2','a3']);
// attempt-2 disappears from the staged results; the rest must survive in order.
const after=controller.setCandidates(candidates.filter(entry=>entry.item_id!=='a2'));
console.log(JSON.stringify({{
  selection:controller.selection(),
  omitted:after.omitted,
  state:after.state,
  columns:controller.comparison().candidates.map(column=>column.item_id),
}}));
""", COMPARE)
        self.assertEqual(payload["selection"], ["a1", "a3"])
        self.assertEqual(payload["omitted"], ["a2"])
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["columns"], ["a1", "a3"])

    def test_selection_survives_re_render_and_further_toggles(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const host={{innerHTML:'',attrs:{{}},setAttribute(k,v){{this.attrs[k]=v;}},removeAttribute(k){{delete this.attrs[k];}}}};
const controller=api.create({{candidates}});
controller.toggle('a1');
controller.mount(host);
const first=host.innerHTML;
controller.toggle('a3');
const second=host.innerHTML;
console.log(JSON.stringify({{
  selection:controller.selection(),
  firstHasA1:first.includes('data-compare-item="a1"'),
  secondHasA1:second.includes('data-compare-item="a1"'),
  secondHasA3:second.includes('data-compare-item="a3"'),
  columns:second.split({json.dumps(COLUMN_OPEN)}).length-1,
}}));
""", COMPARE)
        self.assertEqual(payload["selection"], ["a1", "a3"])
        self.assertTrue(payload["firstHasA1"])
        self.assertTrue(payload["secondHasA1"])
        self.assertTrue(payload["secondHasA3"])
        self.assertEqual(payload["columns"], 2)

    def test_comparison_columns_carry_side_by_side_metadata_and_preview(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const controller=api.create({{candidates}});
controller.select(['a1','a3']);
const comparison=controller.comparison();
console.log(JSON.stringify({{
  schema:comparison.schema_version,
  state:comparison.state,
  selected_count:comparison.selected_count,
  candidate_count:comparison.candidate_count,
  columns:comparison.candidates.map(column=>({{
    position:column.position, item_id:column.item_id, kind:column.kind, title:column.title,
    run_id:column.run_id, attempt_id:column.attempt_id, output_name:column.output_name, ordinal:column.ordinal,
    preview_source:column.preview_source, preview_state:column.preview_state, preview_url:column.preview_url,
    hasImg:column.preview_html.includes('<img '), hasText:column.preview_html.includes('a caption'),
  }})),
}}));
""", PREVIEW, COMPARE)
        self.assertEqual(payload["schema"], "workbench.result-compare/1")
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["selected_count"], 2)
        self.assertEqual(payload["candidate_count"], 5)
        first, second = payload["columns"]
        self.assertEqual([first["position"], second["position"]], [0, 1])
        self.assertEqual(first["item_id"], "a1")
        self.assertEqual(second["item_id"], "a3")
        # Metadata comes from the run-result linkage, not from a promoted node.
        self.assertEqual((first["run_id"], first["attempt_id"], first["output_name"]), ("run-1", "attempt-1", "poster"))
        self.assertEqual((second["run_id"], second["attempt_id"], second["output_name"]), ("run-1", "attempt-1", "caption"))
        self.assertEqual(first["preview_source"], "registry")
        self.assertEqual(first["preview_state"], "ready")
        # The column keeps the candidate's own reference alongside the preview.
        self.assertEqual(first["preview_url"], "/a.png")
        self.assertEqual(second["preview_url"], "")
        self.assertTrue(first["hasImg"])
        self.assertTrue(second["hasText"])

    def test_mounted_workspace_renders_columns_and_reports_its_state(self):
        payload = run_program(f"""
const api=sandbox.window.WorkbenchCanvasResultCompare;
{CANDIDATES}
const host={{innerHTML:'',attrs:{{}},setAttribute(k,v){{this.attrs[k]=v;}},removeAttribute(k){{delete this.attrs[k];}}}};
const controller=api.create({{candidates}});
const mounted=controller.mount(host);
const empty=host.innerHTML;
controller.select(['a1','a2']);
const html=host.innerHTML;
const keys=Object.keys(controller);
console.log(JSON.stringify({{
  empty,
  state:host.attrs['data-result-compare'],
  columns:html.split({json.dumps(COLUMN_OPEN)}).length-1,
  positions:[...html.matchAll(/data-compare-position="(\\d+)"/g)].map(m=>m[1]),
  items:[...html.matchAll(/data-compare-item="([^"]+)"/g)].map(m=>m[1]),
  meta:html.includes('<dt>attempt</dt>'),
  selected:html.includes('2 of 4 selected'),
  keys,
  promotionEntryPoints:keys.filter(key=>/material|promote|createNode|node/i.test(key)),
  destroy:typeof mounted.destroy==='function',
}}));
""", PREVIEW, COMPARE)
        self.assertIn("Select at least two results to compare", payload["empty"])
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["columns"], 2)
        self.assertEqual(payload["positions"], ["0", "1"])
        self.assertEqual(payload["items"], ["a1", "a2"])
        self.assertTrue(payload["meta"])
        self.assertTrue(payload["selected"])
        self.assertEqual(payload["promotionEntryPoints"], [])
        self.assertTrue(payload["destroy"])

    def test_candidates_from_joins_cards_and_items_on_item_id(self):
        # The join is keyed by item_id, never by position. The second card has no
        # staged item, so it must come through with its own metadata and no value
        # rather than silently borrowing the first item's value.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCompare;
const cards=[
  {item_id:'i1', kind:'image', title:'poster', subtitle:'image · attempt-1', preview_url:'/a.png', source:{run_id:'run-1',attempt_id:'attempt-1',output_name:'poster',ordinal:0}},
  {item_id:'orphan', kind:'image', title:'gone', subtitle:'', preview_url:'/x.png', source:{}},
  {kind:'image', title:'no identity', source:{}},
];
const items=[
  {item_id:'i1', kind:'image', value:{kind:'image',url:'/a.png'}, run_id:'run-1', attempt_id:'attempt-1', output_name:'poster', ordinal:0},
];
const candidates=api.candidatesFrom(cards, items);
console.log(JSON.stringify({count:candidates.length,candidates,ids:candidates.map(entry=>entry.item_id)}));
""", COMPARE)
        # The identity-less card is dropped; the item-less card is not.
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["ids"], ["i1", "orphan"])
        candidate, orphan = payload["candidates"]
        self.assertEqual(candidate["item_id"], "i1")
        self.assertEqual(candidate["preview_url"], "/a.png")
        self.assertEqual(candidate["run_id"], "run-1")
        self.assertEqual(candidate["value"], {"kind": "image", "url": "/a.png"})
        # No cross-contamination: the orphan keeps its own title/ref and no value.
        self.assertEqual(orphan["title"], "gone")
        self.assertEqual(orphan["preview_url"], "/x.png")
        self.assertEqual(orphan["run_id"], "")
        self.assertIsNone(orphan.get("value"))

    def test_candidates_stay_run_results_and_nothing_is_promoted(self):
        # The DoD, end to end: stage through the tray, compare two candidates,
        # and prove the tray's staged state is untouched and no promotion exists.
        payload = run_program("""
const tray=sandbox.window.WorkbenchCanvasResultTray;
const compare=sandbox.window.WorkbenchCanvasResultCompare;
const graph={nodes:[{id:'task-1'}],edges:[],revision:5};
const graphBefore=JSON.stringify(graph);
const host={innerHTML:'',attrs:{},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const controller=tray.create({projectId:'p1',taskId:'task-1',runId:'run-1',attemptId:'attempt-1'});
controller.ingest({runId:'run-1',attemptId:'attempt-1',outputs:[
  {name:'poster',value:{kind:'image',url:'/a.png'}},
  {name:'poster',value:{kind:'image',url:'/b.png'}},
]});
const stagedBefore=JSON.stringify(controller.snapshot());
const candidates=compare.candidatesFrom(controller.cards(), controller.snapshot().items);
const workspace=compare.create({candidates});
workspace.select(candidates.map(candidate=>candidate.item_id));
workspace.mount(host);
const comparison=workspace.comparison();
console.log(JSON.stringify({
  columns:comparison.candidates.map(column=>({item:column.item_id,run:column.run_id,attempt:column.attempt_id,state:column.preview_state})),
  stagedUnchanged:JSON.stringify(controller.snapshot())===stagedBefore,
  materialized:controller.snapshot().items.map(item=>item.materialized),
  graphUntouched:JSON.stringify(graph)===graphBefore,
  trayKeys:Object.keys(controller),
  workspaceKeys:Object.keys(workspace),
  html:host.innerHTML.includes('data-compare-item'),
}));
""", PREVIEW, TRAY, COMPARE)
        self.assertEqual([column["item"] for column in payload["columns"]], ["attempt-1:poster:0", "attempt-1:poster:1"])
        for column in payload["columns"]:
            self.assertEqual((column["run"], column["attempt"]), ("run-1", "attempt-1"))
            self.assertEqual(column["state"], "ready")
        self.assertTrue(payload["stagedUnchanged"])
        self.assertEqual(payload["materialized"], [False, False])
        self.assertTrue(payload["graphUntouched"])
        self.assertEqual(payload["trayKeys"], ["session_id", "snapshot", "ingest", "cards", "summary", "mount"])
        self.assertNotIn("promote", " ".join(payload["workspaceKeys"]))
        self.assertTrue(payload["html"])

    def test_seam_has_no_canvas_mutation_no_transport_no_scoring_no_classification(self):
        source = COMPARE.read_text(encoding="utf-8")
        for marker in FORBIDDEN_CANVAS_MUTATION_MARKERS:
            self.assertNotIn(marker, source, msg=f"compare must not reference {marker}")
        for marker in FORBIDDEN_TRANSPORT_MARKERS:
            self.assertNotIn(marker, source, msg=f"compare must not reference {marker}")
        for marker in FORBIDDEN_SCORING_MARKERS:
            self.assertNotIn(marker, source, msg=f"compare must not score via {marker}")
        for marker in FORBIDDEN_CLASSIFIER_MARKERS:
            self.assertNotIn(marker, source, msg=f"compare must not classify via {marker}")

    def test_canvas_page_loads_the_compare_runtime_after_the_preview_runtime(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-compare-runtime.js"), 1)
        self.assertLess(
            page.index("workbench/canvas/result-preview-runtime.js"),
            page.index("workbench/canvas/result-compare-runtime.js"),
        )
        self.assertLess(
            page.index("workbench/canvas/result-compare-runtime.js"),
            page.index("workbench/canvas/canvas-app-bootstrap.js"),
        )

    def test_task_rich_node_mounts_the_compare_workspace(self):
        task_module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
{json.dumps(str(COMPARE))}.length;
vm.runInNewContext(fs.readFileSync({json.dumps(str(PREVIEW))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(COMPARE))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(task_module))},'utf8'),sandbox);
const T=sandbox.window.WorkbenchTaskRichNode;
const host={{innerHTML:'',attrs:{{}},setAttribute(k,v){{this.attrs[k]=v;}},removeAttribute(k){{delete this.attrs[k];}}}};
const task=T.create({{node:{{id:'task-1',type:'task',title:'Task'}}}});
const workspace=task.mountResultCompare(host,{{candidates:[
  {{item_id:'a1',kind:'image',title:'poster',preview_url:'/a.png',value:{{kind:'image',url:'/a.png'}}}},
  {{item_id:'a2',kind:'image',title:'poster',preview_url:'/b.png',value:{{kind:'image',url:'/b.png'}}}},
]}});
workspace.select(['a1','a2']);
console.log(JSON.stringify({{hasMount:typeof task.mountResultCompare==='function',state:host.attrs['data-result-compare'],columns:host.innerHTML.split({json.dumps(COLUMN_OPEN)}).length-1}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["hasMount"])
        self.assertEqual(payload["state"], "ready")
        self.assertEqual(payload["columns"], 2)

    def test_task_rich_node_reports_a_missing_compare_module(self):
        task_module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(task_module))},'utf8'),sandbox);
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',type:'task',title:'Task'}}}});
let message='';
try {{ task.mountResultCompare({{}},{{}}); }} catch (error) {{ message=String(error.message); }}
console.log(JSON.stringify({{message}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["message"], "Task result compare is unavailable")

    def test_node_shell_mounts_and_destroys_the_compare_host(self):
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("settings.resultCompareOptions", shell)
        self.assertIn("taskRichNode.mountResultCompare(resultCompareHost, settings.resultCompareOptions)", shell)
        self.assertIn("resultCompareHost?.setAttribute('data-result-compare-host', '')", shell)
        self.assertIn("mountedResultCompare?.destroy?.()", shell)
        scanned = shell
        for token in NODE_SHELL_LEGITIMATE_TOKENS:
            scanned = scanned.replace(token, "")
        for marker in FORBIDDEN_CANVAS_MUTATION_MARKERS:
            self.assertNotIn(marker, scanned, msg=f"node shell must not promote via {marker}")
        # The scrub above only excuses the shell's own factory, not node creation.
        self.assertIn("createNodeFromResult", scanned + "createNodeFromResult")
        self.assertNotIn("createNodeFromResult", scanned)


if __name__ == "__main__":
    unittest.main()
