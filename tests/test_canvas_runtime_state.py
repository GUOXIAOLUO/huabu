import json
import subprocess
import unittest
from pathlib import Path

from tests.canvas_app_source import read_canvas_app_source


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js"
GRAPH_GEOMETRY = ROOT / "static" / "js" / "workbench" / "canvas" / "graph-geometry.js"
GRAPH_INTERACTION = ROOT / "static" / "js" / "workbench" / "canvas" / "graph-interaction.js"
GRAPH_FRAGMENT = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-graph-fragment.js"
WORKFLOW_UI = ROOT / "static" / "js" / "workbench" / "canvas" / "workflow-transfer-ui.js"
PROMPT_DATA = ROOT / "static" / "js" / "workbench" / "canvas" / "prompt-template-data.js"
PROMPT_INTERACTION = ROOT / "static" / "js" / "workbench" / "canvas" / "prompt-template-interaction.js"
PROMPT_APPLICATION = ROOT / "static" / "js" / "workbench" / "canvas" / "prompt-template-application.js"
PROMPT_RENDERER = ROOT / "static" / "js" / "workbench" / "canvas" / "prompt-template-renderer.js"
MEDIA_EDITOR_STATE = ROOT / "static" / "js" / "workbench" / "canvas" / "media-editor-state.js"
MEDIA_TEXT_OVERLAY = ROOT / "static" / "js" / "workbench" / "canvas" / "media-text-overlay.js"
MEDIA_OUTPUT_RENDERER = ROOT / "static" / "js" / "workbench" / "canvas" / "media-output-renderer.js"
MEDIA_TOOLS = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
NODE_PRESENTATION = ROOT / "static" / "js" / "workbench" / "canvas" / "node-presentation.js"
PORT_COMPATIBILITY = ROOT / "static" / "js" / "workbench" / "canvas" / "port-compatibility.js"
EXECUTION_COMPATIBILITY = ROOT / "static" / "js" / "workbench" / "canvas" / "execution-compatibility.js"
NODE_CLIENT = ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js"
GROUP_MEMBERSHIP = ROOT / "static" / "js" / "workbench" / "canvas" / "group-membership.js"
VIEWPORT_RECOVERY = ROOT / "static" / "js" / "workbench" / "canvas" / "viewport-recovery.js"
CANVAS_RECORDS = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-app-records.js"
REMOTE_SYNC = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-remote-sync.js"
SAVE_SCHEDULER = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-save-scheduler.js"
PERSISTENCE = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"


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
    def test_scheduler_drain_waits_until_quiescent_and_cancel_clears_retry(self):
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}},setTimeout,clearTimeout}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(SAVE_SCHEDULER))}, 'utf8'), sandbox);
(async()=>{{ let release, runs=0; let onRetry=0;
  const scheduler=sandbox.window.WorkbenchCanvasSaveScheduler.create({{run:async()=>{{ runs++; if(runs===1) await new Promise(resolve=>release=resolve); }}, onRetry:()=>onRetry++}});
  scheduler.schedule(1); await new Promise(resolve=>setTimeout(resolve,5)); scheduler.schedule(1);
  const draining=scheduler.drain(); await new Promise(resolve=>setTimeout(resolve,5));
  if(runs!==1) throw Error('drain did not wait for in-flight save'); release(); await draining;
  if(runs!==2 || scheduler.hasScheduled() || scheduler.hasPendingAgain() || scheduler.isInFlight()) throw Error('scheduler not quiescent');
  scheduler.schedule(100); scheduler.cancel();
  console.log(JSON.stringify({{runs,onRetry,scheduled:scheduler.hasScheduled(),again:scheduler.hasPendingAgain()}}));
}})().catch(error=>{{console.error(error);process.exit(1);}});
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"runs": 2, "onRetry": 1, "scheduled": False, "again": False})

    def test_adopt_revision_does_not_change_updated_at_or_session_timestamp(self):
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}},fetch:async()=>({{ok:true,status:200,json:async()=>({{}})}})}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PERSISTENCE))}, 'utf8'), sandbox);
const canvas={{id:'c1',updated_at:1234}}; const adopted=sandbox.window.WorkbenchCanvasPersistence.adoptRevision(canvas,9,99);
console.log(JSON.stringify({{canvas,adopted,cursor:sandbox.window.WorkbenchCanvasPersistence.revisionOf('c1')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"canvas": {"id": "c1", "updated_at": 1234}, "adopted": 9, "cursor": 9})

    def test_canvas_metadata_edits_use_the_metadata_boundary_without_graph_put(self):
        source = CANVAS_RECORDS.read_text(encoding="utf-8")
        icon_block = source[source.index("async function setCanvasIcon"):source.index("function startTitleEdit")]
        title_block = source[source.index("async function setCanvasTitle"):source.index("async function openCanvas")]
        for block, field in ((icon_block, "icon"), (title_block, "title")):
            self.assertIn("/api/canvases/${encodeURIComponent(id)}/meta", block)
            self.assertIn("method:'POST'", block)
            self.assertIn(f"JSON.stringify({{{field}", block)
            self.assertNotIn("method:'PUT'", block)
            self.assertNotIn("nodes:target.nodes", block)
            self.assertNotIn("connections:target.connections", block)

    def test_interaction_graph_array_projections_use_the_bounded_legacy_seam(self):
        source = (ROOT / "static/js/workbench/canvas/canvas-app-interaction.js").read_text(encoding="utf-8")
        self.assertNotIn("nodes.push", source)
        self.assertNotIn("connections.push", source)
        mutation = (ROOT / "static/js/workbench/canvas/legacy-canvas-mutation.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchLegacyCanvasMutation", mutation)
        self.assertIn("appendNode", mutation)
        self.assertIn("appendConnection", mutation)

    def test_output_preview_and_compare_share_one_global_pointer_pair(self):
        source = (ROOT / "static/js/workbench/canvas/canvas-app-output-ui.js").read_text(encoding="utf-8")
        self.assertIn("let outputGlobalPointerEventsBound = false;", source)
        self.assertIn("let outputPreviewEventsBound = false;", source)
        self.assertIn("let outputCompareEventsBound = false;", source)
        self.assertIn("if(outputPreviewEventsBound) return;", source)
        self.assertIn("if(outputCompareEventsBound) return;", source)
        self.assertIn("if(outputGlobalPointerEventsBound) return;", source)
        self.assertEqual(source.count("window.addEventListener('mousemove'"), 1)
        self.assertEqual(source.count("window.addEventListener('mouseup'"), 1)

    def test_remote_sync_start_stop_is_idempotent(self):
        script = f"""
const fs = require('fs'), vm = require('vm');
const timers = [];
const sandbox = {{ setInterval: (fn, ms) => {{ timers.push({{fn, ms}}); return timers.length; }}, clearInterval: id => {{ timers[id - 1].cleared = true; }}, window: {{ WorkbenchCanvasPersistence: {{ metadata: async () => ({{ok:false}}) }} }} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(REMOTE_SYNC))}, 'utf8'), sandbox);
const sync = sandbox.window.WorkbenchCanvasRemoteSync.create({{canvasId: () => 'c1', currentUpdatedAt: () => 0, onNewer: async () => {{}}}});
sync.start(); sync.start(); const once = timers.length; sync.stop(); sync.stop();
console.log(JSON.stringify({{once, cleared: timers[0].cleared, running: sync.isRunning()}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"once": 1, "cleared": True, "running": False})
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

    def test_shared_graph_fragment_removes_node_and_incident_edges_for_all_delete_paths(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(GRAPH_FRAGMENT))}, 'utf8'), sandbox);
const G=sandbox.window.WorkbenchCanvasGraphFragment;
const removed=G.removeGraphRecords({{nodes:[{{id:'a'}},{{id:'b'}}],connections:[{{id:'ab',from:'a',to:'b'}},{{id:'zz',from:'b',to:'b'}}],removeIds:['a']}});
const edgeRemoved=G.removeConnection({{connections:[{{id:'ab'}},{{id:'zz'}}],connectionId:'ab'}});
let next=0;
const duplicate=G.duplicateSubgraph({{node:{{id:'g',type:'group',items:['a']}},nodes:[{{id:'g',type:'group',items:['a']}},{{id:'a',type:'image'}}],connections:[{{id:'in',from:'x',to:'a'}}],serializeNode:n=>JSON.parse(JSON.stringify(n)),createNodeId:type=>type+ ++next,childIds:n=>n.items||[],preserveConnections:true,canConnect:()=>true}});
const expanded=[...G.expandNodeIds({{nodes:[{{id:'g',items:['a']}},{{id:'a'}}],initialIds:['g'],childIds:n=>n.items||[]}})];
console.log(JSON.stringify({{removed,edgeRemoved,expanded,duplicate}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "removed": {"nodes": [{"id": "b"}], "connections": [{"id": "zz", "from": "b", "to": "b"}]},
            "edgeRemoved": [{"id": "zz"}],
            "expanded": ["g", "a"],
            "duplicate": {"root": {"id": "group1", "type": "group", "items": ["image2"], "running": False}, "copies": [{"id": "group1", "type": "group", "items": ["image2"], "running": False}, {"id": "image2", "type": "image", "running": False}], "connections": [{"id": "c3", "from": "x", "to": "image2"}], "idMap": {}},
        })
        page_source = read_canvas_app_source(ROOT)
        self.assertGreaterEqual(page_source.count("WorkbenchCanvasGraphFragment.removeGraphRecords"), 9)

    def test_workflow_transfer_ui_owns_modal_lifecycle_and_metadata(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const events=[];
const make=()=>({{classList:{{add:x=>events.push('add:'+x),remove:x=>events.push('remove:'+x)}}}});
const sandbox={{window:{{}}, document:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(WORKFLOW_UI))}, 'utf8'), sandbox);
const meta={{textContent:''}}, sub={{textContent:''}}, api=sandbox.window.WorkbenchCanvasWorkflowTransferUi.create({{
  modal:make(),toggle:make(),dropZone:make(),meta,sub,refreshIcons:()=>events.push('icons'),
  payload:()=>({{nodes:[{{id:'n'}}],connections:[{{id:'c'}}]}}),hasCanvas:()=>true,
}});
api.open(); api.close();
console.log(JSON.stringify({{meta:meta.textContent,sub:sub.textContent,events}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "meta": "已选择 1 个节点，1 条连线",
            "sub": "导出当前框选内容，或把工作流导入到当前画布",
            "events": ["add:open", "add:active", "icons", "remove:open", "remove:active", "remove:drag-over"],
        })

    def test_workflow_transfer_client_owns_safe_export_filename_projection(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "workflow-transfer-client.js"
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}},Date,URL, setTimeout}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
console.log(sandbox.window.WorkbenchCanvasWorkflowTransfer.filenameForExport('A:/bad*name?', '.json', '2026-01-02T03:04:05.000Z'));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), "A_bad_name_-20260102T030405.json")

    def test_media_editor_state_owns_mode_normalization_and_presentation(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_EDITOR_STATE))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasMediaEditorState;
console.log(JSON.stringify({{invalid:S.presentation('unknown'),grid:S.presentation('grid'),preview:S.presentation('preview'),actions:[S.applyAction('outpaint'),S.applyAction('resize'),S.applyAction('unknown')]}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "invalid": {"mode": "crop", "preview": False, "icon": "crop", "labelKey": "canvas.applyCrop", "titleKey": "canvas.cropImage", "subKey": "canvas.cropHint"},
            "grid": {"mode": "grid", "preview": False, "icon": "grid-3x3", "labelKey": "canvas.applyGrid", "titleKey": "canvas.modeGrid", "subKey": "canvas.gridHint"},
            "preview": {"mode": "preview", "preview": True, "icon": "", "labelKey": "", "titleKey": "canvas.previewImage", "subKey": "canvas.previewHint"},
            "actions": ["applyImageOutpaint", "applyImageResize", "applyImageCrop"],
        })

    def test_media_tools_owns_mask_projection_from_drawn_alpha(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm');
const pixels=new Uint8ClampedArray([0,0,0,9, 0,0,0,8]);
const output={{data:new Uint8ClampedArray(8)}};
const context={{getImageData:()=>({{data:pixels}}),createImageData:()=>output,putImageData:value=>output.data=value.data}};
const sandbox={{window:{{}},document:{{createElement:()=>({{width:0,height:0,getContext:()=>context}})}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const mask=sandbox.window.WorkbenchCanvasMediaTools.maskFromCanvas({{width:2,height:1,getContext:()=>context}});
console.log(JSON.stringify(Array.from(mask.getContext().createImageData().data)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [255, 255, 255, 255, 0, 0, 0, 255])

    def test_media_tools_owns_outpaint_bounds_clamping(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const state=sandbox.window.WorkbenchCanvasMediaTools.clampOutpaintState({{x:-4,y:99,w:20,h:10}},100,80);
console.log(JSON.stringify(state));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"x": 0, "y": 0, "w": 100, "h": 80})

    def test_media_tools_owns_drawn_pixel_detection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
const make=data=>({{width:2,height:1,getContext:()=>({{getImageData:()=>({{data}})}})}});
console.log(JSON.stringify({{empty:T.canvasHasPixels(make([0,0,0,0,0,0,0,0])),painted:T.canvasHasPixels(make([0,0,0,0,0,0,0,1]))}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"empty": False, "painted": True})

    def test_media_tools_owns_outpaint_reset(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const state=sandbox.window.WorkbenchCanvasMediaTools.resetOutpaintState({{x:4,y:5,w:9,h:8}},120,90);
console.log(JSON.stringify(state));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"x": 0, "y": 0, "w": 120, "h": 90})

    def test_media_tools_owns_outpaint_natural_size_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.outpaintNaturalSize({{w:150,h:75}},1200,600,300,150)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"w": 600, "h": 300})

    def test_media_tools_owns_resized_image_blob_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const calls=[];
const context={{imageSmoothingEnabled:false,imageSmoothingQuality:'',drawImage:(...args)=>calls.push(args)}};
const canvas={{width:0,height:0,getContext:()=>context,toBlob:resolve=>resolve('blob')}};
const sandbox={{window:{{}}}}; vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
(async()=>{{const result=await sandbox.window.WorkbenchCanvasMediaTools.resizedImageBlob({{naturalWidth:100,naturalHeight:50}},{{targetW:40,targetH:20,scale:.4}},{{createElement:()=>canvas}}); console.log(JSON.stringify({{result,calls,canvas:{{width:canvas.width,height:canvas.height}},smooth:context.imageSmoothingQuality}}));}})();
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "result": {"blob": "blob", "targetW": 40, "targetH": 20, "scale": .4},
            "calls": [[{"naturalWidth": 100, "naturalHeight": 50}, 0, 0, 100, 50, 0, 0, 40, 20]],
            "canvas": {"width": 40, "height": 20}, "smooth": "high",
        })

    def test_media_tools_owns_brush_layer_composition(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const calls=[], context={{drawImage:(...args)=>calls.push(args)}};
const canvas={{width:0,height:0,getContext:()=>context}}; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const image={{naturalWidth:80,naturalHeight:40}}, draw={{id:'draw'}}, text={{id:'text'}};
const output=sandbox.window.WorkbenchCanvasMediaTools.composeBrushCanvas(image,draw,text,{{createElement:()=>canvas}});
console.log(JSON.stringify({{size:{{width:output.width,height:output.height}},calls}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "size": {"width": 80, "height": 40},
            "calls": [[{"naturalWidth": 80, "naturalHeight": 40}, 0, 0, 80, 40], [{"id": "draw"}, 0, 0], [{"id": "text"}, 0, 0]],
        })

    def test_media_tools_owns_crop_blob_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const calls=[], context={{drawImage:(...args)=>calls.push(args)}};
const canvas={{width:0,height:0,getContext:()=>context,toBlob:resolve=>resolve('crop-blob')}}; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
(async()=>{{const blob=await sandbox.window.WorkbenchCanvasMediaTools.cropImageBlob({{naturalWidth:100,naturalHeight:50}},{{x:4,y:5,w:20,h:10}},{{createElement:()=>canvas}}); console.log(JSON.stringify({{blob,size:{{width:canvas.width,height:canvas.height}},calls}}));}})();
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "blob": "crop-blob", "size": {"width": 20, "height": 10},
            "calls": [[{"naturalWidth": 100, "naturalHeight": 50}, 4, 5, 20, 10, 0, 0, 20, 10]],
        })

    def test_media_tools_owns_outpaint_blob_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const calls=[], context={{fillStyle:'',fillRect:(...args)=>calls.push(['fill',...args]),drawImage:(...args)=>calls.push(['image',...args])}};
const canvas={{width:0,height:0,getContext:()=>context,toBlob:resolve=>resolve('outpaint-blob')}}; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
(async()=>{{const blob=await sandbox.window.WorkbenchCanvasMediaTools.outpaintImageBlob({{naturalWidth:100,naturalHeight:50}},{{x:4,y:5,w:140,h:80}},{{createElement:()=>canvas}}); console.log(JSON.stringify({{blob,size:{{width:canvas.width,height:canvas.height}},calls}}));}})();
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "blob": "outpaint-blob", "size": {"width": 140, "height": 80},
            "calls": [["fill", 0, 0, 140, 80], ["image", {"naturalWidth": 100, "naturalHeight": 50}, 4, 5, 100, 50]],
        })

    def test_media_tools_owns_grid_split_blob_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); let index=0; const calls=[];
const context={{drawImage:(...args)=>calls.push(args)}};
const canvas={{width:0,height:0,getContext:()=>context,toBlob:resolve=>resolve('blob-'+(++index))}}; const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
(async()=>{{const result=await sandbox.window.WorkbenchCanvasMediaTools.splitImageBlobs({{naturalWidth:100,naturalHeight:50}},[{{x:0,y:0,w:50,h:25,row:0,col:0}},{{x:50,y:0,w:50,h:25,row:0,col:1}}],{{createElement:()=>canvas}}); console.log(JSON.stringify({{result,calls}}));}})();
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "result": [
                {"blob": "blob-1", "row": 0, "col": 0, "w": 50, "h": 25},
                {"blob": "blob-2", "row": 0, "col": 1, "w": 50, "h": 25},
            ],
            "calls": [
                [{"naturalWidth": 100, "naturalHeight": 50}, 0, 0, 50, 25, 0, 0, 50, 25],
                [{"naturalWidth": 100, "naturalHeight": 50}, 50, 0, 50, 25, 0, 0, 50, 25],
            ],
        })

    def test_media_tools_owns_png_blob_encoding_boundary(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
(async()=>{{console.log(JSON.stringify(await sandbox.window.WorkbenchCanvasMediaTools.toPngBlob({{toBlob:(resolve,type)=>resolve(type)}})));}})();
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), "image/png")

    def test_media_tools_owns_display_to_natural_crop_rect_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.cropRectFromDisplay({{x:2.4,y:3.1,w:20.2,h:10.4}},1000,500,200,100)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"x": 12, "y": 16, "w": 101, "h": 52})

    def test_media_tools_owns_display_to_natural_outpaint_rect_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.outpaintRectFromDisplay({{x:2,y:3,w:30,h:20}},100,50,200,100)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"x": 1, "y": 2, "w": 100, "h": 50})

    def test_media_tools_owns_output_base_name_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.baseNameWithoutExtension('photo.png'),T.baseNameWithoutExtension('photo'),T.baseNameWithoutExtension('', 'fallback')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["photo", "photo", "fallback"])

    def test_media_tools_owns_custom_grid_line_hit_and_position_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, lines=[{{type:'h',pos:.5}},{{type:'v',pos:.25}}];
const hit=T.customLineHit(lines,{{x:25,y:50}},100,100); T.setCustomLinePosition(lines[hit],{{x:80,y:90}},100,100);
console.log(JSON.stringify({{hit,lines}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"hit": 0, "lines": [{"type": "h", "pos": .9}, {"type": "v", "pos": .25}]})

    def test_media_tools_owns_grid_settings_normalization(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.normalizeGridSettings(-2,30,999),T.normalizeGridSettings('x','',-4)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"rows": 1, "cols": 21, "gap": 240}, {"rows": 1, "cols": 1, "gap": 0}])

    def test_media_tools_owns_brush_and_label_style_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{paint:T.brushStyle('brush',12,'#abc'),mask:T.brushStyle('mask',8,'#abc',128),label:T.labelStyle(40,'#def')}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["paint"]["strokeStyle"], "#abc")
        self.assertEqual(payload["mask"]["strokeStyle"], "rgba(255,255,255,0.5019607843137255)")
        self.assertEqual(payload["label"]["font"], "900 40px Arial, sans-serif")
        self.assertEqual(payload["label"]["fillStyle"], "#def")

    def test_media_tools_owns_crop_and_outpaint_drag_geometry(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{out:T.resizeOutpaintRect({{x:10,y:20,w:100,h:80}},'outpaint-right',30,0,120,90),free:T.resizeFreeCropRect({{x:10,y:20,w:100,h:80}},'se',-40,20)}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"out": {"x": 40, "y": 25, "w": 160, "h": 90}, "free": {"x": 10, "y": 20, "w": 60, "h": 100}})

    def test_media_tools_owns_aspect_crop_drag_geometry(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.resizeAspectCropRect({{x:20,y:20,w:100,h:80}},'e',30,0,1,200,200),T.resizeAspectCropRect({{x:20,y:20,w:100,h:80}},'s',0,30,2,200,200)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"x": 20, "y": 0, "w": 120, "h": 120}, {"x": 0, "y": 20, "w": 140, "h": 70}])

    def test_media_tools_owns_custom_grid_cut_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.customGridRects(100,80,[{{type:'h',pos:.5}},{{type:'h',pos:.5}},{{type:'v',pos:.25}}],0)));
"""], check=True, text=True, capture_output=True)
        rects = json.loads(result.stdout)
        self.assertEqual(len(rects), 4)
        self.assertEqual([(rect["row"], rect["col"], rect["w"], rect["h"]) for rect in rects], [(0,0,25,40),(0,1,75,40),(1,0,25,40),(1,1,75,40)])

    def test_workflow_transfer_client_owns_export_envelope_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/workflow-transfer-client.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasWorkflowTransfer;
