"""Focused tests for the R8-17 Result Preview runtime.

The DoD is "Common outputs are inspectable in tray", so these tests drive the
preview registry in a vm sandbox and prove three things: every common result
kind resolves to a real renderer, a reference that cannot be rendered is
reported with an explicit reason instead of rendering nothing, and the Result
Tray renders its staged cards through that registry while keeping the exact
bare marker it rendered before when no registry is loaded.
"""

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "static/js/workbench/canvas/result-preview-runtime.js"
TRAY = ROOT / "static/js/workbench/canvas/result-tray-runtime.js"

# DoD: previewing a result must not create a Canvas node or mutate the graph.
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
# A preview seam owns no transport and no client persistence.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
# Classification belongs to the tray; the preview registry must not re-derive a
# kind from a value shape or a URL extension (that owner is media-kind.js).
FORBIDDEN_CLASSIFIER_MARKERS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp4",
    ".webm",
    ".mp3",
    ".wav",
    ".zip",
    "mediaKindFor",
    "WorkbenchCanvasMediaKind",
)

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


class ResultPreviewRuntimeTests(unittest.TestCase):
    def test_every_common_result_kind_resolves_to_a_registered_renderer(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
console.log(JSON.stringify({
  kinds:api.KINDS,
  resolved:api.KINDS.map(kind=>({kind, renderer:(api.previewFor({item_id:'i',kind,url:'/x',value:'v'})||{}).renderer_id||''})),
  registered:api.create().all().map(d=>d.id+'@'+d.version),
}));
""", PREVIEW)
        self.assertEqual(payload["kinds"], ["text", "image", "video", "audio", "file", "json", "resource", "link", "workflow"])
        unresolved = [entry["kind"] for entry in payload["resolved"] if not entry["renderer"]]
        self.assertEqual(unresolved, [], msg=f"kinds without a renderer: {unresolved}")
        self.assertEqual(len(payload["registered"]), len(payload["kinds"]))

    def test_text_and_json_results_render_their_own_value(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
console.log(JSON.stringify({
  text:api.previewHtml({item_id:'i',kind:'text',value:'a <caption> & more'}),
  json:api.previewHtml({item_id:'i',kind:'json',value:{b:2,a:1}}),
  textState:api.previewFor({item_id:'i',kind:'text',value:'a caption'}).state,
}));
""", PREVIEW)
        self.assertIn("a &lt;caption&gt; &amp; more", payload["text"])
        self.assertIn("result-preview__text", payload["text"])
        # Pretty-printed, key order preserved, and escaped.
        self.assertIn("&quot;b&quot;", payload["json"])
        self.assertIn("\n", payload["json"])
        self.assertEqual(payload["textState"], "ready")

    def test_media_and_reference_results_render_a_real_element(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const cases=[
  {kind:'text', title:'caption', url:'', value:'a caption'},
  {kind:'json', title:'payload', url:'', value:{nodes:['a'],edges:[]}},
  {kind:'image', title:'poster', url:'https://files.test/a.png', value:null},
  {kind:'video', title:'clip', url:'https://files.test/b.mp4', value:null},
  {kind:'audio', title:'track', url:'https://files.test/c.mp3', value:null},
  {kind:'file', title:'blob', url:'https://files.test/d.zip', value:null},
  {kind:'resource', title:'resource.1', url:'file:///e.txt', value:null},
  {kind:'link', title:'link', url:'https://example.test/page', value:null},
  {kind:'workflow', title:'workflow', url:'https://files.test/f.zip', value:null},
];
const out={};
cases.forEach((entry,index)=>{
  const value=entry.value===null?{kind:entry.kind,url:entry.url}:entry.value;
  out[entry.kind]={html:api.previewHtml({item_id:'i'+index,kind:entry.kind,url:entry.url,title:entry.title,value}),
                   state:api.previewFor({item_id:'i'+index,kind:entry.kind,url:entry.url,title:entry.title,value}).state};
});
console.log(JSON.stringify(out));
""", PREVIEW)
        for kind in ("text", "json", "image", "video", "audio", "file", "resource", "link", "workflow"):
            self.assertEqual(payload[kind]["state"], "ready", msg=f"{kind} must be inspectable")
        self.assertIn("<img class=\"result-preview__image\"", payload["image"]["html"])
        self.assertIn('src="https://files.test/a.png"', payload["image"]["html"])
        self.assertIn("<video class=\"result-preview__video\"", payload["video"]["html"])
        self.assertIn(" controls", payload["video"]["html"])
        self.assertIn("<audio class=\"result-preview__audio\"", payload["audio"]["html"])
        self.assertIn("<pre class=\"result-preview__text\"", payload["text"]["html"])
        self.assertIn("<pre class=\"result-preview__json\"", payload["json"]["html"])
        for kind in ("file", "resource", "link", "workflow"):
            self.assertIn("<a class=\"result-preview__", payload[kind]["html"], msg=f"{kind} must render an anchor")
            self.assertIn("href=", payload[kind]["html"])
        self.assertIn('rel="noopener noreferrer"', payload["link"]["html"])

    def test_unavailable_and_failed_references_are_reported_with_a_reason(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const cases={
  no_reference:{item_id:'a',kind:'image',value:{kind:'image',filename:'a.png'}},
  failed_flag:{item_id:'b',kind:'image',url:'/a.png',value:{kind:'image',url:'/a.png',failed:true}},
  error_text:{item_id:'c',kind:'image',url:'/a.png',value:{kind:'image',url:'/a.png',error:'provider exploded'}},
  failed_status:{item_id:'d',kind:'text',value:{kind:'text',status:'failed'}},
  missing_ref:{item_id:'i',kind:'image',url:'/a.png',value:{kind:'image',url:'/a.png',missing:true}},
  missing_item:{item_id:'j',kind:'text',value:'hello',missing:true},
  empty_text:{item_id:'e',kind:'text',value:'   '},
  empty_json:{item_id:'f',kind:'json',value:{}},
  unknown_kind:{item_id:'g',kind:'hologram',url:'/a.bin',value:'x'},
  unsafe_reference:{item_id:'h',kind:'image',url:'javascript:alert(1)',value:{kind:'image',url:'javascript:alert(1)'}},
};
const out={};
Object.keys(cases).forEach(name=>{
  const preview=api.previewFor(cases[name]);
  out[name]={state:preview.state,reason:preview.reason,message:preview.message,html:api.renderPreview(preview)};
});
console.log(JSON.stringify(out));
""", PREVIEW)
        expected = {
            "no_reference": "missing_reference",
            "failed_flag": "failed_output",
            "error_text": "failed_output",
            "failed_status": "failed_output",
            "missing_ref": "missing_reference",
            "missing_item": "missing_reference",
            "empty_text": "empty_output",
            "empty_json": "empty_output",
            "unknown_kind": "unsupported_kind",
            "unsafe_reference": "unsafe_reference",
        }
        for name, reason in expected.items():
            self.assertEqual(payload[name]["state"], "unavailable", msg=name)
            self.assertEqual(payload[name]["reason"], reason, msg=name)
            self.assertIn('data-preview-state="unavailable"', payload[name]["html"], msg=name)
            self.assertIn(f'data-preview-reason="{reason}"', payload[name]["html"], msg=name)
            self.assertTrue(payload[name]["message"], msg=f"{name} needs a human message")

    def test_an_unsafe_reference_never_reaches_an_attribute(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const html=api.previewHtml({item_id:'i',kind:'link',url:'javascript:alert(1)',value:{kind:'link',url:'javascript:alert(1)'}});
console.log(JSON.stringify({html,safe:api.isSafeRef('javascript:alert(1)'),relative:api.isSafeRef('/a.png'),http:api.isSafeRef('https://a.test/x')}));
""", PREVIEW)
        self.assertNotIn("javascript:", payload["html"])
        self.assertNotIn("<a ", payload["html"])
        self.assertFalse(payload["safe"])
        self.assertTrue(payload["relative"])
        self.assertTrue(payload["http"])

    def test_previews_are_frozen_descriptors_carrying_their_provenance(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const preview=api.previewFor({item_id:'attempt-1:poster:0',kind:'image',url:'/a.png',value:{kind:'image',url:'/a.png'}});
console.log(JSON.stringify({
  frozen:Object.isFrozen(preview),
  schema:preview.schema_version,
  renderer:preview.renderer_id,
  version:preview.renderer_version,
  item:preview.item_id,
  kind:preview.kind,
  states:api.STATES,
  reasons:api.REASONS,
}));
""", PREVIEW)
        self.assertTrue(payload["frozen"])
        self.assertEqual(payload["schema"], "workbench.result-preview/1")
        self.assertEqual(payload["renderer"], "result-preview/image")
        self.assertEqual(payload["version"], "1")
        self.assertEqual(payload["item"], "attempt-1:poster:0")
        self.assertEqual(payload["kind"], "image")
        self.assertEqual(payload["states"], ["ready", "unavailable"])
        self.assertEqual(
            payload["reasons"],
            ["empty_output", "failed_output", "missing_reference", "unsafe_reference", "unsupported_kind"],
        )

    def test_registry_rejects_a_duplicate_and_lets_a_caller_override_by_priority(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const registry=api.create();
let duplicate='';
try{ registry.register({id:'result-preview/text',version:'1',kind:'text',canRender:()=>true,render:()=>''}); }catch(error){ duplicate=String(error.name); }
registry.register({id:'custom/text',version:'2',kind:'text',priority:5,canRender:input=>input.kind==='text',render:()=>'<mark>custom</mark>'});
const preview=registry.preview({item_id:'i',kind:'text',value:'hello'});
console.log(JSON.stringify({duplicate,renderer:preview.renderer_id,html:registry.render(preview)}));
""", PREVIEW)
        self.assertEqual(payload["duplicate"], "RangeError")
        self.assertEqual(payload["renderer"], "custom/text")
        self.assertIn("<mark>custom</mark>", payload["html"])

    def test_registry_renders_the_kind_it_is_given_instead_of_reclassifying(self):
        # The tray already classified this item; a .txt reference must stay image.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultPreview;
const preview=api.previewFor({item_id:'i',kind:'image',url:'/a.txt',value:{kind:'image',url:'/a.txt'}});
console.log(JSON.stringify({kind:preview.kind,renderer:preview.renderer_id,html:api.renderPreview(preview)}));
""", PREVIEW)
        self.assertEqual(payload["kind"], "image")
        self.assertEqual(payload["renderer"], "result-preview/image")

    def test_seam_has_no_canvas_mutation_no_transport_and_no_duplicate_classifier(self):
        source = PREVIEW.read_text(encoding="utf-8")
        for marker in FORBIDDEN_CANVAS_MUTATION_MARKERS:
            self.assertNotIn(marker, source, msg=f"preview must not reference {marker}")
        for marker in FORBIDDEN_TRANSPORT_MARKERS:
            self.assertNotIn(marker, source, msg=f"preview must not reference {marker}")
        for marker in FORBIDDEN_CLASSIFIER_MARKERS:
            self.assertNotIn(marker, source, msg=f"preview must not re-implement classification via {marker}")

    def test_tray_renders_its_staged_cards_through_the_preview_registry(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultTray;
const host={innerHTML:'',attrs:{},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const controller=api.create({runId:'run-1',attemptId:'attempt-1'});
controller.ingest({attemptId:'attempt-1',outputs:[
  {name:'caption',value:'a caption'},
  {name:'poster',value:{kind:'image',url:'/a.png'}},
  {name:'broken',value:{kind:'image',filename:'b.png'}},
]});
controller.mount(host);
const html=host.innerHTML;
        console.log(JSON.stringify({
  html,
  images:(html.match(/<img class="result-preview__image"/g)||[]).length,
  textBodies:(html.match(/<pre class="result-preview__text"/g)||[]).length,
  unavailableBodies:(html.match(/result-preview__unavailable/g)||[]).length,
  ready:(html.match(/data-preview-state="ready"/g)||[]).length,
  reason:html.includes('data-preview-reason="missing_reference"'),
  staged:html.includes('3 staged'),
  item:html.includes('data-result-item="attempt-1:poster:0"'),
}));
""", PREVIEW, TRAY)
        self.assertEqual(payload["images"], 1)
        self.assertEqual(payload["textBodies"], 1)
        self.assertEqual(payload["unavailableBodies"], 1)
        self.assertEqual(payload["ready"], 2)
        self.assertTrue(payload["reason"])
        self.assertTrue(payload["staged"])
        self.assertTrue(payload["item"])
        self.assertIn("a caption", payload["html"])

    def test_tray_keeps_its_bare_marker_when_no_registry_is_loaded(self):
        # Composition boundary: the tray alone must render exactly what it
        # rendered before R8-17, so the two modules stay independently testable.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultTray;
const host={innerHTML:'',attrs:{},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const controller=api.create({runId:'run-1',attemptId:'attempt-1'});
controller.ingest({attemptId:'attempt-1',outputs:[
  {name:'caption',value:'a caption'},
  {name:'poster',value:{kind:'image',url:'/a.png'}},
]});
controller.mount(host);
const html=host.innerHTML;
console.log(JSON.stringify({html,images:(html.match(/<img /g)||[]).length,previews:(html.match(/result-card__preview/g)||[]).length,stateMarkers:(html.match(/data-preview-state/g)||[]).length}));
""", TRAY)
        self.assertEqual(payload["images"], 0)
        self.assertEqual(payload["stateMarkers"], 0)
        self.assertEqual(payload["previews"], 1)
        self.assertIn('data-preview-url="/a.png"', payload["html"])

    def test_canvas_page_loads_the_preview_runtime_before_the_tray_runtime(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-preview-runtime.js"), 1)
        self.assertEqual(page.count("workbench/canvas/result-tray-runtime.js"), 1)
        self.assertLess(
            page.index("workbench/canvas/result-preview-runtime.js"),
            page.index("workbench/canvas/result-tray-runtime.js"),
        )


if __name__ == "__main__":
    unittest.main()
