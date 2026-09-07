import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js"
GRAPH_GEOMETRY = ROOT / "static" / "js" / "workbench" / "canvas" / "graph-geometry.js"
GRAPH_INTERACTION = ROOT / "static" / "js" / "workbench" / "canvas" / "graph-interaction.js"
PORT_COMPATIBILITY = ROOT / "static" / "js" / "workbench" / "canvas" / "port-compatibility.js"
EXECUTION_COMPATIBILITY = ROOT / "static" / "js" / "workbench" / "canvas" / "execution-compatibility.js"
NODE_CLIENT = ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js"
GROUP_MEMBERSHIP = ROOT / "static" / "js" / "workbench" / "canvas" / "group-membership.js"
VIEWPORT_RECOVERY = ROOT / "static" / "js" / "workbench" / "canvas" / "viewport-recovery.js"


def run_runtime(script: str):
    source = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(RUNTIME))}, 'utf8'), sandbox);
const Runtime = sandbox.window.WorkbenchCanvasRuntime;
{script}
"""
    result = subprocess.run(["node", "-e", source], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


class CanvasRuntimeStateTests(unittest.TestCase):
    def test_shared_viewport_fit_centers_bounds_and_respects_scale_limits(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(VIEWPORT_RECOVERY))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasViewportRecovery;
console.log(JSON.stringify({{fit:R.fit([{{x:100,y:200,w:200,h:100}}],{{width:1000,height:700}},{{padding:0,inset:0,minScale:.1,maxScale:2}}), empty:R.fit([],{{width:800,height:600}},{{emptyScale:.5}})}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["fit"], {"scale":2, "x":100, "y":-150})
        self.assertEqual(payload["empty"], {"scale":.5, "x":400, "y":300})

    def test_shared_group_membership_resolves_parent_and_scope_without_node_types(self):
        source = GROUP_MEMBERSHIP.read_text(encoding="utf-8")
        self.assertNotIn("node.type", source)
        self.assertNotIn("document.", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(GROUP_MEMBERSHIP))}, 'utf8'), sandbox);
const G=sandbox.window.WorkbenchCanvasGroupMembership, groups=[{{id:'g1',items:['a','b','a']}},{{id:'g2',items:['g1']}}];
console.log(JSON.stringify({{parent:G.containingGroupId(groups,'a'), scopeMember:G.scopeId(groups,['g1','g2'],'a'), scopeGroup:G.scopeId(groups,['g1','g2'],'g2'), missing:G.scopeId(groups,['g1','g2'],'none')}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload, {"parent":"g1", "scopeMember":"g1", "scopeGroup":"g2", "missing":""})

    def test_shared_port_drop_intent_normalizes_both_drag_directions(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(GRAPH_INTERACTION))}, 'utf8'), sandbox);
const I=sandbox.window.WorkbenchCanvasGraphInteraction;
console.log(JSON.stringify({{forward:I.edgeIntentFromPortDrop({{nodeId:'a',port:'out'}},{{nodeId:'b',port:'in'}}), reverse:I.edgeIntentFromPortDrop({{nodeId:'b',port:'in'}},{{nodeId:'a',port:'out'}}), invalid:I.edgeIntentFromPortDrop({{nodeId:'a',port:'out'}},{{nodeId:'b',port:'out'}})}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        expected = {"from": "a", "to": "b", "fromPort": "out", "toPort": "in"}
        self.assertEqual(payload["forward"], expected)
        self.assertEqual(payload["reverse"], expected)
        self.assertIsNone(payload["invalid"])

    def test_shared_port_compatibility_keeps_unknown_legacy_ports_and_rejects_declared_mismatch(self):
        source = PORT_COMPATIBILITY.read_text(encoding="utf-8")
        self.assertNotIn("node.type", source)
        self.assertNotIn("document.", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PORT_COMPATIBILITY))}, 'utf8'), sandbox);
const C=sandbox.window.WorkbenchCanvasPortCompatibility;
console.log(JSON.stringify({{legacy:C.isCompatible({{direction:'out'}},{{direction:'in'}}), typed:C.isCompatible({{direction:'out',dataType:'asset'}},{{direction:'in',dataType:'asset'}}), mismatch:C.isCompatible({{direction:'out',dataType:'asset'}},{{direction:'in',dataType:'text'}}), reversed:C.isCompatible({{direction:'in'}},{{direction:'out'}})}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"legacy": True, "typed": True, "mismatch": False, "reversed": False})

    def test_execution_compatibility_wraps_retained_execution_without_runtime_selection(self):
        source = EXECUTION_COMPATIBILITY.read_text(encoding="utf-8")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("localStorage", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(EXECUTION_COMPATIBILITY))}, 'utf8'), sandbox);
const E=sandbox.window.WorkbenchCanvasExecutionCompatibility;
(async()=>{{
  const completed=await E.run({{canvasKind:'classic', sourceNodeId:'node-1', execute:async()=> 'legacy-result'}});
  let failed;
  try {{ await E.run({{canvasKind:'smart', sourceNodeId:'node-2', execute:async()=>{{throw new Error('retained failure');}}}}); }}
  catch(error) {{ failed={{message:error.message, metadata:error.workbenchExecutionCompatibility}}; }}
  console.log(JSON.stringify({{completed, completedFrozen:Object.isFrozen(completed), failed}}));
}})();
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(
            {key: payload["completed"][key] for key in ("status", "canvasKind", "sourceNodeId", "result")},
            {"status": "completed", "canvasKind": "classic", "sourceNodeId": "node-1", "result": "legacy-result"},
        )
        self.assertTrue(payload["completedFrozen"])
        self.assertEqual(payload["failed"]["message"], "retained failure")
        self.assertEqual(
            {key: payload["failed"]["metadata"][key] for key in ("status", "canvasKind", "sourceNodeId")},
            {"status": "failed", "canvasKind": "smart", "sourceNodeId": "node-2"},
        )

    def test_connected_creation_client_requires_revision_before_network(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{location:{{hostname:'localhost',search:''}}}}, fetch:()=>{{throw new Error('network must not run')}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_CLIENT))}, 'utf8'), sandbox);
try {{ sandbox.window.WorkbenchNodeClient.createNodeAndEdge('canvas', {{}}, 'actor'); }} catch (error) {{ console.log(error.message); }}
"""], check=True, text=True, capture_output=True)
        self.assertIn("positive expected_revision", result.stdout)

    def test_shared_graph_geometry_has_symmetric_port_anchors_and_no_dom_dependency(self):
        source = GRAPH_GEOMETRY.read_text(encoding="utf-8")
        self.assertNotIn("document.", source)
        self.assertNotIn("fetch(", source)
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(GRAPH_GEOMETRY))}, 'utf8'), sandbox);
const G=sandbox.window.WorkbenchCanvasGraphGeometry, r={{x:10,y:20,width:100,height:80}};
console.log(JSON.stringify({{left:G.portAnchor(r,'left'),right:G.portAnchor(r,'right'),path:G.horizontalBezier(G.portAnchor(r,'right'),G.portAnchor({{x:260,y:20,width:100,height:80}},'left'))}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["left"], {"x": 10, "y": 60})
        self.assertEqual(payload["right"], {"x": 110, "y": 60})
        self.assertTrue(payload["path"].startswith("M110 60 C"))
    def test_page_adapter_uses_the_shared_runtime_only_when_opted_in(self):
        # R4-36: smart-canvas.js retired. The unified runtime is owned by
        # canvas.html only.
        source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("unified_canvas') !== '0'", source)
        self.assertIn("canvasUnifiedRuntimeEnabled", source)
        self.assertIn("ensureCanvasViewportController", source)
        self.assertIn("applyCanvasRuntimeSelection", source)
        self.assertIn("canvasViewportController.zoomAt(", source)

    def test_page_adapter_writes_drag_and_resize_through_runtime_commands(self):
        # R4-36: smart-canvas.js retired. The unified runtime drag/resize
        # commands are owned by canvas.html only.
        source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("applyCanvasRuntimeNodeMove", source)
        self.assertIn("applyCanvasRuntimeNodeResize", source)
        self.assertIn("COMMANDS.NODE_MOVE", source)
        self.assertIn("COMMANDS.NODE_RESIZE", source)

    def test_viewport_coordinates_and_anchor_zoom_are_shared(self):
        result = run_runtime("""
const runtime = Runtime.create({viewport:{x:10,y:20,scale:2}, minScale:0.06, maxScale:8});
const before = Runtime.screenToWorld({x:110,y:220}, runtime.snapshot().viewport);
runtime.dispatch({type:Runtime.COMMANDS.VIEWPORT_ZOOM_AT, anchor:{x:110,y:220}, scale:4});
const after = Runtime.screenToWorld({x:110,y:220}, runtime.snapshot().viewport);
console.log(JSON.stringify({before, after, viewport:runtime.snapshot().viewport}));
""")
        self.assertEqual(result["before"], {"x": 50, "y": 100})
        self.assertEqual(result["after"], result["before"])
        self.assertEqual(result["viewport"], {"x": -90, "y": -180, "scale": 4})

    def test_selection_and_geometry_use_one_command_model(self):
        result = run_runtime("""
const runtime = Runtime.create({
  nodes:[{id:'a',x:1,y:2,w:100,h:80},{id:'b',x:5,y:6,width:120,height:90}],
  selectedIds:['a','missing','a'],
});
runtime.dispatch({type:Runtime.COMMANDS.SELECTION_TOGGLE,id:'b'});
runtime.dispatch({type:Runtime.COMMANDS.NODE_MOVE,id:'a',x:30,y:40});
runtime.dispatch({type:Runtime.COMMANDS.NODE_RESIZE,id:'b',width:0,height:150});
console.log(JSON.stringify(runtime.snapshot()));
""")
        self.assertEqual(result["selectedIds"], ["a", "b"])
        geometry = {item["id"]: item for item in result["geometry"]}
        self.assertEqual(geometry["a"], {"id": "a", "x": 30, "y": 40, "width": 100, "height": 80})
        self.assertEqual(geometry["b"]["width"], 1)
        self.assertEqual(geometry["b"]["height"], 150)
        self.assertEqual(result["revision"], 3)

    def test_module_has_no_dom_storage_or_network_dependency(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertNotIn("document.", text)
        self.assertNotIn("localStorage", text)
        self.assertNotIn("sessionStorage", text)
        self.assertNotIn("fetch(", text)
        self.assertNotIn("node.type", text)
        self.assertNotIn("smart-", text)


if __name__ == "__main__":
    unittest.main()