console.log(JSON.stringify(T.exportPayload({{nodes:[{{id:'n1'}},null],connections:[null,{{id:'c1'}}]}},123)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"format":"infinite-canvas-workflow","version":1,"exported_at":123,"nodes":[{"id":"n1"}],"connections":[{"id":"c1"}]})

    def test_media_tools_owns_crop_initialization_and_clamping(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{initial:T.initialCropRect(200,100),clamped:T.clampCropRect({{x:-10,y:90,w:250,h:30}},200,100)}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"initial":{"x":16,"y":8,"w":168,"h":84},"clamped":{"x":0,"y":70,"w":200,"h":30}})

    def test_media_tools_owns_crop_zoom_scaling_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.scaleCropRect({{x:10,y:15,w:40,h:30}},1.5),T.scaleCropRect({{x:10,y:15,w:40,h:30}},0)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"x":15,"y":23,"w":60,"h":45},{"x":10,"y":15,"w":40,"h":30}])

    def test_media_tools_owns_crop_box_dom_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.cropBoxProjection({{x:10,y:15,w:40,h:30}},'crop'),T.cropBoxProjection({{x:10,y:15,w:40,h:30}},'outpaint')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"boxX":10,"boxY":15,"boxWidth":40,"boxHeight":30,"imageLeft":None,"imageTop":None,"frameLeft":10,"frameTop":15,"frameWidth":40,"frameHeight":30},
            {"boxX":0,"boxY":0,"boxWidth":40,"boxHeight":30,"imageLeft":10,"imageTop":15,"frameLeft":0,"frameTop":0,"frameWidth":40,"frameHeight":30},
        ])

    def test_media_editor_state_owns_mode_ui_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/media-editor-state.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaEditorState;
console.log(JSON.stringify([T.uiProjection('preview','brush'),T.uiProjection('grid','grid'),T.uiProjection('outpaint','crop')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"mode":"preview","preview":True,"activeModes":{"crop":False,"mask":False,"brush":False,"resize":False,"grid":False,"outpaint":False},"applyVisible":False,"icon":"","titleKey":"canvas.previewImage","subKey":"canvas.previewHint","clearDrawing":True,"refreshGrid":False,"resetOutpaint":False},
            {"mode":"grid","preview":False,"activeModes":{"crop":False,"mask":False,"brush":False,"resize":False,"grid":True,"outpaint":False},"applyVisible":True,"icon":"grid-3x3","titleKey":"canvas.modeGrid","subKey":"canvas.gridHint","clearDrawing":True,"refreshGrid":True,"resetOutpaint":False},
            {"mode":"outpaint","preview":False,"activeModes":{"crop":False,"mask":False,"brush":False,"resize":False,"grid":False,"outpaint":True},"applyVisible":True,"icon":"expand","titleKey":"canvas.outpaintImage","subKey":"canvas.outpaintHint","clearDrawing":False,"refreshGrid":False,"resetOutpaint":True},
        ])

    def test_media_tools_owns_editor_zoom_and_overflow_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.editorZoomProjection(640,480,1.25),T.editorOverflowProjection(700,500,640,480,36),T.editorOverflowProjection(600,400,640,480,36)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"width":800,"height":600,"label":"125%"},
            {"overflowX":True,"overflowY":True,"overflowing":True},
            {"overflowX":False,"overflowY":False,"overflowing":False},
        ])

    def test_media_editor_state_owns_brush_tool_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/media-editor-state.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaEditorState;
console.log(JSON.stringify([T.brushToolProjection('text','brush'),T.brushToolProjection('unknown','brush'),T.brushToolProjection('text','mask')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"tool":"text","textMode":True},
            {"tool":"free","textMode":False},
            {"tool":"text","textMode":False},
        ])

    def test_media_tools_owns_editor_canvas_size_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.editorCanvasProjection(800,600,400,300),T.editorCanvasProjection(0,0,0,0)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"width":800,"height":600,"cssWidth":400,"cssHeight":300},
            {"width":1,"height":1,"cssWidth":1,"cssHeight":1},
        ])

    def test_media_tools_owns_brush_control_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.brushControlProjection('brush',12,28,'#123456'),T.brushControlProjection('mask',12,28,'#123456',115),T.brushControlProjection('brush',0,0,'')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"size":28,"color":"#123456","alpha":255},
            {"size":12,"color":"#ffffff","alpha":115},
            {"size":20,"color":"#ff2d55","alpha":255},
        ])

    def test_media_tools_owns_output_preview_transform_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.previewTransformProjection(1.5,{{x:12,y:-4}}),T.previewTransformProjection(0,{{}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"transform":"translate(12px, -4px) scale(1.5)","zoomed":True},
            {"transform":"translate(0px, 0px) scale(1)","zoomed":False},
        ])

    def test_media_tools_owns_compare_slider_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.compareSliderProjection(150,100,200),T.compareSliderProjection(50,100,200),T.compareSliderProjection(50,100,0)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"percent":25,"clipPath":"inset(0 75% 0 0)"},
            {"percent":0,"clipPath":"inset(0 100% 0 0)"},
            {"percent":0,"clipPath":"inset(0 100% 0 0)"},
        ])

    def test_media_tools_owns_output_preview_zoom_and_pan_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.previewZoomProjection(1,{{x:0,y:0}},-1,50,40),T.previewZoomProjection(1.1,{{x:2,y:3}},1,50,40),T.previewPanProjection({{sx:10,sy:20,ox:4,oy:5}},25,35)]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertEqual(values[0]["zoom"], 1.1)
        self.assertAlmostEqual(values[0]["pan"]["x"], -5)
        self.assertAlmostEqual(values[0]["pan"]["y"], -4)
        self.assertEqual(values[1]["zoom"], 1)
        self.assertEqual(values[1]["pan"], {"x":0,"y":0})
        self.assertEqual(values[2], {"x":19,"y":20})

    def test_prompt_renderer_owns_prompt_preview_inputs(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/prompt-template-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasPromptTemplateRenderer;
console.log(JSON.stringify([T.renderPreviewInputs([],x=>x),T.renderPreviewInputs([{{label:'A & B'}},null],x=>String(x).replace(/&/g,'&amp;'))]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)[0], '')
        self.assertIn('A &amp; B', json.loads(result.stdout)[1])

    def test_media_input_renderer_owns_list_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/media-input-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaInputRenderer;
console.log(JSON.stringify([T.emptyMarkup('No inputs',x=>x),T.itemMarkup({{label:'A & B',preview:'u'}},1,{{escapeHtml:x=>String(x).replace(/&/g,'&amp;'),preview:x=>`<img src="${{x}}">`,isMissing:()=>false}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('No inputs', values[0])
        self.assertIn('A &amp; B', values[1])
        self.assertIn('<img src="u">', values[1])

    def test_canvas_uses_shared_media_input_renderer_for_runninghub_inputs(self):
        source = read_canvas_app_source(ROOT)
        self.assertIn('WorkbenchCanvasMediaInputRenderer.itemMarkup({', source)
        self.assertNotIn('item.innerHTML = `<span class="input-index">${i + 1}</span>${rhMediaPreviewHtml(ref, kind)}', source)

    def test_canvas_uses_shared_media_input_renderer_for_comfy_inputs(self):
        source = read_canvas_app_source(ROOT)
        self.assertIn('WorkbenchCanvasMediaInputRenderer.emptyMarkup(tr(\'canvas.groupEmpty\')', source)
        self.assertIn('WorkbenchCanvasMediaInputRenderer.itemMarkup({...src, label}', source)

    def test_llm_pane_renderer_owns_panel_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/llm-pane-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLlmPaneRenderer;
console.log(JSON.stringify([T.paneMarkup({{inputValue:'A & B',outputText:'ok',inputHeight:70,outputHeight:80,escapeHtml:x=>String(x).replace(/&/g,'&amp;'),runLabel:'Run'}}),T.chatMarkup({{messages:[],emptyLabel:'Empty',placeholder:'Chat',sendLabel:'Send',escapeHtml:x=>x}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('A &amp; B', values[0])
        self.assertIn('llm-chat-log', values[1])

    def test_llm_pane_renderer_owns_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/llm-pane-renderer.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasLlmPaneRenderer.state;
console.log(JSON.stringify([S({{connectedInput:'  linked  ',userInput:'manual',inputHeight:40,outputHeight:60}}),S({{userInput:'manual'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"readonly": True, "inputValue": "  linked  ", "inputHeight": 70, "outputHeight": 70},
            {"readonly": False, "inputValue": "manual", "inputHeight": 110, "outputHeight": 150},
        ])

    def test_llm_pane_renderer_owns_chat_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/llm-pane-renderer.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasLlmPaneRenderer.chatState;
console.log(JSON.stringify([S({{messages:[{{role:'user',content:'x'}}],input:' hi ',running:true,sendingLabel:'Sending',sendLabel:'Send'}}),S({{messages:null,input:null,running:false,sendingLabel:'Sending',sendLabel:'Send'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"messages": [{"role": "user", "content": "x"}], "input": " hi ", "running": True, "sendLabel": "Sending"},
            {"messages": [], "input": "", "running": False, "sendLabel": "Send"},
        ])

    def test_runninghub_field_renderer_owns_field_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.render({{kind:'boolean',key:'x',label:'Flag',active:true}}),T.render({{kind:'select',key:'y',label:'Mode',value:'a',options:['a','b']}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('setting-check active', values[0])
        self.assertIn('<option value="a" selected>', values[1])

    def test_runninghub_field_renderer_owns_prompt_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(T.promptMarkup({{label:'Prompt &',key:'p',value:'A < B',escapeHtml:x=>String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;'),escapeAttr:x=>x}}));
"""], check=True, text=True, capture_output=True)
        self.assertIn('Prompt &amp;', result.stdout)
        self.assertIn('A &lt; B', result.stdout)

    def test_runninghub_field_renderer_owns_prompt_field_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const fields=[{{nodeId:'n1',fieldName:'prompt',role:'prompt',label:'Prompt'}},{{nodeId:'n1',fieldName:'steps',role:'setting'}}];
console.log(JSON.stringify(R.promptFields(fields,{{roleOf:f=>f.role,keyOf:(n,f)=>n+'::'+f,valueOf:f=>'value:'+f.fieldName}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{
            "field": {"nodeId": "n1", "fieldName": "prompt", "role": "prompt", "label": "Prompt"},
            "key": "n1::prompt", "label": "Prompt", "value": "value:prompt",
        }])

    def test_runninghub_field_renderer_owns_setting_field_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([R.settingField({{type:'slider',min:2,max:9,step:0}},'s','slider','Slider','bad'),R.settingField({{type:'number',random_enabled:true}},'n','number','Number','3',[],true,true),R.settingField({{type:'boolean'}},'b','boolean','Flag','TRUE')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"kind": "slider", "key": "s", "label": "Slider", "numericValue": 2, "min": 2, "max": 9, "step": 0.01},
            {"kind": "number", "key": "n", "label": "Number", "value": "3", "random": True, "randomActive": True},
            {"kind": "boolean", "key": "b", "label": "Flag", "active": True},
        ])

    def test_runninghub_field_renderer_owns_random_toggle_transition(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([R.toggleRandomActive({{seed:false}},'seed'),R.toggleRandomActive({{}},'seed')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"seed": True}, {"seed": False}])

    def test_runninghub_field_renderer_owns_entry_options_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([R.entryOptions({{model:[{{id:'m1',name:'Model'}}],app:[],workflow:[]}},'model:m1',{{idOf:e=>e.id,labelOf:e=>e.name}}),R.entryOptions({{}},'',{{}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('<optgroup', values[0]); self.assertIn('selected', values[0]); self.assertIn('请先在 API 设置', values[1])

    def test_runninghub_field_renderer_owns_payment_options_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(R.paymentOptions('wallet',{{has_key:true,has_wallet_key:false}}));
"""], check=True, text=True, capture_output=True)
        self.assertIn('value="wallet" selected', result.stdout)
        self.assertIn('账户余额 Key（未配置）', result.stdout)

    def test_runninghub_field_renderer_owns_workflow_load_cache_and_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer, cache={{}}; let calls=0;
const fetcher=async id=>({{ok:++calls<2,json:async()=>({{workflow:{{id,ok:true}}}})}});
(async()=>{{const a=await R.loadWorkflow('w1',cache,fetcher); const b=await R.loadWorkflow('w1',cache,fetcher); const c=await R.loadWorkflow('w2',cache,fetcher); console.log(JSON.stringify({{a,b,c,calls,cache}}));}})().catch(e=>{{console.error(e);process.exit(1)}});
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"a": {"id": "w1", "ok": True}, "b": {"id": "w1", "ok": True}, "c": None, "calls": 2, "cache": {"w1": {"id": "w1", "ok": True}}})

    def test_comfy_field_renderer_owns_dynamic_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasComfyFieldRenderer;
console.log(JSON.stringify([T.render({{type:'boolean',id:'x',label:'Flag',active:true}}),T.render({{type:'dropdown',id:'y',label:'Mode',value:'a',options:['a','b']}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('setting-check active', values[0])
        self.assertIn('<option value="a" selected>', values[1])

    def test_media_input_renderer_owns_runninghub_list_state(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/media-input-renderer.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasMediaInputRenderer.listState;
console.log(JSON.stringify([S({{refs:[{{url:'a'}},null,{{url:'b'}}]}}),S({{refs:null}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"refs": [{"url": "a"}, {"url": "b"}], "empty": False},
            {"refs": [], "empty": True},
        ])

    def test_media_input_renderer_list_state_is_shared_by_generic_and_runninghub_paths(self):
        source = read_canvas_app_source(ROOT)
        self.assertGreaterEqual(source.count('WorkbenchCanvasMediaInputRenderer.listState'), 3)
        self.assertIn('const inputState = WorkbenchCanvasMediaInputRenderer.listState({refs:imageInputs});', source)
        self.assertIn('const inputState = WorkbenchCanvasMediaInputRenderer.listState(media);', source)

    def test_comfy_field_renderer_owns_field_projection_and_random_policy(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}},Math:{{min:Math.min,max:Math.max,floor:Math.floor,random:()=>0}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasComfyFieldRenderer;
const fields=[{{id:'prompt',type:'textarea',name:'Prompt'}},{{id:'seed',type:'number',name:'Seed',random_enabled:true,default:7}},{{id:'flag',type:'boolean',default:false}}];
const P=R.create({{currentWorkflow:()=>({{config:{{fields}}}})}}), node={{comfyParams:{{seed:11}}}};
console.log(JSON.stringify({{kinds:fields.map(R.kind),prompts:P.fields(node,'prompt').map(f=>f.id),value:P.paramValue(node,fields[1]),enabled:P.randomEnabled(fields[1]),active:P.randomActive(node,'seed'),seed:P.randomValue({{min:5,max:6,name:'seed'}})}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kinds"], ["prompt", "setting", "setting"])
        self.assertEqual(payload["prompts"], ["prompt"])
        self.assertEqual(payload["value"], 11)
        self.assertTrue(payload["enabled"])
        self.assertTrue(payload["active"])
        self.assertEqual(payload["seed"], 5)

    def test_comfy_field_renderer_owns_random_toggle_transition(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasComfyFieldRenderer.create();
console.log(JSON.stringify([P.toggleRandomActive({{seed:false}},'seed'),P.toggleRandomActive({{}},'seed')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"seed": True}, {"seed": False}])

    def test_comfy_field_renderer_owns_workflow_name_selection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasComfyFieldRenderer;
console.log(JSON.stringify([R.workflowName('b',[{{name:'a'}},{{name:'b'}}]),R.workflowName('x',[{{name:'a'}}]),R.workflowName('x',[])]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["b", "a", ""])

    def test_comfy_field_renderer_owns_workflow_presence_check(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasComfyFieldRenderer;
console.log(JSON.stringify([R.hasWorkflow('a',[{{name:'a'}}]),R.hasWorkflow('x',[{{name:'a'}}]),R.hasWorkflow('a',null)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, False, False])

    def test_comfy_field_renderer_owns_workflow_load_cache_and_failure_cleanup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/comfy-field-renderer.js'))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasComfyFieldRenderer, cache={{}}; let calls=0;
const fetcher=async name=>({{ok:++calls<2,json:async()=>({{name,payload:1}})}});
(async()=>{{const a=await R.loadWorkflow('a',[{{name:'a'}}],cache,fetcher); const b=await R.loadWorkflow('b',[{{name:'b'}}],cache,fetcher); const c=await R.loadWorkflow('a',[{{name:'a'}}],cache,fetcher); console.log(JSON.stringify({{a,b,c,calls,cache}}));}})().catch(e=>{{console.error(e);process.exit(1)}});
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"a": {"name": "a", "payload": 1}, "b": None, "c": {"name": "a", "payload": 1}, "calls": 2, "cache": {"a": {"name": "a", "payload": 1}}})

    def test_loop_prompt_renderer_owns_token_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify([T.render({{showPrompt:true,index:2,total:5,selected:'x《计数》 [progress]',tokens:{{progress:'progress'}}}}),T.render({{showPrompt:false,variable:'x'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['x2 2/5', ''])

    def test_prompt_template_renderer_owns_preview_input_state(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/prompt-template-renderer.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasPromptTemplateRenderer.previewState;
console.log(JSON.stringify([S([{{label:'Prompt'}},null,{{label:'  '}}]),S(null)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"items": [{"label": "Prompt"}], "empty": False},
            {"items": [], "empty": True},
        ])

    def test_loop_layout_projection_owns_body_state(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-layout-projection.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasLoopLayoutProjection.bodyState;
console.log(JSON.stringify([S({{imageInput:true,showPrompt:true}},3,2),S({{}},-1,'x')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"imageInput": True, "showPrompt": True, "imageInputCount": 3, "promptItemCount": 2, "hasUpstreamPrompt": True},
            {"imageInput": False, "showPrompt": False, "imageInputCount": 0, "promptItemCount": 0, "hasUpstreamPrompt": False},
        ])

    def test_loop_layout_projection_owns_cascade_run_state(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-layout-projection.js'))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasLoopLayoutProjection.runState;
console.log(JSON.stringify([S({{targetId:'n1',orderLength:3,active:true,stopping:false,count:4}}),S({{targetId:'',orderLength:0,count:0}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"hasTarget": True, "targetId": "n1", "active": True, "stopping": False, "orderLength": 3, "count": 4},
            {"hasTarget": False, "targetId": "", "active": False, "stopping": False, "orderLength": 0, "count": 1},
        ])

    def test_loop_input_projection_owns_media_batching(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-input-projection.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
console.log(JSON.stringify([T.batch([{{url:'a'}},{{url:'b'}},{{url:'c'}}],1,2,2),T.batch([{{url:'a'}},null],1,0,1)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [[{"url":"b"},{"url":"c"}],[{"url":"a"}]])

    def test_loop_prompt_renderer_owns_token_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify([T.tokenChip('《计数》',{{label:'Count',deleteLabel:'Delete'}}),T.variableMarkup('A《计数》B',{{token:'《计数》',escapeHtml:x=>x,label:'Count',deleteLabel:'Delete'}})]));
"""], check=True, text=True, capture_output=True)
        values = json.loads(result.stdout)
        self.assertIn('loop-token-chip', values[0])
        self.assertIn('A', values[1]); self.assertIn('B', values[1])

    def test_loop_prompt_renderer_owns_token_labels(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify([T.tokenLabel('《计数》',{{'《计数》':'Count'}}),T.tokenLabel('other',{{}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['Count', 'other'])

    def test_loop_layout_projection_owns_panel_sizes(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-layout-projection.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopLayoutProjection;
console.log(JSON.stringify([T.nodeSize({{w:200,h:100}},true),T.nodeSize({{w:400,h:500}},false),T.panelSize({{showPrompt:true,imageInput:true}}),T.panelSize({{}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"width":336,"height":360},{"width":336,"height":None},{"width":336,"height":390},{"width":336,"height":None}
        ])

    def test_loop_prompt_renderer_owns_count_and_split_rules(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify([T.count(0),T.count(140),T.splitItems('1. A\\n2. B'),T.splitItems('single')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [1,100,['A','B'],['single']])

    def test_loop_input_projection_owns_prompt_selection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/loop-input-projection.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
console.log(JSON.stringify([T.select(['a','b'],1,2),T.select(['a','b'],1,3),T.select([],1,1)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['b','a',''])

    def test_media_output_renderer_owns_minimax_lite_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/media-output-renderer.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaOutputRenderer;
console.log(T.renderLite({{url:'v',name:'clip'}},{{urlValue:x=>x.url,kind:()=> 'video',escapeHtml:x=>x,escapeAttr:x=>x,videoPreview:()=>'<video></video>',imagePreview:()=>''}}));
"""], check=True, text=True, capture_output=True)
        self.assertIn('minimax-lite-media is-video', result.stdout)

    def test_media_tools_owns_minimax_pane_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.minimaxPaneProjection({{libraryW:180,previewH:200,videoTrackH:80,refLaneH:40}},{{x:-50,y:100}},1)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"libraryW":170,"previewH":300,"videoTrackH":180,"refLaneH":130})

    def test_media_tools_owns_minimax_playhead_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.minimaxPlayheadProjection(10,4.5),T.minimaxPlayheadProjection(10,20),T.minimaxPlayheadProjection(0,2)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"safeTime":4.5,"percent":45,"label":"4.5s / 10s"},
            {"safeTime":10,"percent":100,"label":"10s / 10s"},
            {"safeTime":0,"percent":0,"label":"0s / 0s"},
        ])

    def test_media_tools_owns_minimax_reference_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.minimaxAspectValue(' 4 : 3 '),T.minimaxUniqueRefs([{{url:'a',kind:'image'}},{{url:'a',kind:'image'}},{{url:'b',kind:'video'}}]),T.minimaxRefSummary([{{url:'a',kind:'image'}},{{url:'b',kind:'video'}}])]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['4:3',[{"url":"a","kind":"image"},{"url":"b","kind":"video"}],'1 图 · 1 视频'])

    def test_media_tools_owns_minimax_segment_compaction(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.minimaxCompactSegments([{{start:4,duration:2}},{{start:0,duration:0}}],9)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"segments":[{"start":0,"duration":1},{"start":1,"duration":2}],"duration":3,"playhead":3})

    def test_media_tools_owns_minimax_active_segment_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
const segments=[{{id:'a',start:0,duration:2}},{{id:'b',start:2,duration:3}}];
console.log(JSON.stringify([T.minimaxActiveSegment(segments,2,''),T.minimaxActiveSegment(segments,9,'b'),T.minimaxActiveSegment([],1,'')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"id":"a","start":0,"duration":2},{"id":"b","start":2,"duration":3},None
        ])

    def test_media_tools_owns_minimax_segment_reference_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
const kind=ref=>ref.kind || 'file';
console.log(JSON.stringify([T.minimaxSegmentRefs({{refs:[{{url:'own',kind:'image'}}]}},[{{url:'up',kind:'video'}}],kind,2),T.minimaxSegmentRefs({{refs:[]}},[{{url:'up',kind:'video'}},{{url:'up2',kind:'audio'}}],kind,2),T.minimaxSegmentRefsByKind([{{url:'a',kind:'image'}},{{url:'b',kind:'video'}}],'video',kind)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            [{"url":"own","kind":"image"}],
            [{"url":"up","kind":"video"},{"url":"up2","kind":"audio"}],
            [{"url":"b","kind":"video"}],
        ])

    def test_media_tools_owns_minimax_segment_result_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, value=x=>typeof x==='string'?x:x?.url||'';
const a=T.minimaxSegmentResult('clip',value), b=T.minimaxSegmentResult({{url:'clip',name:'x'}},value);
console.log(JSON.stringify([a,b,T.minimaxPrependUnique([{{url:'old'}}],{{url:'new'}},value),T.minimaxPrependUnique([{{url:'old'}}],{{url:'old'}},value)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"url":"clip","kind":"video","name":"minimax.mp4"},
            {"url":"clip","name":"x","kind":"video"},
            [{"url":"new"},{"url":"old"}],
            [{"url":"old"}],
        ])

    def test_media_tools_owns_minimax_source_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.minimaxSourceProjection([{{prompt:'first',refs:[{{url:'a'}}]}},{{prompt:'',refs:[{{url:'b'}}]}},null])));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "sources":[{"prompt":"first","refs":[{"url":"a"}]},{"prompt":"","refs":[{"url":"b"}]},None],
            "prompt":"first",
            "refs":[{"url":"a"},{"url":"b"}],
        })

    def test_media_tools_owns_minimax_segment_timing_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.minimaxSegmentTiming({{start:-2,duration:0,trimIn:-1,trimOut:99}},0,8),T.minimaxSegmentTiming({{start:1,duration:2,trimIn:1,trimOut:1}},5,8)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"start":0,"duration":8,"trimIn":0,"trimOut":8},
            {"start":5,"duration":2,"trimIn":1,"trimOut":1.1},
        ])

    def test_media_tools_owns_minimax_segment_visual_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, aspect=x=>String(x).replace(/\\s+/g,'');
console.log(JSON.stringify([T.minimaxSegmentVisuals({{aspectRatio:' 4 : 3 ',megapixels:1}},'16:9',.4,aspect),T.minimaxSegmentVisuals({{}},'1:1',.8,aspect)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"aspectRatio":"4:3","megapixels":1},
            {"aspectRatio":"1:1","megapixels":.8},
        ])

    def test_media_tools_owns_minimax_reference_migration(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, kind=x=>x.kind||'file';
console.log(JSON.stringify(T.minimaxReferenceMigration({{refs:{{image:[{{url:'a'}}],video:[{{url:'b'}}]}},refItems:[{{url:'c',kind:'audio'}}]}},kind,2)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"url":"c","kind":"audio"}, {"url":"a","kind":"image"},
        ])

    def test_media_tools_owns_minimax_output_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, value=x=>typeof x==='string'?x:x?.url||'', kind=x=>x.kind||'video';
console.log(JSON.stringify(T.minimaxOutputProjection({{result:{{url:'current'}},results:[{{url:'old'}},{{name:'bad'}}]}},[{{url:'mat'}},{{name:'bad'}}],value,kind)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "result":{"url":"current","kind":"video"},
            "results":[{"url":"old"}], "materials":[{"url":"mat"}],
        })

    def test_media_tools_owns_minimax_node_config_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, aspect=x=>String(x).replace(/\\s+/g,'');
console.log(JSON.stringify([T.minimaxNodeConfig({{}},aspect,'workflow.json','rh-id'),T.minimaxNodeConfig({{workflow:'custom',rhPayment:'paid',aspectRatio:' 4 : 3 ',megapixels:1}},aspect,'workflow.json','rh-id')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"workflow":"workflow.json","minimaxRunningHubWorkflowId":"rh-id","rhPayment":"free","aspectRatio":"16:9","megapixels":.4},
            {"workflow":"custom","minimaxRunningHubWorkflowId":"rh-id","rhPayment":"paid","aspectRatio":"4:3","megapixels":1},
        ])

    def test_media_tools_owns_minimax_segment_list_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.minimaxSegmentList(null,6,()=> 'generated'),T.minimaxSegmentList([{{id:'keep',start:2}}],6,()=> 'unused') ]));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload[0][0]['id'], 'generated')
        self.assertEqual(payload[0][0]['duration'], 6)
        self.assertEqual(payload[1], [{"id":"keep","start":2}])

    def test_media_tools_owns_minimax_selection_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.minimaxSelectionProjection([{{id:'a',start:0,duration:2}},{{id:'b',start:2,duration:3}}],'b',0),T.minimaxSelectionProjection([{{id:'a',start:0,duration:2}}],'missing',9)]));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]['selectedId'], 'b')
        self.assertEqual(payload[0]['duration'], 5)
        self.assertEqual(payload[1]['selectedId'], 'a')
        self.assertEqual(payload[1]['duration'], 9)

    def test_media_tools_owns_minimax_download_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, value=x=>x?.url||'', file=url=>url.split('/').pop(), safe=(name,fallback)=>name.replace(/[^a-z0-9.]+/gi,'_')||fallback;
console.log(JSON.stringify([T.minimaxDownloadProjection({{url:'/output/a.mp4'}},value,file,safe),T.minimaxDownloadProjection({{url:''}},value,file,safe)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"url":"/output/a.mp4","name":"a.mp4"}, None])

    def test_media_tools_owns_minimax_timeline_interaction(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.minimaxTimelineInteraction([{{id:'a',start:0,duration:2}},{{id:'b',start:2,duration:3}}],5,3,'a')));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['safeTime'], 3)
        self.assertEqual(payload['selectedId'], 'b')
        self.assertTrue(payload['selectionChanged'])

    def test_loop_input_projection_owns_output_media_refs(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection, value=x=>x.url, kind=x=>x.kind;
console.log(JSON.stringify([T.outputMediaRefs([{{url:'a',kind:'image'}},{{url:'b',kind:'video'}}],'image',value,kind,()=>'', '', 'png'),T.outputMediaRefs([{{url:'a',kind:'video'}}],'video',value,kind,()=>'', 'node-1', 'mp4')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            [{"url":"a","name":"output-1.png","kind":"image"}],
            [{"url":"a","name":"output-1.mp4","kind":"video","nodeId":"node-1","outputIndex":0}],
        ])

    def test_loop_input_projection_owns_node_media_refs(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
const nodes=[{{id:'child',type:'image',url:'child.png',name:'Child'}}];
const image=T.nodeMediaRefs({{type:'group',items:['child']}},'image',{{nodes,mediaKindForNode:()=> 'image'}});
console.log(JSON.stringify(image));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"url":"child.png","name":"Child","role":"","kind":"image"}])

    def test_loop_input_projection_owns_config_projection(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
console.log(JSON.stringify(T.config({{count:999,loopStart:0,imageBatchSize:0,mode:'parallel',showPrompt:1,imageInput:1,videoInput:1}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"count":100,"loopStart":1,"imageBatchSize":1,"mode":"parallel","showPrompt":True,"imageInput":True,"videoInput":False})

    def test_loop_prompt_renderer_owns_context_projection(self):
        script = ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify(T.contextProjection({{count:999,variablePrompt:'  hi  '}},{{index:0,total:0}},T.count)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"variable":"hi","count":100,"index":1,"total":100})

    def test_loop_prompt_renderer_owns_editor_text_projection(self):
        script = ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
const text=value=>({{nodeType:3,nodeValue:value}}), chip=token=>({{nodeType:1,classList:{{contains:x=>x==='loop-token-chip'}},dataset:{{token}}}}), br={{nodeType:1,tagName:'BR',childNodes:[]}};
console.log(JSON.stringify(T.editorText({{childNodes:[text('a'),chip('《计数》'),br,text('\\u00a0b')]}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), 'a《计数》\n b')

    def test_loop_input_projection_owns_summary_projection(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
console.log(JSON.stringify([T.summary(3,2),T.summary(-1,0)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"imageInputCount":3,"promptItemCount":2,"hasUpstreamPrompt":True},{"imageInputCount":0,"promptItemCount":0,"hasUpstreamPrompt":False}])

    def test_runninghub_renderer_owns_field_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer, key=(n,f)=>n+':'+f;
const field={{nodeId:'n',fieldName:'ratio',label:'Widescreen',defaultValue:'16:9 (Widescreen)'}};
const params={{}}; console.log(JSON.stringify([T.fieldMatches(field,[/wide/],[],key),T.isFullAspectField(field,f=>f.defaultValue),T.valueForField(field,'9:16',{{normalize:x=>x,defaultValue:f=>f.defaultValue,extractOptions:()=>[]}}),T.setParam(params,[field],[/wide/],[],'1:1',{{keyOf:key,normalize:x=>x,defaultValue:f=>f.defaultValue,extractOptions:()=>[]}}),params]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True,True,'9:16 (Portrait)',True,{"n:ratio":{"value":"1:1 (Square)"}}])

    def test_runninghub_renderer_owns_diagnostics_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer, err=T.detailedError('failed',{{stage:'submit'}});
console.log(JSON.stringify([T.compactJson({{a:'123456'}},5),err.message,err.miniMaxDetails]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['{"a":...','failed',{"stage":"submit"}])

    def test_runninghub_renderer_owns_readable_error_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(T.readableError(new Error('prefix '+JSON.stringify({{error:{{message:'bad'}},node_errors:{{n1:{{class_type:'X',errors:[{{details:'detail'}}]}}}}}})),'runninghub','fallback'));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), 'RunningHub 工作流执行失败：bad；节点 n1（X）：detail')

    def test_runninghub_renderer_owns_payload_error_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const err=T.payloadError('submit',{{detail:{{message:'bad',code:7,taskId:'t1',raw:{{x:1}}}}}},'fallback');
console.log(JSON.stringify([err.message,err.miniMaxDetails]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['RunningHub submit失败：bad：taskId=t1：code=7', {"stage":"submit","taskId":"t1","code":7,"raw":{"x":1},"message":"bad"}])

    def test_runninghub_renderer_owns_log_error_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const error=Object.assign(new Error('bad'),{{miniMaxDetails:{{taskId:'t1',stage:'submit',raw:{{x:1}}}}}});
console.log(T.logErrorText(error,'runninghub','fallback'));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), 'bad\ntaskId: t1\nstage: submit\nraw: {"x":1}')

    def test_runninghub_renderer_owns_entry_selection_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer, id=x=>x.id;
console.log(JSON.stringify([T.selectEntry([{{id:'default',title:'Other'}},{{id:'named',title:' MiniMax '}}],'missing','MiniMax','default',id),T.selectEntry([{{id:'current',title:'Other'}}],'current','Missing','default',id)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"id":"named","title":" MiniMax "},{"id":"current","title":"Other"}])

    def test_runninghub_renderer_owns_preset_param_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer, key=(n,f)=>n+':'+f, params={{}};
T.applyPresetParams(params,[{{nodeId:'n',fieldName:'prompt',label:'Prompt',options:['hello']}}],[{{patterns:[/prompt/],fallbackKeys:[],value:'hello'}}],{{keyOf:key,extractOptions:f=>f.options}});
console.log(JSON.stringify(params));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"n:prompt":{"value":"hello"}})

    def test_runninghub_renderer_owns_field_value_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const kind=f=>f.kind, role=f=>f.role, def=f=>f.defaultValue;
console.log(JSON.stringify([T.fieldValue({{kind:'image'}},null,{{image:[{{url:'img'}}]}},0,{{kindOf:kind,roleOf:role,defaultValue:def}}),T.fieldValue({{kind:'number'}},{{value:'3'}},{{}},0,{{kindOf:kind,roleOf:role,defaultValue:def}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"value":"img","upload":True},{"value":3,"upload":False}])

    def test_runninghub_renderer_owns_media_input_state_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const fields=[{{nodeId:'1',fieldName:'required',kind:'image',required:true}},{{nodeId:'2',fieldName:'optional',kind:'video'}},{{nodeId:'3',fieldName:'ready',kind:'audio',required:true}}];
console.log(JSON.stringify(T.mediaInputState(fields,{{audio:[{{url:'a'}}]}},{{indexes:{{'1::required':0,'2::optional':0,'3::ready':0}},keyOf:(n,f)=>n+'::'+f}})));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual([item['fieldName'] for item in payload['missingRequired']], ['required'])
        self.assertEqual([item['fieldName'] for item in payload['missingOptional']], ['optional'])

    def test_runninghub_field_value_respects_disabled_upstream_media(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify(T.fieldValue({{kind:'image',sourceFromUpstream:false,defaultValue:'fallback'}},{{value:'manual'}},{{image:[{{url:'upstream'}}]}},0,{{kindOf:f=>f.kind,defaultValue:f=>f.defaultValue}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"value":"manual", "upload":False})

    def test_runninghub_renderer_owns_media_field_indexes(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const fields=[{{nodeId:'b',fieldName:'image',kind:'image',imageOrder:2}},{{nodeId:'a',fieldName:'image',kind:'image',imageOrder:1}},{{nodeId:'v',fieldName:'video',kind:'video'}}];
console.log(JSON.stringify(T.mediaIndexes(fields,{{keyOf:(n,f)=>n+'::'+f}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"a::image":0, "b::image":1, "v::video":0})

    def test_runninghub_renderer_owns_workflow_pruning(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const flow={{'1':{{inputs:{{image:'x'}}}},'2':{{inputs:{{source:['1',0],keep:'y'}}}}}};
console.log(JSON.stringify(T.pruneWorkflowForMissingFields(flow,[{{nodeId:'1',fieldName:'image'}}],{{nodeInfoListOf:obj=>Object.keys(obj['1']?.inputs||{{}}).filter(k=>k!=='image'),linkOf:value=>Array.isArray(value)&&value.length===2}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"2":{"inputs":{"keep":"y"}}})

    def test_runninghub_renderer_owns_workflow_label_and_link_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.fieldLabel({{fieldName:'prompt'}}),T.fieldLabel({{nodeId:'7'}}),T.isWorkflowLinkValue(['1',0]),T.isWorkflowLinkValue(['1','0'])]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['prompt', '#7', True, False])

    def test_runninghub_renderer_owns_field_catalog_normalization(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const fields=[{{nodeId:'2',fieldName:'z',kind:'text'}},{{nodeId:'3',fieldName:'b',kind:'image',imageOrder:2,enabled:false}},{{nodeId:'1',fieldName:'a',kind:'image',imageOrder:1,enabled:true}}];
console.log(JSON.stringify([T.usableFields(fields).map(f=>f.nodeId),T.sortFields(fields,{{kindOf:f=>f.kind}}).map(f=>f.nodeId)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [['1'], ['1','3','2']])

    def test_runninghub_renderer_owns_field_metadata_normalization(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.paramKey('1','prompt'),T.fieldKind({{fieldType:'IMAGE'}}),T.fieldKind({{fieldName:'audio'}}),T.fieldRole({{fieldName:'positive_prompt'}}),T.defaultValue({{fieldValue:['x','y']}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['1::prompt','image','audio','prompt','x'])

    def test_runninghub_renderer_owns_field_option_extraction(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.extractOptions({{options:[{{label:'A'}},{{value:'B'}}]}}),T.extractOptions({{fieldName:'mode'}},{{mode:['x','y']}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [['A','B'], ['x','y']])

    def test_runninghub_renderer_owns_random_field_eligibility(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.randomEnabled({{fieldType:'NUMBER',random_enabled:true}}),T.randomEnabled({{fieldType:'TEXT',random_enabled:true}}),T.randomEnabled({{fieldType:'NUMBER',random_enabled:false}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, False, False])

    def test_runninghub_renderer_owns_random_state_read(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.randomActive({{}},'x'),T.randomActive({{x:false}},'x'),T.randomActive({{x:true}},'x')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, False, True])

    def test_loop_input_projection_owns_prompt_items(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
const nodes=[{{id:'target',showPrompt:true}},{{id:'p',type:'prompt',text:'  hello  '}},{{id:'g',type:'promptGroup',items:['p2']}},{{id:'p2',type:'prompt',text:'world'}},{{id:'llm',type:'llm',outputText:'answer'}}];
const connections=[{{to:'target',from:'p'}},{{to:'target',from:'g'}},{{to:'target',from:'llm'}}];
console.log(JSON.stringify(T.legacyPromptItems(nodes[0],connections,nodes,()=>'')));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['hello','world','answer'])

    def test_loop_prompt_renderer_owns_prompt_counter_projection(self):
        script = ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
console.log(JSON.stringify([T.textLength('你好a'),T.counterMarkup('abcd',3)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [3, {"count":4,"over":True,"markup":"<div class=\"prompt-counter over\"><span>4</span><span>/ 3</span></div>"}])

    def test_loop_prompt_renderer_owns_token_insertion_boundary(self):
        script = ROOT / 'static/js/workbench/canvas/loop-prompt-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopPromptRenderer;
const editor={{children:[],focus(){{}},appendChild(node){{this.children.push(node);}}}};
const doc={{createElement(){{return {{firstElementChild:{{}},set innerHTML(value){{this.html=value;}}}};}},createTextNode(value){{return {{value}};}}}};
console.log(JSON.stringify([T.insertToken(editor,'《计数》',{{document:doc,chipMarkup:'<span></span>'}}),editor.children.length]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, 2])

    def test_runninghub_renderer_owns_source_summary(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const sources=[{{refs:[{{url:'i1',kind:'image'}},{{url:'v1',kind:'video'}}],prompt:'p1'}},{{refs:[{{url:'i2',kind:'image'}},{{url:'a1',kind:'audio'}}],prompt:'p2'}}];
console.log(JSON.stringify(T.sourceSummary(sources,{{kindOf:r=>r.kind,imageLimit:1}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"refs":[{"url":"i1","kind":"image"},{"url":"v1","kind":"video"},{"url":"i2","kind":"image"},{"url":"a1","kind":"audio"}],"image":[{"url":"i1","kind":"image"}],"video":[{"url":"v1","kind":"video"}],"audio":[{"url":"a1","kind":"audio"}],"prompt":"p1\n\np2"})

    def test_runninghub_renderer_owns_workflow_node_info_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify(T.workflowNodeInfoList({{'1':{{inputs:{{image:'x.png',count:3,link:['2',0],flag:true}}}}}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"nodeId":"1","fieldName":"image","fieldValue":"x.png","fieldType":"IMAGE","source":"workflow"},{"nodeId":"1","fieldName":"count","fieldValue":"3","fieldType":"NUMBER","source":"workflow"},{"nodeId":"1","fieldName":"flag","fieldValue":"true","fieldType":"BOOLEAN","source":"workflow"}])

    def test_runninghub_renderer_owns_entry_identity_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.entryId({{workflowId:'wf1'}},'workflow'),T.entryLabel({{id:'wf123456'}},'workflow'),T.entryKey('app','a1'),T.parseEntryKey('model:m1')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['wf1','工作流 123456','app:a1',{"kind":"model","id":"m1"}])

    def test_runninghub_renderer_owns_entry_collection_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify(T.allEntries({{model:['m1'],app:[{{appId:'a1'}}],workflow:[{{workflowId:'w1'}}]}},{{idOf:(entry,kind)=>T.entryId(entry,kind)}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"kind":"model","id":"m1","entry":"m1"},{"kind":"app","id":"a1","entry":{"appId":"a1"}},{"kind":"workflow","id":"w1","entry":{"workflowId":"w1"}}])

    def test_runninghub_renderer_owns_entry_reference_resolution(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const entries=[{{kind:'workflow',id:'w1'}},{{kind:'app',id:'a1'}}];
console.log(JSON.stringify([T.resolveEntryRef({{rhConfigKey:'app:a1'}},entries),T.resolveEntryRef({{workflowId:'w1'}},entries)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"kind":"app","id":"a1"},{"kind":"workflow","id":"w1"}])

    def test_runninghub_renderer_owns_visible_entry_filter(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify(T.visibleEntries([{{id:'ok'}},{{id:'disabled',enabled:false}},{{id:'hidden',hidden:true}}])));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"id":"ok"}])

    def test_runninghub_renderer_owns_workflow_config_source_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.entryFields({{fields:[{{fieldName:'x'}}]}}),T.workflowEntryHasSavedConfig({{workflowJson:{{'1':{{}}}}}}),T.firstObjectSource({{}},{{a:1}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [[{"fieldName":"x"}],True,{"a":1}])

    def test_runninghub_renderer_owns_current_entry_mode_projection(self):
        script = ROOT / 'static/js/workbench/canvas/runninghub-field-renderer.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
console.log(JSON.stringify([T.currentEntry({{entry:{{id:'a1'}}}}),T.currentKind({{rhMode:'workflow'}},''),T.currentKind({{rhMode:'app'}},'model')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"id":"a1"},'workflow','model'])

    def test_media_tools_owns_output_dom_keys(self):
        script = ROOT / 'static/js/workbench/canvas/media-tools.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputDomKeyForItem({{url:'u1'}}),T.outputDomKeyForPending({{id:'p1'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ['url:u1','pending:p1'])

    def test_neutral_execution_host_exposes_explicit_classic_contract(self):
        script = ROOT / 'static/js/workbench/canvas/execution-host.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const calls=[]; const api=sandbox.window.WorkbenchCanvasExecutionHost.createClassic({{markRunning:(n,v)=>calls.push(['running',v]),writeOutputText:()=>calls.push(['text']),setRunStatus:()=>calls.push(['status']),render:()=>calls.push(['render']),save:()=>calls.push(['save']),notifyError:()=>calls.push(['error'])}});
api.markRunning({{}},0); api.writeOutputText({{}},'x'); api.setRunStatus({{}},'done',''); api.render({{}}); api.save(); api.notifyError('e');
console.log(JSON.stringify(calls));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [['running',False],['text'],['status'],['render'],['save'],['error']])

    def test_classic_execution_host_delegates_to_neutral_classic_contract(self):
        neutral = ROOT / 'static/js/workbench/canvas/execution-host.js'
        classic = ROOT / 'static/js/workbench/canvas/classic-execution-host.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(neutral))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(classic))}, 'utf8'), sandbox);
const api=sandbox.window.WorkbenchCanvasClassicExecutionHost.create({{markRunning(){{}},writeOutputText(){{}},setRunStatus(){{}},render(){{}},save(){{}},notifyError(){{}}}});
console.log(JSON.stringify(typeof api.setRunStatus === 'function' && typeof sandbox.window.WorkbenchCanvasExecutionHost.createClassic === 'function'));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), True)

    def test_neutral_execution_host_exposes_classic_chat_lifecycle_contract(self):
        script = ROOT / 'static/js/workbench/canvas/execution-host.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const calls=[]; const api=sandbox.window.WorkbenchCanvasExecutionHost.createClassicChat({{appendMessage:(n,m)=>calls.push(['append',m.role]),clearChatInput:()=>calls.push(['clear']),writeOutputText:()=>calls.push(['text']),markRunning:(n,v)=>calls.push(['running',v]),render:()=>calls.push(['render']),save:()=>calls.push(['save']),notifyError:()=>calls.push(['error'])}});
api.appendMessage({{}},{{role:'user'}}); api.clearChatInput({{}}); api.writeOutputText({{}},'x'); api.markRunning({{}},0); api.render({{}}); api.save(); api.notifyError('e');
console.log(JSON.stringify(calls));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [['append','user'],['clear'],['text'],['running',False],['render'],['save'],['error']])

    def test_classic_chat_host_delegates_to_neutral_contract(self):
        neutral = ROOT / 'static/js/workbench/canvas/execution-host.js'
        classic = ROOT / 'static/js/workbench/canvas/classic-execution-host.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(neutral))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(classic))}, 'utf8'), sandbox);
const api=sandbox.window.WorkbenchCanvasClassicExecutionHost.createChat({{appendMessage(){{}},clearChatInput(){{}},writeOutputText(){{}},markRunning(){{}},render(){{}},save(){{}},notifyError(){{}}}});
console.log(JSON.stringify(typeof api.appendMessage === 'function' && typeof sandbox.window.WorkbenchCanvasExecutionHost.createClassicChat === 'function'));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), True)

    def test_classic_execution_adapter_has_no_duplicate_fallback_implementation(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-execution-host.js').read_text(encoding='utf-8')
        self.assertNotIn('const REQUIRED_OPERATIONS', source)
        self.assertNotIn('h.markRunning(node, Boolean(running))', source)
        self.assertIn('createClassic(host)', source)
        self.assertIn('createClassicChat(host)', source)

    def test_minimax_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runMiniMaxNode')
        end = source.index('async function uploadCanvasUrlToComfy', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', readable)", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_comfy_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runComfyNode')
        end = source.index('async function runQueuedComfyGenerate', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_runninghub_model_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runRhModelNode')
        end = source.index('async function runGenerator', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_generic_generator_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runGenerator(')
        end = source.index('async function runGeneratorLegacy', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(gen, true)', body)
        self.assertIn("executionHost.setRunStatus(gen, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(gen, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('gen.runStatus =', body)
        self.assertNotIn('gen.runError =', body)

    def test_legacy_generator_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runGeneratorLegacy')
        end = source.index('async function midjourneyRequest', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(gen, true)', body)
        self.assertIn("executionHost.setRunStatus(gen, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(gen, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('gen.runStatus =', body)
        self.assertNotIn('gen.runError =', body)

    def test_midjourney_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runMidjourneyNode')
        end = source.index('async function runMidjourneyAction', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'running', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', error.message || String(error))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_midjourney_completion_uses_classic_host(self):
        source = read_canvas_app_source(ROOT)
        start = source.index('async function completeMidjourneyRun')
        end = source.index('async function runMidjourneyNode', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn('executionHost.markRunning(node, false)', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_video_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runVideoNode')
        end = source.index('async function runMiniMaxRunningHub', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_ltx_director_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runLTXDirectorNode')
        end = source.index('function rhUseWallet', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_runninghub_workflow_execution_routes_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('async function runRhNode')
        end = source.index('async function runRhModelNode', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, true)', body)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", body)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_midjourney_action_and_modal_route_lifecycle_writes_through_classic_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        for start_marker, end_marker in [('async function runMidjourneyAction', 'async function runMidjourneyModal'), ('async function runMidjourneyModal', 'async function runVideoNode')]:
            start = source.index(start_marker)
            end = source.index(end_marker, start)
            body = source[start:end]
            self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
            self.assertIn('executionHost.markRunning(node, true)', body)
            self.assertIn("executionHost.setRunStatus(node, 'running', '')", body)
            self.assertIn("executionHost.setRunStatus(node, 'failed', error.message || String(error))", body)
            self.assertIn('executionHost.save()', body)
            self.assertNotIn('node.runStatus =', body)
            self.assertNotIn('node.runError =', body)

    def test_canvas_image_task_failure_uses_classic_execution_host(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        start = source.index('function failCanvasImageTask')
        end = source.index('function outputForNode', start)
        body = source[start:end]
        self.assertIn('const executionHost = gen ? ensureClassicExecutionHost() : null;', body)
        self.assertIn("executionHost.setRunStatus(gen, 'failed', pending.error)", body)
        self.assertIn("executionHost.setRunStatus(gen, 'failed', message || tr('canvas.generationFailed'))", body)
        self.assertIn('executionHost.markRunning(gen, false)', body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('gen.runStatus =', body)
        self.assertNotIn('gen.runError =', body)

    def test_canvas_image_task_completion_uses_classic_execution_host(self):
        source = read_canvas_app_source(ROOT)
        start = source.index('function completeCanvasImageTask')
        end = source.index('function failCanvasImageTask', start)
        body = source[start:end]
        self.assertIn('const executionHost = gen ? ensureClassicExecutionHost() : null;', body)
        self.assertIn("executionHost.setRunStatus(gen, 'done', '')", body)
        self.assertIn('executionHost.markRunning(gen, false)', body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('gen.runStatus =', body)
        self.assertNotIn('gen.runError =', body)

    def test_recovered_pending_output_uses_classic_execution_host(self):
        source = read_canvas_app_source(ROOT)
        start = source.index('function completeRecoverPendingOutput')
        end = source.index('async function queryRecoverPendingOutput', start)
        body = source[start:end]
        self.assertIn('const executionHost = gen ? ensureClassicExecutionHost() : null;', body)
        self.assertIn("executionHost.setRunStatus(gen, 'done', '')", body)
        self.assertIn('executionHost.markRunning(gen, false)', body)
        self.assertIn('executionHost.save()', body)
        self.assertNotIn('gen.runStatus =', body)
        self.assertNotIn('gen.runError =', body)

    def test_classic_executor_runtime_has_no_direct_execution_state_writes(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-executor-runtime.js').read_text(encoding='utf-8')
        for pattern in ('node.running =', 'node.runStatus =', 'node.runError =', 'gen.running =', 'gen.runStatus =', 'gen.runError ='):
            self.assertNotIn(pattern, source, pattern)

    def test_stuck_generator_cleanup_routes_running_reset_through_execution_host(self):
        source = read_canvas_app_source(ROOT)
        start = source.index('function clearStuckGeneratorRunning')
        end = source.index('async function runComfyNode', start)
        body = source[start:end]
        self.assertIn('ensureClassicExecutionHost().markRunning(node, false);', body)
        self.assertNotIn('node.running = false;', body)

    def test_transient_canvas_run_state_reset_uses_execution_host(self):
        source = read_canvas_app_source(ROOT)
        start = source.index('function resetTransientRunState')
        end = source.index('function canvasLocalAssetUrls', start)
        body = source[start:end]
        self.assertIn('const executionHost = ensureClassicExecutionHost();', body)
        self.assertIn('executionHost.markRunning(node, false)', body)
        self.assertIn("executionHost.setRunStatus(node, '', '')", body)
        self.assertNotIn('node.running = false;', body)
        self.assertNotIn('node.runStatus = \'\';', body)
        self.assertNotIn('node.runError = \'\';', body)

    def test_runninghub_config_refresh_clears_status_through_execution_host(self):
        source = read_canvas_app_source(ROOT)
        for start_marker, end_marker in [('async function rhFetchAppInfo', 'async function rhFetchWorkflowInfo'), ('async function rhFetchWorkflowInfo', 'async function rhImportWorkflowJson')]:
            start = source.index(start_marker)
            end = source.index(end_marker, start)
            body = source[start:end]
            self.assertIn("ensureClassicExecutionHost().setRunStatus(node, '', '')", body)
            self.assertNotIn("node.runStatus = '';", body)
            self.assertNotIn("node.runError = '';", body)

    def test_canvas_execution_state_writes_are_confined_to_host_callbacks(self):
        source = read_canvas_app_source(ROOT)
        runtime = source[source.index('function clearStuckGeneratorRunning'):source.index('function ensureClassicChatExecutionHost')]
        self.assertNotIn('node.running = false;', runtime)
        self.assertNotIn("node.runStatus = '';", runtime)
        self.assertNotIn("node.runError = '';", runtime)
        self.assertIn('markRunning: (node, running)', source)
        self.assertIn('setRunStatus: (node, status, error)', source)

    def test_cascade_cleanup_uses_execution_status_seam(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-cascade-orchestrator.js').read_text(encoding='utf-8')
        start = source.index('function clearCascadeNodeState')
        end = source.index('// ── Context lifecycle', start)
        body = source[start:end]
        self.assertIn("'setNodeRunStatus'", source)
        self.assertIn("setNodeRunStatus(node, '', '')", body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_cascade_main_pass_uses_execution_status_seam(self):
        source = (ROOT / 'static/js/workbench/canvas/classic-cascade-orchestrator.js').read_text(encoding='utf-8')
        start = source.index('function runOneCascadePass')
        end = source.index('// ── Click-binding', start)
        body = source[start:end]
        self.assertIn("setNodeRunStatus(n, 'queued', '')", body)
        self.assertIn("setNodeRunStatus(node, 'running', '')", body)
        self.assertIn("setNodeRunStatus(node, 'done', '')", body)
        self.assertIn("setNodeRunStatus(node, 'failed', err.message || String(err))", body)
        self.assertNotIn('node.runStatus =', body)
        self.assertNotIn('node.runError =', body)

    def test_canvas_loads_neutral_execution_host_before_classic_adapter(self):
        page = (ROOT / 'static/canvas.html').read_text(encoding='utf-8')
        neutral = page.index('workbench/canvas/execution-host.js')
        classic = page.index('workbench/canvas/classic-execution-host.js')
        editor = page.index('workbench/canvas/canvas-app-bootstrap.js')
        self.assertLess(neutral, classic)
        self.assertLess(classic, editor)

    def test_canvas_busts_classic_execution_adapter_after_contract_change(self):
        page = (ROOT / 'static/canvas.html').read_text(encoding='utf-8')
        self.assertIn('classic-execution-host.js?v=2026.09.09.2', page)

    def test_canvas_list_busts_canvas_page_after_execution_adapter_change(self):
        source = (ROOT / 'static/js/canvas-list.js').read_text(encoding='utf-8')
        self.assertIn('v=2026.09.09.3', source)

    def test_canvas_entry_chain_busts_manager_and_list_after_execution_adapter_change(self):
        index = (ROOT / 'static/index.html').read_text(encoding='utf-8')
        listing = (ROOT / 'static/canvas-list.html').read_text(encoding='utf-8')
        self.assertIn('canvas-list.html?v=2026.09.09.4', index)
        self.assertIn('canvas-list.js?v=2026.09.09.4', listing)

    def test_loop_input_projection_owns_connected_batch(self):
        script = ROOT / 'static/js/workbench/canvas/loop-input-projection.js'
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(script))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasLoopInputProjection;
const node={{id:'loop',imageInput:true}}, connections=[{{to:'loop',from:'a'}},{{to:'loop',from:'b'}}];
const resolve=id=>id==='a'?[{{url:'a1'}},{{url:'a2'}}]:[{{url:'b1'}}];
console.log(JSON.stringify([T.legacyConnectedBatch(node,connections,resolve,1,2,1,true),T.legacyConnectedBatch(node,connections,resolve,1,2,1,false)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [[{"url":"a1"},{"url":"a2"}],[]])

    def test_media_tools_owns_editor_pointer_coordinate_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.canvasPoint(60,45,10,5,100,80,200,160)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"x":100,"y":80})

    def test_media_tools_owns_resize_control_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.resizeControlProjection(1000,500,.5)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"sourceW":1000,"sourceH":500,"scale":.5,"targetW":500,"targetH":250,"text":"500×250"})

    def test_media_editor_state_owns_action_dispatch_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_EDITOR_STATE))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasMediaEditorState, calls=[];
S.dispatch('outpaint',{{applyImageOutpaint:()=>calls.push('outpaint')}});
S.dispatch('unknown',{{applyImageCrop:()=>calls.push('crop')}});
console.log(JSON.stringify(calls));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["outpaint", "crop"])

    def test_workflow_transfer_client_normalizes_import_shapes_and_removes_empty_records(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/workflow-transfer-client.js'))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasWorkflowTransfer;
console.log(JSON.stringify([T.normalizeImported([{{id:'a'}},null]),T.normalizeImported({{workflow:{{nodes:[null,{{id:'b'}}],connections:[null,{{id:'c'}}]}}}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"nodes":[{"id":"a"}],"connections":[]},{"nodes":[{"id":"b"}],"connections":[{"id":"c"}]}])

    def test_media_tools_owns_crop_handle_hit_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.cropHandleFromPoint(2,2,100,80),T.cropHandleFromPoint(50,40,100,80),T.cropHandleFromPoint(98,40,100,80)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["nw", "move", "e"])

    def test_media_tools_owns_crop_pointer_delta_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.pointerDelta(10,20,4,55)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"dx":-6,"dy":35})

    def test_media_tools_owns_crop_drag_snapshot_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasMediaTools.createCropDrag('crop-se',10,20,{{x:1,y:2,w:3,h:4}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"mode":"crop-se","sx":10,"sy":20,"start":{"x":1,"y":2,"w":3,"h":4}})

    def test_media_tools_owns_downloadable_output_url_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.downloadableImageUrls([{{url:'/output/a.png'}},{{url:'/assets/b.jpg'}},{{url:'https://x/y'}}],item=>item.url,url=>url==='/assets/b.jpg')));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["/output/a.png"])

    def test_media_tools_owns_output_resolution_metadata_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputResolutionParts('1024×768',1250),T.outputResolutionParts('',-1)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"resolution":"1024×768","runMs":1250},{"resolution":"--","runMs":0}])

    def test_media_tools_owns_output_download_name_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputDownloadName('/output/a.webp?x=1',123),T.outputDownloadName('',456)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["canvas-output-123.webp","canvas-output-456.png"])

    def test_media_tools_owns_run_duration_format_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.formatRunDuration(0),T.formatRunDuration(1250),T.formatRunDuration(61000)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["0s","1s","1m 01s"])

    def test_media_tools_owns_output_value_and_metadata_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, images=['/output/a.png',{{url:'/output/b.png',runMs:10}},null];
console.log(JSON.stringify([T.outputUrlValue(images[0]),T.outputUrlValue(images[1]),T.outputMetaFor(images,'/output/b.png'),T.outputMetaFor(images,'/missing')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["/output/a.png","/output/b.png",{"url":"/output/b.png","runMs":10},{}])

    def test_media_tools_owns_output_image_name_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputImageName('/output/%E4%B8%AD.png?x=1'),T.outputImageName('')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["中.png","output image"])

    def test_media_tools_owns_output_grid_layout_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, layout={{type:'grid-split',groupId:'g1'}};
console.log(JSON.stringify([T.outputGridLayout([{{grid:{{groupId:'g1'}}}}],layout),T.outputGridLayout([{{grid:{{groupId:'g2'}}}}],layout),T.outputGridLayout([],layout)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"type":"grid-split","groupId":"g1"},None,None])

    def test_media_tools_owns_output_grid_placement_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputGridPlacement({{row:-1,col:2,w:0,h:3}}),T.outputGridPlacement(null)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"row":0,"col":2,"w":1,"h":3},None])

    def test_media_tools_owns_output_presentation_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.outputPresentation({{url:'/output/a.png',name:'A',runMs:20,grid:{{row:1,col:2,w:3,h:4}}}},{{useGrid:true,kindOf:()=> 'image'}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"url":"/output/a.png","kind":"image","name":"A","runMs":20,"placement":{"row":1,"col":2,"w":3,"h":4}})

    def test_media_tools_owns_output_append_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(T.appendOutputRecords([{{url:'/old',viewed:true}}],[{{url:'/new',name:'N',kind:'image'}}],{{url:'/src',name:'S'}},[{{runMs:7}}],{{type:'grid-split',groupId:'g'}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"images":[{"url":"/new","viewed":False,"runMs":7,"run":None,"name":"N","kind":"image"}],"outputLayout":{"type":"grid-split","groupId":"g"},"imageComparisons":{"/new":{"url":"/src","name":"S"}}})

    def test_media_tools_owns_output_viewed_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.markOutputViewed([{{url:'/a'}},{{url:'/b',viewed:true}}],'/a'),T.markOutputViewed([{{url:'/a',viewed:true}}],'/a')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"images":[{"url":"/a","viewed":True},{"url":"/b","viewed":True}],"changed":True},{"images":[{"url":"/a","viewed":True}],"changed":False}])

    def test_media_tools_owns_output_compare_url_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, images=[{{url:'/out',run:{{refs:[{{url:'/ref'}}]}}}}];
console.log(JSON.stringify([T.outputCompareUrl('/out',{{'/out':'/explicit'}},images),T.outputCompareUrl('/out',{{'/out':{{url:'/object'}}}},images),T.outputCompareUrl('/out',{{}},images)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["/explicit","/object","/ref"])

    def test_media_tools_owns_lightbox_source_priority_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, normalize=(item,out)=>{{const url=typeof item==='string'?item:item.url; return url ? {{url,outId:out?.id||''}} : null;}};
console.log(JSON.stringify([T.collectLightboxItems({{sourceOut:{{id:'o',type:'output',images:[{{url:'/one'}}]}},normalize}}),T.collectLightboxItems({{outputNodes:[{{id:'o2',type:'output',images:[{{url:'/two'}}]}}],logs:[{{outputs:['/three']}}],normalize}}),T.collectLightboxItems({{logs:[{{outputs:['/three']}}],normalize}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [[{"url":"/one","outId":"o"}],[{"url":"/two","outId":"o2"}],[{"url":"/three","outId":""}]])

    def test_media_tools_owns_lightbox_navigation_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools, items=[{{url:'/a'}},{{url:'/b'}},{{url:'/c'}}];
console.log(JSON.stringify([T.nextLightboxItem(items,'/b',1),T.nextLightboxItem(items,'/a',-1),T.nextLightboxItem(items,'/x',1),T.nextLightboxItem([], '/a',1)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"url":"/c"},{"url":"/c"},{"url":"/b"},None])

    def test_media_tools_owns_lightbox_index_clamping_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.clampListIndex(-2,3),T.clampListIndex(9,3),T.clampListIndex(1,0)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [0,2,-1])

    def test_media_tools_owns_lightbox_visibility_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.lightboxVisibility('video'),T.lightboxVisibility('image')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"video":True,"image":False,"compare":False},{"video":False,"image":True,"compare":True}])

    def test_media_tools_owns_lightbox_open_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.lightboxProjection({{kind:'video',groupCount:3,compareUrl:'/ref'}}),T.lightboxProjection({{kind:'image',groupCount:2}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"videoMode":True,"visibility":{"video":True,"image":False,"compare":False},"showDownloadAll":True,"compareUrl":"/ref"},
            {"videoMode":False,"visibility":{"video":False,"image":True,"compare":True},"showDownloadAll":True,"compareUrl":""},
        ])

    def test_media_output_renderer_owns_type_specific_card_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_OUTPUT_RENDERER))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasMediaOutputRenderer;
const html=R.render({{url:'/output/a.png',name:'A',runMs:20}},{{presentation:()=>({{url:'/output/a.png',kind:'audio',name:'A',runMs:20,placement:null}}),escapeAttr:x=>x,escapeHtml:x=>x,formatDuration:x=>x+'ms',isMissing:()=>false,missingHtml:()=>'',videoPreview:()=>'',imagePreview:()=>'',tr:()=> 'x'}});
console.log(JSON.stringify(html));
"""], check=True, text=True, capture_output=True)
        self.assertIn('output-audio-card', json.loads(result.stdout))
        self.assertIn('20ms', json.loads(result.stdout))

    def test_media_text_overlay_owns_record_geometry_and_hit_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TEXT_OVERLAY))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTextOverlay;
const ctx={{save:()=>{{}},restore:()=>{{}},measureText:()=>({{width:40,actualBoundingBoxAscent:8,actualBoundingBoxDescent:2}})}};
const item=T.create(' hello ',{{x:20,y:30}},{{createId:()=> 'txt1',defaultText:()=> 'fallback',brushSize:8,color:'#abc'}});
const box=T.measure(item,ctx);
console.log(JSON.stringify({{item,box,hit:T.hit([item],{{x:20,y:30}},ctx)?.id,miss:T.hit([item],{{x:200,y:300}},ctx)}}));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["item"]["id"], "txt1")
        self.assertEqual(payload["item"]["text"], "hello")
        self.assertEqual(payload["hit"], "txt1")
        self.assertIsNone(payload["miss"])

    def test_media_tools_owns_output_filename_suffix_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_TOOLS))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([T.outputFileName('photo.jpg','_crop'),T.outputFileName('photo','_resize','webp')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["photo_crop.png", "photo_resize.webp"])

    def test_prompt_template_data_owns_projection_and_filter_behavior(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData, item={{name:'中文',name_en:'English',scene:'scene',positive:'  bright  ',negative:'dark',params:{{steps:20}},category:'view'}};
console.log(JSON.stringify({{name:P.name(item,false),english:P.name(item,true),text:P.text(item,'full'),search:P.searchText(item),visible:P.visibleItems({{items:[item,{{name:'other',category:'mine'}}],category:'view',query:'BRIGHT'}}).length,defaultName:P.defaultName('第一行\\n第二行'),category:P.categoryLabel('view',{{builtinLabels:{{view:'视图'}}}})}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "name": "中文", "english": "English",
            "text": "bright\n\nNegative prompt:\ndark\n\nParams:\nsteps: 20",
            "search": "中文 english scene    bright   dark ", "visible": 1, "defaultName": "第一行",
            "category": "视图",
        })

    def test_prompt_template_data_owns_category_counts(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasPromptTemplateData.categoryCounts([{{category:'view'}},{{category:'view'}},{{category:'mine'}},{{}}])));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"all": 4, "view": 2, "mine": 2})

    def test_prompt_template_data_owns_selected_item_fallback(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.selectedId([{{id:'a'}},{{id:'b'}}],'b'),P.selectedId([{{id:'a'}},{{id:'b'}}],'x'),P.selectedId([], 'x')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["b", "a", ""])

    def test_prompt_template_data_owns_current_prompt_node_text_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.nodeText([{{id:'p',type:'prompt',text:'  hello  '}}],'p'),P.nodeText([{{id:'i',type:'image',text:'ignored'}}],'i'),P.nodeText([], 'p')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["hello", "", ""])

    def test_prompt_template_data_owns_parameter_summary_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.paramsText({{params:{{steps:20,model:'x'}}}}),P.paramsText({{}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["steps: 20\nmodel: x", ""])

    def test_prompt_template_data_owns_selected_item_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.selectedItem([{{id:'a'}},{{id:'b'}}],'b'),P.selectedItem([{{id:'a'}},{{id:'b'}}],'x'),P.selectedItem([], 'x')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"id": "b"}, {"id": "a"}, None])

    def test_prompt_template_data_owns_source_label_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.sourceLabel({{builtin:true}},{{builtin:'内置',mine:'我的'}}),P.sourceLabel({{}},{{builtin:'内置',mine:'我的'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["内置", "我的"])

    def test_prompt_template_data_owns_detail_source_label_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.detailSourceLabel({{builtin:true}},{{builtin:'内置模板',mine:'我的模板'}}),P.detailSourceLabel({{}},{{builtin:'内置模板',mine:'我的模板'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["内置模板", "我的模板"])

    def test_prompt_template_data_owns_display_scene_fallback(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.displayScene({{scene:'scene',positive:'positive'}},false),P.displayScene({{positive:'positive'}},false)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["scene", "positive"])

    def test_prompt_template_data_owns_negative_text_normalization(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.negativeText({{negative:'  avoid blur  '}}),P.negativeText({{negative:'   '}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["avoid blur", ""])

    def test_prompt_template_data_owns_positive_text_normalization(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasPromptTemplateData;
console.log(JSON.stringify([P.positiveText({{positive:'  bright  '}}),P.positiveText({{}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["bright", ""])

    def test_prompt_template_data_owns_preview_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasPromptTemplateData.preview({{positive:'  bright ',negative:' dark ',params:{{steps:20}}}})));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"positive": "bright", "negative": "dark", "params": "steps: 20"})

    def test_prompt_template_data_owns_item_card_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
const html=sandbox.window.WorkbenchCanvasPromptTemplateData.itemCard({{id:'t1',name:'Name',scene:'Scene',positive:'Prompt',category:'view',builtin:true}},'t1',{{escapeHtml:x=>'H:'+x,escapeAttr:x=>'A:'+x,categoryLabel:x=>'C:'+x,sourceLabels:{{builtin:'Builtin',mine:'Mine'}}}});
console.log(JSON.stringify(html));
"""], check=True, text=True, capture_output=True)
        self.assertIn('prompt-template-card active', json.loads(result.stdout))
        self.assertIn('H:Name', json.loads(result.stdout))
        self.assertIn('H:Builtin', json.loads(result.stdout))

    def test_prompt_template_data_owns_empty_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasPromptTemplateData.emptyState('No matches',value=>'H:'+value)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), '<div class="prompt-template-list-empty">H:No matches</div>')

    def test_prompt_template_data_owns_detail_empty_state_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_DATA))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchCanvasPromptTemplateData.detailEmptyState('Pick one',value=>'H:'+value)));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), '<div class="prompt-template-empty">H:Pick one</div>')

    def test_prompt_template_renderer_owns_category_list_and_detail_markup(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_RENDERER))}, 'utf8'), sandbox);
const R=sandbox.window.WorkbenchCanvasPromptTemplateRenderer;
const esc=value=>String(value).replace(/[<>]/g, ch=>ch==='<'?'&lt;':'&gt;');
const out=R.render({{categories:[{{id:'all',name:'All'}}],groups:[{{id:'view'}}],counts:{{all:1,view:1}},category:'all',items:[{{id:'t1',name:'<Name>',scene:'Scene',positive:'Bright',category:'view',builtin:true}}],selected:{{id:'t1',name:'<Name>',positive:' raw ',negative:' avoid ',params:{{steps:20}},category:'view',builtin:true}},editable:false,tr:key=>key,escapeHtml:esc,escapeAttr:esc,name:item=>item.name,scene:item=>item.scene,categoryLabel:id=>id,sourceLabel:()=> 'Builtin',positiveText:item=>item.positive.trim(),negativeText:item=>item.negative.trim(),paramsText:item=>'steps: '+item.params.steps}});
console.log(JSON.stringify(out));
"""], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertIn('data-template-cat="all"', payload["categories"])
        self.assertIn('data-template-id="t1"', payload["body"])
        self.assertIn('&lt;Name&gt;', payload["body"])
        self.assertIn('data-template-apply="full"', payload["body"])
        self.assertIn('>raw<', payload["body"])
        self.assertIn('>avoid<', payload["body"])
        self.assertIn('>steps: 20<', payload["body"])

    def test_node_presentation_owns_neutral_title_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasNodePresentation.title;
console.log(JSON.stringify([T({{type:'image'}},k=>k),T({{type:'ltxDirector'}},k=>'译:'+k),T({{type:'unknown'}},k=>'译:'+k)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["Image", "译:canvas.ltxDirector", "译:canvas.apiGenerate"])

    def test_node_presentation_owns_status_label_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasNodePresentation.statusLabel;
console.log(JSON.stringify([S('running'),S('failed'),S('unknown')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["运行中", "失败", ""])

    def test_node_presentation_owns_status_visibility_policy(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasNodePresentation.shouldShowStatus;
console.log(JSON.stringify([S({{type:'llm',runStatus:'running'}}),S({{type:'llm',runStatus:'failed'}}),S({{type:'llm',runStatus:'failed',_cascadeFailed:true}}),S({{type:'image',runStatus:'running'}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, False, True, False])

    def test_node_presentation_owns_status_markup_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const html=sandbox.window.WorkbenchCanvasNodePresentation.statusMarkup({{type:'llm',runStatus:'running',_cascadeIdx:2}},value=>'['+value+']');
console.log(JSON.stringify(html));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), '<span class="node-run-status running"><span class="dot"></span>[运行中] 2</span>')

    def test_node_presentation_owns_media_title_override(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const D=sandbox.window.WorkbenchCanvasNodePresentation.displayTitle;
console.log(JSON.stringify([D({{type:'image',url:'x'}},'Image','Photo'),D({{type:'image'}},'Image','Photo'),D({{type:'llm',url:'x'}},'LLM','Photo')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["Photo", "Image", "LLM"])

    def test_node_presentation_owns_node_class_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const C=sandbox.window.WorkbenchCanvasNodePresentation.className;
console.log(JSON.stringify([C({{type:'image',url:'x'}},true,true),C({{type:'prompt'}},false,false)]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["node image-node has-image sized selected", "node prompt-node   "])

    def test_node_presentation_owns_media_kind_title_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const T=sandbox.window.WorkbenchCanvasNodePresentation.mediaTitle;
console.log(JSON.stringify([T('video'),T('audio'),T('image'),T('other')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["Video", "Audio", "Image", "Image"])

    def test_node_presentation_owns_default_node_size_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const S=sandbox.window.WorkbenchCanvasNodePresentation.defaultSize;
console.log(JSON.stringify([S('image'),S('llm'),S('unknown')]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"w":260,"h":336},{"w":420,"h":590},{"w":260,"h":0}])

    def test_node_presentation_owns_fixed_size_policy(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const F=sandbox.window.WorkbenchCanvasNodePresentation.isFixedSize;
console.log(JSON.stringify([F({{h:100}},{{h:0}}),F({{}},{{h:100}}),F({{}},{{h:0}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, True, False])

    def test_node_presentation_owns_dimension_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const D=sandbox.window.WorkbenchCanvasNodePresentation.dimensions;
console.log(JSON.stringify([D({{w:100,h:200}},{{w:80,h:90}}),D({{}},{{w:80,h:90}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"width":100,"height":200},{"width":80,"height":90}])

    def test_node_presentation_owns_position_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_PRESENTATION))}, 'utf8'), sandbox);
const P=sandbox.window.WorkbenchCanvasNodePresentation.position;
console.log(JSON.stringify([P({{x:12,y:34}}),P({{x:null,y:undefined}})]));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"left":12,"top":34},{"left":0,"top":0}])

    def test_prompt_template_interaction_owns_event_routing(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const calls=[], listeners={{}};
const search={{addEventListener:(type,fn)=>listeners.search=fn}}, library={{addEventListener:(type,fn)=>listeners.library=fn}};
const close={{}}, panel={{addEventListener:(type,fn)=>listeners[type]=fn}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_INTERACTION))}, 'utf8'), sandbox);
sandbox.window.WorkbenchCanvasPromptTemplateInteraction.create({{search,library,close,panel,callbacks:{{
  queryChanged:value=>calls.push(['query',value]), libraryChanged:value=>calls.push(['library',value]),
  apply:value=>calls.push(['apply',value]), select:value=>calls.push(['select',value])
}}}});
listeners.search({{target:{{value:'bright'}}}});
listeners.library({{target:{{value:''}}}});
const target={{closest:selector=>selector.includes('template-apply')?{{dataset:{{templateApply:'negative'}}}}:null}};
listeners.click({{target,stopPropagation:()=>{{}}}});
console.log(JSON.stringify(calls));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [["query", "bright"], ["library", "system"], ["apply", "negative"]])

    def test_prompt_template_application_owns_node_text_mutation_and_close(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}}, events=[];
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_APPLICATION))}, 'utf8'), sandbox);
const A=sandbox.window.WorkbenchCanvasPromptTemplateApplication, node={{id:'p',type:'prompt',text:'old'}};
const applied=A.apply({{template:{{positive:'new'}},node,mode:'full',textFor:(template,mode)=>template.positive+':'+mode,close:()=>events.push('close')}});
const rejected=A.apply({{template:null,node,textFor:()=>'',close:()=>events.push('bad')}});
console.log(JSON.stringify({{applied,rejected,node,events}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "applied": True, "rejected": False,
            "node": {"id": "p", "type": "prompt", "text": "new:full"},
            "events": ["close"],
        })

    def test_prompt_template_interaction_owns_scroll_snapshot_restore(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const make=()=>({{scrollTop:4,querySelector:selector=>({{scrollTop:7,scrollLeft:9}})}});
const panel=make(), sandbox={{window:{{requestAnimationFrame:fn=>fn()}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_INTERACTION))}, 'utf8'), sandbox);
const I=sandbox.window.WorkbenchCanvasPromptTemplateInteraction, snapshot=I.snapshot(panel);
panel.scrollTop=0; I.restore(panel,snapshot,sandbox.window.requestAnimationFrame);
console.log(JSON.stringify({{snapshot,restored:panel.scrollTop}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "snapshot": {"panelTop": 4, "tabLeft": 9, "listTop": 7, "detailTop": 7},
            "restored": 4,
        })

    def test_prompt_template_interaction_owns_open_button_projection(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm');
const buttons=[{{dataset:{{promptTemplateNodeId:'n1'}},classList:{{toggle:(name,value)=>buttons[0].state=[name,value]}},setAttribute:(name,value)=>buttons[0].aria=[name,value]}},{{dataset:{{promptTemplateNodeId:'n2'}},classList:{{toggle:(name,value)=>buttons[1].state=[name,value]}},setAttribute:(name,value)=>buttons[1].aria=[name,value]}}];
const sandbox={{window:{{}}}}; vm.runInNewContext(fs.readFileSync({json.dumps(str(PROMPT_INTERACTION))}, 'utf8'), sandbox);
sandbox.window.WorkbenchCanvasPromptTemplateInteraction.syncOpenButtons({{querySelectorAll:()=>buttons}},{{classList:{{contains:()=>true}}}},'n2');
console.log(JSON.stringify(buttons.map(button=>({{state:button.state,aria:button.aria}}))));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"state": ["active", False], "aria": ["aria-pressed", "false"]},
            {"state": ["active", True], "aria": ["aria-pressed", "true"]},
        ])

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

    def test_connection_result_projection_is_shared_and_revision_safe(self):
        result = subprocess.run(["node", "-e", f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{location:{{hostname:'localhost',search:''}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(NODE_CLIENT))}, 'utf8'), sandbox);
const C=sandbox.window.WorkbenchNodeClient;
const connections=[], undoStack=[]; let revision=0; let committed=0;
const edge=C.applyConnectionResult({{edge:{{id:'e1',from:'a',to:'b'}},canvas_revision:7}}, {{
  connections, fromId:'a', toId:'b', undoStack, undoSnapshot:{{before:true}}, undoLimit:1,
  onRevision:value=>{{revision=value;}}, onAfterCommit:()=>{{committed++;}}
}});
let invalid;
try {{ C.applyConnectionResult({{edge:{{id:'e2',from:'a',to:'other'}}}}, {{connections,fromId:'a',toId:'b'}}); }}
catch (error) {{ invalid=error.constructor.name+':'+error.message; }}
console.log(JSON.stringify({{edge,connections,undo:undoStack.length,revision,committed,invalid}}));
"""], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "edge": {"id": "e1", "from": "a", "to": "b"},
            "connections": [{"id": "e1", "from": "a", "to": "b"}],
            "undo": 1, "revision": 7, "committed": 1,
            "invalid": "TypeError:connection result must preserve the requested edge endpoints",
        })
        source = NODE_CLIENT.read_text(encoding="utf-8")
        self.assertIn("applyConnectionResult", source)
        page_source = read_canvas_app_source(ROOT)
        connection_block = page_source[page_source.index("async function createVersionedConnection"):
                                       page_source.index("function startLink", page_source.index("async function createVersionedConnection"))]
        self.assertIn("WorkbenchNodeClient.applyConnectionResult", connection_block)
        self.assertNotIn("connections.push({id:result.edge.id", connection_block)

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
    def test_page_adapter_uses_the_single_shared_runtime_after_flag_retirement(self):
        # R4-36: smart-canvas.js retired. The unified runtime is owned by
        # canvas.html only.
        source = read_canvas_app_source(ROOT)
        self.assertIn("const canvasUnifiedRuntimeEnabled = Boolean(window.WorkbenchCanvasRuntime);", source)
        self.assertNotIn("get('unified_canvas')", source)
        self.assertIn("canvasUnifiedRuntimeEnabled", source)
        self.assertIn("ensureCanvasViewportController", source)
        self.assertIn("applyCanvasRuntimeSelection", source)
        self.assertIn("ensureCanvasViewportController().zoomAt(", source)

    def test_page_adapter_writes_drag_and_resize_through_runtime_commands(self):
        # R4-36: smart-canvas.js retired. The unified runtime drag/resize
        # commands are owned by canvas.html only.
        source = read_canvas_app_source(ROOT)
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
