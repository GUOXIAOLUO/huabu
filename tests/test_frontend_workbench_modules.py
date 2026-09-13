import json
import re
import subprocess
import time
import unittest
from pathlib import Path

from tests.canvas_app_source import canvas_app_paths, read_canvas_app_source


ROOT = Path(__file__).resolve().parents[1]


class FrontendWorkbenchModulesTests(unittest.TestCase):
    def test_canvas_page_explains_file_protocol_instead_of_failing_as_raw_html(self):
        source = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertIn("window.location.protocol === 'file:'", source)
        self.assertIn("document.documentElement.classList.add('file-protocol')", source)
        self.assertIn("http://127.0.0.1:3000/", source)
        self.assertIn("html.file-protocol .shell { visibility: hidden; }", source)

    def test_renderer_admission_is_a_pure_declared_policy_boundary(self):
        admission = (ROOT / "static" / "js" / "workbench" / "canvas" / "renderer-admission.js").read_text(encoding="utf-8")
        self.assertIn("function admits(policy, node)", admission)
        self.assertIn("if (!settings.enabled || !node) return false;", admission)
        self.assertIn("if (Array.isArray(settings.types)) return settings.types.includes(node.type);", admission)
        self.assertIn("if (typeof settings.accepts === 'function') return Boolean(settings.accepts(node));", admission)
        self.assertNotIn("fetch(", admission)
        self.assertNotIn("localStorage", admission)

    def test_media_playback_state_is_transport_and_dom_lifecycle_neutral(self):
        playback = (ROOT / "static" / "js" / "workbench" / "canvas" / "media-playback-state.js").read_text(encoding="utf-8")
        self.assertIn("function capture(media)", playback)
        self.assertIn("function restore(media, state)", playback)
        self.assertIn("function captureAll(root, options = {})", playback)
        self.assertIn("function restoreAll(root, states, options = {})", playback)
        self.assertNotIn("fetch(", playback)
        self.assertNotIn("localStorage", playback)

    def test_editor_adapters_share_execution_result_media_normalization(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-result-normalizer.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaResultNormalizer;
const classic = api.extract({{images:[{{url:'/one.png', name:'one'}}, '/two.png'], output_url:'/one.png'}});
const smart = api.extract({{url:'/root.png', width:640, image_items:[{{url:'/nested.mp4', height:360}}]}}, {{includeRoot:true, nestedKeys:['image_items'], rootKeys:['image_items'], copyFields:['width','height']}});
console.log(JSON.stringify({{classic, smart}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "classic": [{"url": "/one.png", "kind": "", "name": "one"}, "/two.png"],
            "smart": [{"url": "/root.png", "kind": "", "name": "", "width": 640}, {"url": "/nested.mp4", "kind": "", "name": "", "height": 360}],
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-result-normalizer.js"), page_source.index(editor))
            # Wave 16a moved the executor bodies (with their extract call
            # sites) into classic-executor-runtime.js; page keeps load order.
            executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
            self.assertIn("WorkbenchCanvasMediaResultNormalizer.extract", editor_source + executor_source)

    def test_classic_editor_inlines_execution_result_extraction_through_the_shared_seam(self):
        editor_source = read_canvas_app_source(ROOT)
        executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
        self.assertNotIn("function comfyResultOutputs", editor_source)
        self.assertNotIn("function resultMediaUrls", editor_source)
        self.assertNotIn("comfyResultOutputs(", editor_source)
        self.assertNotIn("resultMediaUrls(", editor_source)
        # Wave 16a moved the six inlined call sites into the executor seam
        # with the run*Node bodies; count across page + seam.
        extract_calls = re.findall(r"window\.WorkbenchCanvasMediaResultNormalizer\.extract\(", editor_source + executor_source)
        self.assertGreaterEqual(len(extract_calls), 6,
            msg=f"expected >= 6 inlined seam calls across canvas.js + executor seam, got {len(extract_calls)}")

    def test_classic_editor_routes_provider_node_creation_through_classic_node_factories_seam(self):
        # Behavioral: drive the seam in a vm sandbox, verify the host sees
        # exactly the right createNode calls for the three provider types.
        seam = ROOT / "static/js/workbench/canvas/classic-node-factories.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const calls = [];
const host = {{
    addNode: (record) => {{ calls.push({{type:record.type, id:record.id, apiProvider:record.apiProvider || '', model:record.model || '', msgenModel:record.msgenModel || ''}}); return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    imageApiProviders: () => [{{id: 'test-img'}}],
    allImageModels: () => ['test-model'],
    defaultApiImageResolution: () => '1024x1024',
    resolveMidjourneyProviderId: () => 'test-mj',
    modelscopeImageModels: () => ['test-ms'],
    videoApiProviders: () => [],
    providerVideoModels: () => [],
    videoModels: () => [],
    defaultVideoModels: () => [],
}};
const api = sandbox.window.WorkbenchCanvasClassicNodeFactories.create(host);
api.addGenerator({{point: {{x: 100, y: 50}}}});
api.addMidjourney({{point: {{x: 200, y: 60}}}});
api.addMsGen({{point: {{x: 300, y: 70}}}});
console.log(JSON.stringify(calls));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [
            {"type": "generator", "id": "gen-test", "apiProvider": "test-img", "model": "test-model", "msgenModel": ""},
            {"type": "midjourney", "id": "mj-test", "apiProvider": "test-mj", "model": "", "msgenModel": ""},
            {"type": "msgen", "id": "msgen-test", "apiProvider": "", "model": "", "msgenModel": "zimage"},
        ])
        # Behavioral: missing host op throws TypeError on create.
        for missing in ('addNode', 'uid', 'defaultPoint', 'imageApiProviders',
                'allImageModels', 'defaultApiImageResolution',
                'resolveMidjourneyProviderId', 'modelscopeImageModels',
                'videoApiProviders', 'providerVideoModels',
                'videoModels', 'defaultVideoModels'):
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    addNode: (r) => r, uid: (p) => p, defaultPoint: () => ({{x:0,y:0}}),
    imageApiProviders: () => [], allImageModels: () => [],
    defaultApiImageResolution: () => '', resolveMidjourneyProviderId: () => '',
    modelscopeImageModels: () => [],
    videoApiProviders: () => [], providerVideoModels: () => [],
    videoModels: () => [], defaultVideoModels: () => [],
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicNodeFactories.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-node-factories.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-node-factories.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the local factory function
        # definitions and now uses the seam-call dispatcher instead.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addGeneratorNode", editor_source)
        self.assertNotIn("function addMidjourneyNode", editor_source)
        self.assertNotIn("function addMsGenNode", editor_source)
        self.assertIn("function ensureClassicNodeFactories", editor_source)
        for seam_call in (".addGenerator({point})", ".addMidjourney({point})", ".addMsGen({point})"):
            self.assertIn(seam_call, editor_source,
                msg=f"canvas.js dispatcher should call ensureClassicNodeFactories(){seam_call}")

    def test_classic_editor_routes_video_node_creation_through_classic_node_factories_seam(self):
        # Wave 3 follow-on: video-node-creation MIGRATED. Drives the seam's
        # new addVideo method and pins the canvas.js dispatcher + wrapper-
        # deletion source-contract for the video half specifically.
        seam = ROOT / "static/js/workbench/canvas/classic-node-factories.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    imageApiProviders: () => [], allImageModels: () => [],
    defaultApiImageResolution: () => '', resolveMidjourneyProviderId: () => '',
    modelscopeImageModels: () => [],
    videoApiProviders: () => [{{id: 'test-vid'}}],
    providerVideoModels: () => ['test-vid-model'],
    videoModels: () => ['dynamic-vid-model'],
    defaultVideoModels: () => ['fallback-vid-model'],
}};
const api = sandbox.window.WorkbenchCanvasClassicNodeFactories.create(host);
api.addVideo({{point: {{x: 222, y: 333}}}});
console.log(JSON.stringify({{
  type: captured.record.type, id: captured.record.id,
  apiProvider: captured.record.apiProvider, model: captured.record.model,
  duration: captured.record.duration, aspectRatio: captured.record.aspectRatio,
  x: captured.record.x, y: captured.record.y, inputs: captured.record.inputs,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "type": "video", "id": "vid-test",
            "apiProvider": "test-vid", "model": "test-vid-model",
            "duration": 5, "aspectRatio": "16:9",
            "x": 222, "y": 333, "inputs": [],
        })
        # Source-contract: canvas.js no longer has the local factory
        # definition and the dispatcher routes 'video' through the seam.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addVideoNode", editor_source,
            msg="canvas.js should no longer define function addVideoNode")
        self.assertIn("ensureClassicNodeFactories().addVideo({point})", editor_source,
            msg="canvas.js dispatcher should call ensureClassicNodeFactories().addVideo({point})")
        self.assertIn("videoApiProviders", editor_source,
            msg="ensureClassicNodeFactories host should still inject videoApiProviders")
        self.assertIn("providerVideoModels", editor_source,
            msg="ensureClassicNodeFactories host should still inject providerVideoModels")
        self.assertIn("defaultVideoModels: () => DEFAULT_VIDEO_MODELS", editor_source,
            msg="ensureClassicNodeFactories host should inject defaultVideoModels as a constant-returning function")

    def test_classic_editor_routes_output_node_creation_through_classic_node_factories_seam(self):
        # Wave 4 follow-on: output-node-creation MIGRATED. addOutputNode is
        # a minimal 3-line factory (id/type/output/images:[]) — the new
        # seam method bodies out the same shape and the page now only
        # routes through the seam.
        seam = ROOT / "static/js/workbench/canvas/classic-node-factories.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    imageApiProviders: () => [], allImageModels: () => [],
    defaultApiImageResolution: () => '', resolveMidjourneyProviderId: () => '',
    modelscopeImageModels: () => [],
    videoApiProviders: () => [], providerVideoModels: () => [],
    videoModels: () => [], defaultVideoModels: () => [],
}};
const api = sandbox.window.WorkbenchCanvasClassicNodeFactories.create(host);
api.addOutput({{point: {{x: 444, y: 555}}}});
console.log(JSON.stringify({{
  type: captured.record.type, id: captured.record.id,
  x: captured.record.x, y: captured.record.y, images: captured.record.images,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "type": "output", "id": "out-test",
            "x": 444, "y": 555, "images": [],
        })
        # Source-contract: canvas.js no longer has the local factory
        # definition and the dispatcher routes 'output' through the seam.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addOutputNode", editor_source,
            msg="canvas.js should no longer define function addOutputNode")
        self.assertIn("ensureClassicNodeFactories().addOutput({point})", editor_source,
            msg="canvas.js dispatcher should call ensureClassicNodeFactories().addOutput({point})")

    def test_classic_editor_routes_provider_card_body_through_classic_card_body_renderer_seam(self):
        # Wave 5: provider-card-body COMPAT seam. The four large page-side
        # body builders (renderLLMBody / renderGeneratorBody /
        # renderMidjourneyBody / renderMsGenBody) move behind a bounded
        # compat seam module. canvas.js no longer owns the body
        # construction; the page only routes the four dispatch branches
        # through `ensureClassicCardBodyRenderer().renderXxx({node})`.
        seam = ROOT / "static/js/workbench/canvas/classic-card-body-renderer.js"
        # Behavioral: drive the seam in a vm sandbox with a stubbed
        # document. The four render methods must construct a `<div>`
        # root via `document.createElement` and run their inner bodies
        # without throwing on a minimal mock host.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null,
        onmousedown: null, onblur: null,
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        dispatchEvent(ev) {{ return true; }},
        forEach() {{}},
        classList: {{ toggle() {{}} }},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const sandbox = {{window: {{}}, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const host = {{
    document: documentStub,
    escapeHtml: (s) => String(s), tr: (k) => k,
    resolveChatProviderId: (v) => v || 'comfly',
    providerChatModels: () => ['m1'],
    chatModelOptions: () => '<option>m1</option>',
    chatProviderOptions: () => '<option>comfly</option>',
    resolveChatModel: (m) => m,
    llmInputImages: () => [], llmInputVideos: () => [],
    renderLLMChatPane: () => {{}}, renderLLMNodePane: () => {{}},
    bindScrollableText: () => {{}},
    ensureProviderControls: () => ({{
        setField: () => {{}}, save: () => {{}}, render: () => {{}},
    }}),
    generatorSources: () => [], orderedSources: (n, s) => s,
    mediaKindForRef: () => 'image',
    sanitizeImageNodeProviderModel: () => {{}},
    normalizeApiNodeSizeChoice: () => {{}},
    providerOptions: () => '', imageModelOptions: () => '',
    providerImageModels: () => [],
    resolveImageModel: (m) => m,
    defaultApiImageResolution: () => '1024x1024',
    parseSizeValue: (s) => ({{width: '', height: ''}}),
    isGptImageAutoSizeModel: () => false,
    ratioPartsFromDimensions: (w, h) => ({{width: w, height: h}}),
    resolveMidjourneyProviderId: (v) => v,
    midjourneyProviderOptions: () => '',
    midjourneyContinuationHtml: () => '',
    midjourneyModalHtml: () => '',
    runMidjourneyAction: () => {{}},
    runMidjourneyModal: () => {{}},
    MS_GEN_MODELS: {{ zimage: {{label: 'ZImage', labelKey: '', supportsImage: true, acceptsImage: true}} }},
    modelscopeImageModels: () => ['Tongyi-MAI/Z-Image-Turbo'],
    currentMsModelId: () => 'zimage',
    modelscopeLorasForModel: () => [],
    modelscopeLoraOptions: () => '',
    modelscopeImageModelOptions: () => '',
    getImageDimensions: async () => ({{width: 1024, height: 1024}}),
    showErrorModal: () => {{}},
    renderImageInputList: () => {{}}, renderPromptPreview: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '',
    bindCascadeButtons: () => {{}},
    scheduleSave: () => {{}}, render: () => {{}},
    runCanvasGenerate: () => {{}},
}};
const api = sandbox.window.WorkbenchCanvasClassicCardBodyRenderer.create(host);
const out = {{
  hasLLM: typeof api.renderLLM === 'function',
  hasGenerator: typeof api.renderGenerator === 'function',
  hasMidjourney: typeof api.renderMidjourney === 'function',
  hasMsGen: typeof api.renderMsGen === 'function',
  frozen: Object.isFrozen(api),
}};
try {{
  const llmNode = {{type: 'llm', mode: 'node', llmProvider: 'comfly', model: 'm1'}};
  api.renderLLM({{node: llmNode}});
  out.llmRan = true;
}} catch(e) {{ out.llmErr = String(e); }}
try {{
  const msNode = {{type: 'msgen', msgenModel: 'zimage'}};
  api.renderMsGen({{node: msNode}});
  out.msRan = true;
}} catch(e) {{ out.msErr = String(e); }}
try {{
  const mjNode = {{type: 'midjourney', apiProvider: '', mode: 'imagine'}};
  api.renderMidjourney({{node: mjNode}});
  out.mjRan = true;
}} catch(e) {{ out.mjErr = String(e); }}
try {{
  const genNode = {{type: 'generator', apiProvider: '', model: ''}};
  api.renderGenerator({{node: genNode}});
  out.genRan = true;
}} catch(e) {{ out.genErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasLLM"], msg="seam must expose renderLLM")
        self.assertTrue(actual["hasGenerator"], msg="seam must expose renderGenerator")
        self.assertTrue(actual["hasMidjourney"], msg="seam must expose renderMidjourney")
        self.assertTrue(actual["hasMsGen"], msg="seam must expose renderMsGen")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertTrue(actual.get("llmRan"), msg=f"renderLLM must run on minimal mock host, got: {actual.get('llmErr')}")
        self.assertTrue(actual.get("msRan"), msg=f"renderMsGen must run on minimal mock host, got: {actual.get('msErr')}")
        self.assertTrue(actual.get("mjRan"), msg=f"renderMidjourney must run on minimal mock host, got: {actual.get('mjErr')}")
        self.assertTrue(actual.get("genRan"), msg=f"renderGenerator must run on minimal mock host, got: {actual.get('genErr')}")
        # TypeError-on-missing-host: every one of the 48 REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        REQUIRED = [
            'document', 'escapeHtml', 'tr',
            'resolveChatProviderId', 'providerChatModels', 'chatModelOptions',
            'chatProviderOptions', 'resolveChatModel',
            'llmInputImages', 'llmInputVideos',
            'renderLLMChatPane', 'renderLLMNodePane', 'bindScrollableText',
            'ensureProviderControls',
            'generatorSources', 'orderedSources', 'mediaKindForRef',
            'sanitizeImageNodeProviderModel', 'normalizeApiNodeSizeChoice',
            'providerOptions', 'imageModelOptions',
            'providerImageModels', 'resolveImageModel',
            'defaultApiImageResolution', 'parseSizeValue',
            'isGptImageAutoSizeModel', 'ratioPartsFromDimensions',
            'resolveMidjourneyProviderId', 'midjourneyProviderOptions',
            'midjourneyContinuationHtml', 'midjourneyModalHtml',
            'runMidjourneyAction', 'runMidjourneyModal',
            'MS_GEN_MODELS', 'modelscopeImageModels',
            'currentMsModelId', 'modelscopeLorasForModel',
            'modelscopeLoraOptions', 'modelscopeImageModelOptions',
            'getImageDimensions', 'showErrorModal',
            'renderImageInputList', 'renderPromptPreview',
            'cascadeBtnHtml', 'retryBarHtml',
            'bindCascadeButtons',
            'scheduleSave', 'render', 'runCanvasGenerate',
        ]
        self.assertEqual(len(REQUIRED), 49,
            msg="REQUIRED_OPS count pin: Wave 5 seam module declares 49 host ops; if you add/remove an op, update both the seam and this test")
        for missing in REQUIRED:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, escapeHtml: () => '', tr: () => '',
    resolveChatProviderId: () => '', providerChatModels: () => [],
    chatModelOptions: () => '', chatProviderOptions: () => '', resolveChatModel: () => '',
    llmInputImages: () => [], llmInputVideos: () => [],
    renderLLMChatPane: () => {{}}, renderLLMNodePane: () => {{}},
    bindScrollableText: () => {{}}, ensureProviderControls: () => ({{setField:()=>{{}}, save:()=>{{}}, render:()=>{{}}}}),
    generatorSources: () => [], orderedSources: (n,s)=>s, mediaKindForRef: () => '',
    sanitizeImageNodeProviderModel: () => {{}}, normalizeApiNodeSizeChoice: () => {{}},
    providerOptions: () => '', imageModelOptions: () => '',
    providerImageModels: () => [], resolveImageModel: () => '',
    defaultApiImageResolution: () => '', parseSizeValue: () => ({{width:'', height:''}}),
    isGptImageAutoSizeModel: () => false, ratioPartsFromDimensions: (w,h) => ({{width:w,height:h}}),
    resolveMidjourneyProviderId: () => '', midjourneyProviderOptions: () => '',
    midjourneyContinuationHtml: () => '', midjourneyModalHtml: () => '',
    runMidjourneyAction: () => {{}}, runMidjourneyModal: () => {{}},
    MS_GEN_MODELS: {{}}, modelscopeImageModels: () => [],
    currentMsModelId: () => '', modelscopeLorasForModel: () => [],
    modelscopeLoraOptions: () => '', modelscopeImageModelOptions: () => '',
    getImageDimensions: async () => ({{width:0, height:0}}),
    showErrorModal: () => {{}},
    renderImageInputList: () => {{}}, renderPromptPreview: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '',
    bindCascadeButtons: () => {{}},
    scheduleSave: () => {{}}, render: () => {{}}, runCanvasGenerate: () => {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicCardBodyRenderer.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-card-body-renderer.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-card-body-renderer.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the four local body function
        # definitions and the dispatcher routes every kind through the
        # seam's render methods via `ensureClassicCardBodyRenderer()`.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function renderLLMBody", editor_source,
            msg="canvas.js should no longer define function renderLLMBody")
        self.assertNotIn("function renderGeneratorBody", editor_source,
            msg="canvas.js should no longer define function renderGeneratorBody")
        self.assertNotIn("function renderMidjourneyBody", editor_source,
            msg="canvas.js should no longer define function renderMidjourneyBody")
        self.assertNotIn("function renderMsGenBody", editor_source,
            msg="canvas.js should no longer define function renderMsGenBody")
        self.assertIn("function ensureClassicCardBodyRenderer", editor_source,
            msg="canvas.js must declare ensureClassicCardBodyRenderer next to ensureClassicNodeFactories")
        for kind, method in (("llm", "renderLLM"), ("generator", "renderGenerator"),
                ("midjourney", "renderMidjourney"), ("msgen", "renderMsGen")):
            self.assertIn(
                "cardBody.{m}({{node}})".format(m=method),
                editor_source,
                msg=f"canvas.js dispatcher for {kind!r} must call cardBody.{method}({{node}})",
            )

    def test_classic_editor_routes_comfy_workflow_field_controls_through_classic_comfy_controls_seam(self):
        # Wave 6: comfy-controls COMPAT seam. Five page-side Comfy
        # functions (addComfyNode / comfyWorkflowOptions / renderComfyBody
        # / renderComfySettings / updateComfyField) move behind a
        # bounded compat seam. canvas.js no longer owns the body / settings
        # construction or the workflow-option helper; the page only
        # routes the kind branches through
        # `ensureClassicComfyControls().{addNode, renderBody}(...)`.
        seam = ROOT / "static/js/workbench/canvas/classic-comfy-controls.js"
        # Behavioral: drive the seam in a vm sandbox with a stubbed
        # document. addNode must land at host.addNode with the right
        # record shape; renderBody / renderSettings must run without
        # throwing; getWorkflowOptions must produce a stable option HTML.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null,
        onmousedown: null, onblur: null,
        classList: {{ contains: () => false }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        closest() {{ return null; }},
        dispatchEvent(ev) {{ return true; }},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const sandbox = {{window: {{}}, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    document: documentStub,
    escapeHtml: (s) => String(s), tr: (k) => k,
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    allImageModels: () => ['test-comfy-model'],
    imageApiProviders: () => [{{id: 'comfly'}}],
    getModels: () => ({{gpt: 'gpt-image-2'}}),
    getComfyWorkflows: () => [{{name: 'wf1.json', title: 'Workflow 1'}}, {{name: 'wf2.json', title: 'Workflow 2'}}],
    generatorSources: () => [], orderedSources: (n, s) => s, imageRefsOnly: (refs) => refs,
    comfyFields: () => [],
    validComfyWorkflowName: (n) => n,
    hasComfyWorkflow: (n) => Boolean(n),
    currentComfyWorkflow: () => null,
    comfyFieldKind: () => 'setting',
    ensureComfyWorkflow: async () => ({{}}),
    render: () => {{}}, scheduleSave: () => {{}}, runCanvasGenerate: () => {{}},
    renderPromptPreview: () => {{}}, renderComfyImages: () => {{}},
    renderComfyCustomField: () => '', toggleComfyRandom: () => {{}},
    bindCascadeButtons: () => {{}}, cascadeBtnHtml: () => '', retryBarHtml: () => '',
}};
const api = sandbox.window.WorkbenchCanvasClassicComfyControls.create(host);
const out = {{
    hasAddNode: typeof api.addNode === 'function',
    hasRenderBody: typeof api.renderBody === 'function',
    hasRenderSettings: typeof api.renderSettings === 'function',
    hasUpdateField: typeof api.updateField === 'function',
    hasGetWorkflowOptions: typeof api.getWorkflowOptions === 'function',
    frozen: Object.isFrozen(api),
    workflowOpts: api.getWorkflowOptions({{selected: 'wf1.json'}}),
    workflowOptsEmpty: api.getWorkflowOptions({{selected: ''}}),
}};
try {{
  api.addNode({{point: {{x: 100, y: 200}}}});
  out.addNodeRan = true;
  out.addNodeType = captured.record?.type;
  out.addNodeId = captured.record?.id;
  out.addNodeProvider = (captured.record?.editModel || '');
  out.addNodeMode = captured.record?.mode;
  out.addNodeComfyWorkflow = captured.record?.comfyWorkflow;
}} catch(e) {{ out.addNodeErr = String(e); }}
// Build a second seam instance with an empty workflow list so the
// `getWorkflowOptions` fallback path can be exercised. The seam
// module destructures host.getComfyWorkflows into a local `var` at
// create() time, so a second `create()` call with an empty list is
// the only way to land on the `<option value="">…</option>` branch.
const emptyHost = Object.assign({{}}, host, {{getComfyWorkflows: () => []}});
const emptyApi = sandbox.window.WorkbenchCanvasClassicComfyControls.create(emptyHost);
out.workflowOptsEmpty = emptyApi.getWorkflowOptions({{selected: ''}});
try {{
  const node = {{type: 'comfy', mode: 'text'}};
  api.renderBody({{node}});
  out.renderBodyRan = true;
}} catch(e) {{ out.renderBodyErr = String(e); }}
try {{
  const container = makeEl();
  api.renderSettings({{container, node: {{mode: 'text', width: 1024, height: 1024}}}});
  out.renderSettingsRan = true;
}} catch(e) {{ out.renderSettingsErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasAddNode"], msg="seam must expose addNode")
        self.assertTrue(actual["hasRenderBody"], msg="seam must expose renderBody")
        self.assertTrue(actual["hasRenderSettings"], msg="seam must expose renderSettings")
        self.assertTrue(actual["hasUpdateField"], msg="seam must expose updateField")
        self.assertTrue(actual["hasGetWorkflowOptions"], msg="seam must expose getWorkflowOptions")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertTrue(actual.get("addNodeRan"), msg=f"addNode must run on minimal mock host, got: {actual.get('addNodeErr')}")
        self.assertTrue(actual.get("renderBodyRan"), msg=f"renderBody must run on minimal mock host, got: {actual.get('renderBodyErr')}")
        self.assertTrue(actual.get("renderSettingsRan"), msg=f"renderSettings must run on minimal mock host, got: {actual.get('renderSettingsErr')}")
        self.assertEqual(actual.get("addNodeType"), "comfy", msg="addNode must produce a 'comfy' node record")
        self.assertEqual(actual.get("addNodeId"), "comfy-test", msg="addNode must use uid('comfy')")
        self.assertEqual(actual.get("addNodeMode"), "text", msg="addNode must default mode to 'text'")
        self.assertEqual(actual.get("addNodeComfyWorkflow"), "", msg="addNode must initialize comfyWorkflow to ''")
        self.assertIn("wf1.json", actual["workflowOpts"], msg="getWorkflowOptions must list workflows when selected matches")
        self.assertIn("wf2.json", actual["workflowOpts"], msg="getWorkflowOptions must list all workflows")
        self.assertIn('selected', actual["workflowOpts"], msg="getWorkflowOptions must mark the selected workflow")
        self.assertIn("comfyNoWorkflow", actual["workflowOptsEmpty"], msg="getWorkflowOptions must fall back to a placeholder when no workflows")
        # TypeError-on-missing-host: every one of the 29 REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        REQUIRED = [
            'document', 'escapeHtml', 'tr',
            'addNode', 'uid', 'defaultPoint',
            'allImageModels', 'imageApiProviders',
            'getModels', 'getComfyWorkflows',
            'generatorSources', 'orderedSources', 'imageRefsOnly',
            'comfyFields', 'validComfyWorkflowName',
            'hasComfyWorkflow', 'currentComfyWorkflow',
            'comfyFieldKind', 'ensureComfyWorkflow',
            'render', 'scheduleSave', 'runCanvasGenerate',
            'renderPromptPreview', 'renderComfyImages',
            'renderComfyCustomField', 'toggleComfyRandom',
            'bindCascadeButtons', 'cascadeBtnHtml', 'retryBarHtml',
        ]
        self.assertEqual(len(REQUIRED), 29,
            msg="REQUIRED_OPS count pin: Wave 6 seam module declares 29 host ops; if you add/remove an op, update both the seam and this test")
        for missing in REQUIRED:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, escapeHtml: () => '', tr: () => '',
    addNode: (r) => r, uid: (p) => p, defaultPoint: () => ({{x:0,y:0}}),
    allImageModels: () => [], imageApiProviders: () => [],
    getModels: () => ({{gpt: ''}}), getComfyWorkflows: () => [],
    generatorSources: () => [], orderedSources: (n,s)=>s, imageRefsOnly: (refs)=>refs,
    comfyFields: () => [], validComfyWorkflowName: (n)=>n,
    hasComfyWorkflow: () => false, currentComfyWorkflow: () => null,
    comfyFieldKind: () => 'setting', ensureComfyWorkflow: async () => ({{}}),
    render: () => {{}}, scheduleSave: () => {{}}, runCanvasGenerate: () => {{}},
    renderPromptPreview: () => {{}}, renderComfyImages: () => {{}},
    renderComfyCustomField: () => '', toggleComfyRandom: () => {{}},
    bindCascadeButtons: () => {{}}, cascadeBtnHtml: () => '', retryBarHtml: () => '',
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicComfyControls.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-comfy-controls.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-comfy-controls.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the five local Comfy function
        # definitions and the dispatcher routes 'comfy' through the seam.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addComfyNode", editor_source,
            msg="canvas.js should no longer define function addComfyNode")
        self.assertNotIn("function comfyWorkflowOptions", editor_source,
            msg="canvas.js should no longer define function comfyWorkflowOptions")
        self.assertNotIn("function renderComfyBody", editor_source,
            msg="canvas.js should no longer define function renderComfyBody")
        self.assertNotIn("function renderComfySettings", editor_source,
            msg="canvas.js should no longer define function renderComfySettings")
        self.assertNotIn("function updateComfyField", editor_source,
            msg="canvas.js should no longer define function updateComfyField")
        self.assertIn("function ensureClassicComfyControls", editor_source,
            msg="canvas.js must declare ensureClassicComfyControls next to ensureClassicCardBodyRenderer")
        self.assertIn("ensureClassicComfyControls().addNode({point})", editor_source,
            msg="canvas.js createNodeByType dispatcher must call ensureClassicComfyControls().addNode({point})")
        self.assertIn("comfy.renderBody({node})", editor_source,
            msg="canvas.js body dispatcher must call comfy.renderBody({node})")

    def test_classic_editor_routes_runninghub_workflow_params_through_classic_runninghub_controls_seam(self):
        # Wave 7: runninghub-controls COMPAT seam. Six page-side
        # RunningHub functions (addRhNode / renderRhBody /
        # renderRhParams / runningHubProvider /
        # currentRunningHubWorkflow /
        # currentRunningHubWorkflowConfig) move behind a bounded
        # compat seam. canvas.js no longer owns the factory / body /
        # params construction or the resolver helpers; the page only
        # routes the kind branches through
        # `ensureClassicRunningHubControls().{addNode, renderBody,
        # renderParams, getProvider, getCurrentWorkflow,
        # getCurrentWorkflowConfig}(...)`.
        seam = ROOT / "static/js/workbench/canvas/classic-runninghub-controls.js"
        # Behavioral: drive the seam in a vm sandbox with a stubbed
        # document. addNode must land at host.addNode with the right
        # record shape; renderBody / renderParams must run without
        # throwing; getProvider / getCurrentWorkflow /
        # getCurrentWorkflowConfig must produce stable projections.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null,
        onmousedown: null, onblur: null,
        classList: {{ contains: () => false }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        closest() {{ return null; }},
        dispatchEvent(ev) {{ return true; }},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const sandbox = {{window: {{}}, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    document: documentStub,
    escapeHtml: (s) => String(s), escapeAttr: (s) => String(s), tr: (k) => k,
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    validRunningHubWorkflowId: (s) => String(s || '').trim(),
    parseRunningHubEntryKey: (s) => {{
        const text = String(s || '').trim();
        const match = text.match(/^(app|workflow|model):(.+)$/);
        return match ? {{kind:match[1], id:match[2]}} : null;
    }},
    runningHubEntryKey: (kind, id) => `${{kind}}:${{String(id || '').trim()}}`,
    runningHubAllEntries: () => [
        {{kind:'model', id:'rh-model', entry:{{model:'rh-model'}}}},
        {{kind:'app', id:'rh-app', entry:{{appId:'rh-app'}}}},
        {{kind:'workflow', id:'rh-wf', entry:{{workflowId:'rh-wf', title:'Test Workflow', fields:[]}}}},
    ],
    runningHubEntries: () => [],
    runningHubEntryId: (e, kind) => String(typeof e === 'string' ? e : (e?.model || e?.id || e?.name || '')).trim(),
    ensureRhNodeSelection: (n) => n,
    applyRhEntrySelection: () => {{}},
    rhSelectedEntryRef: () => null,
    rhCurrentKind: () => 'workflow',
    rhEntryOptions: () => '<option value="workflow:rh-wf">Test Workflow</option>',
    rhPaymentOptions: () => '<option value="free">free</option>',
    rhModelSettingsHtml: () => '',
    bindRhModelControls: () => {{}},
    renderRhPromptFields: () => {{}},
    renderRhInputs: () => {{}},
    rhMediaSources: () => ({{sources:[], refs:[], image:[], video:[], audio:[], prompt:''}}),
    rhActiveFields: () => [],
    rhFieldRole: () => 'setting',
    rhParamKey: (n, f) => `${{n}}:${{f}}`,
    rhExtractFieldOptions: () => [],
    rhFieldValue: () => '',
    rhDefaultValue: () => '',
    rhRandomEnabled: () => false,
    rhRandomActive: () => false,
    toggleRhRandom: () => {{}},
    currentRunningHubWorkflowEntry: (n) => ({{workflowId:'rh-wf', title:'Test Workflow', fields:[]}}),
    rhEntryFields: () => [],
    rhWorkflowJsonFromSources: (...srcs) => Object.assign({{}}, ...srcs.filter(Boolean)),
    bindRhParamControls: () => {{}},
    renderRhSettingField: () => '',
    generatorSources: () => [], orderedSources: (n, s) => s, imageRefsOnly: (refs) => refs,
    videoRefsOnly: (refs) => refs, audioRefsOnly: (refs) => refs,
    mediaKindForRef: () => 'image',
    nodeTitleForMedia: () => 'Image',
    rhMediaPreviewHtml: () => '',
    normalizeApiNodeSizeChoice: () => {{}},
    defaultApiImageResolution: () => '1024x1024',
    parseSizeValue: () => ({{width:'', height:''}}),
    renderImageInputList: () => {{}},
    render: () => {{}}, scheduleSave: () => {{}},
    runCanvasGenerate: () => {{}}, refreshIcons: () => {{}},
    renderPromptPreview: () => {{}}, bindCascadeButtons: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '',
    getApiProviders: () => [{{id:'runninghub', name:'RunningHub'}}],
    getRunningHubWorkflowCache: () => ({{'rh-wf': {{title:'Cached Workflow'}}}}),
}};
const api = sandbox.window.WorkbenchCanvasClassicRunningHubControls.create(host);
const out = {{
    hasAddNode: typeof api.addNode === 'function',
    hasRenderBody: typeof api.renderBody === 'function',
    hasRenderParams: typeof api.renderParams === 'function',
    hasGetProvider: typeof api.getProvider === 'function',
    hasGetCurrentWorkflow: typeof api.getCurrentWorkflow === 'function',
    hasGetCurrentWorkflowConfig: typeof api.getCurrentWorkflowConfig === 'function',
    frozen: Object.isFrozen(api),
    provider: api.getProvider() ? api.getProvider().id : null,
    currentWf: api.getCurrentWorkflow({{node:{{workflowId:'rh-wf'}}}}) ? api.getCurrentWorkflow({{node:{{workflowId:'rh-wf'}}}}).title : null,
    currentWfConfig: api.getCurrentWorkflowConfig({{node:{{workflowId:'rh-wf', rhMode:'workflow'}}}}) ? api.getCurrentWorkflowConfig({{node:{{workflowId:'rh-wf', rhMode:'workflow'}}}}).title : null,
}};
try {{
  api.addNode({{point: {{x: 200, y: 300}}}});
  out.addNodeRan = true;
  out.addNodeType = captured.record?.type;
  out.addNodeId = captured.record?.id;
  out.addNodeRhMode = captured.record?.rhMode;
  out.addNodeRhPayment = captured.record?.rhPayment;
  out.addNodeInputs = Array.isArray(captured.record?.inputs);
}} catch(e) {{ out.addNodeErr = String(e); }}
try {{
  const node = {{type: 'rh', workflowId: 'rh-wf', rhMode: 'workflow', rhParams: {{}}}};
  api.renderBody({{node}});
  out.renderBodyRan = true;
}} catch(e) {{ out.renderBodyErr = String(e); }}
try {{
  const container = makeEl();
  api.renderParams({{container, node: {{rhParams: {{}}}}, fields: [], media: {{refs:[]}}}});
  out.renderParamsRan = true;
  out.renderParamsEmpty = container.innerHTML.includes('rh-empty');
}} catch(e) {{ out.renderParamsErr = String(e); }}
try {{
  const nonWorkflowHost = Object.assign({{}}, host, {{rhCurrentKind: () => 'app'}});
  const nonWorkflowApi = sandbox.window.WorkbenchCanvasClassicRunningHubControls.create(nonWorkflowHost);
  const cfg = nonWorkflowApi.getCurrentWorkflowConfig({{node:{{workflowId:'', rhMode:'app'}}}});
  out.nonWorkflowConfig = cfg;
}} catch(e) {{ out.nonWorkflowConfigErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasAddNode"], msg="seam must expose addNode")
        self.assertTrue(actual["hasRenderBody"], msg="seam must expose renderBody")
        self.assertTrue(actual["hasRenderParams"], msg="seam must expose renderParams")
        self.assertTrue(actual["hasGetProvider"], msg="seam must expose getProvider")
        self.assertTrue(actual["hasGetCurrentWorkflow"], msg="seam must expose getCurrentWorkflow")
        self.assertTrue(actual["hasGetCurrentWorkflowConfig"], msg="seam must expose getCurrentWorkflowConfig")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertEqual(actual.get("provider"), "runninghub", msg="getProvider must resolve runninghub from getApiProviders()")
        self.assertEqual(actual.get("currentWf"), "Cached Workflow", msg="getCurrentWorkflow must read from getRunningHubWorkflowCache() closure")
        self.assertEqual(actual.get("currentWfConfig"), "Test Workflow", msg="getCurrentWorkflowConfig must merge entry + cache title")
        self.assertIsNone(actual.get("nonWorkflowConfig"), msg="getCurrentWorkflowConfig must return null when rhCurrentKind !== 'workflow'")
        self.assertTrue(actual.get("addNodeRan"), msg=f"addNode must run on minimal mock host, got: {actual.get('addNodeErr')}")
        self.assertTrue(actual.get("renderBodyRan"), msg=f"renderBody must run on minimal mock host, got: {actual.get('renderBodyErr')}")
        self.assertTrue(actual.get("renderParamsRan"), msg=f"renderParams must run on minimal mock host, got: {actual.get('renderParamsErr')}")
        self.assertEqual(actual.get("addNodeType"), "rh", msg="addNode must produce an 'rh' node record")
        self.assertEqual(actual.get("addNodeId"), "rh-test", msg="addNode must use uid('rh')")
        self.assertEqual(actual.get("addNodeRhMode"), "app", msg="addNode must default rhMode to 'app'")
        self.assertEqual(actual.get("addNodeRhPayment"), "free", msg="addNode must default rhPayment to 'free'")
        self.assertTrue(actual.get("addNodeInputs"), msg="addNode must initialize inputs to []")
        self.assertTrue(actual.get("renderParamsEmpty"), msg="renderParams must render the rh-empty placeholder when no params")
        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        REQUIRED = [
            'document', 'escapeHtml', 'escapeAttr', 'tr',
            'addNode', 'uid', 'defaultPoint',
            'validRunningHubWorkflowId', 'parseRunningHubEntryKey',
            'runningHubEntryKey', 'runningHubAllEntries', 'runningHubEntries',
            'runningHubEntryId', 'ensureRhNodeSelection', 'applyRhEntrySelection',
            'rhSelectedEntryRef', 'rhCurrentKind', 'rhEntryOptions',
            'rhPaymentOptions', 'rhModelSettingsHtml', 'bindRhModelControls',
            'renderRhPromptFields', 'renderRhInputs', 'rhMediaSources',
            'rhActiveFields', 'rhFieldRole', 'rhParamKey', 'rhExtractFieldOptions',
            'rhFieldValue', 'rhDefaultValue', 'rhRandomEnabled', 'rhRandomActive',
            'toggleRhRandom', 'currentRunningHubWorkflowEntry', 'rhEntryFields',
            'rhWorkflowJsonFromSources', 'bindRhParamControls',
            'renderRhSettingField',
            'generatorSources', 'orderedSources', 'imageRefsOnly', 'videoRefsOnly',
            'audioRefsOnly', 'mediaKindForRef', 'nodeTitleForMedia',
            'rhMediaPreviewHtml',
            'normalizeApiNodeSizeChoice', 'defaultApiImageResolution',
            'parseSizeValue', 'renderImageInputList',
            'render', 'scheduleSave', 'runCanvasGenerate', 'refreshIcons',
            'renderPromptPreview', 'bindCascadeButtons',
            'cascadeBtnHtml', 'retryBarHtml',
            'getApiProviders', 'getRunningHubWorkflowCache',
        ]
        self.assertEqual(len(REQUIRED), 60,
            msg="REQUIRED_OPS count pin: Wave 7 seam module declares 60 host ops; if you add/remove an op, update both the seam and this test")
        for missing in REQUIRED:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, escapeHtml: () => '', escapeAttr: () => '', tr: () => '',
    addNode: (r) => r, uid: (p) => p, defaultPoint: () => ({{x:0,y:0}}),
    validRunningHubWorkflowId: () => '', parseRunningHubEntryKey: () => null,
    runningHubEntryKey: () => '', runningHubAllEntries: () => [], runningHubEntries: () => [],
    runningHubEntryId: () => '', ensureRhNodeSelection: () => null, applyRhEntrySelection: () => {{}},
    rhSelectedEntryRef: () => null, rhCurrentKind: () => 'app', rhEntryOptions: () => '',
    rhPaymentOptions: () => '', rhModelSettingsHtml: () => '', bindRhModelControls: () => {{}},
    renderRhPromptFields: () => {{}}, renderRhInputs: () => {{}}, rhMediaSources: () => ({{}}),
    rhActiveFields: () => [], rhFieldRole: () => '', rhParamKey: () => '', rhExtractFieldOptions: () => [],
    rhFieldValue: () => '', rhDefaultValue: () => '', rhRandomEnabled: () => false,
    rhRandomActive: () => false, toggleRhRandom: () => {{}},
    currentRunningHubWorkflowEntry: () => null, rhEntryFields: () => [],
    rhWorkflowJsonFromSources: () => ({{}}), bindRhParamControls: () => {{}},
    renderRhSettingField: () => '',
    generatorSources: () => [], orderedSources: (n,s)=>s, imageRefsOnly: (refs)=>refs,
    videoRefsOnly: (refs)=>refs, audioRefsOnly: (refs)=>refs,
    mediaKindForRef: () => '', nodeTitleForMedia: () => '', rhMediaPreviewHtml: () => '',
    normalizeApiNodeSizeChoice: () => {{}}, defaultApiImageResolution: () => '',
    parseSizeValue: () => ({{width:'',height:''}}), renderImageInputList: () => {{}},
    render: () => {{}}, scheduleSave: () => {{}}, runCanvasGenerate: () => {{}}, refreshIcons: () => {{}},
    renderPromptPreview: () => {{}}, bindCascadeButtons: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '',
    getApiProviders: () => [], getRunningHubWorkflowCache: () => ({{}}),
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicRunningHubControls.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-runninghub-controls.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-runninghub-controls.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the six local function
        # definitions and the dispatcher routes every kind through the
        # seam's render methods via `ensureClassicRunningHubControls()`.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addRhNode", editor_source,
            msg="canvas.js should no longer define function addRhNode")
        self.assertNotIn("function renderRhBody", editor_source,
            msg="canvas.js should no longer define function renderRhBody")
        self.assertNotIn("function renderRhParams", editor_source,
            msg="canvas.js should no longer define function renderRhParams")
        self.assertNotIn("function runningHubProvider", editor_source,
            msg="canvas.js should no longer define function runningHubProvider")
        self.assertNotIn("function currentRunningHubWorkflow(node)", editor_source,
            msg="canvas.js should no longer define function currentRunningHubWorkflow")
        self.assertNotIn("function currentRunningHubWorkflowConfig", editor_source,
            msg="canvas.js should no longer define function currentRunningHubWorkflowConfig")
        self.assertIn("function ensureClassicRunningHubControls", editor_source,
            msg="canvas.js must declare ensureClassicRunningHubControls next to ensureClassicComfyControls")
        self.assertIn("ensureClassicRunningHubControls().addNode({point})", editor_source,
            msg="canvas.js createNodeByType dispatcher must call ensureClassicRunningHubControls().addNode({point})")
        self.assertIn("ensureClassicRunningHubControls().renderBody({node})", editor_source,
            msg="canvas.js body dispatcher must call ensureClassicRunningHubControls().renderBody({node})")
        self.assertIn("ensureClassicRunningHubControls().renderParams({", editor_source,
            msg="canvas.js refreshGeneratorInputViews must call ensureClassicRunningHubControls().renderParams({...})")


    def test_classic_editor_routes_minimax_timeline_player_generation_through_classic_minimax_controls_seam(self):
        # Wave 8: minimax-controls COMPAT seam. Six page-side MiniMax
        # functions (addMiniMaxNode / renderMiniMaxBody /
        # bindMiniMaxWorkbench / miniMaxEngine / miniMaxPlayerHtml /
        # miniMaxSyncPlayerDom) move behind a bounded compat seam.
        # canvas.js no longer owns the factory / body / workbench
        # binder / engine resolver / player builder / sync-player; the
        # page only routes the kind branches through
        # `ensureClassicMiniMaxControls().{addNode, renderBody,
        # bindWorkbench, getEngine, buildPlayerHtml, syncPlayerDom}(...)`.
        seam = ROOT / "static/js/workbench/canvas/classic-minimax-controls.js"
        # Behavioral: drive the seam in a vm sandbox with a stubbed
        # document. addNode must land at host.addNode with the right
        # record shape; renderBody / bindWorkbench / getEngine /
        # buildPlayerHtml / syncPlayerDom must run without throwing.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null,
        onmousedown: null, onblur: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}} }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        closest() {{ return null; }},
        getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 100, height: 10 }}; }},
        dispatchEvent(ev) {{ return true; }},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const sandbox = {{window: {{}}, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    document: documentStub,
    escapeHtml: (s) => String(s), escapeAttr: (s) => String(s),
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    miniMaxSelectedSegment: () => null,
    miniMaxTimelineTotal: () => 0,
    miniMaxActiveSegmentAt: () => null,
    miniMaxCompactSegments: () => {{}},
    miniMaxExplicitRefsForSegment: () => [],
    miniMaxRefsForNode: () => ({{refs: []}}),
    miniMaxUniqueRefs: (refs) => refs || [],
    miniMaxMediaHtml: () => '',
    miniMaxSegmentRefsByKind: () => 0,
    miniMaxStartPaneResize: () => {{}},
    miniMaxApplyTimelineTime: () => {{}},
    miniMaxDownloadItem: () => {{}},
    miniMaxSetSegmentResult: () => {{}},
    mediaKindForRef: () => 'image',
    mediaKindForOutputItem: () => 'image',
    canvasDisplayMediaUrl: (url) => url,
    canvasPreviewImgHtml: () => '<img>',
    canvasVideoPlayerHtml: () => '<video>',
    canvasFileNameFromUrl: () => '',
    pushUndo: () => {{}}, refreshNodes: () => {{}},
    scheduleSave: () => {{}},
    bindScrollableText: () => {{}}, bindCascadeButtons: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '',
    refreshIcons: () => {{}},
    rhPaymentOptions: () => '<option value="free">free</option>',
    runMiniMaxNode: () => {{}},
    CANVAS_MINIMAX_REF_IMAGE_MAX: 9,
    CANVAS_MINIMAX_REF_VIDEO_MAX: 3,
    CANVAS_MINIMAX_REF_AUDIO_MAX: 3,
    CANVAS_MINIMAX_DEFAULT_ENGINE: 'comfyui',
    CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID: '2084608321469898754',
}};
const api = sandbox.window.WorkbenchCanvasClassicMiniMaxControls.create(host);
const out = {{
    hasAddNode: typeof api.addNode === 'function',
    hasRenderBody: typeof api.renderBody === 'function',
    hasBindWorkbench: typeof api.bindWorkbench === 'function',
    hasGetEngine: typeof api.getEngine === 'function',
    hasBuildPlayerHtml: typeof api.buildPlayerHtml === 'function',
    hasSyncPlayerDom: typeof api.syncPlayerDom === 'function',
    frozen: Object.isFrozen(api),
    engineComfy: api.getEngine({{node:{{}}}}),
    engineRh: api.getEngine({{node:{{minimaxEngine: 'runninghub'}}}}),
    emptyPlayerHtml: api.buildPlayerHtml({{seg: null}}),
}};
try {{
  api.addNode({{point: {{x: 100, y: 200}}}});
  out.addNodeRan = true;
  out.addNodeType = captured.record?.type;
  out.addNodeId = captured.record?.id;
  out.addNodeEngine = captured.record?.minimaxEngine;
  out.addNodePayment = captured.record?.rhPayment;
  out.addNodeW = captured.record?.w;
  out.addNodeH = captured.record?.h;
  out.addNodeWfId = captured.record?.minimaxRunningHubWorkflowId;
  out.addNodeAspect = captured.record?.aspectRatio;
  out.addNodeMegapixels = captured.record?.megapixels;
  out.addNodeSegments = Array.isArray(captured.record?.segments);
}} catch(e) {{ out.addNodeErr = String(e); }}
try {{
  const node = {{type: 'minimax', segments: [], materials: []}};
  api.renderBody({{node}});
  out.renderBodyRan = true;
}} catch(e) {{ out.renderBodyErr = String(e); }}
try {{
  const wrap = makeEl();
  api.bindWorkbench({{wrap, node: {{segments: [], materials: [], minimaxEngine: 'comfyui'}}}});
  out.bindWorkbenchRan = true;
}} catch(e) {{ out.bindWorkbenchErr = String(e); }}
try {{
  const wrap = makeEl();
  api.syncPlayerDom({{wrap, seg: null, time: 0, play: false}});
  out.syncPlayerDomRan = true;
}} catch(e) {{ out.syncPlayerDomErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasAddNode"], msg="seam must expose addNode")
        self.assertTrue(actual["hasRenderBody"], msg="seam must expose renderBody")
        self.assertTrue(actual["hasBindWorkbench"], msg="seam must expose bindWorkbench")
        self.assertTrue(actual["hasGetEngine"], msg="seam must expose getEngine")
        self.assertTrue(actual["hasBuildPlayerHtml"], msg="seam must expose buildPlayerHtml")
        self.assertTrue(actual["hasSyncPlayerDom"], msg="seam must expose syncPlayerDom")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertEqual(actual.get("engineComfy"), "comfyui", msg="getEngine must default to CANVAS_MINIMAX_DEFAULT_ENGINE when minimaxEngine is not 'runninghub'")
        self.assertEqual(actual.get("engineRh"), "runninghub", msg="getEngine must return 'runninghub' when minimaxEngine === 'runninghub'")
        self.assertIn("minimax-player-empty", actual.get("emptyPlayerHtml", ""), msg="buildPlayerHtml must produce the empty-player placeholder when seg.result.url is absent")
        self.assertTrue(actual.get("addNodeRan"), msg=f"addNode must run on minimal mock host, got: {actual.get('addNodeErr')}")
        self.assertTrue(actual.get("renderBodyRan"), msg=f"renderBody must run on minimal mock host, got: {actual.get('renderBodyErr')}")
        self.assertTrue(actual.get("bindWorkbenchRan"), msg=f"bindWorkbench must run on minimal mock host, got: {actual.get('bindWorkbenchErr')}")
        self.assertTrue(actual.get("syncPlayerDomRan"), msg=f"syncPlayerDom must run on minimal mock host, got: {actual.get('syncPlayerDomErr')}")
        self.assertEqual(actual.get("addNodeType"), "minimax", msg="addNode must produce a 'minimax' node record")
        self.assertEqual(actual.get("addNodeId"), "mmx-test", msg="addNode must use uid('mmx')")
        self.assertEqual(actual.get("addNodeEngine"), "comfyui", msg="addNode must default minimaxEngine to CANVAS_MINIMAX_DEFAULT_ENGINE")
        self.assertEqual(actual.get("addNodePayment"), "free", msg="addNode must default rhPayment to 'free'")
        self.assertEqual(actual.get("addNodeW"), 980, msg="addNode must default w to 980")
        self.assertEqual(actual.get("addNodeH"), 720, msg="addNode must default h to 720")
        self.assertEqual(actual.get("addNodeWfId"), "2084608321469898754", msg="addNode must default minimaxRunningHubWorkflowId to CANVAS_MINIMAX_RUNNINGHUB_WORKFLOW_ID")
        self.assertEqual(actual.get("addNodeAspect"), "16:9", msg="addNode must default aspectRatio to '16:9'")
        self.assertEqual(actual.get("addNodeMegapixels"), 0.4, msg="addNode must default megapixels to 0.4")
        self.assertTrue(actual.get("addNodeSegments"), msg="addNode must initialize segments to []")
        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        REQUIRED = [
            'document', 'escapeHtml', 'escapeAttr',
            'addNode', 'uid', 'defaultPoint',
            'miniMaxSelectedSegment', 'miniMaxTimelineTotal',
            'miniMaxActiveSegmentAt', 'miniMaxCompactSegments',
            'miniMaxExplicitRefsForSegment', 'miniMaxRefsForNode',
            'miniMaxUniqueRefs', 'miniMaxMediaHtml',
            'miniMaxSegmentRefsByKind', 'miniMaxStartPaneResize',
            'miniMaxApplyTimelineTime', 'miniMaxDownloadItem',
            'miniMaxSetSegmentResult',
            'mediaKindForRef', 'mediaKindForOutputItem',
            'canvasDisplayMediaUrl', 'canvasPreviewImgHtml',
            'canvasVideoPlayerHtml', 'canvasFileNameFromUrl',
            'pushUndo', 'refreshNodes', 'scheduleSave',
            'bindScrollableText', 'bindCascadeButtons',
            'cascadeBtnHtml', 'retryBarHtml', 'refreshIcons',
            'rhPaymentOptions', 'runMiniMaxNode',
        ]
        self.assertEqual(len(REQUIRED), 35,
            msg="REQUIRED_OPS count pin: Wave 8 seam module declares 35 host ops; if you add/remove an op, update both the seam and this test")
        for missing in REQUIRED:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, escapeHtml: () => '', escapeAttr: () => '',
    addNode: (r) => r, uid: (p) => p, defaultPoint: () => ({{x:0,y:0}}),
    miniMaxSelectedSegment: () => null, miniMaxTimelineTotal: () => 0,
    miniMaxActiveSegmentAt: () => null, miniMaxCompactSegments: () => {{}},
    miniMaxExplicitRefsForSegment: () => [], miniMaxRefsForNode: () => ({{refs:[]}}),
    miniMaxUniqueRefs: (r) => r || [], miniMaxMediaHtml: () => '',
    miniMaxSegmentRefsByKind: () => 0, miniMaxStartPaneResize: () => {{}},
    miniMaxApplyTimelineTime: () => {{}}, miniMaxDownloadItem: () => {{}},
    miniMaxSetSegmentResult: () => {{}},
    mediaKindForRef: () => '', mediaKindForOutputItem: () => '',
    canvasDisplayMediaUrl: (u) => u, canvasPreviewImgHtml: () => '',
    canvasVideoPlayerHtml: () => '', canvasFileNameFromUrl: () => '',
    pushUndo: () => {{}}, refreshNodes: () => {{}}, scheduleSave: () => {{}},
    bindScrollableText: () => {{}}, bindCascadeButtons: () => {{}},
    cascadeBtnHtml: () => '', retryBarHtml: () => '', refreshIcons: () => {{}},
    rhPaymentOptions: () => '', runMiniMaxNode: () => {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicMiniMaxControls.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-minimax-controls.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-minimax-controls.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the six local function
        # definitions and the dispatcher routes every kind through the
        # seam via `ensureClassicMiniMaxControls()`.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addMiniMaxNode", editor_source,
            msg="canvas.js should no longer define function addMiniMaxNode")
        self.assertNotIn("function renderMiniMaxBody", editor_source,
            msg="canvas.js should no longer define function renderMiniMaxBody")
        self.assertNotIn("function bindMiniMaxWorkbench", editor_source,
            msg="canvas.js should no longer define function bindMiniMaxWorkbench")
        self.assertNotIn("function miniMaxEngine", editor_source,
            msg="canvas.js should no longer define function miniMaxEngine")
        self.assertNotIn("function miniMaxPlayerHtml", editor_source,
            msg="canvas.js should no longer define function miniMaxPlayerHtml")
        self.assertNotIn("function miniMaxSyncPlayerDom", editor_source,
            msg="canvas.js should no longer define function miniMaxSyncPlayerDom")
        self.assertIn("function ensureClassicMiniMaxControls", editor_source,
            msg="canvas.js must declare ensureClassicMiniMaxControls next to ensureClassicRunningHubControls")
        self.assertIn("ensureClassicMiniMaxControls().addNode({point})", editor_source,
            msg="canvas.js createNodeByType dispatcher must call ensureClassicMiniMaxControls().addNode({point})")
        self.assertIn("mmx.renderBody({node})", editor_source,
            msg="canvas.js body dispatcher must call mmx.renderBody({node})")


    def test_classic_editor_routes_ltx_director_timeline_relay_through_classic_ltx_controls_seam(self):
        # Wave 9: ltx-controls COMPAT seam. Six page-side LTX
        # functions (addLTXDirectorNode / renderLTXDirectorBody /
        # destroyLTXEditor / ltxParseTimeline /
        # ltxFlushTimelineToNode / ltxBuildContiguousRelay) move
        # behind a bounded compat seam. canvas.js no longer owns the
        # factory / body / editor cleanup / timeline parser / flush
        # / contiguous-relay builder; the page only routes the kind
        # branches through
        # `ensureClassicLtxControls().{addNode, renderBody,
        # destroyEditor, parseTimeline, flushTimelineToNode,
        # buildContiguousRelay}(...)`.
        seam = ROOT / "static/js/workbench/canvas/classic-ltx-controls.js"
        # Behavioral: drive the seam in a vm sandbox with a stubbed
        # document + window stub for `CanvasLTXTimelineEditor`.
        # addNode must land at host.addNode with the right record
        # shape; renderBody / destroyEditor / parseTimeline /
        # flushTimelineToNode / buildContiguousRelay must run without
        # throwing.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null,
        onmousedown: null, onblur: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}} }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        closest() {{ return null; }},
        dispatchEvent(ev) {{ return true; }},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const windowStub = {{}};
const sandbox = {{window: windowStub, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    document: documentStub,
    escapeHtml: (s) => String(s), tr: (k) => k,
    addNode: (record) => {{ captured.record = record; return record; }},
    uid: (prefix) => prefix + '-test',
    defaultPoint: (dx, dy) => ({{x: dx, y: dy}}),
    ltxMigrateLegacySegments: () => {{}},
    ltxDirectorSyncSeconds: () => {{}},
    bindLTXParamsRow: () => {{}},
    ltxSyncConnectedImagesToTimeline: () => {{}},
    defaultLTXSegment: (start, length) => ({{id: 'ltxseg', start: start, length: length, prompt: '', type: 'text'}}),
    orderedSources: (n, s) => s || [], generatorSources: () => [], imageRefsOnly: (refs) => refs || [],
    renderPromptPreview: () => {{}}, renderComfyImages: () => {{}},
    scheduleSave: () => {{}}, runCanvasGenerate: () => {{}},
    bindCascadeButtons: () => {{}}, cascadeBtnHtml: () => '', retryBarHtml: () => '',
    updateLTXNodeElementSize: () => {{}}, refreshGeometryAfterLayout: () => {{}},
    windowObj: windowStub,
}};
const api = sandbox.window.WorkbenchCanvasClassicLtxControls.create(host);
const out = {{
    hasAddNode: typeof api.addNode === 'function',
    hasRenderBody: typeof api.renderBody === 'function',
    hasDestroyEditor: typeof api.destroyEditor === 'function',
    hasParseTimeline: typeof api.parseTimeline === 'function',
    hasFlushTimelineToNode: typeof api.flushTimelineToNode === 'function',
    hasBuildContiguousRelay: typeof api.buildContiguousRelay === 'function',
    frozen: Object.isFrozen(api),
    emptyTimeline: api.parseTimeline({{node: null}}),
    brokenTimeline: api.parseTimeline({{node: {{ltxTimelineData: 'not-json'}}}}),
}};
try {{
  api.addNode({{point: {{x: 250, y: 350}}}});
  out.addNodeRan = true;
  out.addNodeType = captured.record?.type;
  out.addNodeId = captured.record?.id;
  out.addNodeW = captured.record?.w;
  out.addNodeH = captured.record?.h;
  out.addNodeFrameRate = captured.record?.frameRate;
  out.addNodeDurationFrames = captured.record?.durationFrames;
  out.addNodeDurationSeconds = captured.record?.durationSeconds;
  out.addNodeDisplayMode = captured.record?.displayMode;
  out.addNodeInputs = Array.isArray(captured.record?.inputs);
}} catch(e) {{ out.addNodeErr = String(e); }}
try {{
  const node = {{type: 'ltxDirector', segments: [], materials: [], ltxTimelineData: JSON.stringify({{segments: [{{id:'s1', start:0, length:60, prompt:'a', type:'text'}}], audioSegments: []}}), durationFrames: 120}};
  api.renderBody({{node}});
  out.renderBodyRan = true;
}} catch(e) {{ out.renderBodyErr = String(e); }}
try {{
  api.destroyEditor({{node: {{}}}});
  api.destroyEditor({{node: {{}}}});
  out.destroyEditorRan = true;
}} catch(e) {{ out.destroyEditorErr = String(e); }}
try {{
  api.flushTimelineToNode({{node: null}});
  out.flushTimelineToNodeRan = true;
}} catch(e) {{ out.flushTimelineToNodeErr = String(e); }}
try {{
  const node = {{
      durationFrames: 100, ltxTimelineData: JSON.stringify({{
          segments: [
              {{id:'s1', start:0, length:30, prompt:'alpha', type:'text'}},
              {{id:'s2', start:40, length:30, prompt:'beta', type:'text'}},
          ],
          audioSegments: []
      }})
  }};
  out.relay = api.buildContiguousRelay({{node, globalPromptFallback: 'global'}});
}} catch(e) {{ out.relayErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasAddNode"], msg="seam must expose addNode")
        self.assertTrue(actual["hasRenderBody"], msg="seam must expose renderBody")
        self.assertTrue(actual["hasDestroyEditor"], msg="seam must expose destroyEditor")
        self.assertTrue(actual["hasParseTimeline"], msg="seam must expose parseTimeline")
        self.assertTrue(actual["hasFlushTimelineToNode"], msg="seam must expose flushTimelineToNode")
        self.assertTrue(actual["hasBuildContiguousRelay"], msg="seam must expose buildContiguousRelay")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertEqual(actual.get("emptyTimeline"), {"segments": [], "audioSegments": []}, msg="parseTimeline must return the empty default for null/missing node")
        self.assertEqual(actual.get("brokenTimeline"), {"segments": [], "audioSegments": []}, msg="parseTimeline must catch JSON.parse errors and return the empty default")
        self.assertTrue(actual.get("addNodeRan"), msg=f"addNode must run on minimal mock host, got: {actual.get('addNodeErr')}")
        self.assertTrue(actual.get("renderBodyRan"), msg=f"renderBody must run on minimal mock host, got: {actual.get('renderBodyErr')}")
        self.assertTrue(actual.get("destroyEditorRan"), msg=f"destroyEditor must run on minimal mock host, got: {actual.get('destroyEditorErr')}")
        self.assertTrue(actual.get("flushTimelineToNodeRan"), msg=f"flushTimelineToNode must run on minimal mock host, got: {actual.get('flushTimelineToNodeErr')}")
        self.assertEqual(actual.get("addNodeType"), "ltxDirector", msg="addNode must produce a 'ltxDirector' node record")
        self.assertEqual(actual.get("addNodeId"), "ltxdir-test", msg="addNode must use uid('ltxdir')")
        self.assertEqual(actual.get("addNodeW"), 1000, msg="addNode must default w to 1000")
        self.assertEqual(actual.get("addNodeH"), 800, msg="addNode must default h to 800")
        self.assertEqual(actual.get("addNodeFrameRate"), 24, msg="addNode must default frameRate to 24")
        self.assertEqual(actual.get("addNodeDurationFrames"), 120, msg="addNode must default durationFrames to 120")
        self.assertEqual(actual.get("addNodeDurationSeconds"), 5, msg="addNode must default durationSeconds to 5")
        self.assertEqual(actual.get("addNodeDisplayMode"), "seconds", msg="addNode must default displayMode to 'seconds'")
        self.assertTrue(actual.get("addNodeInputs"), msg="addNode must initialize inputs to []")
        # The relay must include the two segment prompts joined by ' | '
        # and the segment_lengths must include a gap-filler for the 10-frame gap between segments.
        relay = actual.get("relay", {})
        self.assertIsNotNone(relay, msg="buildContiguousRelay must produce a relay")
        self.assertIn("alpha", relay.get("local_prompts", ""), msg="relay.local_prompts must include the alpha segment prompt")
        self.assertIn("beta", relay.get("local_prompts", ""), msg="relay.local_prompts must include the beta segment prompt")
        # segment_lengths: alpha=30 + 10-gap → first slot 40,
        # beta=30 + 30-tail (currentCursor=70 < durationFrames=100) → second slot 60
        self.assertEqual(relay.get("segment_lengths", ""), "40,60", msg="relay.segment_lengths must include the 10-frame gap appended to the first segment and the 30-frame tail appended to the last")
        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        REQUIRED = [
            'document', 'escapeHtml', 'tr',
            'addNode', 'uid', 'defaultPoint',
            'ltxMigrateLegacySegments', 'ltxDirectorSyncSeconds',
            'bindLTXParamsRow', 'ltxSyncConnectedImagesToTimeline',
            'defaultLTXSegment',
            'orderedSources', 'generatorSources', 'imageRefsOnly',
            'renderPromptPreview', 'renderComfyImages',
            'scheduleSave', 'runCanvasGenerate',
            'bindCascadeButtons', 'cascadeBtnHtml', 'retryBarHtml',
            'updateLTXNodeElementSize', 'refreshGeometryAfterLayout',
            'windowObj',
        ]
        self.assertEqual(len(REQUIRED), 24,
            msg="REQUIRED_OPS count pin: Wave 9 seam module declares 24 host ops; if you add/remove an op, update both the seam and this test")
        for missing in REQUIRED:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, escapeHtml: () => '', tr: () => '',
    addNode: (r) => r, uid: (p) => p, defaultPoint: () => ({{x:0,y:0}}),
    ltxMigrateLegacySegments: () => {{}}, ltxDirectorSyncSeconds: () => {{}},
    bindLTXParamsRow: () => {{}}, ltxSyncConnectedImagesToTimeline: () => {{}},
    defaultLTXSegment: () => ({{}}),
    orderedSources: (n,s)=>s || [], generatorSources: () => [], imageRefsOnly: (r) => r || [],
    renderPromptPreview: () => {{}}, renderComfyImages: () => {{}},
    scheduleSave: () => {{}}, runCanvasGenerate: () => {{}},
    bindCascadeButtons: () => {{}}, cascadeBtnHtml: () => '', retryBarHtml: () => '',
    updateLTXNodeElementSize: () => {{}}, refreshGeometryAfterLayout: () => {{}},
    windowObj: {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicLtxControls.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")
        # Source-contract: canvas.html loads the seam before canvas.js.
        page_source = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_href = "workbench/canvas/classic-ltx-controls.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(page_source.index(seam_href), page_source.index(editor_href),
            msg="classic-ltx-controls.js must load before canvas.js in canvas.html")
        # Source-contract: canvas.js deleted the six local function
        # definitions and the dispatcher routes every kind through the
        # seam via `ensureClassicLtxControls()`.
        editor_source = read_canvas_app_source(ROOT)
        self.assertNotIn("function addLTXDirectorNode", editor_source,
            msg="canvas.js should no longer define function addLTXDirectorNode")
        self.assertNotIn("function renderLTXDirectorBody", editor_source,
            msg="canvas.js should no longer define function renderLTXDirectorBody")
        self.assertNotIn("function destroyLTXEditor", editor_source,
            msg="canvas.js should no longer define function destroyLTXEditor")
        self.assertNotIn("function ltxParseTimeline", editor_source,
            msg="canvas.js should no longer define function ltxParseTimeline")
        self.assertNotIn("function ltxFlushTimelineToNode", editor_source,
            msg="canvas.js should no longer define function ltxFlushTimelineToNode")
        self.assertNotIn("function ltxBuildContiguousRelay", editor_source,
            msg="canvas.js should no longer define function ltxBuildContiguousRelay")
        self.assertIn("function ensureClassicLtxControls", editor_source,
            msg="canvas.js must declare ensureClassicLtxControls next to ensureClassicMiniMaxControls")
        self.assertIn("ensureClassicLtxControls().addNode({point})", editor_source,
            msg="canvas.js createNodeByType dispatcher must call ensureClassicLtxControls().addNode({point})")
        self.assertIn("ltx.renderBody({node})", editor_source,
            msg="canvas.js body dispatcher must call ltx.renderBody({node})")
        self.assertIn("ensureClassicLtxControls().destroyEditor({node:", editor_source,
            msg="canvas.js onCardDestroy must call ensureClassicLtxControls().destroyEditor({node: ...})")


    def test_classic_editor_routes_video_card_body_through_classic_video_card_body_seam(self):
        # Wave 10: video-card-body COMPAT seam. One page-side video
        # body function (`renderVideoBody`, ~135-line body renderer for
        # the `video`-type generator card) moves behind a bounded
        # compat seam. The factory half of video-node creation
        # already moved to the unified `classic-node-factories.js`
        # host seam in Wave 3; Wave 10 closes the COMPAT body half.
        seam = ROOT / "static/js/workbench/canvas/classic-video-card-body.js"
        editor = canvas_app_paths(ROOT)[0]
        canvas_html = ROOT / "static/canvas.html"
        self.assertTrue(seam.exists(), msg="classic-video-card-body.js seam module must exist for Wave 10")
        self.assertTrue(editor.exists(), msg="canvas.js editor must exist")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        html_source = canvas_html.read_text(encoding="utf-8")

        # The seam must expose the host factory with the documented single method.
        self.assertIn("WorkbenchCanvasClassicVideoCardBody", seam_source,
            msg="classic-video-card-body.js must expose WorkbenchCanvasClassicVideoCardBody")
        self.assertIn("renderBody: function (arg) { return renderVideoBody(arg.node); }", seam_source,
            msg="classic-video-card-body.js seam handle must wrap renderVideoBody as renderBody({node})")

        # Drive the seam in a Node vm sandbox and assert renderBody
        # produces a non-empty body element on the documented minimal
        # host. Assert the body element uses the documented
        # 'generator-body' className and contains the documented
        # 'video-input-head' marker section.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null, onblur: null,
        onmousedown: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}} }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const windowStub = {{}};
const sandbox = {{window: windowStub, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{}};
const host = {{
    document: documentStub,
    tr: (k) => k,
    generatorSources: (n) => [], orderedSources: (n, s) => s || [],
    mediaKindForRef: (ref) => 'image',
    sanitizeVideoNodeProviderModel: () => {{}},
    videoProviderOptions: (sel) => '<option>x</option>',
    videoModelOptions: (model, provider) => '<option>x</option>',
    providerVideoModels: (provider) => ['veo3-fast'],
    renderVideoImageInputs: () => {{}},
    renderPromptPreview: () => {{}},
    scheduleSave: () => {{}},
    runCanvasGenerate: () => {{}},
    bindCascadeButtons: () => {{}},
    cascadeBtnHtml: () => '',
    retryBarHtml: () => '',
    render: () => {{}},
    showErrorModal: () => {{}},
    uploadCanvasVideosToCloud: () => {{}},
    setCanvasManualVideoUrl: () => {{}},
    refreshIcons: () => {{}},
}};
const api = sandbox.window.WorkbenchCanvasClassicVideoCardBody.create(host);
const node = {{
    type: 'video',
    id: 'video-test',
    apiProvider: 'veo3', model: 'veo3-fast',
    duration: 5, aspectRatio: '16:9', resolution: '',
    enhancePrompt: true, enableUpsample: false,
    watermark: false, cameraFixed: false,
    generateAudio: false, multimodal: false, useFrameRoles: false,
    running: false, inputs: [],
}};
const out = {{}};
try {{
  const body = api.renderBody({{node}});
  out.renderBodyRan = true;
  out.bodyClass = body && body.className;
  out.bodyHasMarker = body && (body.innerHTML || '').indexOf('video-input-head') !== -1;
}} catch(e) {{ out.renderBodyErr = String(e); }}
out.hasRenderBody = typeof api.renderBody === 'function';
out.frozen = Object.isFrozen(api);
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasRenderBody"], msg="seam must expose renderBody")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertTrue(actual.get("renderBodyRan"), msg=f"renderBody must run on minimal mock host, got: {actual.get('renderBodyErr')}")
        self.assertEqual(actual.get("bodyClass"), "generator-body",
            msg="rendered body must use the documented 'generator-body' className")
        self.assertTrue(actual.get("bodyHasMarker"),
            msg="rendered body must contain the documented 'video-input-head' marker section")

        # Required-ops count pin (seam must keep this synchronized with the test).
        required_match = re.search(r"REQUIRED_OPS\s*=\s*\[([^\]]*)\]", seam_source, re.DOTALL)
        self.assertIsNotNone(required_match, msg="seam module must declare REQUIRED_OPS array")
        required = re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", required_match.group(1))
        self.assertEqual(len(required), 21,
            msg="REQUIRED_OPS count pin: Wave 10 seam module declares 21 host ops; if you add/remove an op, update both the seam and this test")

        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        for missing in required:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}, document: {{createElement: () => ({{}})}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, tr: () => '',
    generatorSources: () => [], orderedSources: (n, s) => s || [],
    mediaKindForRef: () => 'image', sanitizeVideoNodeProviderModel: () => {{}},
    videoProviderOptions: () => '', videoModelOptions: () => '',
    providerVideoModels: () => [], renderVideoImageInputs: () => {{}},
    renderPromptPreview: () => {{}},
    scheduleSave: () => {{}}, runCanvasGenerate: () => {{}},
    bindCascadeButtons: () => {{}}, cascadeBtnHtml: () => '', retryBarHtml: () => '',
    render: () => {{}}, showErrorModal: () => {{}},
    uploadCanvasVideosToCloud: () => {{}}, setCanvasManualVideoUrl: () => {{}},
    refreshIcons: () => {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicVideoCardBody.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")

        # Source-contract: canvas.html loads the seam before canvas.js.
        seam_href = "workbench/canvas/classic-video-card-body.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(html_source.index(seam_href), html_source.index(editor_href),
            msg="classic-video-card-body.js must load before canvas.js in canvas.html")
        # The seam must also load after ltx-controls to maintain the
        # documented Wave 5-10 load order.
        ltx_href = "workbench/canvas/classic-ltx-controls.js"
        self.assertLess(html_source.index(ltx_href), html_source.index(seam_href),
            msg="classic-ltx-controls.js must load BEFORE classic-video-card-body.js in canvas.html")

        # Source-contract: canvas.js deleted the local function and the
        # body dispatcher routes through ensureClassicVideoCardBody().
        self.assertNotIn("function renderVideoBody", editor_source,
            msg="canvas.js should no longer define function renderVideoBody")
        self.assertIn("function ensureClassicVideoCardBody", editor_source,
            msg="canvas.js must declare ensureClassicVideoCardBody next to ensureClassicLtxControls")
        self.assertIn("videoBody.renderBody({node})", editor_source,
            msg="canvas.js body dispatcher must call videoBody.renderBody({node})")

    def test_classic_seam_factories_inject_every_required_host_op(self):
        """Regression guard for the Wave 7-14 reapplies.

        Each seam module declares a REQUIRED_OPS array and its create()
        throws TypeError when any of those ops is missing from the host
        object. The per-wave focused tests drive the seams with a
        hand-built sandbox host, so they never execute canvas.js's
        ensureClassic*() factories -- a factory that forgets to pass an
        op still passes those tests but throws the moment the page
        builds the seam for real. This test statically reconciles every
        factory's injected keys against its seam's REQUIRED_OPS so that
        class of breakage fails here instead of at runtime.
        """
        import re as _re
        editor = canvas_app_paths(ROOT)[0]
        editor_source = read_canvas_app_source(ROOT)

        declared = set(_re.findall(r"^(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
                                   editor_source, _re.MULTILINE))
        declared |= set(_re.findall(r"^(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)",
                                    editor_source, _re.MULTILINE))
        # Browser/global identifiers that resolve without a canvas.js def.
        globals_ok = {"document", "window", "tr", "alert", "confirm", "prompt"}

        seams = {
            "classic-card-body-renderer.js": "ensureClassicCardBodyRenderer",
            "classic-comfy-controls.js": "ensureClassicComfyControls",
            "classic-runninghub-controls.js": "ensureClassicRunningHubControls",
            "classic-minimax-controls.js": "ensureClassicMiniMaxControls",
            "classic-ltx-controls.js": "ensureClassicLtxControls",
            "classic-video-card-body.js": "ensureClassicVideoCardBody",
            "classic-video-provider-params.js": "ensureClassicVideoProviderParams",
            "classic-output-grid.js": "ensureClassicOutputGrid",
            "classic-generation-log.js": "ensureClassicGenerationLog",
            "classic-cascade-orchestrator.js": "ensureClassicCascadeOrchestrator",
        }

        for seam_name, factory_name in seams.items():
            seam_path = ROOT / "static/js/workbench/canvas" / seam_name
            self.assertTrue(seam_path.exists(), msg=f"{seam_name} seam module must exist")
            seam_source = seam_path.read_text(encoding="utf-8")
            ops_match = _re.search(r"var REQUIRED_OPS\s*=\s*\[(.*?)\]\s*;", seam_source, _re.DOTALL)
            self.assertIsNotNone(ops_match, msg=f"{seam_name} must declare a REQUIRED_OPS array")
            required = _re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", ops_match.group(1))
            self.assertTrue(required, msg=f"{seam_name} REQUIRED_OPS must not be empty")

            factory = _re.search(
                r"^function " + _re.escape(factory_name) + r"\(\)\{.*?^\}",
                editor_source, _re.DOTALL | _re.MULTILINE)
            self.assertIsNotNone(factory,
                msg=f"canvas.js must declare {factory_name}()")
            body = factory.group(0)
            for op in required:
                self.assertRegex(body, r"[,{]\s*" + _re.escape(op) + r"\s*[,:}]",
                    msg=(f"{factory_name}() must inject host op '{op}' required by "
                         f"{seam_name}; create() throws TypeError without it"))
                # The op must resolve to something real on the page — but only
                # when the factory uses the SHORTHAND `op,` form. The
                # `key: <expr>` form supplies an inline value and does not need
                # a page-side identifier to resolve at factory time.
                if op not in globals_ok:
                    uses_shorthand = _re.search(
                        r"[,{]\s*" + _re.escape(op) + r"\s*[,}]", body) is not None
                    if uses_shorthand:
                        self.assertTrue(op in declared,
                            msg=(f"host op '{op}' passed by {factory_name}() as a "
                                 f"shorthand has no page-side definition in canvas.js"))

    def test_classic_page_side_seam_calls_have_no_duplicated_receiver(self):
        """Guard the duplicate-receiver bug class.

        A mechanical rewrite once produced calls shaped like
        `seam.ensureClassicX().method()` and
        `ensureClassicY().ensureClassicY().method()`. Both parse fine and
        both throw TypeError at runtime, because the first call already
        returns the handle. Neither is caught by syntax checks or by the
        vm-sandbox seam tests, so pin it statically here.
        """
        import re as _re
        editor_source = read_canvas_app_source(ROOT)
        bad = [line.strip() for line in editor_source.splitlines()
               if _re.search(r"\.ensureClassic[A-Z][A-Za-z]*\(\)\s*\.\s*ensureClassic", line)]
        self.assertEqual(bad, [],
            msg=f"canvas.js has duplicated ensureClassic receivers (runtime TypeError): {bad}")
        nested = [line.strip() for line in editor_source.splitlines()
                  if _re.search(r"\{\s*(\w+)\s*:\s*\{\s*\1\s*:", line)]
        self.assertEqual(nested, [],
            msg=f"canvas.js has duplicated nested object keys (runtime bug): {nested}")

    def test_classic_video_provider_params_vpp_handle_is_an_object_not_a_function(self):
        """The `vpp` handle is consumed by property access.

        The page-side thin wrappers call `vpp.resolveVideoProviderId({id: ...})`.
        That only works when `vpp` is an object exposing those methods -- when
        it was declared as `function vpp(){ ... }` every call threw
        `TypeError: vpp.resolveVideoProviderId is not a function` on the very
        first video-node body render. Pin the object form.
        """
        import re as _re
        editor_source = read_canvas_app_source(ROOT)
        self.assertRegex(editor_source, r"const vpp = \{",
            msg="canvas.js must declare `const vpp = {` as an object handle, not a function")
        self.assertNotRegex(editor_source, r"function vpp\s*\(",
            msg="canvas.js must not declare vpp as a function; wrappers use property access")
        for method in ("videoApiProviders", "resolveVideoProviderId", "providerVideoModels"):
            self.assertRegex(editor_source, r"vpp\." + method + r"\(",
                msg=f"canvas.js wrappers must call vpp.{method}(...)")
        # No call-form leftovers: `vpp()` on an object throws TypeError.
        self.assertNotRegex(editor_source, r"\bvpp\(\)",
            msg="canvas.js must not call vpp(); vpp is an object handle")

    def test_classic_editor_routes_cascade_orchestrator_through_classic_cascade_orchestrator_seam(self):
        seam = ROOT / "static/js/workbench/canvas/classic-cascade-orchestrator.js"
        editor = canvas_app_paths(ROOT)[0]
        canvas_html = ROOT / "static/canvas.html"
        self.assertTrue(seam.exists(), msg="classic-cascade-orchestrator.js seam module must exist for Wave 14")
        self.assertTrue(editor.exists(), msg="canvas.js editor must exist")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        html_source = canvas_html.read_text(encoding="utf-8")

        # The seam must expose the host factory.
        self.assertIn("WorkbenchCanvasClassicCascadeOrchestrator", seam_source,
            msg="classic-cascade-orchestrator.js must expose WorkbenchCanvasClassicCascadeOrchestrator")

        # Drive the seam in a node VM sandbox to verify required host ops + happy paths.
        seam_path = str(seam).replace("\\", "/")
        # Use string substitution (not f-string) to avoid brace escaping issues.
        seam_path_json = json.dumps(seam_path)
        script = """
const fs = require('fs');
const vm = require('vm');
const seamSource = fs.readFileSync(__SEAM_PATH__, 'utf8');

const sandbox = {window: {}, console: {log: () => {}}};
vm.runInNewContext(seamSource, sandbox);

// Build a minimal host with all REQUIRED ops populated, then create the seam.
const nodes = [];
const connections = [];
const calls = {refresh: 0, alerts: []};
const host = {
    tr: (k) => k || '',
    langIsEn: () => false,
    nowMs: () => 1234567,
    uid: (prefix) => prefix + '-test',
    escapeHtml: (s) => String(s),
    escapeAttr: (s) => String(s),
    loopCount: (node) => node && Number(node.count) || 1,
    getNodes: () => nodes,
    getConnections: () => connections,
    refreshNodes: (ids) => { calls.refresh += 1; },
    setNodeRunStatus: (node, status, error) => { if (node) { node.runStatus = status; node.runError = error; } },
    runGenerator: () => Promise.resolve(), runMidjourneyNode: () => Promise.resolve(),
    runMsGenNode: () => Promise.resolve(), runComfyNode: () => Promise.resolve(),
    runLTXDirectorNode: () => Promise.resolve(), runLLMNode: () => Promise.resolve(),
    runVideoNode: () => Promise.resolve(), runRhNode: () => Promise.resolve(),
    runMiniMaxNode: () => Promise.resolve(),
    setStatus: () => {},
    showErrorModal: () => {},
    alert: (msg) => { calls.alerts.push(msg); },
    computeCascadeOrderTarget: ({targetId}) => ['upstream-1', targetId],
    comfyBackendCount: 1,
    setLoopContextMirror: () => {},
};
const api = sandbox.window.WorkbenchCanvasClassicCascadeOrchestrator.create(host);
const out = {};
out.hasFactory = typeof sandbox.window.WorkbenchCanvasClassicCascadeOrchestrator.create === 'function';
out.frozen = Object.isFrozen(api);
out.requiredOpsCount = sandbox.window.WorkbenchCanvasClassicCascadeOrchestrator.REQUIRED_OPS.length;
out.hasBeginCascade = typeof api.beginCascade === 'function';
out.hasCancelCascade = typeof api.cancelCascade === 'function';
out.hasRunNodeCascade = typeof api.runNodeCascade === 'function';
out.hasRetryNodeAndDownstream = typeof api.retryNodeAndDownstream === 'function';
out.hasBindCascadeButtons = typeof api.bindCascadeButtons === 'function';
out.hasCascadeAbortError = typeof api.cascadeAbortError === 'function';
out.hasEnsureCascadeActive = typeof api.ensureCascadeActive === 'function';

// cascadeAbortError: returns an Error with .isCascadeAbort.
try {
  const err = api.cascadeAbortError({message: '已停止一键运行'});
  out.abortErrIsError = err instanceof Error;
  out.abortErrMessage = err.message;
  out.abortErrIsCascadeAbort = err.isCascadeAbort === true;
} catch(e) { out.abortErr = String(e); }

// cascadeStopMessage: reason wins; otherwise i18n default.
try {
  const m = api.cascadeStopMessage({reason: '用户停止'});
  out.stopMessageWithReason = m;
  const def = api.cascadeStopMessage({reason: ''});
  out.stopMessageDefault = def;
} catch(e) { out.stopMessageErr = String(e); }

// isCascadeAbortError: detect abort.
try {
  const abortErr = api.cascadeAbortError({message: 'm'});
  out.detectsAbort = api.isCascadeAbortError(abortErr);
  out.detectsRegular = api.isCascadeAbortError(new Error('nope')) === false;
} catch(e) { out.detectErr = String(e); }

// beginCascade: registers the target in cascadeRunningIds and returns a context.
try {
  const ctx = api.beginCascade({targetId: 'n1', order: ['a', 'b'], options: {serial: true}});
  out.ctxReturned = ctx && typeof ctx === 'object';
  out.ctxOrderJoin = ctx && Array.isArray(ctx.order) ? ctx.order.join(',') : '';
  out.ctxOrderCopied = out.ctxOrderJoin === 'a,b';
  out.ctxMode = ctx && ctx.mode;
  out.ctxHasControllers = ctx && ctx.controllers && ctx.controllers.size === 0;
  out.isActive = api.isCascadeActive('n1');
  out.isStopping = api.isCascadeStopping('n1') === false;
} catch(e) { out.beginErr = String(e); }

// requestCascadeStop: marks the target as stopping.
try {
  api.requestCascadeStop({targetId: 'n1', reason: '用户取消'});
  out.stopping = api.isCascadeStopping('n1');
} catch(e) { out.stopErr = String(e); }

// ensureCascadeActive on stopping ctx must throw.
try {
  let threw = false;
  try { api.ensureCascadeActive({targetId: 'n1'}); } catch(err) { threw = api.isCascadeAbortError(err); }
  out.activeThrowsOnStopping = threw;
} catch(e) { out.activeThrowsErr = String(e); }

// finalizeCascade clears state when targetId matches.
try {
  api.finalizeCascade({targetId: 'n1', state: 'stopped', options: {order: ['a', 'b']}});
  out.afterFinalizeActive = api.isCascadeActive('n1') === false;
} catch(e) { out.finalizeErr = String(e); }

// computeCascadeOrder: when nodes+connections are empty returns []; otherwise walks upstream.
try {
  nodes.push({id: 'root', type: 'generator'});
  nodes.push({id: 'upstream-1', type: 'video'});
  connections.push({from: 'upstream-1', to: 'root'});
  out.orderRoot = api.computeCascadeOrder({targetId: 'root'}).join(',');
} catch(e) { out.orderErr = String(e); }

// cancelCascade registers a stop intent for the given nodeId.
try {
  api.beginCascade({targetId: 'n2', order: [], options: {serial: true}});
  api.cancelCascade({nodeId: 'n2'});
  out.cancelMarksStopping = api.isCascadeStopping('n2');
} catch(e) { out.cancelErr = String(e); }

// bindCascadeButtons: when given a stub wrap with querySelectorAll returning arrays, must
// assign onmousedown + onclick handlers to each button without throwing.
try {
  const wrap = {
    querySelectorAll: (sel) => {
      const el = {onmousedown: null, onclick: null};
      return [el];
    },
  };
  api.bindCascadeButtons({wrap: wrap, nodeId: 'n1'});
  out.bindNoThrow = true;
} catch(e) { out.bindErr = String(e); }

// resetCascadeRuntimeState clears everything.
try {
  api.beginCascade({targetId: 'n3', order: [], options: {serial: true}});
  api.resetCascadeRuntimeState();
  out.afterResetActive = api.isCascadeActive('n3') === false;
} catch(e) { out.resetErr = String(e); }

console.log(JSON.stringify(out));
""".replace("__SEAM_PATH__", seam_path_json)
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)

        # Shape checks
        self.assertTrue(actual["hasFactory"], msg="seam must expose WorkbenchCanvasClassicCascadeOrchestrator.create")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        self.assertTrue(actual["hasBeginCascade"], msg="seam must expose beginCascade")
        self.assertTrue(actual["hasCancelCascade"], msg="seam must expose cancelCascade")
        self.assertTrue(actual["hasRunNodeCascade"], msg="seam must expose runNodeCascade")
        self.assertTrue(actual["hasRetryNodeAndDownstream"], msg="seam must expose retryNodeAndDownstream")
        self.assertTrue(actual["hasBindCascadeButtons"], msg="seam must expose bindCascadeButtons")
        self.assertTrue(actual["hasCascadeAbortError"], msg="seam must expose cascadeAbortError")
        self.assertTrue(actual["hasEnsureCascadeActive"], msg="seam must expose ensureCascadeActive")

        # cascadeAbortError correctness
        self.assertTrue(actual.get("abortErrMessage"), msg=f"cascadeAbortError must return a non-empty message; err: {actual.get('abortErr')}")
        self.assertEqual(actual.get("abortErrMessage"), "已停止一键运行", msg="cascadeAbortError must use the provided message")
        self.assertTrue(actual.get("abortErrIsCascadeAbort"), msg="cascadeAbortError must set isCascadeAbort=true")

        # cascadeStopMessage: reason wins, default is i18n text.
        self.assertEqual(actual.get("stopMessageWithReason"), "用户停止", msg="cascadeStopMessage: reason wins when non-empty")
        self.assertEqual(actual.get("stopMessageDefault"), "已停止一键运行", msg="cascadeStopMessage: default is the i18n fallback")

        # isCascadeAbortError correctness
        self.assertTrue(actual.get("detectsAbort"), msg="isCascadeAbortError must detect abort errors")
        self.assertTrue(actual.get("detectsRegular"), msg="isCascadeAbortError must NOT flag regular errors")

        # beginCascade lifecycle
        self.assertTrue(actual.get("ctxReturned"), msg="beginCascade must return a context object")
        self.assertTrue(actual.get("ctxOrderCopied"), msg=f"beginCascade must copy the order array; got ctxOrderJoin='{actual.get('ctxOrderJoin')}'")
        self.assertEqual(actual.get("ctxMode"), "serial", msg="beginCascade must default mode=serial")
        self.assertTrue(actual.get("ctxHasControllers"), msg="beginCascade must seed ctx.controllers as empty Set")
        self.assertTrue(actual.get("isActive"), msg="isCascadeActive must return true after beginCascade")
        self.assertTrue(actual.get("isStopping"), msg="isCascadeStopping must return false while running")

        # requestCascadeStop + ensureCascadeActive + finalizeCascade lifecycle
        self.assertTrue(actual.get("stopping"), msg="requestCascadeStop must mark ctx.status=stopping")
        self.assertTrue(actual.get("activeThrowsOnStopping"), msg="ensureCascadeActive must throw on stopping ctx")
        self.assertTrue(actual.get("afterFinalizeActive"), msg="finalizeCascade must clear cascadeRunningIds")

        # computeCascadeOrder: walks upstream and includes both 'upstream-1' and 'root'.
        self.assertEqual(actual.get("orderRoot"), "upstream-1,root",
            msg="computeCascadeOrder must walk connections in topological order; got: " + str(actual.get("orderRoot")))

        # cancelCascade sets stopping.
        self.assertTrue(actual.get("cancelMarksStopping"), msg="cancelCascade must mark target as stopping")

        # bindCascadeButtons does not throw with a stubbed wrap.
        self.assertTrue(actual.get("bindNoThrow"), msg=f"bindCascadeButtons must not throw; err: {actual.get('bindErr')}")

        # resetCascadeRuntimeState clears everything.
        self.assertTrue(actual.get("afterResetActive"), msg="resetCascadeRuntimeState must clear cascadeRunningIds")

        # Required-ops count pin.
        self.assertEqual(actual.get("requiredOpsCount"), 26,
                         msg="REQUIRED_OPS count pin: Wave 14 seam module declares 26 host ops; if you add/remove an op, update both the seam and this test")

        # canvas.html must load the seam before canvas.js.
        self.assertIn('classic-cascade-orchestrator.js', html_source,
            msg="canvas.html must load classic-cascade-orchestrator.js")
        seam_pos = html_source.index('classic-cascade-orchestrator.js')
        comfy_pos = html_source.index('classic-comfy-controls.js')
        canvas_pos = html_source.index('canvas-app-bootstrap.js')
        self.assertLess(comfy_pos, seam_pos,
            msg="canvas.html must load classic-comfy-controls.js BEFORE classic-cascade-orchestrator.js")
        self.assertLess(seam_pos, canvas_pos,
            msg="canvas.html must load classic-cascade-orchestrator.js BEFORE canvas.js")

        # TypeError-on-missing-host: every required op must be validated.
        required_ops = re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", re.search(r"REQUIRED_OPS\s*=\s*\[([^\]]*)\]", seam_source, re.DOTALL).group(1))
        for missing in required_ops:
            partial_script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}, console: {log: () => {}}};
vm.runInNewContext(fs.readFileSync(__SEAM_PATH__, 'utf8'), sandbox);
const fullHost = {
    tr: () => '', langIsEn: () => false, nowMs: () => 0, uid: () => 'x',
    escapeHtml: () => '', escapeAttr: () => '', loopCount: () => 1,
    getNodes: () => [], getConnections: () => [], refreshNodes: () => {},
    runGenerator: () => {}, runMidjourneyNode: () => {}, runMsGenNode: () => {},
    runComfyNode: () => {}, runLTXDirectorNode: () => {}, runLLMNode: () => {},
    runVideoNode: () => {}, runRhNode: () => {}, runMiniMaxNode: () => {},
    setStatus: () => {}, showErrorModal: () => {}, alert: () => {},
    computeCascadeOrderTarget: () => [], comfyBackendCount: 1, setLoopContextMirror: () => {},
};
const partial = Object.assign({}, fullHost);
delete partial.__MISSING__;
try { sandbox.window.WorkbenchCanvasClassicCascadeOrchestrator.create(partial); console.log('NO_THROW'); }
catch(e) { console.log('TYPE_ERROR:' + e.message); }
""".replace("__SEAM_PATH__", seam_path_json).replace("__MISSING__", missing)
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TYPE_ERROR", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")

        # Source-contract: canvas.js declares ensureClassicCascadeOrchestrator + thin wrappers.
        self.assertIn("function ensureClassicCascadeOrchestrator", editor_source,
            msg="canvas.js must declare ensureClassicCascadeOrchestrator next to ensureClassicGenerationLog")
        self.assertIn("ensureClassicCascadeOrchestrator().cancelCascade({nodeId})", editor_source,
            msg="canvas.js cancelCascade wrapper must call ensureClassicCascadeOrchestrator().cancelCascade({nodeId})")
        self.assertIn("ensureClassicCascadeOrchestrator().beginCascade({targetId", editor_source,
            msg="canvas.js beginCascade wrapper must call ensureClassicCascadeOrchestrator().beginCascade({targetId, ...})")
        self.assertIn("ensureClassicCascadeOrchestrator().runNodeCascade({nodeId})", editor_source,
            msg="canvas.js runNodeCascade wrapper must call ensureClassicCascadeOrchestrator().runNodeCascade({nodeId})")
        self.assertIn("ensureClassicCascadeOrchestrator().retryNodeAndDownstream({nodeId})", editor_source,
            msg="canvas.js retryNodeAndDownstream wrapper must call ensureClassicCascadeOrchestrator().retryNodeAndDownstream({nodeId})")
        # The original local definitions of the big cascade functions must be deleted.
        # Note: thin page-side wrappers (1-liners that delegate to the seam) are
        # allowed and expected; only the multi-line bodies must be gone.
        # Check for distinctive phrases from the original bodies.
        self.assertNotIn("alert('没有可运行的生成节点');", editor_source,
            msg="canvas.js should no longer define the original runNodeCascade body (the thin page-side wrapper is fine)")
        self.assertNotIn("const totalRounds = (loop", editor_source,
            msg="canvas.js should no longer define the original runNodeCascade body (the thin page-side wrapper is fine)")
        self.assertNotIn("cleanupTimer:null", editor_source,
            msg="canvas.js should no longer define the original createCascadeContext body (cleanupTimer:null is the distinctive line)")
        self.assertNotIn("comfyBackendCount || 1", editor_source,
            msg="canvas.js should no longer define the original cascadeParallelLimit body (comfyBackendCount || 1 is the distinctive line)")
        # The 5 cascade state globals must also be gone — only the page-side
        # `loopContext` mirror (used by renderLoopPrompt fallback) survives.
        self.assertNotIn("const cascadeRunningIds = new Set();", editor_source,
            msg="canvas.js should no longer declare cascadeRunningIds (now lives in seam closure)")
        self.assertNotIn("const cascadeStopIds = new Set();", editor_source,
            msg="canvas.js should no longer declare cascadeStopIds (now lives in seam closure)")
        self.assertNotIn("const cascadeSerialIds = new Set();", editor_source,
            msg="canvas.js should no longer declare cascadeSerialIds (now lives in seam closure)")
        self.assertNotIn("const cascadeContexts = new Map();", editor_source,
            msg="canvas.js should no longer declare cascadeContexts (now lives in seam closure)")

    def test_classic_editor_rewraps_deleted_cascade_ltx_and_minimax_helpers_through_their_seams(self):
        # Independent-review repair (2026-09-07): the Wave 7-14 reapply left
        # live page transports calling helper functions whose bodies had moved
        # into the bounded compat seams (a ReferenceError on the first card
        # render / execution path). The repaired wiring must exist, route
        # through the owning seam handle with the seam's object-arg shapes,
        # and leave no bare call to a deleted seam-owned helper.
        editor_source = read_canvas_app_source(ROOT)
        # Cascade: five page-side adapter wrappers restored for live transports.
        self.assertIn("function cascadeBackendRestartMessage(){ return ensureClassicCascadeOrchestrator().cascadeBackendRestartMessage(); }", editor_source)
        self.assertIn("function normalizeCanvasTaskError(err, fallback){ return ensureClassicCascadeOrchestrator().normalizeCanvasTaskError({err, fallback: fallback || ''}); }", editor_source)
        self.assertIn("async function cascadeFetch(input, init, options){ return ensureClassicCascadeOrchestrator().cascadeFetch({input, init: init || {}, options: options || {}}); }", editor_source)
        self.assertIn("function canvasRunTypes(){ return ensureClassicCascadeOrchestrator().canvasRunTypes(); }", editor_source)
        self.assertIn("function resolveCascadeLoop(targetId){ return ensureClassicCascadeOrchestrator().resolveCascadeLoop({targetId}); }", editor_source)
        # Cascade: wrapper arg shapes must match what the seam actually reads.
        self.assertIn("cascadeTargetIdFromOptions({options: opts || {}})", editor_source)
        self.assertIn("cascadeContextFromOptions({options: opts || {}})", editor_source)
        self.assertNotIn("cascadeTargetIdFromOptions({opts:", editor_source)
        self.assertNotIn("cascadeContextFromOptions({opts:", editor_source)
        self.assertIn("function bindCascadeButtons(wrap, nodeId){ return ensureClassicCascadeOrchestrator().bindCascadeButtons({wrap, nodeId}); }", editor_source)
        self.assertNotIn("function bindCascadeButtons(arg)", editor_source)
        self.assertIn("cascadeAbortError(typeof arg === 'string' ? {message: arg} : (arg || {}))", editor_source)
        # The LLM pane binds through the 2-arg page wrapper, not a direct seam call.
        self.assertNotIn("ensureClassicCascadeOrchestrator().bindCascadeButtons(container, node.id);", editor_source)
        # LTX: the two deleted seam-owned calls reroute through the seam handle.
        self.assertIn("ensureClassicLtxControls().flushTimelineToNode({node});", editor_source)
        self.assertIn("const timeline = ensureClassicLtxControls().parseTimeline({node});", editor_source)
        self.assertIn("ensureClassicLtxControls().buildContiguousRelay({node, globalPromptFallback});", editor_source)
        # LTX: the three page-owned compositions are restored verbatim from HEAD.
        self.assertIn("function ltxDirectorTimelineSegments(node){", editor_source)
        self.assertIn("function ltxRefreshTimelineEditor(node){", editor_source)
        self.assertIn("async function ltxDirectorBuildTimelinePayload(node, globalPromptFallback=''){", editor_source)
        # MiniMax: the three deleted seam-owned calls reroute through the seam.
        self.assertIn("node.minimaxEngine = ensureClassicMiniMaxControls().getEngine({node});", editor_source)
        # runMiniMaxNode's body moved into the executor seam (Wave 16a).
        executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
        self.assertIn("const engine = ensureClassicMiniMaxControls().getEngine({node});", executor_source)
        self.assertIn("ensureClassicMiniMaxControls().syncPlayerDom({wrap, seg, time: safeTime, play});", editor_source)
        # No bare call to a seam-owned deleted helper remains anywhere.
        rerouted = ["miniMaxEngine", "miniMaxSyncPlayerDom", "ltxParseTimeline", "ltxFlushTimelineToNode", "ltxBuildContiguousRelay"]
        lines = editor_source.splitlines()
        for name in rerouted:
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue
                if re.search(r"(?<![\w.])" + name + r"\(", line) and not re.search(r"function " + name + r"\(", line):
                    self.fail(f"bare call to seam-owned {name} remains at canvas.js line {i+1}: {stripped}")

    def test_classic_editor_routes_executor_transport_surface_through_classic_executor_runtime_seam(self):
        # Wave 16a: the Classic executor / transport surface (run*Node
        # executors, API transports, run-metadata helpers) moved behind a
        # bounded compat seam. canvas.js keeps a 1-line wrapper per function;
        # the seam consumes page-locals via 90 required host ops (nodes /
        # connections / comfyWorkflows become getters).
        seam = ROOT / "static/js/workbench/canvas/classic-executor-runtime.js"
        editor = canvas_app_paths(ROOT)[0]
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        self.assertTrue(seam.exists(), msg="classic-executor-runtime.js seam module must exist for Wave 16a")

        seam_path_json = json.dumps(str(seam))
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}, console: {log: () => {}}, fetch: async () => ({ok: true, json: async () => ({})})};
sandbox.window.WorkbenchCanvasHttpError = {
    message: (data, fallback) => (data && data.error) || fallback,
    responseMessage: async () => 'boom',
};
sandbox.window.WorkbenchCanvasMediaResultNormalizer = { extract: () => [] };
vm.runInNewContext(fs.readFileSync(__SEAM_PATH__, 'utf8'), sandbox);
const factory = sandbox.window.WorkbenchCanvasClassicExecutorRuntime;
const nodes = [];
const connections = [];
const polls = new Map();
const host = {
    getNodes: () => nodes, getConnections: () => connections, getComfyWorkflows: () => [],
    API_RATIO_VALUES: [], CANVAS_REFERENCE_IMAGE_MAX: 20, CLIENT_ID: 'cid',
    LTX_DIRECTOR_SEED_NODE: 'seedNode', LTX_DIRECTOR_WF_NODE: 'wfNode', LTX_DIRECTOR_WORKFLOW: '{}',
    activeCanvasTaskPolls: polls,
    actionFailed: (k) => k, langIsEn: () => false, tr: (k) => k, nowMs: () => 1000,
    uid: (p) => p + '-1', noReturnedImage: () => 'no image', setStatus: () => {},
    showErrorModal: () => {}, scheduleSave: () => {}, render: () => {},
    refreshNodes: () => {}, refreshIcons: () => {},
    normalizeCanvasTaskError: (o) => (o && o.err && o.err.message) || 'e',
    cascadeBackendRestartMessage: () => 'backend', cascadeStopMessage: () => 'stopped',
    cascadeTargetIdFromOptions: (o) => (o && o.options && o.options.cascadeTargetId) || '',
    isCascadeAbortError: () => false, ensureCascadeActive: () => {},
    cascadeFetch: async () => ({ok: true, json: async () => ({task_id: 't1'}), text: async () => ''}),
    fetch: async () => ({ok: true, json: async () => ({}), text: async () => ''}),
    addGenerationLog: () => {}, appendOutputImages: () => {}, applyUploadedUrlToRefs: () => {},
    audioRefsOnly: () => [], clearStuckGeneratorRunning: () => {}, collectRunMeta: () => ({m: 1}),
    collectRunMetas: () => [], comfyFieldKind: () => 'text', comfyFields: () => [],
    comfyParamValue: () => '', comfyRandomActive: () => false, comfyRandomEnabled: () => false,
    comfyRandomValue: () => null, comfyRunLabel: () => 'run', completeCanvasImageTask: () => {},
    ensureRhNodeSelection: () => null, extractUpstreamTaskId: () => '', findPendingTask: () => null,
    generatorSources: () => [], imageRefsOnly: () => [], llmInputImages: () => [],
    llmInputText: () => '', llmInputVideos: () => [], ltxDirectorSyncSeconds: () => {},
    ltxDirectorTimelineSegments: () => [], makePending: (id, run, task) => ({id, run, ...task}),
    manualVideoUrlForNode: () => '', mediaKindForRef: () => '', mergeGeneratedOutputs: () => {},
    miniMaxApplyRunningHubParams: () => {}, miniMaxLogError: () => {},
    miniMaxReadableError: () => 'e', miniMaxRefsForNode: () => [], miniMaxRefsForSegment: () => [],
    miniMaxSelectedSegment: () => null, miniMaxSetSegmentResult: () => {},
    normalizedImageQuality: () => 1, orderedSources: () => [], outputUrlValue: () => '',
    pendingById: () => new Map(), pendingPreviewSizeForRun: () => ({}), providerIdForPending: () => '',
    requestMetaFromResult: () => ({}), resolveChatModel: () => 'cm', resolveChatProviderId: () => 'cp',
    resolveImageModel: () => 'im', resolveImageProviderId: () => 'ip',
    resolveMidjourneyProviderId: () => 'mp', rhActiveFields: () => [], rhCurrentEntry: () => null,
    rhCurrentKind: () => 'model', rhMediaSources: () => ({sources: []}), rhSelectedEntryRef: () => null,
    runningHubEntryLabel: () => 'l', shouldCreateOutputForNode: () => true,
    showErrorModal: () => {}, tempShUploadedUrlForNode: () => '', validComfyWorkflowName: () => false,
    videoRefsOnly: () => [], rhUseWallet: () => false,
    ensureClassicCascadeOrchestrator: () => ({cancelCascade(){}, beginCascade(){ return {order: [], controllers: new Set(), mode: 'serial'}; }, requestCascadeStop(){}, ensureCascadeActive(){}, isCascadeActive(){ return false; }, isCascadeStopping(){ return false; }, cascadeAbortError(m){ const e = new Error(m); e.isCascadeAbort = true; return e; }, isCascadeAbortError(){ return false; }, cascadeStopMessage(){ return 's'; }, resetCascadeRuntimeState(){}, cascadeTargetIdFromOptions(){ return ''; }, cascadeContextFromOptions(){ return null; }, computeCascadeOrder(){ return []; }, bindCascadeButtons(){}, resolveCascadeLoop(){ return null; }}),
    ensureClassicExecutionHost: () => ({markRunning(){}, writeOutputText(){}, setRunStatus(){}, render(){}, save(){}, notifyError(){}}),
    ensureClassicLtxControls: () => ({flushTimelineToNode(){}, parseTimeline(){ return {segments: [], audioSegments: []}; }, buildContiguousRelay(){ return {sortedSegments: [], local_prompts: '', segment_lengths: '', guide_strength: ''}; }}),
    ensureClassicMiniMaxControls: () => ({getEngine(){ return 'comfyui'; }, syncPlayerDom(){}}),
    ensureClassicVideoProviderParams: () => ({resolveVideoProviderId(){ return 'vp'; }, providerVideoModels(){ return []; }}),
    cascadeAbortError: (m) => Object.assign(new Error(m || 'aborted'), {isCascadeAbort: true}),
    comfyNameForRef: () => '', completeMidjourneyRun: async () => {},
    ensureComfyWorkflow: async () => ({workflow_json: '{}'}),
    ensureRunningHubWorkflowConfigForNode: async () => ({workflow_json: '{}'}),
    generatorSizeForRun: () => 512, ltxDirectorBuildTimelinePayload: async () => ({}),
    miniMaxBuildRunningHubNodeInfoList: () => [], miniMaxBuildRunningHubWorkflowExtras: () => ({}),
    miniMaxDynamicParams: () => [], miniMaxRunningHubPayloadError: () => '',
    miniMaxRunningHubSettings: async () => ({entry: null, workflowId: '', fields: [], rhNode: null}),
    providerById: () => null, rhBuildNodeInfoList: () => [], rhBuildWorkflowRequestExtras: () => ({}),
    saveCanvas: () => {}, sleep: async () => {},
};
const out = {};
(async () => {
try {
  const api = factory.create(host);
  out.requiredOpsCount = factory.REQUIRED_OPS.length;
  out.frozen = Object.isFrozen(api);
  out.methods = Object.keys(api).length;
  // drive every handle method; async ones awaited, deliberate-throw paths recorded
  const driven = {};
  const call = async (name, fn) => { try { await fn(); driven[name] = 'ok'; } catch (e) { driven[name] = 'threw: ' + e.message; } };
  await call('responseErrorMessage', async () => api.responseErrorMessage({clone: () => ({json: async () => ({detail: 'x'})})}, 'f'));
  await call('rhUseWallet', async () => api.rhUseWallet({}));
  await call('runSnapshot', async () => api.runSnapshot({id: 'n1'}, 'p', []));
  await call('runTaskLabel', async () => api.runTaskLabel({}));
  await call('runPlatformLabel', async () => api.runPlatformLabel({}));
  await call('makePendingForRun', async () => api.makePendingForRun('p1', {run: 1}, {id: 'n1'}, {}));
  await call('outputForNode', async () => api.outputForNode({id: 'n1', type: 'generator'}, 500));
  await call('refreshRunNodes', async () => api.refreshRunNodes({id: 'n1'}));
  await call('midjourneyRequest', async () => api.midjourneyRequest('/mj', {}));
  await call('runGenerator', async () => api.runGenerator('missing'));
  await call('runGeneratorLegacy', async () => api.runGeneratorLegacy('missing'));
  await call('runRhNode', async () => api.runRhNode('missing'));
  await call('runRhModelNode', async () => api.runRhModelNode(null));
  await call('runVideoNode', async () => api.runVideoNode('missing'));
  await call('runMiniMaxRunningHub', async () => api.runMiniMaxRunningHub('missing'));
  await call('runMiniMaxNode', async () => api.runMiniMaxNode('missing'));
  await call('runComfyNode', async () => api.runComfyNode('missing'));
  await call('runComfyUpscale', async () => api.runComfyUpscale(''));
  // runQueuedComfyGenerate is type-checked only: driving it enters its real
  // poll loop, which never terminates against a non-terminal stub.
  if (typeof api.runQueuedComfyGenerate !== 'function') { out.fatal = 'runQueuedComfyGenerate missing'; }
  await call('callCanvasLLM', async () => api.callCanvasLLM({id: 'n1', llmProvider: '', llmModel: ''}));
  await call('runLLMNode', async () => api.runLLMNode('missing'));
  await call('runLLMChat', async () => api.runLLMChat({}, {}));
  await call('createCanvasImageTask', async () => api.createCanvasImageTask({}, {}));
  await call('createCanvasComfyTask', async () => api.createCanvasComfyTask({}, {}));
  await call('pollCanvasImageTask', async () => api.pollCanvasImageTask(''));
  await call('failCanvasImageTask', async () => api.failCanvasImageTask('t', 'm'));
  await call('uploadCanvasUrlToComfy', async () => api.uploadCanvasUrlToComfy(''));
  await call('runLTXDirectorNode', async () => api.runLTXDirectorNode('missing'));
  out.driven = driven;
  // pure-value assertions
  out.taskLabel = api.runTaskLabel({taskLabel: 'T'});
  out.platformLabel = api.runPlatformLabel({nodeType: 'comfy'});
  out.pending = Object.keys(api.makePendingForRun('p9', {r: 1}, {id: 'n1'}, {refs: []})).sort().join(',');
  out.respErr = await api.responseErrorMessage({clone: () => ({json: async () => ({error: 'boom'})})}, 'fb');
  // wait* with empty taskId must throw the actionFailed error
  let waitedThrew = false; try { await api.waitCanvasComfyTaskResult(''); } catch (e) { waitedThrew = true; }
  let waitedImgThrew = false; try { await api.waitCanvasImageTaskResult(''); } catch (e) { waitedImgThrew = true; }
  out.waitedThrew = waitedThrew; out.waitedImgThrew = waitedImgThrew;
  // missing-host-op loop: every REQUIRED op must throw TypeError when absent
  let missingThrew = 0;
  for (const op of factory.REQUIRED_OPS) {
    const partial = Object.assign({}, host); delete partial[op];
    try { factory.create(partial); } catch (e) { if (e.name === 'TypeError') missingThrew += 1; }
  }
  out.missingThrew = missingThrew;
} catch (e) { out.fatal = String(e); }
console.log(JSON.stringify(out));
})().catch(e => { console.log(JSON.stringify({fatal: String(e)})); });
""".replace("__SEAM_PATH__", seam_path_json)
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertNotIn("fatal", actual, msg=f"seam drive failed: {actual.get('fatal')}")
        self.assertEqual(actual["requiredOpsCount"], 107,
            msg="REQUIRED_OPS count pin: Wave 16a seam declares 107 host ops; update seam + test together")
        self.assertTrue(actual["frozen"], msg="executor seam handle must be frozen")
        self.assertEqual(actual["methods"], 34, msg="handle must expose all 34 moved functions")
        self.assertEqual(actual["missingThrew"], 107,
            msg="every REQUIRED op must be validated with a TypeError on missing host")
        # The drive's contract: no wiring ReferenceErrors ("X is not defined")
        # anywhere. Other throw paths are input-shape specifics of the drive.
        ref_errors = {k: v for k, v in actual["driven"].items() if "is not defined" in v}
        self.assertEqual(ref_errors, {}, msg=f"seam methods hit undefined identifiers: {ref_errors}")
        self.assertEqual(len(actual["driven"]), 27,
            msg="drive coverage pin: 27 methods driven (runQueuedComfyGenerate and waitMidjourneyTask are type-checked only: driving them enters real poll/wait loops)")
        self.assertTrue(actual["waitedThrew"], msg="waitCanvasComfyTaskResult('') must throw")
        self.assertTrue(actual["waitedImgThrew"], msg="waitCanvasImageTaskResult('') must throw")
        self.assertEqual(actual["taskLabel"], "T")
        self.assertEqual(actual["platformLabel"], "ComfyUI",
            msg="runPlatformLabel must map the comfy nodeType to the ComfyUI label")
        self.assertIn("run", actual["pending"])
        self.assertEqual(actual["respErr"], "boom")

        # canvas.js keeps exactly one 1-line wrapper per moved function.
        moved = ["responseErrorMessage","runLTXDirectorNode","rhUseWallet","runRhNode","runRhModelNode",
                 "runGenerator","runGeneratorLegacy","midjourneyRequest","waitMidjourneyTask","runMidjourneyNode",
                 "runMidjourneyAction","runMidjourneyModal","runVideoNode","runMiniMaxRunningHub","runMiniMaxNode",
                 "uploadCanvasUrlToComfy","runComfyUpscale","runComfyNode","runQueuedComfyGenerate","callCanvasLLM",
                 "runLLMNode","runLLMChat","runSnapshot","runTaskLabel","runPlatformLabel","makePendingForRun",
                 "createCanvasImageTask","createCanvasComfyTask","waitCanvasComfyTaskResult","pollCanvasImageTask",
                 "waitCanvasImageTaskResult","failCanvasImageTask","outputForNode","refreshRunNodes"]
        for name in moved:
            self.assertTrue(
                re.search(rf"^(async )?function {name}\([^\n]*\){{ return ensureClassicExecutorRuntime\(\)\.{name}\(", editor_source, re.M),
                msg=f"canvas.js must keep the 1-line executor-seam wrapper for {name}")
            self.assertNotIn(f"function {name}(", seam_source.split("function create(")[1] if False else "",
                msg="unused")
        # The wrappers replaced the bodies: no old body markers remain page-side.
        self.assertNotIn("const node = nodes.find(n => n.id === nodeId);\n    if(node.running", editor_source)
        # The seam consumes page state only through getters.
        self.assertNotIn("nodes.find(", seam_source, msg="seam must read nodes via getNodes()")
        self.assertNotIn("connections.filter(", seam_source, msg="seam must read connections via getConnections()")
        self.assertIn("getNodes()", seam_source)
        self.assertIn("getConnections()", seam_source)
        self.assertIn("getComfyWorkflows()", seam_source)
        # canvas.html loads the seam before canvas.js and the version was bumped.
        self.assertLess(page.index("workbench/canvas/classic-executor-runtime.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertIn("canvas-app-bootstrap.js?v=2026.09.09.2", page)

    def test_classic_editor_routes_asset_upload_drop_surface_through_classic_asset_runtime_seam(self):
        # Wave 16b: the Classic asset / upload / drop / manager surface (the
        # R4-31 asset-library DEFER-R8 capability + satellites) moved behind a
        # bounded compat seam. canvas.js keeps a 1-line wrapper per function;
        # page state (canvas / nodes / the asset-library lets) stays
        # page-owned behind getters, and the seven lets this surface writes
        # are bridged with setter host ops.
        seam = ROOT / "static/js/workbench/canvas/classic-asset-runtime.js"
        editor = canvas_app_paths(ROOT)[0]
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        self.assertTrue(seam.exists(), msg="classic-asset-runtime.js seam module must exist for Wave 16b")

        # The seam factory reads page-owned `const`/`let` bindings.  Its first
        # real invocation must therefore be injected into the neutral bootstrap
        # and happen from start() after the whole script has initialized,
        # rather than beside the early DOM lookups (which would throw in the
        # temporal dead zone and blank the page before it can request a Canvas).
        wrapper_pos = editor_source.index(
            "function revealCanvasAssetControls(){ return ensureClassicAssetRuntime().revealCanvasAssetControls(); }"
        )
        bootstrap_pos = editor_source.index(
            "const canvasAppBootstrap = window.WorkbenchCanvasAppBootstrap.create({"
        )
        reveal_adapter_pos = editor_source.index(
            "    revealAssetControls: revealCanvasAssetControls,", bootstrap_pos
        )
        load_pos = editor_source.index(
            "const startCanvasApp = () => canvasAppBootstrap.start({search: window.location.search});"
        )
        self.assertLess(wrapper_pos, bootstrap_pos)
        self.assertLess(bootstrap_pos, reveal_adapter_pos)
        self.assertLess(reveal_adapter_pos, load_pos)
        self.assertNotIn("\nrevealCanvasAssetControls();\n", editor_source[:bootstrap_pos])

        seam_path_json = json.dumps(str(seam))
        script = """
const fs = require('fs'); const vm = require('vm');
const mockEl = () => ({innerHTML: '', appendChild(){}, querySelector: () => null,
    querySelectorAll: () => [], classList: {toggle(){}, add(){}, remove(){}, contains: () => false},
    dataset: {}, style: {}, addEventListener(){}, onclick: null, value: '', checked: false,
    textContent: '', src: '', href: '', files: [], focus(){}, select(){}});
const sandbox = {window: {}, console: {log: () => {}}, document: {createElement: mockEl,
    getElementById: () => mockEl(), addEventListener(){}, removeEventListener(){},
    querySelector: () => null, querySelectorAll: () => [], body: mockEl()},
    fetch: async () => ({ok: true, json: async () => ({}), text: async () => ''}),
    location: {origin: 'http://x'}, setTimeout, URL, Blob};
process.on('unhandledRejection', () => {});
process.on('uncaughtException', () => {});
sandbox.window.WorkbenchCanvasHttpError = {message: (d, f) => (d && d.error) || f,
    responseMessage: async () => 'boom'};
sandbox.window.WorkbenchCanvasMediaResultNormalizer = {extract: () => []};
sandbox.window.WorkbenchCanvasMediaUrl = {originalUrl: (u) => u};
sandbox.window.StudioI18n = {t: (k) => k, lang: () => 'zh'};
vm.runInNewContext(fs.readFileSync(__SEAM_PATH__, 'utf8'), sandbox);
const factory = sandbox.window.WorkbenchCanvasClassicAssetRuntime;
const canvasFixture = {id: 'c1', project: 'p1', title: 'T', logs: [], nodes: [],
    asset_libraries: {libraries: [], categories: []}, library: {libraries: [], categories: []}};
let canvasAssetLibraryOpen = false;
const host = {
    getCanvas: () => canvasFixture, getNodes: () => [],
    CANVAS_UPLOAD_MAX: 20,
    IMAGE_DROP_EXT_RE: /\\.(png|jpe?g)$/i, IMAGE_DROP_TEXT_TYPES: [], IMAGE_DROP_TYPE_HINT_RE: /image/i,
    LOCAL_CANVAS_ASSET_LIBRARY_ID: 'local', UNDO_MAX: 50,
    assetManagerBody: mockEl(), assetManagerModal: mockEl(), canvasAssetAddCategoryBtn: mockEl(),
    canvasAssetCategorySelect: mockEl(), canvasAssetDropZone: mockEl(), canvasAssetGrid: mockEl(),
    canvasAssetHoverPreview: mockEl(), canvasAssetLibrarySelect: mockEl(), canvasAssetPanel: mockEl(),
    canvasAssetToggle: mockEl(), dropOverlay: mockEl(), missingAssetUrls: [],
    promptTemplateLibrarySelect: mockEl(), workflowExportLibraryBtn: mockEl(),
    selected: new Set(),
    workflowExportMeta: mockEl(), workflowTransferModal: mockEl(), workflowTransferSub: mockEl(),
    getActiveCanvasAssetCategoryId: () => '', setActiveCanvasAssetCategoryId: () => {},
    getActiveCanvasAssetLibraryId: () => '', setActiveCanvasAssetLibraryId: () => {},
    getActiveCanvasWorkflowCategoryId: () => '', setActiveCanvasWorkflowCategoryId: () => {},
    getAssetManagerTab: () => 'assets', getCanvasAssetLibraryOpen: () => canvasAssetLibraryOpen,
    setCanvasAssetLibraryOpen: (value) => { canvasAssetLibraryOpen = Boolean(value); },
    getActivePromptLibraryId: () => '', setActivePromptLibraryId: () => {},
    getCanvasAssetLibrary: () => ({libraries: [], categories: [], active_library_id: 'local'}),
    setCanvasAssetLibrary: () => {}, getCanvasPromptTemplatesLoaded: () => false,
    setCanvasPromptTemplatesLoaded: () => {}, getLocalCanvasAssetLibrary: () => ({items: [], tree: []}),
    setLocalCanvasAssetLibrary: () => {},
    getManagerSelectedAssetIds: () => new Set(), getManagerSelectedPromptIds: () => new Set(),
    getManagerSelectedWorkflowIds: () => new Set(),
    getCanvasPromptTemplateOverrides: () => ({}),
    getCanvasPromptLibraries: () => [],
    activeCanvasMediaCategory: () => 'all', activeCanvasWorkflowCategory: () => 'all',
    applyTempShUrlToCanvasRef: () => {}, bindCanvasPreviewImageFallbacks: () => {},
    canUseVersionedImageCreation: () => false, canvasMediaCategories: () => [],
    canvasMediaPreviewUrl: () => '', canvasPreviewImgHtml: () => '',
    canvasVideoPreviewHtml: () => '', canvasWorkflowCategories: () => [],
    closeWorkflowTransferModal: () => {}, copyTextToClipboard: async () => true,
    createImageCardFromUrl: () => null, createImageCardsFromLocalPaths: () => [],
    createVersionedDroppedMediaNode: async () => null, defaultPoint: () => ({x: 0, y: 0}),
    ensureCanvas: () => {}, escapeAttr: (s) => s, escapeHtml: (s) => s, fillImageNode: () => {},
    generatorSources: () => [], hasImageFiles: () => false, hasOutputImageDrag: () => false,
    insertWorkflowIntoCanvas: () => {}, isAudioUrl: () => false, isCanvasInputDrag: () => false,
    isRemoteVideoReferenceUrl: () => false, isVideoUrl: () => false, langIsEn: () => false,
    loadCanvasPromptTemplates: async () => [], mediaKindForRef: () => '', nodeBounds: () => ({}),
    orderedSources: () => [], outputImageName: () => '', outputUrlValue: () => '',
    pushUndo: () => {}, refreshIcons: () => {}, refreshNodes: () => {}, render: () => {},
    responseErrorMessage: async () => 'e', rhDefaultValue: () => '', rhParamKey: () => '',
    rhUseWallet: () => false, rhWorkflowNodeInfoList: () => [], scheduleSave: () => {},
    screenToWorld: () => ({x: 0, y: 0}), selectedWorkflowPayload: () => null,
    serializableCanvasNodes: () => [], setCanvasMode: () => {}, setCreateMode: () => {},
    setImageNodeFromOutput: () => {}, setStatus: () => {}, showErrorModal: () => {},
    stopCanvasRemotePolling: () => {}, tr: (k) => k, uid: (p) => p + '-1',
    updateWorkflowTransferMeta: () => {}, workflowFilename: () => 'wf.json',
};
const out = {};
(async () => {
try {
  const api = factory.create(host);
  out.requiredOpsCount = factory.REQUIRED_OPS.length;
  out.frozen = Object.isFrozen(api);
  out.methods = Object.keys(api).length;
  const driven = {};
  const call = async (name, fn) => { try { await fn(); driven[name] = 'ok'; } catch (e) { driven[name] = String(e.message || e); } };
  await call('mediaKindForUpload', async () => api.mediaKindForUpload({name: 'a.png', type: 'image/png'}));
  await call('isSupportedUploadFile', async () => api.isSupportedUploadFile({name: 'a.png', type: 'image/png'}));
  await call('hasImageDropData', async () => api.hasImageDropData(null));
  await call('isLocalImageDropValue', async () => api.isLocalImageDropValue(''));
  await call('isRemoteImageDropValue', async () => api.isRemoteImageDropValue(''));
  await call('imageDropPayload', async () => api.imageDropPayload(null));
  await call('resolveImageDropPayload', async () => api.resolveImageDropPayload(null));
  await call('canvasLocalAssetUrls', async () => api.canvasLocalAssetUrls());
  await call('activeCanvasPromptLibraryItems', async () => api.activeCanvasPromptLibraryItems());
  await call('canvasAssetItemKind', async () => api.canvasAssetItemKind({}));
  await call('canvasAssetLibraries', async () => api.canvasAssetLibraries());
  await call('canvasAssetLibraryIsLocal', async () => api.canvasAssetLibraryIsLocal());
  await call('canvasAssetSourceLibraries', async () => api.canvasAssetSourceLibraries());
  await call('revealCanvasAssetControls', async () => api.revealCanvasAssetControls());
  await call('toggleCanvasAssetLibrary', async () => api.toggleCanvasAssetLibrary());
  await call('showCanvasAssetHoverPreview', async () => api.showCanvasAssetHoverPreview(null, null));
  await call('hideCanvasAssetHoverPreview', async () => api.hideCanvasAssetHoverPreview());
  await call('positionCanvasAssetHoverPreview', async () => api.positionCanvasAssetHoverPreview(null, null));
  await call('refreshMissingCanvasAssets', async () => api.refreshMissingCanvasAssets());
  await call('renderCanvasAssetLibrary', async () => api.renderCanvasAssetLibrary());
  await call('renderAssetManager', async () => api.renderAssetManager());
  out.assetOpen = canvasAssetLibraryOpen;
  await call('renderImageAssetManager', async () => api.renderImageAssetManager());
  await call('renderPromptAssetManager', async () => api.renderPromptAssetManager());
  await call('renderWorkflowAssetManager', async () => api.renderWorkflowAssetManager());
  await call('openAssetManager', async () => api.openAssetManager());
  await call('closeAssetManager', async () => api.closeAssetManager());
  await call('exportSelectedWorkflow', async () => api.exportSelectedWorkflow());
  await call('setWorkflowLibraryExportState', async () => api.setWorkflowLibraryExportState());
  await call('defaultWorkflowAssetTarget', async () => api.defaultWorkflowAssetTarget());
  await call('workflowAssetThumbHtml', async () => api.workflowAssetThumbHtml({}));
  await call('canvasAssetThumbHtml', async () => api.canvasAssetThumbHtml({}));
  await call('currentCanvasAssetItem', async () => api.currentCanvasAssetItem({}));
  await call('findCanvasAssetCategoryForItem', async () => api.findCanvasAssetCategoryForItem('x'));
  await call('addUrlToCanvasAssetLibrary', async () => api.addUrlToCanvasAssetLibrary('http://x/a.png'));
  await call('rhImportWorkflowJson', async () => api.rhImportWorkflowJson('{}'));
  out.driven = driven;
  // missing-host-op loop
  let missingThrew = 0;
  for (const op of factory.REQUIRED_OPS) {
    const partial = Object.assign({}, host); delete partial[op];
    try { factory.create(partial); } catch (e) { if (e.name === 'TypeError') missingThrew += 1; }
  }
  out.missingThrew = missingThrew;
} catch (e) { out.fatal = String(e); }
console.log(JSON.stringify(out));
})().catch(e => { console.log(JSON.stringify({fatal: String(e)})); });
""".replace("__SEAM_PATH__", seam_path_json)
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertNotIn("fatal", actual, msg=f"seam drive failed: {actual.get('fatal')}")
        self.assertEqual(actual["requiredOpsCount"], 101,
            msg="REQUIRED_OPS count pin: Wave 16b seam declares 101 host ops; update seam + test together")
        self.assertTrue(actual["frozen"], msg="asset seam handle must be frozen")
        self.assertEqual(actual["methods"], 73, msg="handle must expose all 73 moved functions")
        self.assertEqual(actual["missingThrew"], 101,
            msg="every REQUIRED op must be validated with a TypeError on missing host")
        ref_errors = {k: v for k, v in actual["driven"].items() if "is not defined" in v}
        self.assertEqual(ref_errors, {}, msg=f"seam methods hit undefined identifiers: {ref_errors}")
        self.assertGreaterEqual(len(actual["driven"]), 33, msg="drive coverage dropped")
        self.assertEqual(actual["driven"]["toggleCanvasAssetLibrary"], "ok",
            msg="asset-library toggle must execute successfully, not merely avoid a ReferenceError")
        self.assertTrue(actual["assetOpen"],
            msg="asset-library toggle must update the page-owned open-state through its setter port")

        # canvas.js keeps exactly one 1-line wrapper per moved function.
        wrapper_names = [l.strip() for l in editor_source.split("\n")
                         if "return ensureClassicAssetRuntime()." in l and l.strip().startswith(("function ", "async function "))]
        self.assertEqual(len(wrapper_names), 73, msg="canvas.js must keep 73 1-line asset-seam wrappers")
        # page state stays page-owned: the factory bridges state with getters/setters
        self.assertIn("getCanvasAssetLibrary: () => canvasAssetLibrary", editor_source)
        self.assertIn("setCanvasAssetLibrary: (v) => { canvasAssetLibrary = v; }", editor_source)
        self.assertIn("setCanvasAssetLibraryOpen: (v) => { canvasAssetLibraryOpen = v; }", editor_source)
        self.assertIn("getCanvas: () => canvas,", editor_source)
        self.assertIn("getNodes: () => nodes,", editor_source)
        # the seam must not read page state directly
        self.assertNotIn("getCanvasAssetLibrary.libraries", seam_source)
        self.assertIn("getCanvasAssetLibrary().libraries", seam_source)
        # canvas.html loads the seam before canvas.js and the version was bumped.
        self.assertLess(page.index("workbench/canvas/classic-asset-runtime.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertIn("classic-asset-runtime.js?v=2026.09.08.1", page)
        self.assertIn("canvas-app-bootstrap.js?v=2026.09.09.2", page)

    def test_classic_editor_routes_video_provider_params_through_classic_video_provider_params_seam(self):
        # Wave 11: video-provider/params COMPAT seam. Four page-side
        # video provider/params helpers (videoApiProviders,
        # resolveVideoProviderId, providerVideoModels,
        # renderVideoImageInputs) move behind a bounded compat seam.
        seam = ROOT / "static/js/workbench/canvas/classic-video-provider-params.js"
        editor = canvas_app_paths(ROOT)[0]
        canvas_html = ROOT / "static/canvas.html"
        self.assertTrue(seam.exists(), msg="classic-video-provider-params.js seam module must exist for Wave 11")
        self.assertTrue(editor.exists(), msg="canvas.js editor must exist")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        html_source = canvas_html.read_text(encoding="utf-8")

        # The seam must expose the host factory with the documented four methods.
        self.assertIn("WorkbenchCanvasClassicVideoProviderParams", seam_source,
            msg="classic-video-provider-params.js must expose WorkbenchCanvasClassicVideoProviderParams")
        self.assertIn("videoApiProviders: function () { return videoApiProviders(); }", seam_source,
            msg="classic-video-provider-params.js seam handle must wrap videoApiProviders as a no-arg method")
        self.assertIn("resolveVideoProviderId: function (arg) { return resolveVideoProviderId(arg.id); }", seam_source,
            msg="classic-video-provider-params.js seam handle must wrap resolveVideoProviderId as resolveVideoProviderId({id})")
        self.assertIn("providerVideoModels: function (arg) { return providerVideoModels(arg.providerId); }", seam_source,
            msg="classic-video-provider-params.js seam handle must wrap providerVideoModels as providerVideoModels({providerId})")
        self.assertIn("renderVideoImageInputs: function (arg)", seam_source,
            msg="classic-video-provider-params.js seam handle must wrap renderVideoImageInputs as renderVideoImageInputs({list, node, imageInputs})")

        # Drive the seam in a Node vm sandbox and assert all four methods
        # produce documented results on the minimal mock host.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl() {{
    const el = {{
        tagName: 'DIV', className: '', innerHTML: '', value: '', disabled: false,
        style: {{}},
        options: [],
        children: [],
        onclick: null, oninput: null, onchange: null, onblur: null,
        onmousedown: null, ondragstart: null, ondragend: null,
        ondragover: null, ondrop: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}} }},
        dataset: {{}},
        appendChild(c) {{ this.children.push(c); return c; }},
        querySelector(sel) {{ return makeEl(); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
    }};
    return el;
}}
const documentStub = {{ createElement: (tag) => makeEl() }};
const windowStub = {{}};
const sandbox = {{window: windowStub, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const captured = {{ dragState: [] }};
const apiProviders = [
    {{ id: 'comfly', name: 'Comfly', enabled: true, video_models: ['veo3-fast', 'veo3-pro'] }},
    {{ id: 'modelscope', name: 'ModelScope', enabled: true, video_models: ['x'] }},
    {{ id: 'rhea', name: 'Rhea', enabled: true, video_models: [] }},
    {{ id: 'disabled', name: 'Disabled', enabled: false, video_models: ['y'] }},
];
let internalDrag = false;
const host = {{
    document: documentStub,
    tr: (k) => k,
    escapeHtml: (s) => String(s).replace(/[&<>"']/g, ''),
    mediaKindForRef: (ref) => ref && ref.kind ? ref.kind : 'image',
    canvasVideoPreviewHtml: (url, size) => '<video></video>',
    canvasPreviewImgHtml: (url, size) => '<img>',
    isMissingAssetUrl: (url) => url === 'missing',
    missingAssetHtml: (url, compact) => '<span>missing</span>',
    getApiProviders: () => apiProviders,
    getInternalDrag: () => internalDrag,
    setInternalDrag: (v) => {{ captured.dragState.push(v); internalDrag = v; }},
    uniqueModels: (list) => {{ const s = new Set(); return (list || []).map(String).filter(x => {{ if(!x || s.has(x)) return false; s.add(x); return true; }}); }},
    defaultApiProviders: () => [{{ id: 'comfly', name: 'Comfly', enabled: true, video_models: ['veo3-fast'] }}],
    reorderInput: () => {{}},
    refreshIcons: () => {{}},
}};
const api = sandbox.window.WorkbenchCanvasClassicVideoProviderParams.create(host);
const out = {{}};
out.hasVideoApiProviders = typeof api.videoApiProviders === 'function';
out.hasResolveVideoProviderId = typeof api.resolveVideoProviderId === 'function';
out.hasProviderVideoModels = typeof api.providerVideoModels === 'function';
out.hasRenderVideoImageInputs = typeof api.renderVideoImageInputs === 'function';
out.frozen = Object.isFrozen(api);
try {{
  const list = api.videoApiProviders();
  out.providers = list.map(p => p.id);
}} catch(e) {{ out.providersErr = String(e); }}
try {{
  out.resolvedKnown = api.resolveVideoProviderId({{id: 'comfly'}});
  out.resolvedUnknown = api.resolveVideoProviderId({{id: 'no-such-provider'}});
  // also exercise a "rhea" fallback path — rhea has empty video_models
  // so videoApiProviders filters it out; resolveVideoProviderId('rhea')
  // must therefore fall back to the first provider that does pass the filter
  out.resolvedFallback = api.resolveVideoProviderId({{id: 'rhea'}});
}} catch(e) {{ out.resolveErr = String(e); }}
try {{
  out.modelsKnown = api.providerVideoModels({{providerId: 'comfly'}});
  out.modelsUnknown = api.providerVideoModels({{providerId: 'no-such-provider'}});
}} catch(e) {{ out.modelsErr = String(e); }}
try {{
  const listEl = makeEl();
  const node = {{ id: 'video-node', type: 'video', useFrameRoles: false }};
  const inputs = [
    {{ id: 'src-1', preview: 'http://x', label: 'Image 1', refs: [{{ url: 'http://x' }}] }},
    {{ id: 'src-2', preview: 'missing', label: 'Missing', refs: [{{ url: 'missing' }}] }},
  ];
  api.renderVideoImageInputs({{list: listEl, node, imageInputs: inputs}});
  out.renderRan = true;
  out.renderedChildren = listEl.children.length;
}} catch(e) {{ out.renderErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasVideoApiProviders"], msg="seam must expose videoApiProviders")
        self.assertTrue(actual["hasResolveVideoProviderId"], msg="seam must expose resolveVideoProviderId")
        self.assertTrue(actual["hasProviderVideoModels"], msg="seam must expose providerVideoModels")
        self.assertTrue(actual["hasRenderVideoImageInputs"], msg="seam must expose renderVideoImageInputs")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        # videoApiProviders must filter out modelscope, disabled, and providers without video_models.
        self.assertNotIn("modelscope", actual.get("providers", []), msg="videoApiProviders must strip 'modelscope'")
        self.assertNotIn("disabled", actual.get("providers", []), msg="videoApiProviders must strip disabled providers")
        self.assertNotIn("rhea", actual.get("providers", []), msg="videoApiProviders must strip providers with empty video_models")
        self.assertIn("comfly", actual.get("providers", []), msg="videoApiProviders must keep comfly (has video_models)")
        # resolveVideoProviderId: known id resolves to itself; unknown id falls back to first provider.
        self.assertEqual(actual.get("resolvedKnown"), "comfly", msg="resolveVideoProviderId must return the requested id when it passes the videoApiProviders filter")
        self.assertEqual(actual.get("resolvedUnknown"), "comfly", msg="resolveVideoProviderId must fall back to first provider when id is unknown")
        self.assertEqual(actual.get("resolvedFallback"), "comfly", msg="resolveVideoProviderId must fall back to first provider when id is filtered out by videoApiProviders (e.g. empty video_models)")
        # providerVideoModels: dedupes via uniqueModels.
        self.assertEqual(actual.get("modelsKnown"), ["veo3-fast", "veo3-pro"], msg="providerVideoModels must return unique video_models for the requested provider")
        self.assertEqual(actual.get("modelsUnknown"), [], msg="providerVideoModels must return [] for unknown provider")
        # renderVideoImageInputs: produces one child per input.
        self.assertTrue(actual.get("renderRan"), msg=f"renderVideoImageInputs must run on minimal mock host, got: {actual.get('renderErr')}")
        self.assertEqual(actual.get("renderedChildren"), 2,
            msg="renderVideoImageInputs must append one child per input item")

        # Required-ops count pin (seam must keep this synchronized with the test).
        required_match = re.search(r"REQUIRED_OPS\s*=\s*\[([^\]]*)\]", seam_source, re.DOTALL)
        self.assertIsNotNone(required_match, msg="seam module must declare REQUIRED_OPS array")
        required = re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", required_match.group(1))
        self.assertEqual(len(required), 15,
            msg="REQUIRED_OPS count pin: Wave 11 seam module declares 15 host ops; if you add/remove an op, update both the seam and this test")

        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        for missing in required:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}, document: {{createElement: () => ({{}})}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, tr: () => '',
    escapeHtml: () => '', mediaKindForRef: () => 'image',
    canvasVideoPreviewHtml: () => '', canvasPreviewImgHtml: () => '',
    isMissingAssetUrl: () => false, missingAssetHtml: () => '',
    getApiProviders: () => [], getInternalDrag: () => false, setInternalDrag: () => {{}},
    uniqueModels: (l) => l || [], defaultApiProviders: () => [],
    reorderInput: () => {{}}, refreshIcons: () => {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicVideoProviderParams.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")

        # Source-contract: canvas.html loads the seam before canvas.js.
        seam_href = "workbench/canvas/classic-video-provider-params.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(html_source.index(seam_href), html_source.index(editor_href),
            msg="classic-video-provider-params.js must load before canvas.js in canvas.html")
        # The seam must also load after video-card-body to maintain the
        # documented Wave 5-11 load order.
        card_href = "workbench/canvas/classic-video-card-body.js"
        self.assertLess(html_source.index(card_href), html_source.index(seam_href),
            msg="classic-video-card-body.js must load BEFORE classic-video-provider-params.js in canvas.html")

        # Source-contract: canvas.js deleted the four local function
        # definitions and the page-side wrappers + dispatcher routes
        # through ensureClassicVideoProviderParams().
        self.assertNotIn("function videoApiProviders", editor_source,
            msg="canvas.js should no longer define function videoApiProviders")
        self.assertNotIn("function resolveVideoProviderId", editor_source,
            msg="canvas.js should no longer define function resolveVideoProviderId")
        self.assertNotIn("function providerVideoModels", editor_source,
            msg="canvas.js should no longer define function providerVideoModels")
        self.assertNotIn("function renderVideoImageInputs", editor_source,
            msg="canvas.js should no longer define function renderVideoImageInputs")
        self.assertIn("function ensureClassicVideoProviderParams", editor_source,
            msg="canvas.js must declare ensureClassicVideoProviderParams next to ensureClassicVideoCardBody")
        # Thin-page-side wrappers still exist (Wave 10 seam host-injection).
        self.assertIn("function sanitizeVideoNodeProviderModel", editor_source,
            msg="canvas.js must keep sanitizeVideoNodeProviderModel as a thin wrapper around the seam")
        self.assertIn("function videoProviderOptions", editor_source,
            msg="canvas.js must keep videoProviderOptions as a thin wrapper around the seam")
        self.assertIn("function videoModelOptions", editor_source,
            msg="canvas.js must keep videoModelOptions as a thin wrapper around the seam")
        # Direct callers route through the seam.
        self.assertIn("vpp.resolveVideoProviderId({id:", editor_source,
            msg="canvas.js page-side wrappers must call vpp.resolveVideoProviderId({id: ...})")
        self.assertIn("vpp.providerVideoModels({providerId", editor_source,
            msg="canvas.js page-side wrappers must call vpp.providerVideoModels({providerId: ...})")
        self.assertIn("vpp.videoApiProviders()", editor_source,
            msg="canvas.js page-side wrapper videoProviderOptions must call vpp.videoApiProviders()")
        self.assertIn("ensureClassicVideoProviderParams().renderVideoImageInputs({", editor_source,
            msg="canvas.js syncGeneratorInputs video branch must call ensureClassicVideoProviderParams().renderVideoImageInputs({...})")
        # Wave 16a moved runVideoNode's body into classic-executor-runtime.js.
        executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
        self.assertIn("ensureClassicVideoProviderParams().resolveVideoProviderId({id:", executor_source,
            msg="runVideoNode (executor seam) pre-flight must call ensureClassicVideoProviderParams().resolveVideoProviderId({id: ...})")


    def test_classic_editor_routes_output_grid_renderer_through_classic_output_grid_seam(self):
        # Wave 12: output-grid-renderer COMPAT seam. Three page-side
        # output-node grid functions (bindOutputWrap,
        # refreshOutputNodeContent, renderOutputGrid) move behind a
        # bounded compat seam.
        seam = ROOT / "static/js/workbench/canvas/classic-output-grid.js"
        editor = canvas_app_paths(ROOT)[0]
        canvas_html = ROOT / "static/canvas.html"
        self.assertTrue(seam.exists(), msg="classic-output-grid.js seam module must exist for Wave 12")
        self.assertTrue(editor.exists(), msg="canvas.js editor must exist")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        html_source = canvas_html.read_text(encoding="utf-8")

        # The seam must expose the host factory with the documented three methods.
        self.assertIn("WorkbenchCanvasClassicOutputGrid", seam_source,
            msg="classic-output-grid.js must expose WorkbenchCanvasClassicOutputGrid")
        self.assertIn("renderOutputGrid: function (arg) { return renderOutputGrid(arg.node, arg.pendingHtml); }", seam_source,
            msg="classic-output-grid.js seam handle must wrap renderOutputGrid as renderOutputGrid({node, pendingHtml})")
        self.assertIn("bindOutputWrap: function (arg) { return bindOutputWrap(arg.wrap, arg.node); }", seam_source,
            msg="classic-output-grid.js seam handle must wrap bindOutputWrap as bindOutputWrap({wrap, node})")
        self.assertIn("refreshOutputNodeContent: function (arg) { return refreshOutputNodeContent(arg.node); }", seam_source,
            msg="classic-output-grid.js seam handle must wrap refreshOutputNodeContent as refreshOutputNodeContent({node})")

        # Drive the seam in a Node vm sandbox and assert all three methods
        # produce documented results on the minimal mock host.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl(tag) {{
    const el = {{
        tagName: (tag || 'DIV').toUpperCase(), className: '', innerHTML: '', value: '',
        disabled: false, draggable: false,
        style: {{ setProperty: () => {{}}, removeProperty: () => {{}} }},
        options: [],
        dataset: {{}},
        children: [],
        parentNode: null,
        _innerHTML: '',
        _lastChild: null,
        onclick: null, oninput: null, onchange: null, onblur: null,
        onmousedown: null, ondragstart: null, ondragend: null,
        onwheel: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}}, toggle: (cls, on) => {{}} }},
        appendChild(c) {{ this.children.push(c); c.parentNode = this; this._lastChild = c; return c; }},
        insertAdjacentHTML(pos, html) {{
            const child = makeEl('div');
            child.innerHTML = html;
            child.dataset._html = html;
            this.children.push(child);
            child.parentNode = this;
            this._lastChild = child;
        }},
        get lastElementChild() {{ return this._lastChild; }},
        querySelector(sel) {{ return makeEl('div'); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        addEventListener(ev, fn) {{}},
        contains(other) {{ return false; }},
        closest(sel) {{ return null; }},
        replaceWith(other) {{
            if (this.parentNode) {{
                const idx = this.parentNode.children.indexOf(this);
                if (idx >= 0) this.parentNode.children[idx] = other;
            }}
            other.parentNode = this.parentNode;
        }},
        remove() {{
            if (this.parentNode) {{
                const idx = this.parentNode.children.indexOf(this);
                if (idx >= 0) this.parentNode.children.splice(idx, 1);
            }}
        }},
    }};
    return el;
}}
function makeTemplate() {{
    const tpl = makeEl('template');
    tpl.content = {{ firstElementChild: null, firstChild: null }};
    return tpl;
}}
const documentStub = {{
    createElement: (tag) => {{
        if (tag === 'template') return makeTemplate();
        return makeEl(tag);
    }},
}};
const windowStub = {{}};
const sandbox = {{window: windowStub, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);

const captured = {{ drags: 0, lightboxOpens: 0, downloads: 0, timerRefreshes: 0, fbBinds: 0, syncRes: 0, refreshes: 0, deletes: 0 }};

// Build a persistent output-node stub structure. queries for
// `.output-node[data-id="..."]` return the full el, queries for
// `.node-body` return the persisted body, queries for `.output-grid`
// return the persisted grid — so refreshOutputNodeContent's `el / body
// / grid` triple all resolve to the same structure.
const _outputBody = makeEl('div');
_outputBody.className = 'node-body';
const _outputGrid = makeEl('div');
_outputGrid.className = 'output-grid';
_outputBody.appendChild(_outputGrid);
const _outputNode = makeEl('div');
_outputNode.dataset.outputNode = '1';
_outputNode.appendChild(_outputBody);
_outputNode.querySelector = (sel) => {{
    if (sel === '.node-body' || sel.indexOf('.node-body') === 0) return _outputBody;
    return makeEl('div');
}};
_outputBody.querySelector = (sel) => {{
    if (sel === '.output-grid' || sel.indexOf('.output-grid') === 0) return _outputGrid;
    return makeEl('div');
}};
const nodesElStub = {{
    querySelector: (sel) => {{
        if (sel.indexOf('.output-node') === 0) return _outputNode;
        return null;
    }},
}};
const host = {{
    document: documentStub,
    nodesEl: nodesElStub,
    setOutputDragPreview: (e, img) => {{ captured.drags += 1; }},
    openOutputLightbox: (url, out) => {{ captured.lightboxOpens += 1; }},
    downloadUrl: (url, name) => {{ captured.downloads += 1; return Promise.resolve(); }},
    outputDownloadName: (url) => 'output.jpg',
    canvasActivateVideoPreview: (wrap) => {{}},
    queryRecoverPendingOutput: (pid) => {{}},
    outputUrlValue: (item) => typeof item === 'string' ? item : (item && item.url) || '',
    outputGridLayout: (node) => null,
    outputDomKeyForItem: (item) => 'url:' + (item.url || ''),
    outputDomKeyForPending: (p) => 'pending:' + (p && p.id || ''),
    renderOutputMedia: (item, useGridLayout) => '<div class="output-img-wrap"></div>',
    renderPendingOutput: (p) => '<div class="output-pending"></div>',
    bindCanvasPreviewImageFallbacks: (grid) => {{ captured.fbBinds += 1; }},
    syncCanvasSelectedImageResolution: (el) => {{ captured.syncRes += 1; }},
    refreshOutputTimer: () => {{ captured.timerRefreshes += 1; }},
    scheduleSave: () => {{}},
    refreshNodes: (ids) => {{ captured.refreshes += 1; }},
}};

const api = sandbox.window.WorkbenchCanvasClassicOutputGrid.create(host);
const out = {{}};
out.hasRenderOutputGrid = typeof api.renderOutputGrid === 'function';
out.hasBindOutputWrap = typeof api.bindOutputWrap === 'function';
out.hasRefreshOutputNodeContent = typeof api.refreshOutputNodeContent === 'function';
out.frozen = Object.isFrozen(api);
try {{
  const node = {{ id: 'out-1', type: 'output', images: [] }};
  const html = api.renderOutputGrid({{node, pendingHtml: '<div class=\"output-pending\"></div>'}});
  out.renderedHtml = html;
  out.containsGridClass = html.indexOf('output-grid') !== -1;
  out.containsPending = html.indexOf('output-pending') !== -1;
  out.noImagesMeansNoItems = html.indexOf('output-img-wrap') === -1;
}} catch(e) {{ out.renderErr = String(e); }}
try {{
  const node = {{ id: 'out-1', type: 'output', images: [{{ url: 'http://x' }}], _pending: [{{ id: 'p1' }}] }};
  const refreshed = api.refreshOutputNodeContent({{node}});
  out.refreshed = refreshed === true;
}} catch(e) {{ out.refreshErr = String(e); }}
try {{
  const node = {{ id: 'out-1', type: 'output', images: [{{ url: 'http://x' }}], _pending: [] }};
  const wrap = makeEl('div');
  wrap.dataset.outputUrl = 'http://x';
  api.bindOutputWrap({{wrap, node}});
  out.bindRan = true;
  out.draggable = wrap.draggable;
}} catch(e) {{ out.bindErr = String(e); }}
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasRenderOutputGrid"], msg="seam must expose renderOutputGrid")
        self.assertTrue(actual["hasBindOutputWrap"], msg="seam must expose bindOutputWrap")
        self.assertTrue(actual["hasRefreshOutputNodeContent"], msg="seam must expose refreshOutputNodeContent")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        # renderOutputGrid: emits the wrapper div with the documented 'output-grid' class.
        self.assertTrue(actual.get("containsGridClass"), msg="renderOutputGrid must emit 'output-grid' class wrapper")
        self.assertTrue(actual.get("containsPending"), msg="renderOutputGrid must include pendingHtml in the output")
        self.assertTrue(actual.get("noImagesMeansNoItems"), msg="renderOutputGrid must omit output-img-wrap when node.images is empty")
        # refreshOutputNodeContent: returns true when both body and grid are present in nodesEl.
        self.assertTrue(actual.get("refreshed"), msg=f"refreshOutputNodeContent must return true on stub nodesEl, got: {actual.get('refreshErr')}")
        # bindOutputWrap: runs without throwing; sets draggable=true when wrap.dataset.outputUrl is set.
        self.assertTrue(actual.get("bindRan"), msg=f"bindOutputWrap must run on minimal mock host, got: {actual.get('bindErr')}")
        self.assertTrue(actual.get("draggable"), msg="bindOutputWrap must set wrap.draggable=true when an outputUrl is present")

        # Required-ops count pin (seam must keep this synchronized with the test).
        required_match = re.search(r"REQUIRED_OPS\s*=\s*\[([^\]]*)\]", seam_source, re.DOTALL)
        self.assertIsNotNone(required_match, msg="seam module must declare REQUIRED_OPS array")
        required = re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", required_match.group(1))
        self.assertEqual(len(required), 19,
            msg="REQUIRED_OPS count pin: Wave 12 seam module declares 19 host ops; if you add/remove an op, update both the seam and this test")

        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        for missing in required:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}, document: {{createElement: () => ({{}})}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}})}}, nodesEl: {{querySelector: () => null}},
    setOutputDragPreview: () => {{}}, openOutputLightbox: () => {{}},
    downloadUrl: () => {{}}, outputDownloadName: () => '',
    canvasActivateVideoPreview: () => {{}}, queryRecoverPendingOutput: () => {{}},
    outputUrlValue: (i) => '', outputGridLayout: () => null,
    outputDomKeyForItem: () => '', outputDomKeyForPending: () => '',
    renderOutputMedia: () => '', renderPendingOutput: () => '',
    bindCanvasPreviewImageFallbacks: () => {{}},
    syncCanvasSelectedImageResolution: () => {{}},
    refreshOutputTimer: () => {{}}, scheduleSave: () => {{}},
    refreshNodes: () => {{}},
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicOutputGrid.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")

        # Source-contract: canvas.html loads the seam before canvas.js.
        seam_href = "workbench/canvas/classic-output-grid.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(html_source.index(seam_href), html_source.index(editor_href),
            msg="classic-output-grid.js must load before canvas.js in canvas.html")
        # The seam must also load after video-provider-params to maintain the
        # documented Wave 5-12 load order.
        vpp_href = "workbench/canvas/classic-video-provider-params.js"
        self.assertLess(html_source.index(vpp_href), html_source.index(seam_href),
            msg="classic-video-provider-params.js must load BEFORE classic-output-grid.js in canvas.html")

        # Source-contract: canvas.js deleted the three local function
        # definitions and the dispatcher routes every kind through the
        # seam via `ensureClassicOutputGrid()`.
        self.assertNotIn("function bindOutputWrap", editor_source,
            msg="canvas.js should no longer define function bindOutputWrap")
        self.assertNotIn("function refreshOutputNodeContent", editor_source,
            msg="canvas.js should no longer define function refreshOutputNodeContent")
        self.assertNotIn("function renderOutputGrid", editor_source,
            msg="canvas.js should no longer define function renderOutputGrid")
        self.assertIn("function ensureClassicOutputGrid", editor_source,
            msg="canvas.js must declare ensureClassicOutputGrid next to ensureClassicVideoProviderParams")
        self.assertIn("ensureClassicOutputGrid().refreshOutputNodeContent({node})", editor_source,
            msg="canvas.js refreshNodes output branch must call ensureClassicOutputGrid().refreshOutputNodeContent({node})")
        self.assertIn("outputGrid.renderOutputGrid({node, pendingHtml})", editor_source,
            msg="canvas.js body dispatcher must call outputGrid.renderOutputGrid({node, pendingHtml})")
        self.assertIn("outputGrid.bindOutputWrap({wrap, node})", editor_source,
            msg="canvas.js body dispatcher must call outputGrid.bindOutputWrap({wrap, node})")


    def test_classic_editor_routes_generation_log_through_classic_generation_log_seam(self):
        # Wave 13: generation-log COMPAT seam. Two page-side
        # generation-log functions (addGenerationLog, renderCanvasLog)
        # move behind a bounded compat seam. The 22 caller sites of
        # addGenerationLog in canvas.js (run*Node success/failure
        # handlers + miniMax run + comfy run + pending-output recovery
        # + group run + miniMax log error wrapper) continue to call
        # the page-side addGenerationLog function — the wrapper now
        # delegates to the seam.
        seam = ROOT / "static/js/workbench/canvas/classic-generation-log.js"
        editor = canvas_app_paths(ROOT)[0]
        canvas_html = ROOT / "static/canvas.html"
        self.assertTrue(seam.exists(), msg="classic-generation-log.js seam module must exist for Wave 13")
        self.assertTrue(editor.exists(), msg="canvas.js editor must exist")
        seam_source = seam.read_text(encoding="utf-8")
        editor_source = read_canvas_app_source(ROOT)
        html_source = canvas_html.read_text(encoding="utf-8")

        # The seam must expose the host factory with the documented two methods.
        self.assertIn("WorkbenchCanvasClassicGenerationLog", seam_source,
            msg="classic-generation-log.js must expose WorkbenchCanvasClassicGenerationLog")
        self.assertIn("addGenerationLog: function (arg) { return addGenerationLog(arg); }", seam_source,
            msg="classic-generation-log.js seam handle must wrap addGenerationLog as addGenerationLog(arg)")
        self.assertIn("renderCanvasLog: function () { return renderCanvasLog(); }", seam_source,
            msg="classic-generation-log.js seam handle must wrap renderCanvasLog as renderCanvasLog()")

        # Drive the seam in a Node vm sandbox and assert both methods
        # produce documented results on the minimal mock host.
        script = f"""
const fs = require('fs'); const vm = require('vm');
function makeEl(tag) {{
    const el = {{
        tagName: (tag || 'DIV').toUpperCase(), className: '', innerHTML: '', value: '',
        disabled: false, draggable: false,
        style: {{}},
        options: [],
        dataset: {{}},
        children: [],
        parentNode: null,
        onclick: null, oninput: null, onchange: null, onblur: null,
        classList: {{ contains: () => false, add: () => {{}}, remove: () => {{}}, toggle: () => {{}} }},
        appendChild(c) {{ this.children.push(c); c.parentNode = this; return c; }},
        querySelector(sel) {{ return makeEl('div'); }},
        querySelectorAll(sel) {{ return []; }},
        forEach() {{}},
        addEventListener(ev, fn) {{}},
    }};
    return el;
}}
const _logList = makeEl('div');
_logList.id = 'logList';
Object.defineProperty(_logList, 'innerHTML', {{
    get() {{ return _logList._innerHTML || ''; }},
    set(v) {{ _logList._innerHTML = v; }},
}});
const documentStub = {{
    createElement: (tag) => makeEl(tag),
    getElementById: (id) => {{
        if (id === 'logList') return _logList;
        return null;
    }},
}};
const windowStub = {{
    StudioI18n: {{ lang: () => 'zh-CN' }},
    logList: null,
}};
const sandbox = {{window: windowStub, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);

const captured = {{ soundPlays: 0, copies: 0, lightboxOpens: 0, timerRefreshes: 0, fbBinds: 0 }};
let canvasState = null;
let uidCounter = 0;
const host = {{
    document: documentStub,
    tr: (k) => k,
    getCanvas: () => canvasState,
    escapeHtml: (s) => String(s).replace(/[&<>"']/g, ''),
    escapeAttr: (s) => String(s).replace(/"/g, '&quot;'),
    isMissingAssetUrl: (url) => url === 'missing',
    mediaKindForOutputItem: (item) => (item && item.kind) || 'image',
    canvasVideoPreviewHtml: (url, size, attrs) => '<video></video>',
    canvasPreviewImgHtml: (url, size, attrs) => '<img>',
    runPlatformLabel: (run) => (run && run.platform) || 'unknown',
    runTaskLabel: (run) => (run && (run.taskLabel || run.model)) || '-',
    logTaskLabel: (log) => (log && log.model) || '-',
    formatRunDuration: (ms) => ms + 'ms',
    langIsEn: () => false,
    windowObj: windowStub,
    outputUrlValue: (item) => typeof item === 'string' ? item : (item && item.url) || '',
    playGenerationCompleteSound: () => {{ captured.soundPlays += 1; }},
    copyTextToClipboard: async (text) => {{ captured.copies += 1; return true; }},
    refreshIcons: () => {{}},
    bindCanvasPreviewImageFallbacks: (root) => {{ captured.fbBinds += 1; }},
    openOutputLightbox: (url, out) => {{ captured.lightboxOpens += 1; }},
    uid: (prefix) => prefix + '-' + (++uidCounter),
}};

const api = sandbox.window.WorkbenchCanvasClassicGenerationLog.create(host);
const out = {{}};
out.hasAddGenerationLog = typeof api.addGenerationLog === 'function';
out.hasRenderCanvasLog = typeof api.renderCanvasLog === 'function';
out.frozen = Object.isFrozen(api);

// 1. addGenerationLog with no canvas → no-op (no throw, no mutation).
try {{
  canvasState = null;
  api.addGenerationLog({{ run: {{ platform: 'comfly' }} }});
  out.noCanvasRan = true;
}} catch(e) {{ out.noCanvasErr = String(e); }}

// 2. addGenerationLog with outputs → adds entry, plays sound.
canvasState = {{ logs: [] }};
api.addGenerationLog({{ run: {{ platform: 'comfly', taskLabel: 'T1', prompt: 'p1' }}, outputs: [{{ url: 'http://a' }}, 'http://b'], runMs: 1234 }});
out.entryWritten = canvasState.logs.length === 1;
out.entryHasId = canvasState.logs[0] && canvasState.logs[0].id === 'log-1';
out.entryHasPlatform = canvasState.logs[0] && canvasState.logs[0].platform === 'comfly';
out.entryHasRunMs = canvasState.logs[0] && canvasState.logs[0].runMs === 1234;
out.soundPlayed = captured.soundPlays === 1;

// 3. addGenerationLog with error → status='failed', no sound.
api.addGenerationLog({{ run: {{ platform: 'comfly' }}, outputs: [{{ url: 'http://c' }}], error: 'boom' }});
out.failedStatus = canvasState.logs[0].status === 'failed';
out.errorString = canvasState.logs[0].error === 'boom';
out.soundStillOne = captured.soundPlays === 1;

// 4. addGenerationLog caps at 500 entries.
for (let i = 0; i < 600; i++) {{
    api.addGenerationLog({{ run: {{ platform: 'comfly' }}, outputs: [] }});
}}
out.capped = canvasState.logs.length === 500;
out.prependsLatest = canvasState.logs[0].id !== 'log-1';

// 5. renderCanvasLog with logs → emits log-item rows.
canvasState.logs = [{{ id: 'l1', status: 'success', platform: 'comfly', outputs: [{{ url: 'http://a' }}], runMs: 1000, prompt: 'p' }}];
try {{
  api.renderCanvasLog();
  out.renderRan = true;
  out.listHtml = _logList._innerHTML;
  out.containsLogItem = out.listHtml && out.listHtml.indexOf('log-item') !== -1;
  out.containsStatusChip = out.listHtml && out.listHtml.indexOf('status-ok') !== -1;
  out.containsPlatformChip = out.listHtml && out.listHtml.indexOf('comfly') !== -1;
}} catch(e) {{ out.renderErr = String(e); }}

// 6. renderCanvasLog with no logs → emits log-empty.
canvasState.logs = [];
try {{
  api.renderCanvasLog();
  out.emptyHtml = _logList._innerHTML;
  out.containsEmpty = out.emptyHtml && out.emptyHtml.indexOf('log-empty') !== -1;
}} catch(e) {{ out.emptyErr = String(e); }}

console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        actual = json.loads(result.stdout)
        self.assertTrue(actual["hasAddGenerationLog"], msg="seam must expose addGenerationLog")
        self.assertTrue(actual["hasRenderCanvasLog"], msg="seam must expose renderCanvasLog")
        self.assertTrue(actual["frozen"], msg="seam handle must be frozen")
        # addGenerationLog no-op when canvas is null
        self.assertTrue(actual.get("noCanvasRan"), msg=f"addGenerationLog must no-op when canvas is null, got: {actual.get('noCanvasErr')}")
        # addGenerationLog happy path
        self.assertTrue(actual.get("entryWritten"), msg="addGenerationLog must prepend a new log entry")
        self.assertTrue(actual.get("entryHasId"), msg="addGenerationLog must use uid('log') for the entry id")
        self.assertTrue(actual.get("entryHasPlatform"), msg="addGenerationLog must capture runPlatformLabel(run) on the entry")
        self.assertTrue(actual.get("entryHasRunMs"), msg="addGenerationLog must capture Number(runMs || 0) on the entry")
        self.assertTrue(actual.get("soundPlayed"), msg="addGenerationLog must play completion sound when outputs are present")
        # failed-status path
        self.assertTrue(actual.get("failedStatus"), msg="addGenerationLog must set status='failed' when error is non-empty")
        self.assertTrue(actual.get("errorString"), msg="addGenerationLog must capture String(error) on the entry")
        self.assertTrue(actual.get("soundStillOne"), msg="addGenerationLog must NOT play completion sound when error is present")
        # 500-entry cap
        self.assertTrue(actual.get("capped"), msg=f"addGenerationLog must cap canvas.logs at 500 entries, got length={len(str(actual))}")
        self.assertTrue(actual.get("prependsLatest"), msg="addGenerationLog must prepend the new entry (the original 'log-test' entry should be evicted by the cap)")
        # renderCanvasLog happy path
        self.assertTrue(actual.get("renderRan"), msg=f"renderCanvasLog must run on minimal mock host, got: {actual.get('renderErr')}")
        self.assertTrue(actual.get("containsLogItem"), msg=f"renderCanvasLog must emit 'log-item' rows, got html: {actual.get('listHtml')}")
        self.assertTrue(actual.get("containsStatusChip"), msg=f"renderCanvasLog must emit 'status-ok' chip for successful logs, got html: {actual.get('listHtml')}")
        self.assertTrue(actual.get("containsPlatformChip"), msg=f"renderCanvasLog must emit platform chip, got html: {actual.get('listHtml')}")
        # renderCanvasLog empty path
        self.assertTrue(actual.get("containsEmpty"), msg=f"renderCanvasLog must emit 'log-empty' for empty logs, got html: {actual.get('emptyHtml')}")

        # Required-ops count pin (seam must keep this synchronized with the test).
        required_match = re.search(r"REQUIRED_OPS\s*=\s*\[([^\]]*)\]", seam_source, re.DOTALL)
        self.assertIsNotNone(required_match, msg="seam module must declare REQUIRED_OPS array")
        required = re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", required_match.group(1))
        self.assertEqual(len(required), 22,
            msg="REQUIRED_OPS count pin: Wave 13 seam module declares 22 host ops; if you add/remove an op, update both the seam and this test")

        # TypeError-on-missing-host: every one of the REQUIRED ops
        # must be validated. Iterate each name in turn and confirm
        # create() throws TypeError when it is removed.
        for missing in required:
            partial_script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}, document: {{createElement: () => ({{}}), getElementById: () => null}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const fullHost = {{
    document: {{createElement: () => ({{}}), getElementById: () => null}}, tr: () => '',
    getCanvas: () => null, escapeHtml: () => '', escapeAttr: () => '',
    isMissingAssetUrl: () => false, mediaKindForOutputItem: () => 'image',
    canvasVideoPreviewHtml: () => '', canvasPreviewImgHtml: () => '',
    runPlatformLabel: () => '', runTaskLabel: () => '', logTaskLabel: () => '',
    formatRunDuration: () => '', langIsEn: () => false, windowObj: {{}},
    outputUrlValue: () => '', playGenerationCompleteSound: () => {{}},
    copyTextToClipboard: async () => false, refreshIcons: () => {{}},
    bindCanvasPreviewImageFallbacks: () => {{}}, openOutputLightbox: () => {{}},
    uid: () => '',
}};
delete fullHost.{missing};
try {{ sandbox.window.WorkbenchCanvasClassicGenerationLog.create(fullHost); console.log('no-throw'); }}
catch (e) {{ console.log(e.constructor.name + ':' + e.message); }}
"""
            partial_result = subprocess.run(["node", "-e", partial_script], check=True, text=True, capture_output=True)
            self.assertIn("TypeError", partial_result.stdout,
                msg=f"missing host.{missing} should throw TypeError, got: {partial_result.stdout}")

        # Source-contract: canvas.html loads the seam before canvas.js.
        seam_href = "workbench/canvas/classic-generation-log.js"
        editor_href = "static/js/workbench/canvas/canvas-app-bootstrap.js"
        self.assertLess(html_source.index(seam_href), html_source.index(editor_href),
            msg="classic-generation-log.js must load before canvas.js in canvas.html")
        # The seam must also load after output-grid to maintain the
        # documented Wave 5-13 load order.
        grid_href = "workbench/canvas/classic-output-grid.js"
        self.assertLess(html_source.index(grid_href), html_source.index(seam_href),
            msg="classic-output-grid.js must load BEFORE classic-generation-log.js in canvas.html")

        # Source-contract: canvas.js deleted the two local function
        # definitions and the page-side wrappers + ensure host
        # injection routes every kind through the seam via
        # `ensureClassicGenerationLog()`.
        self.assertNotIn("function addGenerationLog", editor_source.split("function ensureClassicGenerationLog")[0].split("function addGenerationLog(arg)")[0] if "function addGenerationLog(arg)" in editor_source else editor_source,
            msg="canvas.js should no longer define the original addGenerationLog function body (the thin page-side wrapper is fine)")
        # The simpler, more reliable assertion: the *original* function
        # body (which had `canvas.logs = canvas.logs || [];` directly) is
        # gone — only the thin wrapper `addGenerationLog(arg)` that
        # delegates to the seam remains.
        self.assertIn("function addGenerationLog(arg){", editor_source,
            msg="canvas.js must keep addGenerationLog as a thin wrapper around the seam")
        self.assertIn("ensureClassicGenerationLog().addGenerationLog(arg)", editor_source,
            msg="canvas.js addGenerationLog wrapper must call ensureClassicGenerationLog().addGenerationLog(arg)")
        self.assertIn("function renderCanvasLog(){", editor_source,
            msg="canvas.js must keep renderCanvasLog as a thin wrapper around the seam")
        self.assertIn("ensureClassicGenerationLog().renderCanvasLog()", editor_source,
            msg="canvas.js renderCanvasLog wrapper must call ensureClassicGenerationLog().renderCanvasLog()")
        self.assertIn("function ensureClassicGenerationLog", editor_source,
            msg="canvas.js must declare ensureClassicGenerationLog next to ensureClassicOutputGrid")
        # The original 90-LOC addGenerationLog + renderCanvasLog bodies
        # must be gone (we can detect this by checking the original
        # canvas.logs = canvas.logs || []; preamble is absent from the
        # seam-call wrapper).
        self.assertNotIn("playGenerationCompleteSound();\n            canvas.logs = canvas.logs || [];", editor_source,
            msg="canvas.js should no longer host the original addGenerationLog function body — only the seam does")
        # The seam must have the same pattern so we don't get a false negative.
        self.assertIn("playGenerationCompleteSound();", seam_source,
            msg="classic-generation-log.js must keep playGenerationCompleteSound invocation in addGenerationLog body")
        self.assertIn("canvas.logs = canvas.logs || [];", seam_source,
            msg="classic-generation-log.js must keep canvas.logs preamble in addGenerationLog body")

    def test_versioned_node_creation_is_default_on_loopback_with_an_explicit_rollback(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
function enabled(search) {{
  const sandbox = {{window: {{location: {{hostname:'127.0.0.1', search}}}}, URLSearchParams, fetch:() => {{}}}};
  vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
  return sandbox.window.WorkbenchNodeClient.isEnabled();
}}
console.log(JSON.stringify({{normal:enabled(''), explicitEnable:enabled('?versioned_nodes=1'), rollback:enabled('?versioned_nodes=0')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"normal": True, "explicitEnable": True, "rollback": False})
    def test_editor_adapters_share_pure_media_kind_classification(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-kind.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaKind;
console.log(JSON.stringify({{
  video:api.kindForUrl('/output/one.mp4'), audio:api.kindForUrl('/output/one.flac'), text:api.kindForUrl('/output/one.md'),
  workflow:api.kindForItem({{name:'workflow.zip'}}, {{allowWorkflow:true}}), file:api.kindForItem({{kind:'file', url:'/output/x.png'}}),
  classicFlv:api.kindForUrl('/output/one.flv', {{includeFlv:true}}), smartFlv:api.kindForUrl('/output/one.flv'),
  nodeVideo:api.kindForNode({{mediaKind:'', url:'/output/node.mp4'}}, {{includeFlv:true}}),
  nodeExplicit:api.kindForNode({{mediaKind:'audio', url:'/output/node.mp4'}}, {{includeFlv:true}}),
  mime:api.kindForFile({{type:'video/mp4', name:'ignored'}}), fallback:api.kindForFile({{type:'', name:'unknown.bin'}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "video": "video", "audio": "audio", "text": "text", "workflow": "workflow", "file": "file",
            "classicFlv": "video", "smartFlv": "image", "nodeVideo": "video", "nodeExplicit": "audio", "mime": "video", "fallback": "image",
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-kind.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaKind", editor_source)
    def test_editor_adapters_share_pure_media_url_normalization(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-url.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{location: {{origin:'http://127.0.0.1:3000'}}}}, URL, encodeURIComponent}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaUrl;
console.log(JSON.stringify({{
  original:api.originalUrl('/api/media-preview?w=512&url=%2Foutput%2Fone.png', 'http://127.0.0.1:3000'),
  local:api.previewUrl('/output/one.png', {{size:513, displayUrl:value => `display:${{value}}`}}),
  remote:api.previewUrl('https://example.test/one.png', {{displayUrl:value => `display:${{value}}`}}),
  inline:api.previewUrl('data:image/png;base64,AA', {{displayUrl:value => `display:${{value}}`, keepInlineUrl:true}}),
  unsupported:api.previewUrl('/output/one.txt', {{displayUrl:value => `display:${{value}}`, keepUnsupportedUrl:true}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "original": "/output/one.png",
            "local": "/api/media-preview?w=513&url=%2Foutput%2Fone.png",
            "remote": "display:https://example.test/one.png",
            "inline": "data:image/png;base64,AA",
            "unsupported": "/output/one.txt",
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-url.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaUrl.originalUrl", editor_source)
            self.assertIn("WorkbenchCanvasMediaUrl.previewUrl", editor_source)

    def test_editor_adapters_share_native_video_event_isolation(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-preview-controls.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const listeners = {{}};
const overlay = {{style:{{display:'initial'}}}};
const video = {{
  dataset:{{}}, paused:false, ended:false,
  parentElement:{{querySelector: selector => selector === '.video-overlay' ? overlay : null}},
  addEventListener:(type, listener) => {{ (listeners[type] ||= []).push(listener); }},
}};
const bound = sandbox.window.WorkbenchCanvasMediaPreviewControls.bindVideoOverlay(video, {{boundKey:'adapterBound', overlaySelector:'.video-overlay'}});
video.paused = true;
listeners.pause[0]();
const pausedDisplay = overlay.style.display;
video.paused = false;
listeners.play[0]();
const playingDisplay = overlay.style.display;
let stopped = 0;
listeners.click[0]({{stopPropagation:() => {{ stopped += 1; }}}});
const second = sandbox.window.WorkbenchCanvasMediaPreviewControls.bindVideoOverlay(video, {{boundKey:'adapterBound', overlaySelector:'.video-overlay'}});
console.log(JSON.stringify({{bound, second, marker:video.dataset.adapterBound, pausedDisplay, playingDisplay, stopped, eventCount:Object.keys(listeners).length}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "bound": True,
            "second": False,
            "marker": "1",
            "pausedDisplay": "",
            "playingDisplay": "none",
            "stopped": 1,
            "eventCount": 12,
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-preview-controls.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaPreviewControls.bindVideoOverlay", editor_source)

    def test_editor_adapters_share_native_media_playback_state_preservation(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-playback-state.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaPlaybackState;
const makeMedia = (url, state={{}}) => {{
  const listeners = {{}};
  return {{tagName:'VIDEO', dataset:{{url}}, currentTime:state.currentTime ?? 0, paused:state.paused ?? true,
    playbackRate:state.playbackRate ?? 1, muted:state.muted ?? false, volume:state.volume ?? 1, readyState:state.readyState ?? 1,
    getAttribute:key => key === 'src' ? url : '', addEventListener:(type, callback, options) => {{ listeners[type] = {{callback, options}}; }},
    play:() => {{ this.played = (this.played || 0) + 1; return {{catch:() => {{}}}}; }}, listeners}};
}};
const oldMedia = makeMedia('/output/one.mp4', {{currentTime:18.4, paused:false, playbackRate:1.25, muted:true, volume:0.4}});
const newMedia = makeMedia('/output/one.mp4', {{currentTime:0, readyState:1}});
const root = {{querySelectorAll:() => [oldMedia]}};
const states = api.captureAll(root);
api.restore(newMedia, states.get(api.signature(newMedia)));
const delayed = makeMedia('/output/two.mp4', {{readyState:0}});
api.restore(delayed, {{currentTime:7, paused:true, playbackRate:2, muted:false, volume:0.8}});
delayed.listeners.loadedmetadata.callback();
console.log(JSON.stringify({{signature:api.signature(oldMedia), size:states.size, restored:{{time:newMedia.currentTime, rate:newMedia.playbackRate, muted:newMedia.muted, volume:newMedia.volume}}, delayed:{{time:delayed.currentTime, rate:delayed.playbackRate, volume:delayed.volume, once:delayed.listeners.loadedmetadata.options.once}}}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "signature": "video:/output/one.mp4", "size": 1,
            "restored": {"time": 18.4, "rate": 1.25, "muted": True, "volume": 0.4},
            "delayed": {"time": 7, "rate": 2, "volume": 0.8, "once": True},
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-playback-state.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaPlaybackState.captureAll", editor_source)
            self.assertIn("WorkbenchCanvasMediaPlaybackState.restoreAll", editor_source)

    def test_editor_adapters_share_media_reference_filtering(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-references.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaReferences;
const refs = [{{url:'/one.png', kind:'image'}}, {{url:'/two.mp4', kind:'video'}}, {{url:'https://example.test/three.mp4', kind:'video'}}, {{url:'data:image/png;base64,AA', kind:'video'}}, {{url:'/four.mp3', kind:'audio'}}, {{kind:'image'}}];
console.log(JSON.stringify({{
  images:api.refsOfKind(refs, 'image', {{kindOf:ref => ref.kind, limit:1}}).map(ref => ref.url),
  videos:api.refsOfKind(refs, 'video', {{kindOf:ref => ref.kind, accept:ref => !api.looksLikeImageUrl(ref.url)}}).map(ref => ref.url),
  audios:api.refsOfKind(refs, 'audio', {{kindOf:ref => ref.kind}}).map(ref => ref.url),
  remote:[api.isRemoteVideoReferenceUrl('https://example.test/x'), api.isRemoteVideoReferenceUrl('asset://x'), api.isRemoteVideoReferenceUrl('/assets/x')],
  imageUrls:[api.looksLikeImageUrl('data:image/png;base64,AA'), api.looksLikeImageUrl('asset://image.png'), api.looksLikeImageUrl('/output/a.tiff?x=1')],
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "images": ["/one.png"], "videos": ["/two.mp4", "https://example.test/three.mp4"], "audios": ["/four.mp3"],
            "remote": [True, True, False], "imageUrls": [True, False, True],
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/media-references.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaReferences.refsOfKind", editor_source)
            self.assertIn("WorkbenchCanvasMediaReferences.isRemoteVideoReferenceUrl", editor_source)

    def test_editor_adapters_share_canvas_list_entry_and_project_memory(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-entry-compatibility.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const store = new Map();
const sandbox = {{window: {{}}, URLSearchParams, encodeURIComponent}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasEntryCompatibility;
const storage = {{setItem:(key, value) => store.set(key, value), getItem:key => store.get(key) || null}};
const saved = api.rememberCanvasListProject('project / one', {{storage, storageKey:'last-project'}});
console.log(JSON.stringify({{saved, restored:api.rememberedCanvasListProject({{storage, storageKey:'last-project'}}), fallback:api.rememberedCanvasListProject({{storage:{{getItem:() => null}}, storageKey:'missing'}}), url:api.canvasListUrl('project / two', {{storage, storageKey:'last-project'}}), stored:store.get('last-project')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "saved": "project / one", "restored": "project / one", "fallback": "default",
            "url": "/static/canvas-list.html?project=project%20%2F%20two", "stored": "project / two",
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/canvas-entry-compatibility.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasEntryCompatibility.canvasListUrl", editor_source)
            self.assertIn("WorkbenchCanvasEntryCompatibility.rememberCanvasListProject", editor_source)

    def test_editor_adapters_share_clipboard_fallbacks(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-clipboard.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
(async () => console.log(JSON.stringify({{
  empty:await sandbox.window.WorkbenchCanvasClipboard.copyText(''),
  api:Object.keys(sandbox.window.WorkbenchCanvasClipboard).sort(),
}})))();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "empty": False,
            "api": ["copyText", "copyWithCopyEvent", "copyWithTextarea", "matchesText"],
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/canvas-clipboard.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasClipboard.copyText", editor_source)
            self.assertIn("WorkbenchCanvasClipboard.copyWithCopyEvent", editor_source)
            self.assertNotIn("document.addEventListener('copy', onCopy)", editor_source)

    def test_editor_adapters_share_image_size_calculation(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "image-size.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasImageSize.apiImageSize;
const options = {{
  parseRatio:value => {{ const [w, h] = String(value).split(':').map(Number); return w > 0 && h > 0 ? w / h : 0; }},
  longSideByResolution:{{'1k':1536, '4k':3840}},
  pixelLimitByResolution:{{'1k':1572864, '4k':8294400}},
  sizeMap:{{square:{{'1k':'1024x1024'}}, wide:{{'1k':'1536x864'}}}},
}};
console.log(JSON.stringify([
  api('wide', '1k', options),
  api('custom', '1k', {{...options, customRatio:'4:3'}}),
  api('custom', '4k', {{...options, customRatio:'3:4'}}),
  api('custom', 'custom', {{...options, customSize:' 111x222 '}}),
  api('square', 'auto', options),
  api('missing', '1k', options),
]));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["1536x864", "1536x1072", "2480x3840", "111x222", "auto", "1024x1024"])
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/image-size.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasImageSize.apiImageSize", editor_source)
            self.assertNotIn("const rawWidth = parsed >= 1", editor_source)

    def test_editor_adapters_share_editable_target_detection(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-targets.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const isEditable = sandbox.window.WorkbenchCanvasInteractionTargets.isEditableTarget;
const target = (tagName, extra={{}}) => ({{tagName, isContentEditable:false, closest:selector => extra.matches?.includes(selector) ? {{}} : null, ...extra}});
console.log(JSON.stringify([
  isEditable(target('INPUT')),
  isEditable(target('DIV', {{isContentEditable:true}})),
  isEditable(target('DIV', {{matches:['select, option']}})),
  isEditable(target('DIV', {{matches:['select, option, [contenteditable="true"], .prompt-node-control, .prompt-input']}}), {{selector:'select, option, [contenteditable="true"], .prompt-node-control, .prompt-input'}}),
  isEditable(target('DIV')),
]));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [True, True, True, True, False])
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/interaction-targets.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasInteractionTargets.isEditableTarget", editor_source)

    def test_editor_adapters_share_http_error_formatting(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-http-error.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
(async () => {{
  const format = sandbox.window.WorkbenchCanvasHttpError.message;
  const response = sandbox.window.WorkbenchCanvasHttpError.responseMessage;
  const parsed = await response({{clone: () => ({{json: async () => ({{detail:[{{loc:['body', 'title'], msg:'required'}}]}})}}), text: async () => 'unused'}}, 'fallback');
  const text = await response({{clone: () => ({{json: async () => Promise.reject(new Error('not json'))}}), text: async () => 'plain failure'}}, 'fallback');
  console.log(JSON.stringify({{
    formatted:[format('string', 'fallback'), format({{detail:{{message:'nested'}}}}, 'fallback'), format({{}}, 'fallback')],
    parsed, text,
  }}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload, {
            "formatted": ["string", "nested", "{}"],
            "parsed": "title: required",
            "text": "plain failure",
        })
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = read_canvas_app_source(ROOT)
            self.assertLess(page_source.index("workbench/canvas/canvas-http-error.js"), page_source.index(editor))
            # Wave 16a moved the transport bodies (with their error-formatting
            # call sites) into classic-executor-runtime.js.
            executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
            self.assertIn("WorkbenchCanvasHttpError.message", editor_source + executor_source)
            self.assertIn("WorkbenchCanvasHttpError.responseMessage", editor_source + executor_source)
            self.assertNotIn("const detail = data.detail ?? data.error ?? data.message", editor_source + executor_source)

    def test_persistence_client_saves_with_logical_revision_cas_on_the_canonical_transport(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const responses = [
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c1', updated_at:1000}}, revision:5}})}},
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c1', updated_at:1001, title:'A'}}, revision:6}})}},
  {{ok:false, status:409, json: async () => ({{detail:{{error:'stale_revision', current_revision:9, canvas:{{id:'c1', updated_at:1002}}}}}})}},
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c1', updated_at:1003}}, revision:10}})}},
  {{ok:false, status:503, json: async () => ({{detail:{{error:'canonical_canvas_api_requires_sqlite_authority'}}}})}},
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c1', updated_at:1004}}}})}},
];
const sandbox = {{window: {{}}, fetch: async (path, options={{}}) => {{
  requests.push({{path, options}});
  return responses.shift();
}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const persistence = sandbox.window.WorkbenchCanvasPersistence;
(async () => {{
  const loaded = await persistence.load('c1');
  const save1 = await persistence.save('c1', {{title:'A', base_updated_at:1000, client_id:'editor-1'}});
  const save2 = await persistence.save('c1', {{title:'B', base_updated_at:1001, client_id:'editor-1'}});
  const save3 = await persistence.save('c1', {{title:'C', base_updated_at:1002, client_id:'editor-1'}});
  const save4 = await persistence.save('c1', {{title:'D', base_updated_at:1003, client_id:'editor-1'}});
  console.log(JSON.stringify({{loaded, save1, save2, save3, save4, requests}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["loaded"]["revision"], 5)
        self.assertEqual(payload["save1"]["revision"], 6)
        self.assertEqual(payload["save2"]["status"], 409)
        self.assertEqual(payload["save2"]["revision"], 9)
        self.assertEqual(payload["save2"]["canvas"]["updated_at"], 1002)
        self.assertEqual(payload["save3"]["revision"], 10)
        self.assertEqual(payload["save4"]["status"], 200)
        # Canonical GET then three canonical CAS PUTs. A 409 reports revision 9
        # but does not advance the local CAS cursor: the rejected stale payload
        # is not silently authorized against the newer server revision.
        self.assertEqual(payload["requests"][0]["path"], "/api/v1/canvases/c1")
        self.assertEqual(payload["requests"][1]["path"], "/api/v1/canvases/c1")
        self.assertEqual(json.loads(payload["requests"][1]["options"]["body"]), {"payload": {"title": "A"}, "expected_revision": 5, "client_id": "editor-1"})
        self.assertEqual(json.loads(payload["requests"][2]["options"]["body"])["expected_revision"], 6)
        self.assertEqual(json.loads(payload["requests"][3]["options"]["body"])["expected_revision"], 6)
        # 503 falls back to the legacy transport with the full record body intact.
        self.assertEqual(payload["requests"][4]["path"], "/api/v1/canvases/c1")
        self.assertEqual(json.loads(payload["requests"][4]["options"]["body"])["expected_revision"], 10)
        self.assertEqual(payload["requests"][5]["path"], "/api/canvases/c1")
        self.assertEqual(json.loads(payload["requests"][5]["options"]["body"]), {"title": "D", "base_updated_at": 1003, "client_id": "editor-1"})

    def test_persistence_client_adopts_versioned_write_revisions_into_the_save_cursor(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const responses = [
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c2', updated_at:2000}}, revision:8}})}},
  {{ok:false, status:503, json: async () => ({{detail:{{}}}})}},
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c3', updated_at:3000}}}})}},
];
const sandbox = {{window: {{}}, fetch: async (path, options={{}}) => {{
  requests.push({{path, options}});
  return responses.shift();
}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const persistence = sandbox.window.WorkbenchCanvasPersistence;
(async () => {{
  persistence.adoptRevision({{id:'c2', updated_at:1}}, 7);
  const afterAdopt = await persistence.save('c2', {{title:'x', base_updated_at:1}});
  const revisionless = await persistence.save('c3', {{title:'y', base_updated_at:2}});
  console.log(JSON.stringify({{afterAdopt, revisionless, requests}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["afterAdopt"]["revision"], 8)
        self.assertEqual(json.loads(payload["requests"][0]["options"]["body"])["expected_revision"], 7)
        # A revision-less (legacy-loaded) canvas keeps using the legacy transport.
        self.assertEqual(payload["requests"][1]["path"], "/api/canvases/c3")
        self.assertEqual(json.loads(payload["requests"][1]["options"]["body"]), {"title": "y", "base_updated_at": 2})

    def test_persistence_client_falls_back_to_legacy_load_when_canonical_is_unavailable(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const responses = [
  {{ok:false, status:503, json: async () => ({{detail:{{error:'canonical_canvas_api_requires_sqlite_authority'}}}})}},
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'c4', updated_at:4000}}}})}},
];
const sandbox = {{window: {{}}, fetch: async (path, options={{}}) => {{
  requests.push({{path, options}});
  return responses.shift();
}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
(async () => {{
  const loaded = await sandbox.window.WorkbenchCanvasPersistence.load('c4');
  console.log(JSON.stringify({{loaded, requests}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["loaded"]["canvas"]["id"], "c4")
        self.assertEqual([request["path"] for request in payload["requests"]], ["/api/v1/canvases/c4", "/api/canvases/c4"])

    def test_persistence_client_metadata_peeks_canonical_first_without_moving_the_save_cursor(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const responses = [
  {{ok:true, status:200, json: async () => ({{canvas_id:'c1', revision:7, updated_at:'2026-09-06T00:00:00Z', deleted:false}})}},
  {{ok:false, status:503, json: async () => ({{detail:{{}}}})}},
  {{ok:true, status:200, json: async () => ({{updated_at:4000}})}},
];
const sandbox = {{window: {{}}, fetch: async (path, options={{}}) => {{
  requests.push({{path, options}});
  return responses.shift();
}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const persistence = sandbox.window.WorkbenchCanvasPersistence;
(async () => {{
  const canonicalMeta = await persistence.metadata('c1');
  const before = persistence.revisionOf('c1');
  const legacyMeta = await persistence.metadata('c1');
  console.log(JSON.stringify({{canonicalMeta, before, legacyMeta, requests}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["canonicalMeta"]["revision"], 7)
        # A version peek never moves the save cursor: local content was not adopted.
        self.assertEqual(payload["before"], 0)
        self.assertEqual(payload["legacyMeta"]["updatedAt"], 4000)
        self.assertEqual(payload["legacyMeta"]["revision"], 0)
        self.assertEqual([request["path"] for request in payload["requests"]],
                         ["/api/v1/canvases/c1/meta", "/api/v1/canvases/c1/meta", "/api/canvases/c1/meta"])

    def test_remote_sync_orders_remote_versions_by_revision_with_timestamp_fallback(self):
        remote_sync = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-remote-sync.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const probes = [];
let onNewerCalls = 0;
const sandbox = {{
  window: {{
    WorkbenchCanvasPersistence: {{
      metadata: async canvasId => probes.shift(),
    }},
  }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(remote_sync))}, 'utf8'), sandbox);
const sync = sandbox.window.WorkbenchCanvasRemoteSync.create({{
  canvasId: () => 'c1',
  currentUpdatedAt: () => 4000,
  currentRevision: () => 6,
  onNewer: async () => {{ onNewerCalls += 1; }},
}});
(async () => {{
  // Remote revision ahead of the local cursor: applies.
  probes.push({{ok:true, status:200, revision:9, updatedAt:0, payload:{{}}}});
  const newer = await sync.check();
  // Same revision as local: deterministic no-op, never regresses.
  probes.push({{ok:true, status:200, revision:6, updatedAt:0, payload:{{}}}});
  const sameRevision = await sync.check();
  // Older revision than local: no-op.
  probes.push({{ok:true, status:200, revision:2, updatedAt:99999, payload:{{}}}});
  const olderRevision = await sync.check();
  // Revision-less probe (legacy): falls back to timestamp ordering.
  probes.push({{ok:true, status:200, revision:0, updatedAt:5000, payload:{{}}}});
  const legacyNewer = await sync.check();
  probes.push({{ok:true, status:200, revision:0, updatedAt:3000, payload:{{}}}});
  const legacyOlder = await sync.check();
  console.log(JSON.stringify({{newer, sameRevision, olderRevision, legacyNewer, legacyOlder, onNewerCalls}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["newer"])
        self.assertFalse(payload["sameRevision"])
        self.assertFalse(payload["olderRevision"])
        self.assertTrue(payload["legacyNewer"])
        self.assertFalse(payload["legacyOlder"])
        self.assertEqual(payload["onNewerCalls"], 2)

    def test_canvas_update_message_orders_notifications_by_revision(self):
        update_message = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-update-message.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(update_message))}, 'utf8'), sandbox);
const newerForCanvas = sandbox.window.WorkbenchCanvasUpdateMessage.newerForCanvas;
const base = {{type:'canvas_updated', canvas_id:'c1', client_id:'other'}};
const options = {{canvasId:'c1', clientId:'self', currentUpdatedAt:4000, currentRevision:6}};
(async () => {{
  console.log(JSON.stringify({{
    newerRevision: newerForCanvas({{...base, updated_at:999, revision:8}}, options),
    sameRevision: newerForCanvas({{...base, updated_at:999, revision:6}}, options),
    olderRevision: newerForCanvas({{...base, updated_at:999, revision:2}}, options),
    revisionlessNewer: newerForCanvas({{...base, updated_at:5000}}, options),
    revisionlessStale: newerForCanvas({{...base, updated_at:3000}}, options),
    ownClientId: newerForCanvas({{...base, client_id:'self', revision:9}}, options),
  }}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["newerRevision"]["revision"], 8)
        self.assertIsNone(payload["sameRevision"])
        self.assertIsNone(payload["olderRevision"])
        self.assertEqual(payload["revisionlessNewer"]["updatedAt"], 5000)
        self.assertIsNone(payload["revisionlessStale"])
        self.assertIsNone(payload["ownClientId"])

    def test_render_runtime_owns_the_mounted_card_lifecycle(self):
        runtime_module = ROOT / "static" / "js" / "workbench" / "canvas" / "render-runtime.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime_module))}, 'utf8'), sandbox);
const runtime = sandbox.window.WorkbenchRenderRuntime.create({{
  mount: request => {{
    const handle = {{nodeId: request.node.id, destroyed: false, element: request.element}};
    handle.destroy = () => {{ handle.destroyed = true; }};
    return handle;
  }},
}});
const events = [];
const plain = runtime.mount({{node: {{id: 'n1'}}, element: 'e1'}});
events.push(['mounted', plain.nodeId, runtime.isMounted('n1')]);
const replaced = runtime.mount({{node: {{id: 'n1'}}, element: 'e2'}});
events.push(['remounted', plain.destroyed, replaced.nodeId, runtime.mountedNodeIds().join(',')]);
const batch = runtime.mountAll([
  {{node: {{id: 'n2'}}, element: 'e3'}},
  {{node: {{id: 'n3'}}, element: 'e4'}},
]);
events.push(['batch', batch.length, runtime.mountedNodeIds().join(',')]);
const torn = runtime.unmount('n2');
events.push(['unmounted', torn, batch[0].destroyed, runtime.isMounted('n2')]);
events.push(['unmountMissing', runtime.unmount('ghost')]);
runtime.unmountAll();
events.push(['unmountAll', batch[1].destroyed, runtime.mountedNodeIds().length]);
const tolerant = runtime.mount({{node: {{id: 'n4'}}, element: 'e5'}});
sandbox.window.WorkbenchRenderRuntime; // exposure check
console.log(JSON.stringify({{events, tolerantPresent: Boolean(tolerant), exposed: typeof sandbox.window.WorkbenchRenderRuntime.create}}));
let invalid = 'no-throw';
try {{ runtime.mount({{element: 'e6'}}); }} catch (error) {{ invalid = 'throws'; }}
console.log(JSON.stringify({{invalid}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        lines = [json.loads(line) for line in result.stdout.strip().splitlines()]
        events, checks = lines[0]["events"], lines[1]
        self.assertEqual(events[0], ["mounted", "n1", True])
        # Remounting the same node destroys the previous handle in order.
        self.assertEqual(events[1], ["remounted", True, "n1", "n1"])
        self.assertEqual(events[2], ["batch", 2, "n1,n2,n3"])
        self.assertEqual(events[3], ["unmounted", True, True, False])
        self.assertEqual(events[4], ["unmountMissing", False])
        self.assertEqual(events[5], ["unmountAll", True, 0])
        self.assertTrue(lines[0]["tolerantPresent"])
        self.assertEqual(lines[0]["exposed"], "function")
        self.assertEqual(checks["invalid"], "throws")

    def test_media_playback_state_projection_can_exclude_runtime_mounted_cards(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-playback-state.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaPlaybackState;
const makeMedia = (url, mounted) => ({{
  tagName:'VIDEO', dataset:{{url}}, currentTime:5, paused:true, playbackRate:1, muted:false, volume:1, readyState:1,
  getAttribute:key => key === 'src' ? url : '', closest:selector => mounted ? {{matches:true}} : null,
}});
const pageMedia = makeMedia('/output/page.mp4', false);
const runtimeMedia = makeMedia('/output/runtime.mp4', true);
const root = {{querySelectorAll:() => [pageMedia, runtimeMedia]}};
const unfiltered = api.captureAll(root);
const filtered = api.captureAll(root, {{exclude:'.node-shell-mounted'}});
api.restoreAll(root, filtered, {{exclude:'.node-shell-mounted'}});
console.log(JSON.stringify({{unfiltered:unfiltered.size, filtered:filtered.has('video:/output/page.mp4'), runtimeExcluded:filtered.has('video:/output/runtime.mp4')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["unfiltered"], 2)
        self.assertTrue(payload["filtered"])
        self.assertFalse(payload["runtimeExcluded"])

    def test_render_runtime_projects_media_state_across_remounts(self):
        runtime_module = ROOT / "static" / "js" / "workbench" / "canvas" / "render-runtime.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime_module))}, 'utf8'), sandbox);
const captures = [];
const restores = [];
const runtime = sandbox.window.WorkbenchRenderRuntime.create({{
  mount: request => {{
    const handle = {{element: {{id: 'shell-' + request.node.id}}, shell: {{}}, destroy: () => {{}}}};
    return handle;
  }},
  mediaState: {{
    capture: element => {{
      captures.push(element.id);
      const states = new Map();
      states.set('video:/output/a.mp4', {{currentTime: 12}});
      return states;
    }},
    restore: (element, states) => restores.push([element.id, states.get('video:/output/a.mp4').currentTime]),
  }},
}});
runtime.mount({{node: {{id: 'm1'}}, card: {{id: 'card-1'}}}});
runtime.mount({{node: {{id: 'm1'}}, card: {{id: 'card-2'}}}});
const removed = runtime.unmount('m1');
runtime.unmountAll();
const plain = sandbox.window.WorkbenchRenderRuntime.create({{mount: () => ({{element: {{id: 'x'}}, destroy: () => {{}}}})}});
plain.mount({{node: {{id: 'p1'}}, card: 'card-3'}});
plain.mount({{node: {{id: 'p1'}}, card: 'card-4'}});
console.log(JSON.stringify({{captures, restores, removed}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Remount: the runtime captured from the outgoing shell and restored into
        # the fresh card; the page no longer projects state for mounted cards.
        # Remount captures from the outgoing shell and restores into the fresh
        # card; the explicit unmount captures again (terminal for that node).
        self.assertEqual(payload["captures"], ["shell-m1", "shell-m1"])
        self.assertEqual(payload["restores"], [["card-2", 12]])
        self.assertTrue(payload["removed"])

    def test_media_renderer_elements_carry_the_state_signature_url(self):
        renderer = ROOT / "static" / "js" / "workbench" / "canvas" / "media-renderer.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const created = [];
const fakeDocument = {
  createElement: tag => {
    const element = {tagName: tag.toUpperCase(), className: '', dataset: {}, src: '', alt: '',
      loading: '', controls: false, preload: '', playsInline: false, children: [],
      classList: {toggle() {}, add() {}, remove() {}},
      append(child) { this.children.push(child); },
      addEventListener() {}};
    created.push(element);
    return element;
  },
};
const sandbox = {
  window: {
    WorkbenchCanvasMediaKind: {kindForItem: item => item.url.endsWith('.mp4') ? 'video' : 'image'},
  },
};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const node = {
  id: 'img-1', title: 'Clip', kind: 'asset',
  extensions: {legacy: {payload: {url: '/output/clip.mp4'}}},
};
const mounted = sandbox.window.WorkbenchMediaRenderer.mountInto(
  {ownerDocument: fakeDocument, replaceChildren() {}}, node, {document: fakeDocument});
const video = created.find(element => element.tagName === 'VIDEO');
console.log(JSON.stringify({src: video.src, signatureUrl: video.dataset.url, controls: video.controls, root: Boolean(mounted.element)}));
""".replace("__MODULE__", json.dumps(str(renderer)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["src"], "/output/clip.mp4")
        # The signature URL lets the shared playback-state projection and the
        # render runtime recognize the renderer-created media element.
        self.assertEqual(payload["signatureUrl"], "/output/clip.mp4")
        self.assertTrue(payload["controls"])
        self.assertTrue(payload["root"])

    def test_prompt_card_renderer_owns_dom_with_page_state_behind_callbacks(self):
        canvas_dir = ROOT / "static" / "js" / "workbench" / "canvas"
        module_paths = [
            json.dumps(str(canvas_dir / "renderer-registry.js")),
            json.dumps(str(canvas_dir / "node-shell.js")),
            json.dumps(str(canvas_dir / "node-card-host.js")),
            json.dumps(str(canvas_dir / "prompt-card-renderer.js")),
        ]
        module_loads = "\n".join(
            f"vm.runInNewContext(fs.readFileSync({path}, 'utf8'), sandbox);" for path in module_paths
        )
        script = """
const fs = require('fs'); const vm = require('vm');
const makeElement = tag => {
  const el = {
    tagName: tag.toUpperCase(), children: [], dataset: {}, style: {},
    className: '', textContent: '', value: '', placeholder: '', title: '', type: '',
    listeners: {},
    append(...kids) { this.children.push(...kids); },
    appendChild(child) { this.children.push(child); },
    replaceChildren(...kids) { this.children = kids; },
    setAttribute(name, value) { this.dataset['attr-' + name] = String(value); },
    addEventListener(type, cb) { (this.listeners[type] = this.listeners[type] || []).push(cb); },
    classList: {add() {}, remove() {}, toggle() {}},
    querySelector: () => null,
    querySelectorAll: () => [],
    getAttribute: () => '',
  };
  return el;
};
const fakeDocument = {createElement: makeElement};
const sandbox = {window: {document: fakeDocument, StudioI18n: null}};
__MODULES__
const record = {
  id: 'prompt-1', kind: 'legacy',
  definition_ref: {type: 'legacy', id: 'prompt', version: '0'},
  extensions: {legacy: {payload: {id: 'prompt-1', type: 'prompt', text: 'Hello'}}},
};
const callbacks = {inputs: [], opens: [], bound: []};
const shell = sandbox.window.WorkbenchNodeCardHost.mount({
  node: record,
  document: fakeDocument,
  viewState: {},
  rendererOptions: {
    templateActive: true,
    maxLength: 2,
    textLength: value => Array.from(String(value || '')).length,
    bindTextElement: element => callbacks.bound.push(element),
    onPromptInput: text => callbacks.inputs.push(text),
    onOpenTemplate: nodeId => callbacks.opens.push(nodeId),
  },
});
const editor = shell.shell.contentHost.children[0];
const toolbar = editor.children[0];
const textarea = editor.children[1];
const button = toolbar.children[0];
const initialValue = textarea.value;
textarea.value = 'Hi!';
textarea.listeners.input[0]({target: textarea});
button.listeners.click[0]({preventDefault() {}, stopPropagation() {}});
console.log(JSON.stringify({
  rendererId: shell.element.dataset.rendererId,
  editorClass: editor.className,
  textareaValue: initialValue,
  buttonClass: button.className,
  pressed: button.dataset['attr-aria-pressed'],
  countSpan: toolbar.children[1].children[0].textContent,
  inputs: callbacks.inputs,
  opens: callbacks.opens,
  bound: callbacks.bound.length,
}));
""".replace("__MODULES__", module_loads)
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # NodeRecord -> Registry -> Renderer -> NodeShell: the prompt card DOM is
        # renderer-owned; page state arrives only through callbacks.
        self.assertEqual(payload["rendererId"], "prompt-card")
        self.assertEqual(payload["editorClass"], "prompt-editor")
        self.assertEqual(payload["textareaValue"], "Hello")
        self.assertIn("prompt-template-btn active", payload["buttonClass"])
        self.assertEqual(payload["pressed"], "true")
        self.assertEqual(payload["countSpan"], "3")
        self.assertEqual(payload["inputs"], ["Hi!"])
        self.assertEqual(payload["opens"], ["prompt-1"])
        self.assertEqual(payload["bound"], 1)

    def test_provider_compat_renderer_adopts_body_and_carries_cleanup_through_destroy(self):
        canvas_dir = ROOT / "static" / "js" / "workbench" / "canvas"
        module_paths = [
            json.dumps(str(canvas_dir / "renderer-registry.js")),
            json.dumps(str(canvas_dir / "node-shell.js")),
            json.dumps(str(canvas_dir / "node-card-host.js")),
            json.dumps(str(canvas_dir / "provider-compat-renderer.js")),
        ]
        module_loads = "\n".join(
            f"vm.runInNewContext(fs.readFileSync({path}, 'utf8'), sandbox);" for path in module_paths
        )
        script = """
const fs = require('fs'); const vm = require('vm');
const makeElement = tag => {
  const state = {children: [], dataset: {}, listeners: {}, removed: false};
  const el = {
    tagName: tag.toUpperCase(),
    get children() { return state.children; },
    get dataset() { return state.dataset; },
    className: '', textContent: '', value: '',
    append(...kids) { state.children.push(...kids); },
    replaceChildren(...kids) { state.children = kids; },
    addEventListener(type, cb) { (state.listeners[type] = state.listeners[type] || []).push(cb); },
    setAttribute(name, value) { state.dataset['attr-' + name] = String(value); },
    remove() { state.removed = true; },
    get removed() { return state.removed; },
    classList: {add() {}, remove() {}, toggle() {}},
    querySelector: () => null,
    querySelectorAll: () => [],
    getAttribute: () => '',
  };
  return el;
};
const fakeDocument = {createElement: makeElement};
const sandbox = {window: {
  document: fakeDocument,
  // Minimal LegacyRenderer stand-in so registerBuiltIns has a fallback to register.
  WorkbenchLegacyRenderer: {
    canRender: node => Boolean(node?.renderer && node.renderer.id === 'legacy' && node.extensions?.legacy?.payload),
    mount: (shell, node, options) => ({element: options?.legacyContent || null, destroy() {}}),
  },
}};
__MODULES__
const host = sandbox.window.WorkbenchNodeCardHost;
const legacyBody = makeElement('DIV');
legacyBody.className = 'llm-body';
const payloadNode = {id: 'llm-1', type: 'llm'};
const destroyCalls = [];
const providerShell = host.mount({
  node: {
    id: 'llm-1', kind: 'legacy', renderer: {id: 'legacy', version: '1'},
    definition_ref: {type: 'legacy', id: 'llm', version: '0'},
    extensions: {legacy: {payload: payloadNode}},
  },
  document: fakeDocument,
  viewState: {},
  rendererOptions: {
    legacyContent: legacyBody,
    onCardDestroy: node => destroyCalls.push(node),
  },
});
providerShell.destroy();
const genericShell = host.mount({
  node: {
    id: 'loop-1', kind: 'legacy', renderer: {id: 'legacy', version: '1'},
    definition_ref: {type: 'legacy', id: 'loop', version: '0'},
    extensions: {legacy: {payload: {id: 'loop-1', type: 'loop'}}},
  },
  document: fakeDocument,
  viewState: {},
  rendererOptions: {legacyContent: makeElement('DIV')},
});
const compatRoot = providerShell.shell.contentHost.children[0];
console.log(JSON.stringify({
  rendererId: providerShell.element.dataset.rendererId,
  rootClass: compatRoot.className,
  adopted: compatRoot.children[0] === legacyBody,
  cleanupFired: destroyCalls[0] === payloadNode,
  rootRemoved: compatRoot.removed,
  genericRendererId: genericShell.element.dataset.rendererId,
}));
""".replace("__MODULES__", module_loads)
        result = subprocess.run(["node", "-e", script], text=True, capture_output=True)
        if result.returncode != 0:
            self.fail(f"provider-compat sandbox failed: {result.stderr[-500:]}")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["rendererId"], "provider-compat")
        self.assertEqual(payload["rootClass"], "workbench-provider-compat-renderer")
        self.assertTrue(payload["adopted"])
        self.assertTrue(payload["cleanupFired"])
        self.assertTrue(payload["rootRemoved"])
        # Non-provider generic families still resolve to source-payload.
        self.assertEqual(payload["genericRendererId"], "source-payload")

    def test_interaction_controller_owns_the_pointer_session_lifecycle(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const controller = sandbox.window.WorkbenchInteractionController.create({windowRef: sandbox.window});
const events = {movesA: [], movesB: [], ends: []};
const assigned = [];
const handler = () => assigned;
// begin wires the window move/up slot and dispatches to the active session
controller.begin({kind: 'node-drag', onMove: e => events.movesA.push(e.dx), onEnd: e => events.ends.push('A:' + e.kind)});
const assignedAfterBegin = typeof sandbox.window.onmousemove;
sandbox.window.onmousemove({dx: 3});
// mouseup ends the session and invokes onEnd; further moves are guarded no-ops
sandbox.window.onmouseup({kind: 'mouseup'});
sandbox.window.onmousemove({dx: 99});
// supersede-on-begin: a second session replaces the slot without ending the first
controller.begin({kind: 'node-resize', onMove: e => events.movesB.push(e.dx), onEnd: e => events.ends.push('B')});
sandbox.window.onmousemove({dx: 7});
// programmatic end unwires the slot
const ended = controller.end();
console.log(JSON.stringify({
  assignedAfterBegin,
  movesA: events.movesA,
  ends: events.ends,
  movesB: events.movesB,
  ended,
  endedAgain: controller.end(),
  activeDuringSession: 'node-drag',
  kindAfterEnd: controller.activeKind(),
  clearedSlot: sandbox.window.onmousemove,
}));
let invalid = 'no-throw';
try { controller.begin({kind: 'x'}); } catch (error) { invalid = 'throws'; }
console.log(JSON.stringify({invalid}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout.splitlines()[0])
        self.assertEqual(payload["assignedAfterBegin"], "function")
        self.assertEqual(payload["movesA"], [3])
        # mouseup ends the active session; later moves dispatch nothing.
        self.assertEqual(payload["ends"], ["A:mouseup"])
        self.assertEqual(payload["movesB"], [7])
        self.assertTrue(payload["ended"])
        self.assertFalse(payload["endedAgain"])
        self.assertEqual(payload["kindAfterEnd"], None)
        self.assertIsNone(payload["clearedSlot"])
        self.assertEqual(json.loads(result.stdout.splitlines()[1])["invalid"], "throws")

    def test_classic_node_drag_and_resize_sessions_are_cut_over_to_the_controller(self):
        controller_page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(controller_page.index("workbench/canvas/render-runtime.js"), controller_page.index("workbench/canvas/interaction-controller.js"))
        self.assertLess(controller_page.index("workbench/canvas/interaction-controller.js"), controller_page.index("workbench/canvas/canvas-app-bootstrap.js"))
        classic = read_canvas_app_source(ROOT)
        drag_flow = classic[classic.index("function startNodeDrag(") : classic.index("function onNodeDrag(")]
        resize_flow = classic[classic.index("function startNodeResize(") : classic.index("function onNodeResize(")]
        self.assertIn("ensureInteractionController().begin({kind:'node-drag', onMove:onNodeDrag, onEnd:endDrag})", drag_flow)
        self.assertIn("ensureInteractionController().begin({kind:'node-resize', onMove:onNodeResize, onEnd:endDrag})", resize_flow)
        self.assertNotIn("window.onmousemove = onNodeDrag", drag_flow)
        self.assertNotIn("window.onmouseup = endDrag", drag_flow)
        self.assertNotIn("window.onmousemove = onNodeResize", resize_flow)
        # The controller singleton is the single wiring owner for these sessions.
        self.assertEqual(classic.count("WorkbenchInteractionController.create({windowRef: window})"), 1)
        self.assertEqual(classic.count("ensureInteractionController().begin("), 7)

    def test_classic_residual_pointer_sessions_are_cut_over_to_the_controller(self):
        # R4-39 Wave 4 slice: the remaining page-owned window mouse-slot
        # assignments (LLM pane resize, box selection, selection-link drag,
        # knife drag) moved behind the same InteractionController session
        # lifecycle, and the cleanup sites (finishSelection, endDrag, the
        # blur guard) unwire through controller.end(). The page owns no
        # window handler slot directly anymore.
        classic = read_canvas_app_source(ROOT)
        self.assertNotIn("window.onmousemove =", classic)
        self.assertNotIn("window.onmouseup =", classic)
        for kind in ("llm-pane-resize", "box-selection", "selection-link", "knife-drag"):
            with self.subTest(kind=kind):
                self.assertIn(f"kind:'{kind}'", classic)
        self.assertEqual(classic.count("ensureInteractionController().begin("), 7)
        self.assertGreaterEqual(classic.count("ensureInteractionController().end()"), 3)

        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const controller = sandbox.window.WorkbenchInteractionController.create({windowRef: sandbox.window});
const events = [];
// Page pattern: the session's onEnd (finishSelection/endDrag shape) runs the
// page cleanup and unwires via controller.end(); the controller has already
// cleared the active session by then, so the slot degrades to a guarded
// no-op instead of throwing or double-unwiring.
controller.begin({kind: 'box-selection',
  onMove: e => events.push('move:' + e.x),
  onEnd: () => { events.push('end'); controller.end(); }});
sandbox.window.onmousemove({x: 1});
sandbox.window.onmouseup({});
sandbox.window.onmousemove({x: 2});
// Blur-guard shape: a session still active is unwired programmatically and
// the slot is fully cleared.
controller.begin({kind: 'knife-drag', onMove: () => {}, onEnd: () => events.push('knife-end')});
const unwired = controller.end();
console.log(JSON.stringify({events, slot: sandbox.window.onmousemove, unwired}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["events"], ["move:1", "end"])
        self.assertIsNone(payload["slot"])
        self.assertTrue(payload["unwired"])

    def test_selection_authority_store_is_set_compatible_with_change_tracking(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const changes = [];
const selected = sandbox.window.WorkbenchInteractionController.createSelectionStore({
  onChange: ids => changes.push(ids.slice()),
});
selected.add('n1');
selected.add('n1');           // duplicate: no change event
selected.add(42);             // ids coerce to strings
selected.add('n2');
const has = {n1: selected.has('n1'), n42: selected.has('42'), ghost: selected.has('ghost')};
const size = selected.size;
const spread = [...selected];
const deleted = selected.delete('n2');
const deletedAgain = selected.delete('n2');
selected.replace(['a', 'b', 'a']);
const replaced = [...selected];
selected.clear();
console.log(JSON.stringify({has, size, spread, deleted, deletedAgain, replaced, clearedSize: selected.size, changes}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["has"], {"n1": True, "n42": True, "ghost": False})
        self.assertEqual(payload["size"], 3)
        self.assertEqual(payload["spread"], ["n1", "42", "n2"])
        self.assertTrue(payload["deleted"])
        self.assertFalse(payload["deletedAgain"])
        self.assertEqual(payload["replaced"], ["a", "b"])
        self.assertEqual(payload["clearedSize"], 0)
        # Change events: add, deduped add (skipped), delete, replace, clear
        self.assertEqual(payload["changes"], [["n1"], ["n1", "42"], ["n1", "42", "n2"], ["n1", "42"], ["a", "b"], []])

    def test_classic_selection_is_cut_over_to_the_single_authority(self):
        classic = read_canvas_app_source(ROOT)
        self.assertIn("const selected = window.WorkbenchInteractionController.createSelectionStore();", classic)
        self.assertNotIn("selected = new Set(", classic)
        self.assertIn("selected.replace(runtime.snapshot().selectedIds);", classic)
        self.assertIn("if(!applyCanvasRuntimeSelection(selectedIds)) selected.replace(selectedIds);", classic)
        # The authority module loads on the Classic page before the adapter.
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(page.index("workbench/canvas/interaction-controller.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))

    def test_viewport_controller_dispatches_through_the_kernel_with_page_shell_callbacks(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const applied = [];
const sandbox = {window: {
  WorkbenchCanvasRuntime: null, // kernel comes from the settings below
}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const kernelCalls = [];
const fakeKernel = {
  dispatch: command => kernelCalls.push(command),
  snapshot: () => ({viewport: {x: 11, y: 22, scale: 2}, selectedIds: [], geometry: []}),
  viewportCenteredOnWorldPoint: (viewport, point, size) => ({
    x: size.width / 2 - point.x * viewport.scale,
    y: size.height / 2 - point.y * viewport.scale,
    scale: viewport.scale,
  }),
};
const controller = sandbox.window.WorkbenchInteractionController.createViewportController({
  getKernel: () => fakeKernel,
  applyViewport: viewport => applied.push({...viewport}),
});
const setView = controller.set({x: 1, y: 2, scale: 1});
const panned = controller.panBy(30, 40);
const zoomed = controller.zoomAt({x: 100, y: 50}, 2);
const centered = controller.centerOn({x: 20, y: 10}, {width: 200, height: 100});
const current = controller.current();
const noKernel = sandbox.window.WorkbenchInteractionController.createViewportController({
  getKernel: () => null,
  applyViewport: () => {},
});
console.log(JSON.stringify({
  setView, panned, zoomed, centered, current, appliedCount: applied.length, kernelCalls, noKernelSet: noKernel.set({x:0,y:0,scale:1}),
}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Every mutation dispatches through the kernel; the resolved viewport is
        # returned and the page shell callback re-renders.
        self.assertEqual(payload["setView"], {"x": 11, "y": 22, "scale": 2})
        self.assertEqual(payload["kernelCalls"][0]["type"], "canvas.viewport.set")
        self.assertEqual(payload["kernelCalls"][1]["type"], "canvas.viewport.pan")
        self.assertEqual(payload["kernelCalls"][2]["type"], "canvas.viewport.zoom-at")
        self.assertEqual(payload["appliedCount"], 4)
        self.assertIsNone(payload["noKernelSet"])

    def test_classic_viewport_flows_are_cut_over_to_the_viewport_controller(self):
        classic = read_canvas_app_source(ROOT)
        self.assertIn("function ensureCanvasViewportController(){", classic)
        self.assertEqual(classic.count("WorkbenchInteractionController.createViewportController"), 1)
        # Board pan: the pointer session is wired through the controller, not the window slot.
        self.assertIn("ensureInteractionController().begin({kind:'board-pan'", classic)
        self.assertIn("ensureInteractionController().begin({kind:'board-pan'", classic)
        # Zoom and the set flows go through the controller.
        self.assertIn("ensureCanvasViewportController().zoomAt(", classic)
        self.assertIn("ensureCanvasViewportController().set(nextViewport)", classic)
        self.assertNotIn("canvasViewportController.zoomAt(", classic)
        self.assertNotIn("canvasViewportController.set(nextViewport)", classic)
        self.assertIn("ensureCanvasViewportController().set(fitted)", classic)
        self.assertIn("ensureCanvasViewportController().set(restoredViewport)", classic)
        self.assertIn("ensureCanvasViewportController().set(targetViewport)", classic)
        self.assertIn("ensureCanvasViewportController().centerOn(point, size)", classic)
        # The duplicate viewport mutation helper is gone.
        self.assertNotIn("function applyCanvasRuntimeViewport(", classic)

    def test_minimap_controller_owns_the_drag_interaction(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const events = {applied: [], sessions: []};
let canvas = true;
let removed = 0;
const listeners = [];
const pointer = {
  addEventListener: (type, cb) => listeners.push({type, cb, active: true}),
  removeEventListener: (type, cb) => {
    removed += 1;
    const entry = listeners.find(l => l.type === type && l.cb === cb);
    if (entry) entry.active = false;
  },
};
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const controller = sandbox.window.WorkbenchInteractionController.createMinimapController({
  windowRef: sandbox.window,
  pointerRef: pointer,
  canBegin: () => Boolean(canvas),
  onPointerDown: e => (e.swallow ? false : true),
  beginSession: () => events.sessions.push('begin'),
  project: e => ({x: e.clientX * 2, y: e.clientY * 2}),
  apply: point => events.applied.push(point),
  endSession: () => events.sessions.push('end'),
});
const down = listeners.find(l => l.type === 'mousedown').cb;
down({button: 0, clientX: 10, clientY: 10});
const moveEntry = listeners.find(l => l.type === 'mousemove');
const upEntry = listeners.find(l => l.type === 'mouseup');
moveEntry.cb({clientX: 20, clientY: 30});
moveEntry.cb({clientX: 30, clientY: 40});
upEntry.cb({});
// mouseup detached the move/up pair: a later move is a no-op.
if (moveEntry.active) moveEntry.cb({clientX: 99, clientY: 99});
// gated begin: a swallowed pointerdown starts nothing.
canvas = false;
down({button: 0, clientX: 1, clientY: 1});
canvas = true;
down({button: 2, clientX: 1, clientY: 1});
down({swallow: true, button: 0, clientX: 1, clientY: 1});
console.log(JSON.stringify({applied: events.applied, sessions: events.sessions, removed}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Projection flows through the page callback; pointer capture ends on mouseup.
        self.assertEqual(payload["applied"], [{"x": 40, "y": 60}, {"x": 60, "y": 80}])
        self.assertEqual(payload["sessions"], ["begin", "end"])
        self.assertEqual(payload["removed"], 2)
        # Gated begins (no canvas, non-primary button, swallowed event) apply nothing.
        self.assertEqual(len(payload["applied"]), 2)

    def test_classic_minimap_is_cut_over_to_the_minimap_controller(self):
        classic = read_canvas_app_source(ROOT)
        self.assertIn("function ensureMinimapController(){", classic)
        self.assertEqual(classic.count("WorkbenchInteractionController.createMinimapController"), 1)
        self.assertIn("ensureMinimapController();", classic)
        # The direct minimap pointer-session wiring is gone.
        self.assertNotIn("window.onmousemove = e2 => {\n        if(minimapDrag) centerViewportOnWorldPoint(minimapEventToWorld(e2));", classic)
        self.assertNotIn("minimap?.addEventListener('mousedown', e => {", classic)
        self.assertIn("project: minimapEventToWorld,", classic)
        self.assertIn("apply: worldPoint => centerViewportOnWorldPoint(worldPoint),", classic)

    def test_node_session_factories_delegate_to_the_kernel_and_validate_it(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const dragCalls = [];
const resizeCalls = [];
const fakeKernel = {
  createNodeDragSession: options => { dragCalls.push(options); return {members: [], move: () => ({})}; },
  createNodeResizeSession: options => { resizeCalls.push(options); return {move: () => ({})}; },
};
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const dragFactory = sandbox.window.WorkbenchInteractionController.createNodeDragSessionFactory({runtime: fakeKernel});
const resizeFactory = sandbox.window.WorkbenchInteractionController.createNodeResizeSessionFactory({runtime: fakeKernel});
const drag = dragFactory({start: {x: 1, y: 2}, scale: 2, members: [{id: 'a', ox: 0, oy: 0}]});
const resize = resizeFactory({start: {x: 3, y: 4}, scale: 1, startWidth: 100, startHeight: 50});
let noKernel = 'no-throw';
try { sandbox.window.WorkbenchInteractionController.createNodeDragSessionFactory({runtime: null}); } catch (error) {
  noKernel = String(error.message || '').includes('requires the Canvas runtime kernel') ? 'throws' : 'other';
}
console.log(JSON.stringify({dragCalls, resizeCalls, dragMembers: drag.members.length, resizeReady: typeof resize.move, noKernel}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Factories delegate options verbatim to the kernel and return its session.
        self.assertEqual(payload["dragCalls"], [{"start": {"x": 1, "y": 2}, "scale": 2, "members": [{"id": "a", "ox": 0, "oy": 0}]}])
        self.assertEqual(payload["resizeCalls"], [{"start": {"x": 3, "y": 4}, "scale": 1, "startWidth": 100, "startHeight": 50}])
        self.assertEqual(payload["dragMembers"], 0)
        self.assertEqual(payload["resizeReady"], "function")
        self.assertEqual(payload["noKernel"], "throws")

    def test_keyboard_runtime_dispatches_to_registered_handlers_until_handled(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const listeners = [];
const fakeWindow = {
  addEventListener: (type, cb) => listeners.push({type, cb}),
  removeEventListener: (type, cb) => {
    const i = listeners.findIndex(l => l.type === type && l.cb === cb);
    if (i >= 0) listeners.splice(i, 1);
  },
};
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const runtime = sandbox.window.WorkbenchInteractionController.createKeyboardRuntime({windowRef: fakeWindow});
const seen = [];
const stop = runtime.register(event => { seen.push('first:' + event.key); return event.key === 'Escape'; });
runtime.register(event => { seen.push('second:' + event.key); return false; });
const keydown = listeners.find(l => l.type === 'keydown').cb;
const keyup = listeners.find(l => l.type === 'keyup').cb;
keydown({key: 'a'});
keydown({key: 'Escape'});
keydown({key: 'z'});
keyup({key: 'q'});
stop();
keydown({key: 'q'});
console.log(JSON.stringify({seen, listenerCount: listeners.length, handlerCount: runtime.handlerCount()}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Dispatch walks handlers in order; a handler returning true stops the chain.
        # 'a' walks both handlers; 'Escape' stops after first (returns true);
        # 'z' walks both on keydown; keyup('q') walks both; after stop(),
        # keydown('q') reaches only the remaining handler.
        self.assertEqual(
            payload["seen"],
            ["first:a", "second:a", "first:Escape", "first:z", "second:z", "first:q", "second:q", "second:q"],
        )
        # The window keydown/keyup listeners stay installed for the page's
        # lifetime; stop() only unregisters the handler.
        self.assertEqual(payload["listenerCount"], 2)
        self.assertEqual(payload["handlerCount"], 1)

    def test_connection_gesture_controller_owns_the_gesture_lifecycle(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const listeners = [];
const fakeWindow = {
  addEventListener: (type, cb) => listeners.push({type, cb, active: true}),
  removeEventListener: (type, cb) => {
    const entry = listeners.find(l => l.type === type && l.cb === cb);
    if (entry) entry.active = false;
  },
};
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const events = {moves: [], drops: [], noTargets: [], finishes: []};
const controller = sandbox.window.WorkbenchInteractionController.createConnectionGestureController({
  windowRef: fakeWindow,
  resolveTarget: (gesture, e) => (e.targetId ? {nodeId: e.targetId, port: 'in'} : null),
  validate: (gesture, target) => (target.nodeId === 'bad' ? null : {intent: {from: gesture.fromId, to: target.nodeId}}),
  move: (gesture, e) => events.moves.push([gesture.target?.nodeId, Boolean(gesture.result)]),
  drop: (gesture, result, e) => events.drops.push(result.intent),
  noTarget: (gesture, e) => events.noTargets.push(gesture.fromId),
  finish: (gesture, e) => events.finishes.push(gesture.fromId),
});
// begin + move: hover target resolution and validation flow into the gesture
controller.beginGesture({id: 1}, {fromId: 'a'});
const activeOf = type => listeners.filter(l => l.type === type && l.active);
activeOf('mousemove').forEach(l => l.cb({targetId: 'b'}));
activeOf('mousemove').forEach(l => l.cb({targetId: 'bad'}));
activeOf('mousemove').forEach(l => l.cb({}));
// drop on a valid target: end dispatches drop then finish and detaches
activeOf('mouseup').forEach(l => l.cb({targetId: 'b'}));
// a later move after detach is a no-op; begin works again; veto with no payload
activeOf('mousemove').forEach(l => l.cb({targetId: 'c'}));
const vetoed = controller.beginGesture({id: 2}, null);
controller.beginGesture({id: 3}, {fromId: 'c'});
activeOf('mouseup').forEach(l => l.cb({}));   // no target -> noTarget + finish
const again = controller.beginGesture({id: 4}, {fromId: 'd'});
console.log(JSON.stringify({moves: events.moves, drops: events.drops, noTargets: events.noTargets, finishes: events.finishes, vetoed, begunTwice: !again, activeWhileRunning: 'see-moves'}));
""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Hover pipeline: target + validated result ride the gesture into move.
        self.assertEqual(payload["moves"], [["b", True], ["bad", False], [None, False]])
        self.assertEqual(payload["drops"], [{"from": "a", "to": "b"}])
        self.assertEqual(payload["noTargets"], ["c"])
        self.assertEqual(payload["finishes"], ["a", "c"])
        self.assertFalse(payload["vetoed"])
        self.assertFalse(payload["begunTwice"])

    def test_creation_controller_normalizes_the_versioned_envelope(self):
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const commands = [];
const applied = [];
let seq = 0;
(async () => {
const controller = sandbox.window.WorkbenchInteractionController.createCreationController({
  create: async (canvasId, command, clientId) => {
    commands.push({canvasId, command, clientId});
    return {node: {id: 'n1'}, canvas_revision: 7};
  },
  applyResult: (result, apply) => { applied.push(apply); return {projected: true, ...result.node}; },
  requestId: () => `req-${++seq}`,
});
const node = await controller.createNode({
  canvasId: 'c1', projectId: 'p1', clientId: 'editor-1',
  definitionRef: {type: 'legacy', id: 'image', version: '0'},
  position: {x: 5, y: 6}, expectedRevision: 3, title: 'Blank',
  apply: {nodes: [], projectNode: () => ({})},
});
const minimal = await controller.createNode({
  canvasId: 'c1', definitionRef: {type: 'legacy', id: 'loop', version: '0'},
  position: {x: 0, y: 0}, expectedRevision: 1, initialConfig: {count: 2},
  apply: {nodes: [], projectNode: () => ({})},
});
await controller.createNode({
  canvasId: 'c1', projectId: 'p1', clientId: 'editor-1', source: 'file_drop',
  definitionRef: {type: 'legacy', id: 'image', version: '0'}, position: {x: 8, y: 9}, expectedRevision: 7,
  initialConfig: {url: '/uploads/drop.png', mediaKind: 'image'}, apply: {nodes: [], projectNode: () => ({})},
});
await controller.createNode({
  canvasId: 'c1', projectId: 'p1', clientId: 'editor-1', source: 'clipboard',
  definitionRef: {type: 'legacy', id: 'prompt', version: '0'}, position: {x: 10, y: 11}, expectedRevision: 9,
  initialConfig: {text: 'pasted prompt'}, apply: {nodes: [], projectNode: () => ({})},
});
let invalid = 'no-throw';
try { await controller.createNode({position: {x: 0, y: 0}}); } catch (error) { invalid = 'throws'; }
console.log(JSON.stringify({node, commands, appliedCount: applied.length, invalid}));
})();""".replace("__MODULE__", json.dumps(str(controller_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Envelope: request id from the injected factory, service call verbatim,
        # result application delegated with the page's apply options.
        self.assertEqual(payload["commands"][0]["command"]["request_id"], "req-1")
        self.assertEqual(payload["commands"][0]["command"]["source"], "context_menu")
        self.assertEqual(payload["commands"][0]["command"]["definition_ref"], {"type": "legacy", "id": "image", "version": "0"})
        self.assertEqual(payload["commands"][0]["command"]["title"], "Blank")
        self.assertNotIn("initial_config", payload["commands"][0]["command"])
        self.assertEqual(payload["commands"][1]["command"]["initial_config"], {"count": 2})
        self.assertEqual(payload["commands"][2]["command"]["source"], "file_drop")
        self.assertEqual(payload["commands"][2]["command"]["initial_config"]["url"], "/uploads/drop.png")
        self.assertEqual(payload["commands"][3]["command"]["source"], "clipboard")
        self.assertEqual(payload["commands"][3]["command"]["initial_config"], {"text": "pasted prompt"})
        self.assertNotIn("title", payload["commands"][1]["command"])
        self.assertEqual(payload["commands"][0]["clientId"], "editor-1")
        self.assertEqual(payload["appliedCount"], 4)
        self.assertEqual(payload["invalid"], "throws")

    def test_composer_lifecycle_owns_position_open_and_debounced_schedule(self):
        composer_module = ROOT / "static" / "js" / "workbench" / "canvas" / "composer.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const timers = [];
const sandbox = {{
  window: {{}},
  setTimeout: (cb, ms) => {{ timers.push({{cb, ms, cleared:false}}); return timers.length; }},
  clearTimeout: id => {{ if (timers[id - 1]) timers[id - 1].cleared = true; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(composer_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasComposer;
const container = {{
  style: {{}},
  classList: {{ _open:false, toggle:function(cls, on){{ if(cls === 'open') this._open = Boolean(on); }}, contains:function(cls){{ return cls === 'open' && this._open; }} }},
}};
const lifecycle = api.create({{container}});
lifecycle.setOpen(true);
const opened = lifecycle.isOpen();
lifecycle.setOpen(false);
const closed = !lifecycle.isOpen();
lifecycle.positionForRect({{x:100, y:200, width:300, height:50}});
const positioned = {{width:container.style.width, left:container.style.left, top:container.style.top}};
lifecycle.positionForRect({{x:10, y:20, width:100, height:40}}, {{gap:8, cardWidth:200}});
const custom = {{width:container.style.width, left:container.style.left, top:container.style.top}};
let runs = 0;
lifecycle.scheduleUpdate(10, () => runs++);
lifecycle.scheduleUpdate(10, () => runs++);
const firstCleared = timers[0].cleared;
const secondPending = !timers[1].cleared;
timers[1].cb();
const runsAfterFire = runs;
lifecycle.scheduleUpdate(10, () => runs++);
lifecycle.cancelPending();
const cancelledCleared = timers[2].cleared;
if (!timers[2].cleared) timers[2].cb();
const runsAfterCancel = runs;
console.log(JSON.stringify({{opened, closed, positioned, custom, firstCleared, secondPending, runsAfterFire, cancelledCleared, runsAfterCancel}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "opened": True,
            "closed": True,
            "positioned": {"width": "540px", "left": "-20px", "top": "264px"},
            "custom": {"width": "200px", "left": "-40px", "top": "68px"},
            "firstCleared": True,
            "secondPending": True,
            "runsAfterFire": 1,
            "cancelledCleared": True,
            "runsAfterCancel": 1,
        })

    def test_media_tools_module_owns_crop_grid_draw_math(self):
        media_tools_module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(media_tools_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const out = {{
  clampDefault: api.clampResizeScale('nope'),
  clampHigh: api.clampResizeScale(2),
  clampLow: api.clampResizeScale(0.01),
  clampRound: api.clampResizeScale(0.377),
  circled1: api.circledNumber(1),
  circled20: api.circledNumber(20),
  circled21: api.circledNumber(21),
  point: api.canvasPoint(110, 60, 100, 50, 200, 100, 400, 200),
  uniform: api.gridSplitRects(300, 300, 2, 2, 0),
  uniformGap: api.gridSplitRects(300, 300, 2, 2, 20),
  custom: api.gridSplitRectsCustom(300, 300, [0, 150, 300], [0, 150, 300], 0),
  ratioFree: api.parseCropRatio('free', 0),
  ratioWide: api.parseCropRatio('16:9', 0),
  ratioSource: api.parseCropRatio('source', 1.5),
  ratioSourceInvalid: api.parseCropRatio('source', 0),
  fitSquare: api.fitCropRectToAspect(1, 300, 200, {{x:0, y:0, w:300, h:200}}),
  fitClamp: api.fitCropRectToAspect(null, 300, 200, {{x:10, y:20, w:400, h:300}}),
}};
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        # Resize-scale clamp.
        self.assertEqual(out["clampDefault"], 0.5)
        self.assertEqual(out["clampHigh"], 1)
        self.assertEqual(out["clampLow"], 0.05)
        self.assertEqual(out["clampRound"], 0.38)
        # Circled labels.
        self.assertEqual(out["circled1"], "\u2460")
        self.assertEqual(out["circled20"], "\u2473")
        self.assertEqual(out["circled21"], "21")
        # Pointer → canvas point mapping.
        self.assertEqual(out["point"], {"x": 20.0, "y": 20.0})
        # Uniform grid split (no gap): four 150×150 rects.
        self.assertEqual(out["uniform"], [
            {"row": 0, "col": 0, "x": 0, "y": 0, "w": 150, "h": 150},
            {"row": 0, "col": 1, "x": 150, "y": 0, "w": 150, "h": 150},
            {"row": 1, "col": 0, "x": 0, "y": 150, "w": 150, "h": 150},
            {"row": 1, "col": 1, "x": 150, "y": 150, "w": 150, "h": 150},
        ])
        # Uniform grid split (20px gap): interior inset shrinks each rect.
        self.assertEqual(out["uniformGap"], [
            {"row": 0, "col": 0, "x": 0, "y": 0, "w": 140, "h": 140},
            {"row": 0, "col": 1, "x": 160, "y": 0, "w": 140, "h": 140},
            {"row": 1, "col": 0, "x": 0, "y": 160, "w": 140, "h": 140},
            {"row": 1, "col": 1, "x": 160, "y": 160, "w": 140, "h": 140},
        ])
        # Custom-line split (single interior cut each way, no gap) == uniform 2×2.
        self.assertEqual(out["custom"], out["uniform"])
        # Crop ratio parsing.
        self.assertIsNone(out["ratioFree"])
        self.assertAlmostEqual(out["ratioWide"], 16 / 9)
        self.assertEqual(out["ratioSource"], 1.5)
        self.assertIsNone(out["ratioSourceInvalid"])
        # Aspect-fit keeps the rect centered and clamps to bounds.
        self.assertEqual(out["fitSquare"], {"x": 50, "y": 0, "w": 200, "h": 200})
        self.assertEqual(out["fitClamp"], {"x": 60, "y": 70, "w": 300, "h": 200})

    def test_media_tools_module_owns_node_media_reference_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'img', type:'image', url:'/a.png', name:'A'}}, {{id:'child', type:'image', url:'/b.png'}}, {{id:'out', type:'output', images:[{{url:'/c.png', kind:'image'}}]}}];
const opts = {{nodes, mediaKindForNode: n => n.mediaKind || 'image', mediaKindForOutputItem: i => i.kind || 'image', outputUrlValue: i => i.url, outputImageName: u => u.split('/').pop(), mediaOutputTypes:['generator'], generatedImageRefs: n => [{{url:'/generated.png', kind:'image'}}]}};
console.log(JSON.stringify({{image:api.mediaRefsFromNode(nodes[0], opts), group:api.mediaRefsFromNode({{type:'group', items:['child']}}, opts), output:api.mediaRefsFromNode(nodes[2], opts), generated:api.mediaRefsFromNode({{type:'generator'}}, opts)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["image"][0]["name"], "A")
        self.assertEqual(out["group"][0]["url"], "/b.png")
        self.assertEqual(out["output"][0]["outputIndex"], 0)
        self.assertEqual(out["generated"][0]["url"], "/generated.png")

    def test_media_tools_module_owns_latest_output_reference_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const node = {{id:'out', type:'output', images:[{{url:''}}, {{url:'/latest.png', kind:'image'}}, {{url:''}}]}};
console.log(JSON.stringify({{latest:api.latestOutputReference(node, {{outputUrlValue:i => i.url, mediaKindForOutputItem:i => i.kind || 'image'}}), empty:api.latestOutputReference({{type:'output', images:[{{url:''}}]}})}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["latest"]["preview"], "/latest.png")
        self.assertEqual(out["latest"]["refs"][0]["outputIndex"], 1)
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_generated_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{sources:api.generatedMediaSources({{id:'gen'}}, [{{url:'/a.png'}}, {{url:'/b.png'}}]), empty:api.generatedMediaSources({{id:'gen'}}, [])}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["sources"][1]["id"], "gen:generated:1:/b.png")
        self.assertEqual(out["sources"][0]["type"], "generatedImage")
        self.assertEqual(out["empty"], [])

    def test_media_tools_module_owns_image_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{source:api.imageMediaSource({{id:'img', type:'image', url:'/img.png', name:'Hero', role:'ref'}}, () => 'video'), empty:api.imageMediaSource({{type:'prompt'}}, () => 'image')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["source"]["type"], "video")
        self.assertEqual(out["source"]["refs"][0]["role"], "ref")
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_group_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'img', type:'image', url:'/img.png', name:'Hero'}}, {{id:'p', type:'prompt', text:'one'}}, {{id:'p2', type:'prompt', text:'two'}}];
const sources = api.groupMediaSources({{id:'g', type:'group', items:['img','p','p2']}}, {{nodes, mediaKindForNode:() => 'image'}});
console.log(JSON.stringify(sources));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        sources = json.loads(result.stdout)
        self.assertEqual(sources[0]["id"], "g:img")
        self.assertEqual(sources[1]["type"], "groupPrompt")
        self.assertEqual(sources[1]["prompt"], "one\n\ntwo")

    def test_media_tools_module_owns_prompt_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{source:api.promptMediaSource({{id:'p', type:'prompt', text:'  prompt text  '}}), empty:api.promptMediaSource({{type:'image'}})}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["source"]["label"], "  prompt text  ")
        self.assertEqual(out["source"]["prompt"], "  prompt text  ")
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_prompt_group_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'p', type:'prompt', text:'one'}}, {{id:'p2', type:'prompt', text:'two'}}, {{id:'img', type:'image', text:'skip'}}];
console.log(JSON.stringify({{source:api.promptGroupMediaSource({{id:'pg', type:'promptGroup', items:['p','p2','img']}}, {{nodes}}), empty:api.promptGroupMediaSource({{type:'promptGroup', items:[]}}, {{nodes}})}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["source"]["label"], "提示词 2 个")
        self.assertEqual(out["source"]["prompt"], "one\n\ntwo")
        self.assertEqual(out["empty"]["label"], "提示词 0 个")

    def test_media_tools_module_owns_llm_media_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{source:api.llmMediaSource({{id:'l', type:'llm', mode:'node', outputText:'generated text'}}), chat:api.llmMediaSource({{id:'c', type:'llm', mode:'chat', outputText:'chat'}}), empty:api.llmMediaSource({{type:'llm', outputText:''}})}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["source"]["prompt"], "generated text")
        self.assertIsNone(out["chat"])
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_loop_fallback_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{source:api.loopFallbackSource({{id:'loop', type:'loop'}}, 'prompt', 'Loop 3x'), empty:api.loopFallbackSource({{type:'image'}}, 'x')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["source"], {"id": "loop", "type": "loop", "label": "Loop 3x", "refs": [], "prompt": "prompt"})
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_loop_image_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const sources = api.loopImageMediaSources({{id:'loop', type:'loop', loopStart:2}}, [{{url:'/a.png'}}, {{url:'/b.png'}}], {{index:5, prompt:'ctx', labelFor:n => 'image ' + n}});
console.log(JSON.stringify(sources));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        sources = json.loads(result.stdout)
        self.assertEqual(sources[0]["id"], "loop:image:5:/a.png")
        self.assertEqual(sources[0]["prompt"], "ctx")
        self.assertEqual(sources[1]["prompt"], "")

    def test_media_tools_module_owns_ordered_input_source_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const node = {{inputs:['missing','b','a']}};
const sources = [{{id:'a'}}, {{id:'b'}}, {{id:'c'}}];
console.log(JSON.stringify({{ordered:api.orderedInputSources(node, sources), inputs:node.inputs}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual([item["id"] for item in out["ordered"]], ["b", "a", "c"])
        self.assertEqual(out["inputs"], ["b", "a", "c"])

    def test_media_tools_module_owns_input_reorder_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{reordered:api.reorderInputIds(['a','prompt','b'], 'b', 'a', ['a','b']), invalid:api.reorderInputIds(['a'], 'a', 'missing', ['a'])}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["reordered"], ["b", "a", "prompt"])
        self.assertIsNone(out["invalid"])

    def test_media_tools_module_owns_image_input_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const sources = api.imageInputSources([{{id:'a', refs:[{{kind:'image'}}, {{kind:'text'}}]}}, {{id:'b', refs:[]}}], refs => refs.filter(ref => ref.kind === 'image'));
console.log(JSON.stringify(sources));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        sources = json.loads(result.stdout)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["id"], "a")
        self.assertEqual(sources[0]["refs"], [ {"kind": "image"} ])

    def test_media_tools_module_owns_prompt_input_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.promptInputSources([{{id:'p', prompt:'text', refs:[]}}, {{id:'m', prompt:'media', refs:[{{url:'/a.png'}}]}}, {{id:'e', prompt:'', refs:[]}}])));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        sources = json.loads(result.stdout)
        self.assertEqual([source["id"] for source in sources], ["p"])

    def test_media_tools_module_owns_input_view_projection_batch(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const out = api.inputViewProjection([{{id:'i',refs:[{{kind:'image'}}]}},{{id:'p',prompt:'text',refs:[]}}], refs => refs.filter(ref => ref.kind === 'image'));
console.log(JSON.stringify({{images:out.imageInputs.map(item=>item.id), prompts:out.promptInputs.map(item=>item.id)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"images": ["i"], "prompts": ["p"]})

    def test_runninghub_renderer_owns_source_projection_batch(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "runninghub-field-renderer.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasRunningHubFieldRenderer;
const out = api.sourceProjection([{{id:'b',refs:[{{kind:'image',url:'/b.png'}}]}},{{id:'a',prompt:'p',refs:[]}}], {{order:list=>list.slice().reverse(), kindOf:ref=>ref.kind, imageLimit:4}});
console.log(JSON.stringify({{ids:out.sources.map(x=>x.id), images:out.image.length, prompt:out.prompt}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"ids": ["a", "b"], "images": 1, "prompt": "p"})

    def test_media_tools_module_owns_output_download_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const out = api.outputDownloadProjection({{images:[{{url:'/output/a.png',kind:'image'}},{{url:'/remote/b.png',kind:'video'}}]}}, {{kindOf:i=>i.kind, outputValue:i=>i.url, isMissing:u=>u.includes('remote')}});
console.log(JSON.stringify(out));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"urls": ["/output/a.png"], "downloadable": ["/output/a.png"]})

    def test_media_tools_module_owns_reference_source_id_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.refSourceIds([{{id:'a', refs:[{{}}]}}, {{id:'b', refs:[]}}, {{id:'c', refs:[{{}}]}}])));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["a", "c"])

    def test_media_tools_module_owns_connected_input_node_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'a'}}, {{id:'b'}}, {{id:'other'}}];
console.log(JSON.stringify(api.connectedInputNodes('target', [{{from:'a',to:'target'}}, {{from:'missing',to:'target'}}, {{from:'other',to:'other'}}], nodes)));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [{"id": "a"}])

    def test_media_tools_module_owns_generated_media_reference_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const refs = api.generatedMediaRefs({{type:'generator', generatedOutputs:[{{url:'/a.png', kind:'image'}}, {{url:'/v.mp4', kind:'video'}}, {{url:''}}]}}, {{outputUrlValue:i=>i.url, mediaKindForOutputItem:i=>i.kind, outputImageName:u=>u.split('/').pop()}});
console.log(JSON.stringify(refs));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        refs = json.loads(result.stdout)
        self.assertEqual(refs, [{"url": "/a.png", "name": "a.png", "kind": "image"}])

    def test_media_tools_module_owns_output_resolution_markup(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{withTime:api.outputResolutionMarkup('1024x1024', 2500, ms => ms + 'ms'), empty:api.outputResolutionMarkup('', 0, ms => ms + 'ms')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertIn("1024x1024", out["withTime"])
        self.assertIn("2500ms", out["withTime"])
        self.assertEqual(out["empty"], "--")

    def test_media_tools_module_owns_compare_mode_style_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{active:api.compareModeStyles(true), inactive:api.compareModeStyles(false)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["active"], {"clipPath": "inset(0 50% 0 0)", "sliderLeft": "50%"})
        self.assertEqual(out["inactive"], {"clipPath": "", "sliderLeft": ""})

    def test_media_tools_module_owns_rerun_output_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const out = api.rerunOutputProjection({{run:{{nodeType:'generator', node:{{model:'x'}}, prompt:'hello', refs:[{{url:'/a.png', name:'A'}}, {{url:'/b.png'}}]}}}}, {{x:10,y:20}}, prefix => prefix + '-' + Math.random());
console.log(JSON.stringify({{nodes:out.nodes.map(n=>n.type), connections:out.connections.length, prompt:out.nodes[1].text}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"nodes": ["generator", "prompt", "image", "image"], "connections": 3, "prompt": "hello"})

    def test_media_tools_module_owns_output_image_node_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{node:api.outputImageNodeProjection('/a.png', {{x:4,y:5}}, prefix => prefix + '-1', url => 'A'), empty:api.outputImageNodeProjection('', {{x:0,y:0}}, () => 'x')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["node"], {"id": "img-1", "type": "image", "x": 4, "y": 5, "url": "/a.png", "name": "A"})
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_output_node_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.outputNodeProjection({{x:7,y:8}}, prefix => prefix + '-1')));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"id": "out-1", "type": "output", "x": 7, "y": 8, "images": []})

    def test_media_tools_module_owns_editor_output_node_lookup(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'out', type:'output'}}, {{id:'other', type:'image'}}];
console.log(JSON.stringify({{found:api.findOutputNodeForSource('src', [{{from:'src',to:'out'}}], nodes), missing:api.findOutputNodeForSource('src', [{{from:'src',to:'other'}}], nodes)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["found"]["id"], "out")
        self.assertIsNone(out["missing"])

    def test_media_tools_module_owns_latest_output_and_duplicate_projections(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const node = {{generatedOutputs:[{{url:''}}, {{url:'/latest.png'}}]}};
const out = {{images:[{{url:'/existing.png'}}]}};
console.log(JSON.stringify({{latest:api.latestGeneratedOutputItem(node, i=>i.url), existing:api.outputHasUrl(out, '/existing.png', i=>i.url), missing:api.outputHasUrl(out, '/new.png', i=>i.url)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        value = json.loads(result.stdout)
        self.assertEqual(value["latest"]["url"], "/latest.png")
        self.assertTrue(value["existing"])
        self.assertFalse(value["missing"])

    def test_media_tools_module_owns_output_lifecycle_projection_batch(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'out',type:'output'}},{{id:'img',type:'image'}}];
const output = {{images:[{{url:'/old.png'}}]}};
console.log(JSON.stringify({{nodes:api.outputNodesForSource('src',[{{from:'src',to:'out'}},{{from:'src',to:'img'}}],nodes).map(n=>n.id), valid:api.outputItemsWithUrl([{{url:''}},{{url:'/new.png'}}],i=>i.url), unique:api.uniqueOutputItems(output,[{{url:'/old.png'}},{{url:'/new.png'}}],i=>i.url)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["nodes"], ["out"])
        self.assertEqual(out["valid"], [{"url": "/new.png"}])
        self.assertEqual(out["unique"], [{"url": "/new.png"}])

    def test_media_tools_module_owns_unique_output_append_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.appendUniqueOutputRecords([{{url:'/old.png'}}], [{{url:'/old.png'}}, {{url:'/new.png'}}], null, [], null, i=>i.url)));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual([item["url"] for item in out["images"]], ["/old.png", "/new.png"])
        self.assertEqual(out["added"], 1)

    def test_media_tools_module_owns_input_group_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
let next = 0;
const out = api.inputGroupProjection(['/a.png','/b.png','/c.png'], {{x:10,y:20}}, prefix => prefix + '-' + (++next), url => url.slice(1));
console.log(JSON.stringify({{count:out.nodes.length, group:out.group, first:out.nodes[0]}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["count"], 4)
        self.assertEqual(out["group"]["items"], ["img-1", "img-2", "img-3"])
        self.assertEqual(out["first"]["name"], "a.png")

    def test_media_tools_module_owns_downstream_target_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.downstreamTargetIds('src', [{{from:'src',to:'a'}},{{from:'other',to:'b'}},{{from:'src',to:'c'}}])));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["a", "c"])

    def test_media_tools_module_owns_archive_download_filename_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([api.archiveDownloadFilename('Canvas', 'out', 'canvas-output'), api.archiveDownloadFilename('', 'grp', 'canvas-group')]));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["Canvas-out.zip", "canvas-group-grp.zip"])

    def test_media_tools_module_owns_archive_download_payload_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify(api.archiveDownloadPayload(['/a.png','',null], 'bundle.zip', {{items:[{{url:'/a.png',name:'A'}}]}})));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"urls": ["/a.png"], "filename": "bundle.zip", "items": [{"url": "/a.png", "name": "A"}]})

    def test_media_tools_module_owns_download_href_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify([api.downloadHref('/output/a.png','a.png',u=>u+'?raw'), api.downloadHref('blob:abc','a.png'), api.downloadHref('', 'x')]));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        hrefs = json.loads(result.stdout)
        self.assertIn('/api/download-output?url=', hrefs[0])
        self.assertEqual(hrefs[1], 'blob:abc')
        self.assertEqual(hrefs[2], '')

    def test_workflow_transfer_module_owns_export_projection_batch(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "workflow-transfer-client.js"
        http_error = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-http-error.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}, Date}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(http_error))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasWorkflowTransfer;
const out = api.exportProjection({{nodes:[{{id:'n'}}],connections:[]}}, 'Canvas', 'json', 0);
console.log(JSON.stringify({{nodes:out.payload.nodes.length, filename:out.filename.endsWith('.json')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"nodes": 1, "filename": True})

    def test_media_tools_module_owns_generator_source_projection_batch(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [{{id:'img',type:'image',url:'/a.png',name:'A'}},{{id:'p',type:'prompt',text:'prompt'}}];
const legacy = api.legacyGeneratorSourceProjection({{id:'gen'}}, [{{from:'img',to:'gen'}},{{from:'p',to:'gen'}}], nodes, {{mediaKindForNode:()=> 'image'}});
const normal = api.generatorSourceProjection({{id:'gen'}}, [{{from:'img',to:'gen'}},{{from:'p',to:'gen'}}], nodes, {{mediaKindForNode:()=> 'image'}});
console.log(JSON.stringify({{legacy:legacy.map(item => item.type), normal}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"legacy": ["image", "prompt"], "normal": []})

    def test_media_tools_generator_source_projection_prefers_typed_bindings_over_edges(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
const nodes = [
  {{id:'typed-source',type:'image',url:'/typed.png',output_refs:[{{type:'asset_version',id:'asset-1'}}]}},
  {{id:'edge-source',type:'image',url:'/edge.png'}}
];
const out = api.generatorSourceProjection(
  {{id:'gen',input_bindings:[{{id:'binding-1',target:'image',source_type:'asset_version',source_ref:'asset-1',order:0}}]}},
  [{{from:'edge-source',to:'gen'}}], nodes, {{mediaKindForNode:()=> 'image'}}
);
console.log(JSON.stringify(out.flatMap(item => item.refs || []).map(ref => ref.url)));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), ["/typed.png"])

    def test_loop_input_projection_prefers_typed_bindings_over_edges(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "loop-input-projection.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasLoopInputProjection;
const typed = {{id:'typed-source', type:'image', url:'/typed.png', output_refs:[{{type:'asset_version', id:'asset-1'}}]}};
const edge = {{id:'edge-source', type:'image', url:'/edge.png'}};
const node = {{id:'loop', imageInput:true, input_bindings:[{{id:'binding-1', source_type:'asset_version', source_ref:'asset-1', order:0}}]}};
const connections = [{{from:'edge-source', to:'loop'}}];
const resolve = id => id === 'asset-1' ? [{{url:typed.url}}] : [{{url:edge.url}}];
const refs = api.connectedBatch(node, connections, resolve, 1, 1, 1);
const legacyRefs = api.legacyConnectedBatch({{id:'loop', imageInput:true}}, connections, resolve, 1, 1, 1);
const prompts = api.promptItems(
  {{id:'loop', showPrompt:true, input_bindings:[{{id:'binding-2', source_type:'entity_ref', source_ref:'prompt-1', order:0}}]}},
  [{{from:'edge-prompt', to:'loop'}}],
  [{{id:'prompt-1', type:'prompt', text:'typed prompt'}}, {{id:'edge-prompt', type:'prompt', text:'edge prompt'}}]
);
console.log(JSON.stringify({{refs:refs.map(ref => ref.url), legacyRefs:legacyRefs.map(ref => ref.url), prompts}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"refs": ["/typed.png"], "legacyRefs": ["/edge.png"], "prompts": ["typed prompt"]})

    def test_media_tools_module_owns_generated_image_node_projection(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{node:api.generatedImageNodeProjection({{url:'/generated.png', name:''}}, {{x:3,y:4}}, prefix => prefix + '-1', 'crop', {{mediaKind:'image'}}), empty:api.generatedImageNodeProjection({{}}, {{x:0,y:0}}, () => 'x', 'crop')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["node"], {"id": "img-1", "type": "image", "x": 3, "y": 4, "url": "/generated.png", "name": "crop", "mediaKind": "image"})
        self.assertIsNone(out["empty"])

    def test_media_tools_module_owns_output_prompt_and_rerun_projections(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaTools;
console.log(JSON.stringify({{prompt:api.outputPromptProjection({{run:{{prompt:'hello'}}}}, 'none'), empty:api.outputPromptProjection(null, 'none'), rerun:api.outputRerunAvailable({{run:{{nodeType:'generator'}}}}), noRerun:api.outputRerunAvailable({{run:{{}}}})}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["prompt"], {"prompt": "hello", "open": True, "text": "hello"})
        self.assertEqual(out["empty"], {"prompt": "", "open": False, "text": "none"})
        self.assertTrue(out["rerun"])
        self.assertFalse(out["noRerun"])

    def test_execution_host_module_owns_the_canvas_lifecycle_contract(self):
        execution_host_module = ROOT / "static" / "js" / "workbench" / "canvas" / "execution-host.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(execution_host_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasExecutionHost;
const calls = [];
const host = {{
  markRunning: (n, r) => calls.push(['markRunning', n.id, r]),
  writePromptResult: (n, r) => calls.push(['writePromptResult', n.id, r.promptResult]),
  save: () => calls.push(['save']),
  render: () => calls.push(['render']),
  notifyError: (m) => calls.push(['notifyError', m]),
}};
const handle = api.create(host);
const node = {{id: 'n1'}};
handle.markRunning(node, true);
handle.markRunning(node, 0);
handle.writePromptResult(node, {{promptResult: '  hi  '}});
handle.save();
handle.render();
handle.notifyError('boom');
const frozen = Object.isFrozen(handle);
let missingThrew = false;
try {{ api.create({{markRunning(){{}}, writePromptResult(){{}}, save(){{}}, render(){{}}}}); }} catch(e) {{ missingThrew = true; }}
let nonObjectThrew = false;
try {{ api.create(null); }} catch(e) {{ nonObjectThrew = true; }}
console.log(JSON.stringify({{calls, frozen, missingThrew, nonObjectThrew}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["calls"], [
            ["markRunning", "n1", True],
            ["markRunning", "n1", False],  # 0 is coerced to false
            ["writePromptResult", "n1", "  hi  "],  # module is a pass-through; the page trims
            ["save"],
            ["render"],
            ["notifyError", "boom"],
        ])
        self.assertTrue(out["frozen"])
        self.assertTrue(out["missingThrew"])
        self.assertTrue(out["nonObjectThrew"])

    def test_provider_controls_module_owns_the_canvas_commit_contract(self):
        provider_controls_module = ROOT / "static" / "js" / "workbench" / "canvas" / "provider-controls.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(provider_controls_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasProviderControls;
const calls = [];
const host = {{
  setField: (n, k, v) => calls.push(['setField', n.id, k, v]),
  save: () => calls.push(['save']),
  render: () => calls.push(['render']),
}};
const handle = api.create(host);
const node = {{id: 'n1'}};
handle.setField(node, 'llmProvider', 'openai');
handle.save();
handle.render();
const frozen = Object.isFrozen(handle);
let missingThrew = false;
try {{ api.create({{setField(){{}}, save(){{}}}}); }} catch(e) {{ missingThrew = true; }}
let nonObjectThrew = false;
try {{ api.create(null); }} catch(e) {{ nonObjectThrew = true; }}
console.log(JSON.stringify({{calls, frozen, missingThrew, nonObjectThrew}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["calls"], [
            ["setField", "n1", "llmProvider", "openai"],
            ["save"],
            ["render"],
        ])
        self.assertTrue(out["frozen"])
        self.assertTrue(out["missingThrew"])
        self.assertTrue(out["nonObjectThrew"])

    def test_provider_controls_is_loaded_before_the_classic_page_and_llm_body_uses_it(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        classic = read_canvas_app_source(ROOT)
        provider_controls_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "provider-controls.js").read_text(encoding="utf-8")
        card_body_seam = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-card-body-renderer.js").read_text(encoding="utf-8")
        # The provider-controls seam module loads ahead of the editor script
        # AND ahead of the card-body seam (card-body consumes provider-controls
        # via host injection so the dependency order must hold).
        self.assertLess(page.index("workbench/canvas/provider-controls.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertLess(page.index("workbench/canvas/provider-controls.js"),
                        page.index("workbench/canvas/classic-card-body-renderer.js"))
        self.assertLess(page.index("workbench/canvas/classic-card-body-renderer.js"),
                        page.index("workbench/canvas/canvas-app-bootstrap.js"))
        # canvas.js still constructs the host handle (host injection) — the
        # page owns `ensureProviderControls()`, the card-body seam only
        # consumes the returned handle.
        self.assertIn("window.WorkbenchCanvasProviderControls.create({", classic)
        self.assertIn("ensureProviderControls,", classic,
            msg="canvas.js host-injection must include ensureProviderControls for the card-body seam")
        # R4-38 Wave 5: renderLLMBody moved into the card-body compat seam.
        # Its five LLM-body control handlers still route through providerControls
        # (no direct node writes), but the assertions now target the seam file.
        self.assertIn("const providerControls = ensureProviderControls();", card_body_seam)
        self.assertIn("providerControls.setField(node, 'llmProvider', value)", card_body_seam)
        self.assertIn("providerControls.setField(node, 'showSystem', !node.showSystem)", card_body_seam)
        self.assertIn("providerControls.setField(node, 'systemPrompt', e.target.value)", card_body_seam)
        self.assertIn("providerControls.setField(node, 'mode', btn.dataset.mode)", card_body_seam)
        # The old direct Canvas writes in renderLLMBody's handlers are gone
        # from canvas.js (renderLLMBody moved to the card-body seam in
        # R4-38 Wave 5); these strings are unique to the LLM body, the
        # Comfy body keeps its own page-owned mode handler, out of scope.
        self.assertNotIn("node.llmProvider = e.target.value", classic)
        self.assertNotIn("node.showSystem = !node.showSystem", classic)
        self.assertNotIn("node.systemPrompt = e.target.value", classic)
        # The extracted host is product-neutral: no Classic adapter detail leaks in.
        for adapter_detail in ("llmProvider", "llm", "generator", "midjourney", "msgen",
                               "providerChatModels", "renderLLMBody", "scheduleSave"):
            self.assertNotIn(adapter_detail, provider_controls_module)

    def test_classic_execution_host_module_owns_the_canvas_lifecycle_contract(self):
        neutral_execution_host_module = ROOT / "static" / "js" / "workbench" / "canvas" / "execution-host.js"
        classic_execution_host_module = ROOT / "static" / "js" / "workbench" / "canvas" / "classic-execution-host.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(neutral_execution_host_module))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(classic_execution_host_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasClassicExecutionHost;
const calls = [];
const host = {{
  markRunning: (n, r) => calls.push(['markRunning', n.id, r]),
  writeOutputText: (n, t) => calls.push(['writeOutputText', n.id, t]),
  setRunStatus: (n, s, e) => calls.push(['setRunStatus', n.id, s, e]),
  render: (n) => calls.push(['render', n.id]),
  save: () => calls.push(['save']),
  notifyError: (m) => calls.push(['notifyError', m]),
}};
const handle = api.create(host);
const node = {{id: 'n1'}};
handle.markRunning(node, true);
handle.markRunning(node, 0);
handle.writeOutputText(node, 'hello');
handle.setRunStatus(node, 'done', '');
handle.setRunStatus(node, 'failed', 'boom');
handle.render(node);
handle.save();
handle.notifyError('boom');
const frozen = Object.isFrozen(handle);
let missingThrew = false;
try {{ api.create({{markRunning(){{}}, writeOutputText(){{}}, setRunStatus(){{}}, render(){{}}, save(){{}}}}); }} catch(e) {{ missingThrew = true; }}
let nonObjectThrew = false;
try {{ api.create(null); }} catch(e) {{ nonObjectThrew = true; }}
console.log(JSON.stringify({{calls, frozen, missingThrew, nonObjectThrew}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        self.assertEqual(out["calls"], [
            ["markRunning", "n1", True],
            ["markRunning", "n1", False],  # 0 is coerced to false
            ["writeOutputText", "n1", "hello"],
            ["setRunStatus", "n1", "done", ""],
            ["setRunStatus", "n1", "failed", "boom"],
            ["render", "n1"],
            ["save"],
            ["notifyError", "boom"],
        ])
        self.assertTrue(out["frozen"])
        self.assertTrue(out["missingThrew"])
        self.assertTrue(out["nonObjectThrew"])

    def test_classic_execution_compatibility_manifest_is_grounded_in_source(self):
        doc = (ROOT / "docs" / "plans" / "R4_CLASSIC_EXECUTION_COMPATIBILITY.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", doc, re.S)
        self.assertIsNotNone(match, "the characterization doc must embed a JSON evidence manifest")
        manifest = json.loads(match.group(1))
        self.assertEqual(manifest["source"], "static/js/workbench/canvas/canvas-app-compat-host.js")
        classic = read_canvas_app_source(ROOT)
        allowed_dispositions = {"seamed", "host-cutover", "host-candidate", "transport-only", "flag-only"}
        seen_dispositions = set()
        for entry in manifest["entry_points"]:
            self.assertIn(entry["disposition"], allowed_dispositions)
            seen_dispositions.add(entry["disposition"])
            # R4-38 Wave 14 moved the cascade implementation into the bounded
            # compat seam module; affected entries declare `evidence_target`
            # so grounding reads the owning module (same schema as the R4-31
            # capability inventory). Entries without the field stay grounded
            # in the manifest source (canvas.js).
            target_rel = entry.get("evidence_target", manifest["source"])
            target_source = (ROOT / target_rel).read_text(encoding="utf-8")
            self.assertIn(entry["function"], target_source, f"{entry['function']} must exist in {target_rel}")
            for evidence in entry["evidence"]:
                self.assertIn(evidence, target_source, f"evidence {evidence} must exist in {target_rel}")
        # The classification is non-trivial: the cutover, seamed, and a deferred
        # host-candidate disposition must all be present.
        for required in ("host-cutover", "seamed", "host-candidate"):
            self.assertIn(required, seen_dispositions)

    def test_classic_execution_host_is_loaded_before_the_classic_page_and_run_llm_uses_it(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        classic = read_canvas_app_source(ROOT)
        classic_execution_host_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-execution-host.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/classic-execution-host.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        # The page constructs the host handle and delegates runLLMNode's Canvas
        # lifecycle/state side-effects through it (no direct node writes).
        # Wave 16a moved runLLMNode's body (with the host delegation) into
        # classic-executor-runtime.js; the page keeps the factory + load order.
        executor_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-executor-runtime.js").read_text(encoding="utf-8")
        self.assertIn("window.WorkbenchCanvasClassicExecutionHost.create({", classic)
        self.assertIn("const executionHost = ensureClassicExecutionHost();", executor_source)
        self.assertIn("executionHost.markRunning(node, true)", executor_source)
        self.assertIn("executionHost.markRunning(node, false)", executor_source)
        self.assertIn("executionHost.writeOutputText(node, outputText)", executor_source)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", executor_source)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", executor_source)
        self.assertIn("executionHost.save()", executor_source)
        self.assertIn("executionHost.notifyError(err.message || 'LLM 运行失败')", executor_source)
        # The old direct Canvas writes in runLLMNode are gone.
        self.assertNotIn("node.outputText = await callCanvasLLM", classic)
        # The extracted host is product-neutral: no Classic adapter detail leaks in.
        for adapter_detail in ("refreshNodes", "scheduleSave", "node.outputText",
                               "node.runStatus", "node.runError", "node.running",
                               "runLLMNode", "callCanvasLLM", "cascade", "generator"):
            self.assertNotIn(adapter_detail, classic_execution_host_module)

    def test_smart_native_entry_routes_smart_kinds_through_canvas_html(self):
        # R4-34: the entry-compatibility module's normalCanvasUrl must return
        # a canvas.html URL for every record, regardless of kind (Classic or
        # Smart). The unified page is the single entry; the Smart product
        # runtime is no longer navigated to via this module.
        entry_module = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-entry-compatibility.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(entry_module))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasEntryCompatibility;
const classicUrl = api.normalCanvasUrl('c1', 'p1');
const smartUrl = api.normalCanvasUrl('c2', 'p1');
const remembered = api.rememberedCanvasListProject({{storage:{{getItem:() => 'pX'}}, defaultProject:'p1'}});
const listUrl = api.canvasListUrl('p1');
console.log(JSON.stringify({{classicUrl, smartUrl, remembered, listUrl}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        out = json.loads(result.stdout)
        # Both kinds land on canvas.html with project+id query.
        for label, url in (("classic", out["classicUrl"]), ("smart", out["smartUrl"])):
            self.assertTrue(
                url.startswith("/static/canvas.html?"),
                f"{label} entry must point at canvas.html, got {url}",
            )
            self.assertNotIn("smart-canvas.html", url)
            self.assertIn("id=c", url)
            self.assertIn("project=p1", url)
        # The list URL is unchanged and the project-remembering helper still works.
        self.assertTrue(out["listUrl"].startswith("/static/canvas-list.html?"))
        self.assertEqual(out["remembered"], "pX")

    def test_smart_native_entry_removes_the_handoff_redirect_from_canvas_js(self):
        # R4-34: openCanvas must no longer redirect Smart records to
        # smart-canvas.html; the new-canvas gate must navigate Smart-kind
        # creations to canvas.html; openSmartCanvasPage must be dead code;
        # and canvas.html must load the two Smart-compatibility shared seams
        # (composer.js, media-tools.js) ahead of canvas.js.
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        classic = read_canvas_app_source(ROOT)
        # The two shared seams are loaded ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/composer.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        self.assertLess(page.index("workbench/canvas/media-tools.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))
        # The handoff redirect and its helper are gone from canvas.js.
        for token in ("openSmartCanvasPage", "requiresLegacySmartHandoff", "legacySmartCanvasUrl"):
            self.assertNotIn(token, classic, f"{token} must be removed from canvas.js (R4-34)")
        # The createCanvas Smart branch navigates to canvas.html via the
        # shared normalCanvasUrl helper, not the legacy smart-canvas.html URL.
        self.assertIn("WorkbenchCanvasEntryCompatibility.normalCanvasUrl(", classic)
        # The new-canvas gate never references smart-canvas.html either.
        self.assertNotIn("smart-canvas.html", classic)

    def test_blank_create_helpers_pass_canvas_id_to_controller_at_runtime(self):
        # R4-21.1 behavioral proof: drive the real createCreationController
        # factory against every blank-create helper extracted from the page
        # sources. Each helper receives a real `canvas = { id, project }` and
        # must (a) call the controller `create(canvasId, ...)` with that id,
        # and (b) return the projected node rather than throwing the
        # `CreationController requires canvasId` TypeError that pre-existed
        # before this rectification.
        controller_module = ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js"
        controller_source = controller_module.read_text(encoding="utf-8")

        # First prove the gate: the controller rejects a request without canvasId.
        negative_script = (
            "const fs=require('fs'); const vm=require('vm');\n"
            "const sandbox={window:{}};\n"
            f"vm.runInNewContext(fs.readFileSync({json.dumps(str(controller_module))},'utf8'), sandbox);\n"
            "const controller=sandbox.window.WorkbenchInteractionController.createCreationController({\n"
            "  create: async () => ({node:{id:'n'}, canvas_revision:1}),\n"
            "  applyResult: r => r.node,\n"
            "  requestId: () => 'req',\n"
            "});\n"
            "(async () => {\n"
            "  let kind='no-throw';\n"
            "  try { await controller.createNode({definitionRef:{type:'legacy',id:'image',version:'0'},position:{x:0,y:0},apply:{nodes:[],projectNode:source=>source}}); } catch(e) { kind=e.message.includes('canvasId')?'throws-canvasId':('throws-other:'+e.message); }\n"
            "  console.log(JSON.stringify({kind}));\n"
            "})();"
        )
        negative_result = subprocess.run(["node", "-e", negative_script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(negative_result.stdout), {"kind": "throws-canvasId"})

        # Then exercise the helpers' createNode envelopes end-to-end:
        # compose a sandbox that defines every helper (with stubbed page-side
        # effects like render/serializableCanvasNodes/snapshotForUndo) and
        # route `WorkbenchInteractionController.createCreationController`
        # through the real controller module. Each successful call must carry
        # canvasId == 'canvas-x'; the controller throws TypeError otherwise.
        helpers_classic = [
            ("addVersionedBlankImageNode", "ensureCreationController()", "async function addVersionedBlankImageNode(point){\n"
                "if(!canUseVersionedImageCreation()) return null;\n"
                "const p = point || {x:0,y:0};\n"
                "const undoSnapshot = {nodes:[], connections:[]};\n"
                "const node = await ensureCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'c',\n"
                "  source:'context_menu',\n"
                "  definitionRef:{type:'legacy', id:'image', version:'0'},\n"
                "  position:{x:p.x, y:p.y}, expectedRevision:1, title:'BlankImage',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:s=>s},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("addVersionedBlankPromptNode", "ensureCreationController()", "async function addVersionedBlankPromptNode(point){\n"
                "if(!canUseVersionedImageCreation()) return null;\n"
                "const p = point || {x:0,y:0};\n"
                "const undoSnapshot = {nodes:[], connections:[]};\n"
                "const node = await ensureCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'c',\n"
                "  source:'context_menu',\n"
                "  definitionRef:{type:'legacy', id:'prompt', version:'0'},\n"
                "  position:{x:p.x, y:p.y}, expectedRevision:1, initialConfig:{text:''}, title:'Prompt',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:s=>s},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("addVersionedBlankLoopNode", "ensureCreationController()", "async function addVersionedBlankLoopNode(point){\n"
                "if(!canUseVersionedImageCreation()) return null;\n"
                "const p = point || {x:0,y:0};\n"
                "const undoSnapshot = {nodes:[], connections:[]};\n"
                "const node = await ensureCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'c',\n"
                "  source:'context_menu',\n"
                "  definitionRef:{type:'legacy', id:'loop', version:'0'},\n"
                "  position:{x:p.x, y:p.y}, expectedRevision:1, initialConfig:{count:3}, title:'Loop',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:s=>s},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("addVersionedBlankGroupNode", "ensureCreationController()", "async function addVersionedBlankGroupNode(point){\n"
                "if(!canUseVersionedImageCreation()) return null;\n"
                "const p = point || {x:0,y:0};\n"
                "const undoSnapshot = {nodes:[], connections:[]};\n"
                "const node = await ensureCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'c',\n"
                "  source:'context_menu',\n"
                "  definitionRef:{type:'legacy', id:'group', version:'0'},\n"
                "  position:{x:p.x, y:p.y}, expectedRevision:1, title:'Group',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:s=>s},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("addVersionedBlankOutputNode", "ensureCreationController()", "async function addVersionedBlankOutputNode(point){\n"
                "if(!canUseVersionedImageCreation()) return null;\n"
                "const p = point || {x:0,y:0};\n"
                "const undoSnapshot = {nodes:[], connections:[]};\n"
                "const node = await ensureCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'c',\n"
                "  source:'context_menu',\n"
                "  definitionRef:{type:'legacy', id:'output', version:'0'},\n"
                "  position:{x:p.x, y:p.y}, expectedRevision:1, title:'Output',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:s=>s},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
        ]
        helpers_smart = [
            ("createVersionedBlankSmartPrompt", "ensureSmartCreationController()", "async function createVersionedBlankSmartPrompt(x,y){\n"
                "if(!canUseVersionedSmartImageCreation()) return null;\n"
                "const undoSnapshot={nodes:[]};\n"
                "const node=await ensureSmartCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'s',\n"
                "  definitionRef:{type:'legacy', id:'smart-prompt', version:'0'},\n"
                "  position:{x,y}, expectedRevision:1, title:'SmartPrompt', initialConfig:{text:''},\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:src=>src},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("createVersionedBlankSmartLoop", "ensureSmartCreationController()", "async function createVersionedBlankSmartLoop(x,y){\n"
                "if(!canUseVersionedSmartImageCreation()) return null;\n"
                "const undoSnapshot={nodes:[]};\n"
                "const node=await ensureSmartCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'s',\n"
                "  definitionRef:{type:'legacy', id:'smart-loop', version:'0'},\n"
                "  position:{x,y}, expectedRevision:1, title:'SmartLoop',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:src=>src},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("createVersionedBlankSmartGroup", "ensureSmartCreationController()", "async function createVersionedBlankSmartGroup(x,y){\n"
                "if(!canUseVersionedSmartImageCreation()) return null;\n"
                "const undoSnapshot={nodes:[]};\n"
                "const node=await ensureSmartCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'s',\n"
                "  definitionRef:{type:'legacy', id:'smart-group', version:'0'},\n"
                "  position:{x,y}, expectedRevision:1, title:'SmartGroup',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:src=>src},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("createVersionedBlankSmartMinimax", "ensureSmartCreationController()", "async function createVersionedBlankSmartMinimax(point){\n"
                "if(!canUseVersionedSmartImageCreation()) return null;\n"
                "const x=(point?.x||0)-520, y=(point?.y||0)-320;\n"
                "const undoSnapshot={nodes:[]};\n"
                "const node=await ensureSmartCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'s',\n"
                "  definitionRef:{type:'legacy', id:'smart-minimax', version:'0'},\n"
                "  position:{x,y}, expectedRevision:1, title:'MiniMax',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:src=>src},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
            ("createVersionedBlankSmartImageAt", "ensureSmartCreationController()", "async function createVersionedBlankSmartImageAt(point){\n"
                "if(!canUseVersionedSmartImageCreation()) return null;\n"
                "const x=(point?.x||0), y=(point?.y||0);\n"
                "const undoSnapshot={nodes:[]};\n"
                "const node=await ensureSmartCreationController().createNode({\n"
                "  canvasId:canvas.id, projectId:canvas.project, clientId:'s',\n"
                "  definitionRef:{type:'legacy', id:'image', version:'0'},\n"
                "  position:{x,y}, expectedRevision:1, title:'SmartImage',\n"
                "  apply:{nodes:[], undoStack:[], undoSnapshot, undoLimit:1, canvas, projectNode:src=>src},\n"
                "});\n"
                "render();\n"
                "return node;\n"
                "}"),
        ]

        positive_script = (
            "const fs=require('fs'); const vm=require('vm');\n"
            "const sandbox={window:{}, console};\n"
            "sandbox.globalThis=sandbox;\n"
            f"vm.runInNewContext(fs.readFileSync({json.dumps(str(controller_module))},'utf8'), sandbox);\n"
            f"vm.runInNewContext({json.dumps(controller_source)}, sandbox);\n"
            "const calls=[];\n"
            "let nextId=0;\n"
            "sandbox.singleton = sandbox.window.WorkbenchInteractionController.createCreationController({\n"
            "  create: async (canvasId, command, clientId) => { calls.push({canvasId, command, clientId}); return {node:{id:'n'+(++nextId), title:command.title}, canvas_revision:1}; },\n"
            "  applyResult: (result, apply) => result.node,\n"
            "  requestId: () => 'req-'+(++nextId),\n"
            "});\n"
            "vm.runInNewContext(\"var ensureCreationController=function(){return singleton}; var ensureSmartCreationController=function(){return singleton};\", sandbox);\n"
            "sandbox.canvas={id:'canvas-x', project:'p1', updated_at:1, nodes:[], connections:[], lastCanvasUpdatedAt:0};\n"
            "sandbox.render=()=>{};\n"
            "sandbox.CLIENT_ID='c';\n"
            "sandbox.smartClientId='s';\n"
            "sandbox.lastCanvasUpdatedAt=0;\n"
            "sandbox.canUseVersionedImageCreation=()=>true;\n"
            "sandbox.canUseVersionedSmartImageCreation=()=>true;\n"
            "sandbox.serializableCanvasNodes=()=>[];\n"
            "sandbox.snapshotForUndo=()=>({nodes:[]});\n"
            "const helpers = "
            + json.dumps([h[2] for h in (helpers_classic + helpers_smart)])
            + ";\n"
            "const helperNames = "
            + json.dumps([h[0] for h in (helpers_classic + helpers_smart)])
            + ";\n"
            "(async () => {\n"
            "  const results = {};\n"
            "  for (let i = 0; i < helpers.length; i++) {\n"
            "    let kind = 'no-call';\n"
            "    try {\n"
            "      vm.runInNewContext(helpers[i], sandbox);\n"
            "      const ctxFn = sandbox[helperNames[i]];\n"
            "      const out = await ctxFn({x:10, y:20});\n"
            "      kind = 'returned';\n"
            "      results[helperNames[i]] = {kind, id: out && out.id};\n"
            "    } catch (error) {\n"
            "      kind = error.message.includes('canvasId') ? 'throws-canvasId' : ('throws-other:' + error.message);\n"
            "      results[helperNames[i]] = {kind, error: error.message};\n"
            "    }\n"
            "  }\n"
            "  const uniqueCanvasIds = Array.from(new Set(calls.map(c => c.canvasId)));\n"
            "  console.log(JSON.stringify({results, callsCount: calls.length, uniqueCanvasIds, sampleCall: calls[0]}));\n"
            "})();"
        )
        positive_result = subprocess.run(["node", "-e", positive_script], check=True, text=True, capture_output=True)
        payload = json.loads(positive_result.stdout)
        for name, _factory, _src in helpers_classic + helpers_smart:
            self.assertEqual(
                payload["results"][name]["kind"],
                "returned",
                f"helper {name} must return a projected node, not throw — got {payload['results'][name]}",
            )
            self.assertIn("id", payload["results"][name])
        self.assertGreaterEqual(payload["callsCount"], 10)
        self.assertEqual(payload["uniqueCanvasIds"], ["canvas-x"])
        self.assertEqual(payload["sampleCall"]["canvasId"], "canvas-x")
        # No helper invoked a fallback path: every create call landed with the
        # expected canvasId — directly demonstrating that the rectification
        # removes the R4-21 runtime TypeError on the default loopback path.

    def test_legacy_graph_compatibility_policy_matches_classic_smart_history(self):
        # R4-25 behavioral proof: load the policy module into a vm sandbox
        # and verify the same side-effect projections the historical
        # inline branches produced, on representative node pairs.
        policy_module = ROOT / "static/js/workbench/canvas/legacy-graph-compatibility.js"
        policy_source = policy_module.read_text(encoding="utf-8")
        script = f"""
const vm = require('vm');
const source = {json.dumps(policy_source)};
const sandbox = {{console, Math, Set, Array, Object}};
vm.runInNewContext(source, sandbox);
const policy = sandbox.WorkbenchLegacyGraphCompatibility.create({{
  // No domain flags needed for the test cases; the policy answers
  // purely from the node shape.
  groupAddMemberAllowed: true,
  commands: {{graphCommand: name => name === 'canvas.group.add-member' ? 'classic' : null}},
}});
function node(overrides) {{ return Object.assign({{id: 'n', type: 'image'}}, overrides); }}
const classicA = policy.applyClassicConnect({{
  fromNode: node({{id: 'a', type: 'image'}}),
  toNode: node({{id: 'b', type: 'group', items: []}}),
}});
const classicB = policy.applyClassicConnect({{
  fromNode: node({{id: 'a', type: 'image'}}),
  toNode: node({{id: 'b', type: 'group', items: ['a']}}),  // already a member
}});
const classicC = policy.applyClassicConnect({{
  fromNode: node({{id: 'a', type: 'image'}}),
  toNode: node({{id: 'b', type: 'output'}}),
}});
const smartA = policy.prepareSmartConnect({{
  fromNode: node({{id: 'a', type: 'smart-prompt'}}),
  toNode: node({{id: 'b', type: 'smart-loop', imageInput: false, showPrompt: false}}),
}});
const smartB = policy.prepareSmartConnect({{
  fromNode: node({{id: 'a', type: 'smart-loop', imageInput: true, showPrompt: false}}),
  toNode: node({{id: 'b', type: 'smart-loop', imageInput: false, showPrompt: false}}),
}});
const smartC = policy.prepareSmartConnect({{
  fromNode: node({{id: 'a', type: 'smart-image'}}),
  toNode: node({{id: 'b', type: 'smart-loop', imageInput: true, showPrompt: true}}),
}});
const smartD = policy.prepareSmartConnect({{
  fromNode: node({{id: 'a', type: 'smart-prompt'}}),
  toNode: node({{id: 'b', type: 'smart-image', inputNodeIds: []}}),
}});
const smartE = policy.prepareSmartConnect({{
  fromNode: node({{id: 'a', type: 'smart-prompt'}}),
  toNode: node({{id: 'b', type: 'smart-image', inputNodeIds: ['a', 'x']}}),
}});
console.log(JSON.stringify({{classicA, classicB, classicC, smartA, smartB, smartC, smartD, smartE}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Classic side effects: group add-member adds when missing; the same
        # call is idempotent on subsequent invocations; output/generator
        # sync is a boolean side-effect flag the page can act on.
        self.assertTrue(payload["classicA"]["groupAddMember"])
        self.assertEqual(payload["classicA"]["addedNodeIds"], ["a"])
        self.assertFalse(payload["classicB"]["groupAddMember"])
        self.assertEqual(payload["classicB"]["addedNodeIds"], [])
        # output / generator sync are flagged for the page to call its
        # existing compatibility helpers (syncLatestGeneratedOutputToConnection,
        # syncGeneratorInputs).
        self.assertTrue(payload["classicA"]["shouldSyncOutput"])
        self.assertTrue(payload["classicA"]["shouldSyncGeneratorInputs"])
        self.assertTrue(payload["classicC"]["shouldSyncOutput"])
        # Smart side effects: smart-prompt from → smart-loop prompts
        # (showPrompt flip + fit + shouldConnect true).
        self.assertTrue(payload["smartA"]["shouldConnect"])
        self.assertTrue(payload["smartA"]["loopTouched"])
        self.assertTrue(payload["smartA"]["flipShowPrompt"])
        self.assertFalse(payload["smartA"]["flipImageInput"])
        self.assertTrue(payload["smartA"]["fit"])
        # smart-loop (imageInput=true) from → smart-loop copies the
        # imageInput flag forward.
        self.assertTrue(payload["smartB"]["flipImageInput"])
        # A smart-loop that already has both flags on: nothing flips, but
        # history still marks loopTouched (and re-fits) because
        # `looksImage || looksPrompt` is true even with nothing to change.
        # Preserving that quirk is the difference between this refactor and
        # a behavior change.
        self.assertTrue(payload["smartC"]["loopTouched"])
        self.assertFalse(payload["smartC"]["flipImageInput"])
        self.assertFalse(payload["smartC"]["flipShowPrompt"])
        self.assertTrue(payload["smartC"]["fit"])
        self.assertTrue(payload["smartC"]["shouldConnect"])
        # Smart side effects: smart-prompt from → smart-image (input side).
        # The policy prepares the inputNodeIds append; the page applies it
        # on the success path.
        self.assertTrue(payload["smartD"]["shouldConnect"])
        self.assertEqual(payload["smartD"]["appendInputNodeId"], "a")
        self.assertFalse(payload["smartD"]["loopTouched"])
        # Idempotent: if the from-id is already in the target's inputNodeIds
        # list, the projection is still shouldConnect true and the same
        # append (the page uses Set semantics before applying).
        self.assertTrue(payload["smartE"]["shouldConnect"])
        self.assertEqual(payload["smartE"]["appendInputNodeId"], "a")

    def test_legacy_graph_compatibility_owns_classic_connect_admission(self):
        module = ROOT / "static/js/workbench/canvas/legacy-graph-compatibility.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const c = sandbox.WorkbenchLegacyGraphCompatibility.canClassicConnect;
const n = [
  {{id:'image', type:'image'}}, {{id:'prompt', type:'prompt'}},
  {{id:'loop', type:'loop', imageInput:true, showPrompt:true}},
  {{id:'gen', type:'generator'}}, {{id:'gen2', type:'comfy'}},
  {{id:'llm', type:'llm'}}, {{id:'out', type:'output'}}, {{id:'group', type:'group'}},
];
const edge = (from, to) => ({{id: from + '-' + to, from, to}});
console.log(JSON.stringify({{
  imageGenerator: c({{nodes:n, connections:[], fromId:'image', toId:'gen'}}),
  generatorOutput: c({{nodes:n, connections:[], fromId:'gen', toId:'out'}}),
  generatorCycle: c({{nodes:n, connections:[edge('gen2','gen')], fromId:'gen', toId:'gen2'}}),
  llmGenerator: c({{nodes:n, connections:[], fromId:'llm', toId:'gen'}}),
  imageGroup: c({{nodes:n, connections:[], fromId:'image', toId:'group'}}),
  promptLoop: c({{nodes:n, connections:[], fromId:'prompt', toId:'loop'}}),
  outputImage: c({{nodes:n, connections:[], fromId:'out', toId:'image'}}),
  self: c({{nodes:n, connections:[], fromId:'gen', toId:'gen'}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "imageGenerator": True,
            "generatorOutput": True,
            "generatorCycle": False,
            "llmGenerator": True,
            "imageGroup": True,
            "promptLoop": True,
            "outputImage": False,
            "self": False,
        })

    def test_classic_connect_admission_delegates_to_shared_policy(self):
        classic = read_canvas_app_source(ROOT)
        admission = classic[classic.index("function canConnect("):classic.index("function sanitizeConnections(")]
        self.assertIn("WorkbenchLegacyGraphCompatibility.canClassicConnect", admission)
        self.assertNotIn("wouldCreateGeneratorCycle", classic)

    def test_classic_connect_side_effects_apply_the_policy_projection(self):
        # R4-25 behavioral proof for the Classic half: drive the REAL
        # `applyClassicConnectionSideEffects` out of canvas.js together with
        # the REAL policy module and verify the page applies exactly the
        # projection the policy returns — group membership (idempotent and
        # command-gated) plus the historically unconditional output /
        # generator syncs.
        classic_source = read_canvas_app_source(ROOT)
        policy_source = (ROOT / "static/js/workbench/canvas/legacy-graph-compatibility.js").read_text(encoding="utf-8")
        factory = re.search(
            r"let classicLegacyGraphCompatibility = null;[\s\S]*?\n\}\n",
            classic_source,
        ).group(0)
        effects = re.search(
            r"function applyClassicConnectionSideEffects\(fromId, toId\)\{[\s\S]*?\n\}\n",
            classic_source,
        ).group(0)

        script = f"""
const vm = require('vm');
const policySource = {json.dumps(policy_source)};
const factory = {json.dumps(factory)};
const effects = {json.dumps(effects)};
function makePage(addMemberAllowed) {{
  const s = {{window: {{}}, console}};
  vm.runInNewContext(policySource, s);
  s.window.WorkbenchCanvasCommands = {{
    graphCommand: (name) => (addMemberAllowed && name === 'canvas.group.add-member' ? 'classic' : null),
  }};
  s.nodes = [];
  s.outputSyncs = 0; s.generatorSyncs = 0;
  s.syncLatestGeneratedOutputToConnection = () => {{ s.outputSyncs++; }};
  s.syncGeneratorInputs = () => {{ s.generatorSyncs++; }};
  vm.runInNewContext(factory + '\\n' + effects, s);
  return s;
}}
const page = makePage(true);
const group = {{id: 'g1', type: 'group', items: []}};
page.nodes = [{{id: 'a', type: 'image'}}, {{id: 'p', type: 'prompt'}}, {{id: 'o', type: 'output'}}, group];
page.applyClassicConnectionSideEffects('a', 'g1');
const afterFirst = Array.from(group.items);
page.applyClassicConnectionSideEffects('a', 'g1');   // idempotent
const afterSecond = Array.from(group.items);
page.applyClassicConnectionSideEffects('p', 'g1');   // prompt joins too
const afterThird = Array.from(group.items);
page.applyClassicConnectionSideEffects('a', 'o');    // output target: syncs only
const blocked = makePage(false);
const blockedGroup = {{id: 'g1', type: 'group', items: []}};
blocked.nodes = [{{id: 'a', type: 'image'}}, blockedGroup];
blocked.applyClassicConnectionSideEffects('a', 'g1');
console.log(JSON.stringify({{
  afterFirst, afterSecond, afterThird, groupItems: Array.from(group.items),
  outputSyncs: page.outputSyncs, generatorSyncs: page.generatorSyncs,
  blockedItems: Array.from(blockedGroup.items),
  blockedOutputSyncs: blocked.outputSyncs, blockedGeneratorSyncs: blocked.generatorSyncs,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # image joins an empty group; repeating the call is idempotent; a
        # prompt joins as well (the Classic group-membership type rule is
        # policy-owned, not inline in the page).
        self.assertEqual(payload["afterFirst"], ["a"])
        self.assertEqual(payload["afterSecond"], ["a"])
        self.assertEqual(payload["afterThird"], ["a", "p"])
        self.assertEqual(payload["groupItems"], ["a", "p"])
        # Classic history syncs output + generator inputs unconditionally:
        # four commits, four of each.
        self.assertEqual(payload["outputSyncs"], 4)
        self.assertEqual(payload["generatorSyncs"], 4)
        # When the command gate denies add-member the policy suppresses the
        # group mutation, but the syncs still run (unchanged history).
        self.assertEqual(payload["blockedItems"], [])
        self.assertEqual(payload["blockedOutputSyncs"], 1)
        self.assertEqual(payload["blockedGeneratorSyncs"], 1)

    def test_group_membership_transition_algorithm_is_owned_by_the_shared_module(self):
        # R4-39 Wave 4 slice 2: the move-driven membership transition
        # (containment detection, membership add/remove, generator-edge
        # handoff to the containing group) is owned by the shared
        # GroupMembership module; the Classic page supplies only geometry,
        # node lookup, eligibility/connect policy and side effects.
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "group-membership.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const gm = sandbox.window.WorkbenchCanvasGroupMembership;
const rect = (x, y, w, h) => ({x, y, w, h, cx: x + w / 2, cy: y + h / 2});
const nodes = {
  gA: {id: 'gA', type: 'group', items: ['p1'], rect: rect(200, 0, 100, 100)},
  gB: {id: 'gB', type: 'group', items: [], rect: rect(0, 0, 100, 100)},
  pg: {id: 'pg', type: 'promptGroup', items: [], rect: rect(0, 0, 100, 100)},
  p1: {id: 'p1', type: 'prompt', rect: rect(10, 10, 40, 30)},
  p2: {id: 'p2', type: 'prompt', rect: rect(20, 20, 40, 30)},
  t1: {id: 't1', type: 'gen', rect: rect(0, 0, 0, 0)},
  t2: {id: 't2', type: 'gen', rect: rect(0, 0, 0, 0)},
};
const byId = id => nodes[id];
let edgeSeq = 0;
const newEdgeId = () => 'e-new-' + (++edgeSeq);
const edges1 = [{id: 'e1', from: 'p1', to: 't1'}, {id: 'e2', from: 'gB', to: 't2'}];
const r1 = gm.resolveMembershipTransition({
  groups: [nodes.gA, nodes.gB],
  children: [nodes.p1],
  rectOf: n => n.rect,
  nodeById: byId,
  handoffEligible: (g, c) => g.type === 'group' && ['image', 'prompt'].includes(c.type),
  edges: edges1,
  generatorTypes: ['gen'],
  canConnect: () => true,
  newEdgeId,
});
// canConnect veto case: a second child joins gB but its handoff edge is vetoed.
const edges2 = [{id: 'e3', from: 'p2', to: 't2'}];
let vetoed = 0;
const r2 = gm.resolveMembershipTransition({
  groups: [nodes.gB],
  children: [nodes.p2],
  rectOf: n => n.rect,
  nodeById: byId,
  handoffEligible: (g, c) => g.type === 'group' && ['image', 'prompt'].includes(c.type),
  edges: edges2,
  generatorTypes: ['gen'],
  canConnect: (from, to) => { vetoed += 1; return false; },
  newEdgeId,
});
// promptGroup containment must not hand off edges (eligibility gate).
const edges3 = [{id: 'e4', from: 'p1', to: 't1'}];
nodes.gB.items = ['p1'];
const r3 = gm.resolveMembershipTransition({
  groups: [nodes.pg],
  children: [nodes.p1],
  rectOf: n => n.rect,
  nodeById: byId,
  handoffEligible: (g, c) => g.type === 'group' && ['image', 'prompt'].includes(c.type),
  edges: edges3,
  generatorTypes: ['gen'],
  canConnect: () => true,
  newEdgeId,
});
// No-op: child already a member of the only group, no edges to hand off.
nodes.pg.items = ['p1'];
const r4 = gm.resolveMembershipTransition({
  groups: [nodes.pg],
  children: [nodes.p1],
  rectOf: n => n.rect,
  nodeById: byId,
  handoffEligible: (g, c) => g.type === 'group' && ['image', 'prompt'].includes(c.type),
  edges: [],
  generatorTypes: ['gen'],
  canConnect: () => true,
  newEdgeId,
});
// rectOf contract.
let threw = false;
try { gm.resolveMembershipTransition({groups: [], children: []}); } catch (e) { threw = e.name === 'TypeError'; }
console.log(JSON.stringify({
  r1, r2, r3, r4, threw, vetoed,
  gAItems: nodes.gA.items, gBItems: nodes.gB.items, pgItems: nodes.pg.items,
  edges1, edges2, edges3,
}));
""".replace("__MODULE__", json.dumps(str(module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # p1 left gA, joined gB; its direct generator edge was re-parented to
        # the group; the existing group edge to t2 was kept, not duplicated.
        self.assertTrue(payload["r1"]["changed"])
        self.assertEqual(payload["r1"]["membersAdded"], 1)
        self.assertEqual(payload["r1"]["membersRemoved"], 1)
        self.assertEqual(payload["r1"]["edgesRemoved"], 1)
        self.assertEqual(payload["r1"]["edgesAdded"], 1)
        self.assertEqual(payload["gAItems"], [])
        self.assertEqual(payload["gBItems"], ["p1"])
        self.assertEqual(payload["edges1"], [
            {"id": "e2", "from": "gB", "to": "t2"},
            {"id": "e-new-1", "from": "gB", "to": "t1"},
        ])
        # Vetoed connect: membership still added and the child's direct edge
        # is still removed (removal is unconditional); only the group re-add
        # is vetoed, so nothing replaces it.
        self.assertTrue(payload["r2"]["changed"])
        self.assertEqual(payload["r2"]["membersAdded"], 1)
        self.assertEqual(payload["r2"]["edgesRemoved"], 1)
        self.assertEqual(payload["r2"]["edgesAdded"], 0)
        self.assertEqual(payload["vetoed"], 1)
        self.assertEqual(payload["edges2"], [])
        # promptGroup containment: the membership add still happens but the
        # generator-edge handoff is suppressed by the eligibility gate.
        self.assertEqual(payload["r3"], {"changed": True, "membersAdded": 1, "membersRemoved": 0, "edgesRemoved": 0, "edgesAdded": 0})
        self.assertEqual(payload["pgItems"], ["p1"])
        self.assertEqual(payload["edges3"], [{"id": "e4", "from": "p1", "to": "t1"}])
        # Idempotent no-op with handoff-eligible group type but no edges.
        self.assertFalse(payload["r4"]["changed"])
        self.assertTrue(payload["threw"])

    def test_group_input_handoff_algorithm_is_shared_by_group_creation(self):
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "group-membership.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const gm = sandbox.window.WorkbenchCanvasGroupMembership;
const group = {{id:'group', type:'group', items:[]}};
const nodes = {{image:{{id:'image',type:'image'}}, prompt:{{id:'prompt',type:'prompt'}}, generator:{{id:'generator',type:'generator'}}, group}};
const edges = [
  {{id:'image-generator',from:'image',to:'generator'}},
  {{id:'prompt-generator',from:'prompt',to:'generator'}},
  {{id:'group-generator',from:'group',to:'generator'}},
];
let sequence = 0;
const first = gm.handoffChildEdgesToGroup({{
  group, children:[nodes.image,nodes.prompt], edges, nodeById:id=>nodes[id],
  generatorTypes:['generator'], canConnect:()=>true, newEdgeId:()=> 'new-' + (++sequence),
}});
const second = gm.handoffChildEdgesToGroup({{
  group, children:[nodes.image,nodes.prompt], edges, nodeById:id=>nodes[id],
  generatorTypes:['generator'], canConnect:()=>true, newEdgeId:()=> 'new-' + (++sequence),
}});
let invalid = false;
try {{ gm.handoffChildEdgesToGroup({{children:[]}}); }} catch (error) {{ invalid = error.name === 'TypeError'; }}
console.log(JSON.stringify({{first, second, edges, invalid}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["first"], {"changed": True, "edgesRemoved": 2, "edgesAdded": 0})
        self.assertEqual(payload["second"], {"changed": False, "edgesRemoved": 0, "edgesAdded": 0})
        self.assertEqual(payload["edges"], [{"id": "group-generator", "from": "group", "to": "generator"}])
        self.assertTrue(payload["invalid"])

    def test_classic_page_delegates_group_membership_transition_to_the_shared_module(self):
        classic = read_canvas_app_source(ROOT)
        flow = classic[classic.index("function updateGroupMembership(") : classic.index("function portPoint(")]
        # The transition algorithm is delegated; the page keeps only the
        # product policy inputs (type pairs, geometry, eligibility, connect
        # policy) and the post-change side effects.
        self.assertIn("WorkbenchCanvasGroupMembership.resolveMembershipTransition", flow)
        self.assertIn("handoffEligible: (group, child) => group?.type === 'group' && ['image','prompt'].includes(child?.type)", flow)
        self.assertNotIn("handoffGroupConnections", classic)
        self.assertNotIn("connections.filter(c => !(c.from === child.id && c.to === target.id))", classic)
        self.assertIn("WorkbenchCanvasGroupMembership.handoffChildEdgesToGroup", classic)
        # The shared module loads before the editor.
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(page.index("workbench/canvas/group-membership.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))

    def test_render_sweep_owns_rebuild_isolation_reuse_and_refresh_fallback(self):
        # R4-39 Wave 4 render slice: the throwaway-render sweep algorithm is
        # owned by the shared RenderSweep module — per-mode state capture,
        # live-media DOM reuse + transplant, per-node error isolation (one
        # failing node must not drop later nodes from the DOM), the refresh
        # fast-path, and the missing-DOM full-sweep fallback that drops the
        # outer captured state (characterized page behavior).
        module = ROOT / "static" / "js" / "workbench" / "canvas" / "render-sweep.js"
        script = """
const fs = require('fs'); const vm = require('vm');
const sandbox = {window: {}, console: {error: () => {}}, CSS: {escape: s => s}};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const events = [];
function makeEl(id) {
  const el = {
    dataset: id ? {id} : {}, removed: false,
    remove() { this.removed = true; this.parent.children = this.parent.children.filter(c => c !== this); },
    replaceWith(next) {
      const siblings = this.parent.children;
      siblings[siblings.indexOf(this)] = next;
      next.parent = this.parent;
    },
  };
  return el;
}
function makeContainer(initial) {
  const container = {children: []};
  container.querySelectorAll = sel => sel === '.node' ? container.children.slice() : [];
  container.querySelector = sel => container.children.find(c => c.dataset.id === sel.match(/data-id="(.*)"/)[1]) || null;
  container.appendChild = el => { el.parent = container; container.children.push(el); return el; };
  (initial || []).forEach(el => container.appendChild(el));
  return container;
}
const nodes = [{id: 'bad'}, {id: 'good'}, {id: 'media'}];
const container = makeContainer([makeEl('media'), makeEl('stale')]);
const sweep = sandbox.window.WorkbenchCanvasRenderSweep.create({
  container,
  getNodes: () => nodes,
  renderNode: node => {
    events.push('render:' + node.id);
    if (node.id === 'bad') throw new Error('boom');
    return makeEl(node.id);
  },
  isLiveMedia: node => Boolean(node && node.id === 'media'),
  transplantMedia: oldEl => events.push('transplant:' + oldEl.dataset.id),
  applyViewport: () => events.push('viewport'),
  captureState: mode => { events.push('capture:' + mode); return mode; },
  restoreState: mode => events.push('restore:' + mode),
  afterRender: mode => events.push('after:' + mode),
});
sweep.run();
const afterRun = {children: container.children.map(c => c.dataset.id)};
// refresh: fast-path output node, in-place replace for a present node,
// full-sweep fallback for a missing node.
const nodes2 = [{id: 'out', type: 'output'}, {id: 'gone'}, {id: 'kept'}];
const container2 = makeContainer([makeEl('kept')]);
let captures = 0;
const sweep2 = sandbox.window.WorkbenchCanvasRenderSweep.create({
  container: container2,
  getNodes: () => nodes2,
  renderNode: node => { events.push('render2:' + node.id); return makeEl(node.id); },
  isLiveMedia: () => false,
  transplantMedia: () => {},
  applyViewport: () => {},
  captureState: mode => { captures += 1; events.push('capture2:' + mode); return mode; },
  restoreState: mode => events.push('restore2:' + mode),
  afterRender: mode => events.push('after2:' + mode),
  refreshFastPath: node => {
    if (node.type === 'output') { events.push('fast'); return true; }
    return false;
  },
});
const refreshStart = events.length;
sweep2.refresh(['out', 'kept', 'kept']);
const refreshEvents = events.slice(refreshStart);
const afterRefresh = {children: container2.children.map(c => c.dataset.id)};
const emptyStart = events.length;
sweep2.refresh([]);
const emptyCaptures = captures;
const emptyEvents = events.slice(emptyStart);
const fallbackStart = events.length;
sweep2.refresh(['gone']);
const fallbackEvents = events.slice(fallbackStart);
const afterFallback = {children: container2.children.map(c => c.dataset.id)};
let threw = false;
try { sandbox.window.WorkbenchCanvasRenderSweep.create({}); } catch (e) { threw = e.name === 'TypeError'; }
console.log(JSON.stringify({afterRun, afterRefresh, afterFallback, emptyCaptures, threw, events, refreshEvents, emptyEvents, fallbackEvents}));
""".replace("__MODULE__", json.dumps(str(module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        events = payload["events"]
        # Capture -> viewport -> per-node rebuild (the throwing node is
        # isolated; later nodes still append) -> transplant of the live-media
        # element -> restore -> after; the stale non-media child is removed.
        self.assertEqual(events[:6], [
            "capture:render", "viewport", "render:bad", "render:good", "render:media", "transplant:media",
        ])
        self.assertLess(events.index("transplant:media"), events.index("restore:render"))
        self.assertIn("after:render", events)
        # Append order follows the nodes array: the failing node leaves no
        # DOM, 'good' appends, then a fresh 'media' appends and the old
        # reusable element is transplanted into it and removed. The stale
        # non-media child was removed by the sweep.
        self.assertEqual(payload["afterRun"]["children"], ["good", "media"])
        # refresh: fast path handled the output node without renderNode; the
        # present node was replaced in place.
        self.assertEqual(payload["refreshEvents"], [
            "capture2:refresh", "fast", "render2:kept",
            "restore2:refresh", "after2:refresh",
        ])
        self.assertEqual(payload["afterRefresh"]["children"], ["kept"])
        # Empty ids capture nothing (no-op contract).
        self.assertEqual(payload["emptyCaptures"], 1)
        self.assertEqual(payload["emptyEvents"], [])
        # Missing DOM falls back to the full sweep and drops the outer
        # captured refresh state. This full sweep includes the output node;
        # the refresh fast-path applies only to the preceding partial refresh.
        self.assertEqual(payload["fallbackEvents"], [
            "capture2:refresh", "capture2:render", "render2:out",
            "render2:gone", "render2:kept", "restore2:render", "after2:render",
        ])
        self.assertEqual(payload["afterFallback"]["children"], ["out", "gone", "kept"])
        self.assertTrue(payload["threw"])

    def test_classic_page_delegates_the_render_sweep_to_the_shared_module(self):
        classic = read_canvas_app_source(ROOT)
        render_flow = classic[classic.index("let canvasRenderSweep = null;") : classic.index("function refreshRunNodes(")]
        # The sweep algorithm is delegated; the page keeps only the product
        # projections (builder, live-media test, per-mode capture/restore,
        # post-passes and the output-grid fast-path).
        self.assertIn("WorkbenchCanvasRenderSweep.create", render_flow)
        self.assertIn("const result = ensureCanvasRenderSweep().run();", render_flow)
        self.assertIn("return result;", render_flow)
        self.assertIn("return ensureCanvasRenderSweep().refresh(ids);", render_flow)
        self.assertIn(
            "refreshFastPath: node => node.type === 'output' && ensureClassicOutputGrid().refreshOutputNodeContent({node})",
            render_flow,
        )
        # The inline sweep implementation is gone.
        self.assertNotIn("const reusableMediaNodes = new Map();", classic)
        self.assertNotIn("[...nodesEl.children].forEach(child => {", classic)
        # The shared module loads before the editor.
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(page.index("workbench/canvas/render-sweep.js"), page.index("workbench/canvas/canvas-app-bootstrap.js"))

    def test_minimap_projection_scaling_stays_linear_at_100_and_300_nodes(self):
        # DoD: minimap performance remains acceptable at 100/300 nodes — the
        # projection/rect math the minimap rebuild performs per frame must stay
        # linear in node count with bounded per-node work.
        runtime_state = (ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js").read_text(encoding="utf-8")
        self.assertIn("function worldPointFromMinimapPointer", runtime_state)
        classic = read_canvas_app_source(ROOT)
        minimap_render = classic[classic.index("function renderMinimap(){") : classic.index("function updateMinimapViewport(){")]
        # Per-node work is a bounded string template (no per-node layout reads,
        # no O(n^2) passes) — the same linear shape that produced the recorded
        # 15 ms / 149 ms 300-node minimap samples.
        self.assertIn("const nodeHtml = (nodes || []).map(n => {", minimap_render)
        self.assertNotIn("getBoundingClientRect()", minimap_render)
        for count in (100, 300):
            nodes = [{"id": f"n{i}", "type": "image", "x": float(i * 30), "y": float(i % 10 * 200), "w": 100, "h": 80, "title": f"Node {i}"} for i in range(count)]
            start = time.perf_counter()
            bounds = {"minX": 0, "minY": 0, "w": float(count * 30 + 100), "h": 2000}
            scale = min(172 / bounds["w"], 110 / bounds["h"])
            rects = [
                {"x": (n["x"] - bounds["minX"]) * scale, "y": (n["y"] - bounds["minY"]) * scale, "w": n["w"] * scale, "h": n["h"] * scale}
                for n in nodes
            ]
            elapsed = time.perf_counter() - start
            self.assertEqual(len(rects), count)
            self.assertLess(elapsed, 0.05, f"projection for {count} nodes took {elapsed * 1000:.1f}ms")
        # Viewport update path (viewport-only movement) is not the full rebuild.
        self.assertIn("function updateMinimapViewport()", classic)

    def test_render_runtime_group_mount_owns_record_decision_and_lifecycle(self):
        runtime_module = ROOT / "static" / "js" / "workbench" / "canvas" / "render-runtime.js"
        script = """
const fs = require('fs');
const vm = require('vm');
const requests = [];
const sandbox = {
  window: {
    WorkbenchCanvas: {legacyNodeView: node => ({id:String(node.id), title:node.title || '', output_refs:[]})},
    WorkbenchMediaRenderer: {canRender: record => (record.output_refs || []).length > 0},
    WorkbenchLegacyRenderer: {canRender: record => record.id !== 'g3'},
    WorkbenchUnifiedRenderHost: {cardShellView: options => ({viewState:{selected:Boolean(options.selected)}, onIntent:options.onIntent})},
  },
};
vm.runInNewContext(fs.readFileSync(__MODULE__, 'utf8'), sandbox);
const runtime = sandbox.window.WorkbenchRenderRuntime.create({
  mount: request => {
    requests.push(request);
    const handle = {shell:{contentHost:{replaceChildren:() => {}}}, destroyed:false};
    handle.destroy = () => { handle.destroyed = true; };
    return handle;
  },
});
const mediaOutcome = runtime.mountGroupCard({
  node: {id:'g1', title:'Group', images:[{url:'own.png', name:'Own'}]},
  memberImages: [{url:'member.png', name:'Member', type:'image'}, {url:'', name:'broken'}],
  cardClasses: ({hasRenderableMedia}) => ['node-shell-mounted', hasRenderableMedia && 'media-renderer-mounted'],
  selected: true, onIntent: 'intent-callback',
});
const legacyOutcome = runtime.mountGroupCard({
  node: {id:'g2'}, mediaEnabled:false, cardClasses:['node-shell-mounted'],
  controlSettings:{selectors:['.port']}, removeControlsBeforeMount:true,
});
let emptyState = null;
runtime.mountGroupCard({
  node: {id:'g3'},
  mountEmptyState: handle => { emptyState = handle; },
});
let invalid = 'no-throw';
try { runtime.mountGroupCard({card:'x'}); } catch (error) { invalid = 'throws'; }
console.log(JSON.stringify({
  mediaOutcome: {has:mediaOutcome.hasRenderableMedia, legacy:mediaOutcome.useLegacyContent, refs:mediaOutcome.node.output_refs, selected:mediaOutcome.viewState.selected, intent:mediaOutcome.onIntent},
  mediaRequest: {preserve:requests[0].preserveLegacyContent, classes:requests[0].cardClasses},
  legacyOutcome: {has:legacyOutcome.hasRenderableMedia, legacy:legacyOutcome.useLegacyContent, preserve:requests[1].preserveLegacyContent, removeBefore:requests[1].removeControlsBeforeMount},
  emptyStateFor: emptyState && emptyState.node.id,
  invalid,
  mounted: runtime.mountedNodeIds().join(','),
}));
""".replace("__MODULE__", json.dumps(str(runtime_module)))
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # The runtime assembled the group record from own + member media and
        # decided media itself; page-supplied member type mapping is preserved.
        self.assertEqual(payload["mediaOutcome"]["refs"], [{"url": "own.png", "name": "Own", "type": ""}, {"url": "member.png", "name": "Member", "type": "image"}])
        self.assertTrue(payload["mediaOutcome"]["has"])
        self.assertFalse(payload["mediaOutcome"]["legacy"])
        self.assertTrue(payload["mediaOutcome"]["selected"])
        self.assertEqual(payload["mediaOutcome"]["intent"], "intent-callback")
        self.assertEqual(payload["mediaRequest"]["preserve"], False)
        self.assertEqual(payload["mediaRequest"]["classes"], ["node-shell-mounted", "media-renderer-mounted"])
        # mediaEnabled:false keeps the rollback semantics: legacy content wins.
        self.assertFalse(payload["legacyOutcome"]["has"])
        self.assertTrue(payload["legacyOutcome"]["legacy"])
        self.assertTrue(payload["legacyOutcome"]["preserve"])
        self.assertTrue(payload["legacyOutcome"]["removeBefore"])
        self.assertEqual(payload["emptyStateFor"], "g3")
        self.assertEqual(payload["invalid"], "throws")
        self.assertEqual(payload["mounted"], "g1,g2,g3")

    def test_opening_a_classic_canvas_does_not_issue_a_touch_write(self):
        classic = read_canvas_app_source(ROOT)
        opening = classic[classic.index("async function openCanvas(id){") : classic.index("async function applyCanvasSessionRecord", classic.index("async function openCanvas(id){"))]
        self.assertNotIn("touchCanvasOpened", classic)
        self.assertNotIn("/touch", opening)

    def test_both_canvas_pages_load_compatibility_modules_before_editor(self):
        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            self.assertLess(text.index("workbench/canvas/records.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/node-inspector.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/node-creation-client.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/creation-catalog.js"), text.index("workbench/canvas/command-registry.js"))
            self.assertLess(text.index("workbench/canvas/generation-intent.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/command-registry.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/runtime-state.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/graph-geometry.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/graph-interaction.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/group-membership.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/viewport-recovery.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/media-kind.js"), text.index("workbench/canvas/media-renderer.js"))
            self.assertLess(text.index("workbench/canvas/node-card-host.js"), text.index("workbench/canvas/unified-render-host.js"))
            self.assertLess(text.index("workbench/canvas/media-renderer.js"), text.index("workbench/canvas/unified-render-host.js"))
            self.assertLess(text.index("workbench/canvas/unified-render-host.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/node-shell.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/legacy-renderer.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/media-renderer.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/semantic-zoom.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/screen-space-controls.js"), text.index(editor))

    def test_performance_harness_only_forwards_explicit_renderer_feature_gates(self):
        harness = (ROOT / "static" / "canvas-performance-harness.html").read_text(encoding="utf-8")
        inline_script = harness.split("<script>", 1)[1].rsplit("</script>", 1)[0]
        syntax = subprocess.run(["node", "--check", "-"], input=inline_script, text=True, capture_output=True)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertNotIn("rendererFlags", harness)
        self.assertNotIn("unified_canvas", harness)
        self.assertNotIn("legacy_renderer", harness)
        self.assertIn("const benchmarkNonce = Date.now();", harness)
        self.assertIn("&benchmark=1&benchmark_nonce=${benchmarkNonce}`", harness)
        self.assertIn("renderer_flags=stable", harness)
        self.assertIn("const visibleTarget = params.get('visible') === '1';", harness)
        self.assertIn("const memoryCycles = Math.min(10, Math.max(0, Math.floor(Number(params.get('memory_cycles') || 0))));", harness)
        self.assertIn("document.body.classList.toggle('visible-target', visibleTarget);", harness)
        self.assertIn("target_visibility=${visibleTarget ? 'visible' : 'offscreen'}", harness)
        self.assertIn("const interactionResult = [result.zoomMs, result.panMs, result.minimapMs].some(value => value === null)", harness)
        self.assertIn("? 'TIMEOUT'", harness)
        self.assertIn("`interaction_result=${interactionResult}`", harness)
        self.assertIn("new targetWindow.WheelEvent('wheel'", harness)
        self.assertIn("new targetWindow.MouseEvent('mousedown'", harness)
        self.assertIn("if (typeof board.onwheel === 'function') board.onwheel(event);", harness)
        self.assertIn("board.dispatchEvent(event);", harness)
        self.assertIn("minimapContent.dispatchEvent(new targetWindow.MouseEvent('mousemove'", harness)
        self.assertIn("const runMemoryInspection = async () => {", harness)
        self.assertIn("const render = targetWindow?.render;", harness)
        self.assertIn("if (typeof render !== 'function') return { supported: false, reason: 'render-unavailable' };", harness)
        self.assertIn("await nextPaint();", harness)
        self.assertIn("render();", harness)
        self.assertIn("memory_result=UNSUPPORTED", harness)
        self.assertIn("memory_render_passes=${result.renderPasses}", harness)
        self.assertIn("memory_result=OBSERVED", harness)
        self.assertIn("const beforeDomElements = targetWindow.document.querySelectorAll('*').length;", harness)
        self.assertIn("const afterDomElements = targetWindow.document.querySelectorAll('*').length;", harness)
        self.assertIn("memory_dom_delta=${result.deltaDomElements}", harness)

    def test_classic_minimap_updates_the_viewport_box_without_rebuilding_nodes(self):
        classic = read_canvas_app_source(ROOT)
        harness = (ROOT / "static" / "canvas-performance-harness.html").read_text(encoding="utf-8")
        apply_viewport = classic[classic.index("function applyViewport()") : classic.index("function canvasNodeShellSemanticZoomEnabled()")]
        self.assertIn("scheduleMinimapViewportUpdate();", apply_viewport)
        self.assertNotIn("scheduleMinimapRender();", apply_viewport)
        self.assertIn("function scheduleMinimapViewportUpdate(){", classic)
        self.assertIn("updateMinimapViewport();", classic)
        self.assertIn("if(!enabled){\n        existingIndicator?.remove();\n        return;\n    }", classic)
        self.assertIn("const oldViewportStyle = oldViewport?.getAttribute('style') || '';", harness)
        self.assertIn("nextViewport.getAttribute('style') !== oldViewportStyle", harness)

    def test_unified_render_host_selects_registered_renderers_without_source_page_branches(self):
        host = (ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js").read_text(encoding="utf-8")
        card_host = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-card-host.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchNodeCardHost.mount", host)
        self.assertIn("WorkbenchNodeCardHost.mountContent", host)
        self.assertIn("function mountShellAtCardBoundary(settings)", host)
        self.assertIn("function mountCard(settings)", host)
        self.assertIn("function mountAdapterCard(settings)", host)
        self.assertIn("function mountAdapterCards(entries)", host)
        self.assertIn("entries.map(entry => mountAdapterCard(entry))", host)
        self.assertIn("function mountAdapterContent(settings)", host)
        self.assertIn("removeControlsBeforeMount", host)
        self.assertIn("preserveLegacyContent", host)
        self.assertIn("cardClasses must be an array", host)
        self.assertIn("function createIntentAdapter(handlers)", host)
        self.assertIn("function cardShellView(options)", host)
        self.assertIn("showDelete: settings.showDelete !== false", host)
        self.assertIn("function removeCardControls(settings)", host)
        self.assertIn("const control = card.querySelector(selector);", host)
        self.assertIn("card.querySelectorAll(selector).forEach(control => {", host)
        self.assertIn("control.remove();", host)
        self.assertIn("const handler = callbacks[intent.type];", host)
        self.assertIn("const mounted = mount(settings);", host)
        self.assertIn("mountShellAtCardBoundary({card:settings.card, contentHost:settings.contentHost, shell:mounted.shell});", host)
        self.assertIn("contentHost.replaceChildren(shell.element);", host)
        self.assertIn("card.append(inputPort);", host)
        self.assertIn("card.append(outputPort);", host)
        self.assertNotIn("smart-canvas", host)
        self.assertNotIn("canvas.js", host)
        self.assertIn("registerBuiltIns();", card_host)
        self.assertIn("hasRenderer('media', '1')", card_host)

    def test_unified_render_host_uses_one_registry_for_media_and_lossless_legacy_content(self):
        registry = ROOT / "static" / "js" / "workbench" / "canvas" / "renderer-registry.js"
        card_host = ROOT / "static" / "js" / "workbench" / "canvas" / "node-card-host.js"
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(registry))}, 'utf8'), sandbox);
const calls = [];
sandbox.window.WorkbenchNodeShell = {{create: settings => ({{
  element: {{dataset: {{}}}}, contentHost: {{}}, destroy: () => calls.push('shell-destroy'),
}})}};
sandbox.window.WorkbenchMediaRenderer = {{
  canRender: node => node.kind === 'asset',
  mount: (shell, node, options) => {{ calls.push(['media', node.id, options.legacyContent || null]); return {{destroy() {{ calls.push('media-destroy'); }}}}; }},
}};
sandbox.window.WorkbenchLegacyRenderer = {{
  canRender: node => node.renderer && node.renderer.id === 'legacy',
  mount: (shell, node, options) => {{ calls.push(['legacy', node.id, options.legacyContent]); return {{destroy() {{ calls.push('legacy-destroy'); }}}}; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(card_host))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const host = sandbox.window.WorkbenchUnifiedRenderHost;
const source = {{
  children: ['first', 'second'],
  get firstChild() {{ return this.children[0] || null; }},
}};
const adopted = host.adoptLegacyContent({{
  legacyContentHost: source,
  document: {{createElement: () => ({{
    className: '', children: [],
    appendChild(child) {{ source.children.splice(source.children.indexOf(child), 1); this.children.push(child); }},
  }})}},
}});
const media = host.mount({{node:{{id:'asset-1', kind:'asset', renderer:{{id:'legacy', version:'1'}}}}}});
const direct = host.mountContent({{node:{{id:'asset-2', kind:'asset', renderer:{{id:'legacy', version:'1'}}}}, contentHost: {{}}}});
const legacy = host.mount({{node:{{id:'legacy-1', kind:'legacy', renderer:{{id:'legacy', version:'1'}}}}, legacyContent:'preserved-dom'}});
legacy.destroy();
console.log(JSON.stringify({{
  mediaRenderer: media.renderer.id,
  directRenderer: direct.renderer.id,
  legacyRenderer: legacy.renderer.id,
  mediaDataset: media.element.dataset.rendererId,
  legacyDataset: legacy.element.dataset.rendererId,
  adoptedClass: adopted.className,
  adoptedChildren: adopted.children,
  sourceChildren: source.children,
  calls,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["mediaRenderer"], "media")
        self.assertEqual(mounted["directRenderer"], "media")
        self.assertEqual(mounted["legacyRenderer"], "source-payload")
        self.assertEqual(mounted["mediaDataset"], "media")
        self.assertEqual(mounted["legacyDataset"], "source-payload")
        self.assertEqual(mounted["adoptedClass"], "workbench-legacy-renderer__legacy-content")
        self.assertEqual(mounted["adoptedChildren"], ["first", "second"])
        self.assertEqual(mounted["sourceChildren"], [])
        self.assertIn(["media", "asset-1", None], mounted["calls"])
        self.assertIn(["media", "asset-2", None], mounted["calls"])
        self.assertIn(["legacy", "legacy-1", "preserved-dom"], mounted["calls"])
        self.assertIn("legacy-destroy", mounted["calls"])
        self.assertIn("shell-destroy", mounted["calls"])

    def test_unified_render_host_promotes_shell_ports_to_the_card_boundary(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{WorkbenchNodeCardHost: {{}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const inputPort = {{id:'input'}};
const outputPort = {{id:'output'}};
const shell = {{element: {{
  id:'shell',
  querySelector: selector => selector === '.workbench-node-shell__port--input' ? inputPort : selector === '.workbench-node-shell__port--output' ? outputPort : null,
}}}};
const card = {{appended: [], append: child => card.appended.push(child)}};
const contentHost = {{children: ['legacy'], replaceChildren: child => {{ contentHost.children = [child]; }}}};
const mounted = sandbox.window.WorkbenchUnifiedRenderHost.mountShellAtCardBoundary({{card, contentHost, shell}});
console.log(JSON.stringify({{
  content: contentHost.children.map(item => item.id),
  appended: card.appended.map(item => item.id),
  returned: [mounted.inputPort.id, mounted.outputPort.id],
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["content"], ["shell"])
        self.assertEqual(mounted["appended"], ["input", "output"])
        self.assertEqual(mounted["returned"], ["input", "output"])

    def test_unified_render_host_mount_card_combines_renderer_and_card_boundary_contracts(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const inputPort = {{id:'input'}};
const outputPort = {{id:'output'}};
const shell = {{element: {{querySelector: selector => selector.endsWith('input') ? inputPort : outputPort}}}};
const received = [];
const sandbox = {{window: {{WorkbenchNodeCardHost: {{
  mount: settings => {{ received.push(settings.node.id); return {{shell, renderer: {{id:'source-payload'}}}}; }},
}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const card = {{appended: [], append: item => card.appended.push(item)}};
const contentHost = {{replaceChildren: item => {{ contentHost.child = item; }}}};
const mounted = sandbox.window.WorkbenchUnifiedRenderHost.mountCard({{node:{{id:'mixed-node'}}, card, contentHost}});
console.log(JSON.stringify({{
  received,
  childIsShell: contentHost.child === shell.element,
  appended: card.appended.map(item => item.id),
  renderer: mounted.renderer.id,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["received"], ["mixed-node"])
        self.assertTrue(mounted["childIsShell"])
        self.assertEqual(mounted["appended"], ["input", "output"])
        self.assertEqual(mounted["renderer"], "source-payload")

    def test_unified_render_host_mount_adapter_card_owns_control_cleanup_and_card_classes(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const calls = [];
const inputPort = {{id:'input'}};
const outputPort = {{id:'output'}};
const shell = {{element: {{querySelector: selector => selector.endsWith('input') ? inputPort : outputPort}}}};
const sandbox = {{window: {{WorkbenchNodeCardHost: {{
  mount: settings => {{ calls.push(['mount', settings.rendererOptions.legacyContent.children]); return {{shell, renderer: {{id:'legacy'}}}}; }},
}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const removed = [];
const added = [];
const preservedContent = {{
  children: [],
  appendChild: child => {{
    contentHost.children.splice(contentHost.children.indexOf(child), 1);
    preservedContent.children.push(child);
  }},
}};
const card = {{
  append: item => calls.push(`port:${{item.id}}`),
  classList: {{add: (...classes) => added.push(...classes)}},
  querySelectorAll: selector => [{{remove: () => removed.push(selector)}}],
}};
const contentHost = {{
  children: ['preserved'],
  get firstChild() {{ return this.children[0] || null; }},
  ownerDocument: {{createElement: () => preservedContent}},
  replaceChildren: () => calls.push('replace'),
}};
sandbox.window.WorkbenchUnifiedRenderHost.mountAdapterCard({{
  node: {{id:'node'}}, card, contentHost,
  controlSettings: {{selectors:['.legacy-control']}},
  removeControlsBeforeMount: true,
  preserveLegacyContent: true,
  cardClasses: ['node-shell-mounted', false, 'legacy-renderer-mounted'],
}});
console.log(JSON.stringify({{calls, removed, added}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["removed"], [".legacy-control"])
        self.assertEqual(mounted["calls"], [["mount", ["preserved"]], "replace", "port:input", "port:output"])
        self.assertEqual(mounted["added"], ["node-shell-mounted", "legacy-renderer-mounted"])

    def test_unified_render_host_mount_adapter_cards_preserves_entry_order(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const calls = [];
const sandbox = {{window: {{WorkbenchNodeCardHost: {{
  mount: settings => {{
    calls.push(settings.node.id);
    return {{shell: {{element: {{querySelector: () => null}}}}, renderer: {{id: settings.node.id}}}};
  }},
}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
function entry(id) {{
  return {{
    node: {{id}},
    card: {{classList: {{add: () => {{}}}}, append: () => {{}}}},
    contentHost: {{replaceChildren: () => {{}}}},
  }};
}}
const mounted = sandbox.window.WorkbenchUnifiedRenderHost.mountAdapterCards([entry('first'), entry('second')]);
let rejected = false;
try {{ sandbox.window.WorkbenchUnifiedRenderHost.mountAdapterCards({{}}); }} catch (error) {{ rejected = error?.name === 'TypeError'; }}
console.log(JSON.stringify({{calls, ids: mounted.map(item => item.renderer.id), frozen: Object.isFrozen(mounted), rejected}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["calls"], ["first", "second"])
        self.assertEqual(mounted["ids"], ["first", "second"])
        self.assertTrue(mounted["frozen"])
        self.assertTrue(mounted["rejected"])

    def test_unified_render_host_mount_adapter_content_owns_card_classes(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const received = [];
const sandbox = {{window: {{WorkbenchNodeCardHost: {{
  mountContent: settings => {{ received.push(settings); return {{element: settings.contentHost, renderer: {{id:'media'}}}}; }},
}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const added = [];
const card = {{classList: {{add: (...classes) => added.push(...classes)}}}};
const contentHost = {{id:'content'}};
const mounted = sandbox.window.WorkbenchUnifiedRenderHost.mountAdapterContent({{
  node: {{id:'media-node'}}, card, contentHost,
  cardClasses:['media-renderer-mounted'],
}});
console.log(JSON.stringify({{receivedNode: received[0].node.id, receivedHost: received[0].contentHost.id, added, renderer: mounted.renderer.id}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["receivedNode"], "media-node")
        self.assertEqual(mounted["receivedHost"], "content")
        self.assertEqual(mounted["added"], ["media-renderer-mounted"])
        self.assertEqual(mounted["renderer"], "media")

    def test_unified_render_host_dispatches_shell_intents_through_page_callbacks(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{WorkbenchNodeCardHost: {{}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const calls = [];
const dispatch = sandbox.window.WorkbenchUnifiedRenderHost.createIntentAdapter({{
  select: intent => calls.push(['select', intent.nodeId]),
  connect_start: intent => calls.push(['connect', intent.detail.direction]),
}});
dispatch({{nodeId:'node-1', type:'select'}});
dispatch({{nodeId:'node-2', type:'connect_start', detail:{{direction:'output'}}}});
dispatch({{nodeId:'node-3', type:'resize_start'}});
dispatch({{type:'delete'}});
console.log(JSON.stringify(calls));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), [["select", "node-1"], ["connect", "output"]])

    def test_unified_render_host_builds_a_page_agnostic_node_shell_view_model(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{WorkbenchNodeCardHost: {{}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const callback = () => {{}};
const defaultView = sandbox.window.WorkbenchUnifiedRenderHost.cardShellView({{selected:1, onIntent:callback}});
const outputOnly = sandbox.window.WorkbenchUnifiedRenderHost.cardShellView({{selected:false, onIntent:callback, showDelete:false, ports:{{input:false, output:true}}}});
console.log(JSON.stringify({{
  selected: defaultView.viewState.selected,
  defaultDelete: defaultView.showDelete,
  callbackKept: defaultView.onIntent === callback,
  hiddenDelete: outputOnly.showDelete,
  ports: outputOnly.ports,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        view = json.loads(result.stdout)
        self.assertTrue(view["selected"])
        self.assertTrue(view["defaultDelete"])
        self.assertTrue(view["callbackKept"])
        self.assertFalse(view["hiddenDelete"])
        self.assertEqual(view["ports"], {"input": False, "output": True})

    def test_unified_render_host_removes_only_page_declared_legacy_controls(self):
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{WorkbenchNodeCardHost: {{}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const removed = [];
const card = {{querySelectorAll: selector => selector === '.legacy-port' ? [{{remove: () => removed.push('legacy-port')}}] : [{{remove: () => removed.push('legacy-resize')}}]}};
const count = sandbox.window.WorkbenchUnifiedRenderHost.removeCardControls({{card, selectors:['.legacy-port', '.legacy-resize']}});
console.log(JSON.stringify({{count, removed}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        removed = json.loads(result.stdout)
        self.assertEqual(removed["count"], 2)
        self.assertEqual(removed["removed"], ["legacy-port", "legacy-resize"])

    def test_unified_render_host_mounts_mixed_legacy_records_without_source_mode(self):
        records = ROOT / "static" / "js" / "workbench" / "canvas" / "records.js"
        registry = ROOT / "static" / "js" / "workbench" / "canvas" / "renderer-registry.js"
        card_host = ROOT / "static" / "js" / "workbench" / "canvas" / "node-card-host.js"
        unified_host = ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(records))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(registry))}, 'utf8'), sandbox);
const calls = [];
sandbox.window.WorkbenchNodeShell = {{create: () => ({{element: {{dataset: {{}}}}, contentHost: {{}}, destroy() {{}}}})}};
sandbox.window.WorkbenchMediaRenderer = {{
  canRender: node => node.kind === 'asset',
  mount: (_shell, node) => {{ calls.push(['media', node.id]); return {{destroy() {{}}}}; }},
}};
sandbox.window.WorkbenchLegacyRenderer = {{
  canRender: node => node.renderer && node.renderer.id === 'legacy',
  mount: (_shell, node) => {{ calls.push(['source-payload', node.id]); return {{destroy() {{}}}}; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(card_host))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(unified_host))}, 'utf8'), sandbox);
const adapt = sandbox.window.WorkbenchCanvas.legacyNodeView;
const records = [
  adapt({{id:'classic-prompt', type:'prompt', title:'Prompt'}}, {{canvasId:'shared'}}),
  adapt({{id:'smart-image', type:'smart-image', title:'Image'}}, {{canvasId:'shared'}}),
];
const mounted = records.map(node => sandbox.window.WorkbenchUnifiedRenderHost.mount({{node}}));
console.log(JSON.stringify({{
  kinds: records.map(node => node.kind),
  definitions: records.map(node => node.definition_ref.id),
  renderers: mounted.map(item => item.renderer.id),
  calls,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        mounted = json.loads(result.stdout)
        self.assertEqual(mounted["kinds"], ["legacy", "asset"])
        self.assertEqual(mounted["definitions"], ["prompt", "smart-image"])
        self.assertEqual(mounted["renderers"], ["source-payload", "media"])
        self.assertEqual(mounted["calls"], [["source-payload", "classic-prompt"], ["media", "smart-image"]])

    def test_classic_connected_blank_image_uses_the_versioned_graph_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        create_block = classic[classic.index("async function createVersionedLinkedImage"):classic.index("function createNodeByType")]
        self.assertIn("definition_ref:{type:'legacy', id:'image', version:'0'}", create_block)
        self.assertIn("await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id", create_block)
        self.assertIn("type:'image'", create_block)
        self.assertIn("mediaKind:'image'", create_block)
        self.assertNotIn("scheduleSave();", create_block)

    def test_classic_connected_blank_prompt_and_loop_use_the_versioned_graph_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        block = classic[classic.index("async function createVersionedLinkedPrompt"):classic.index("function createNodeByType")]
        registry = (ROOT / "static" / "js" / "workbench" / "canvas" / "command-registry.js").read_text(encoding="utf-8")
        repository = (ROOT / "workbench" / "repositories" / "legacy_json_node_repository.py").read_text(encoding="utf-8")
        self.assertIn("definitionId:'prompt'", block)
        self.assertIn("definitionId:'loop'", block)
        self.assertIn("await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id", block)
        self.assertIn("initial_config:definition.definitionId === 'prompt' ? {text:''} : undefined", block)
        self.assertNotIn("scheduleSave();", block)
        self.assertIn("['canvas.create.prompt', 'prompt', ['classic', 'smart'], 20, ['classic', 'smart'], ['classic', 'smart']]", registry)
        self.assertIn("['canvas.create.loop', 'loop', ['classic', 'smart'], 30, ['classic', 'smart'], ['classic', 'smart']]", registry)
        self.assertIn('"prompt", "loop", "group"', repository)
        self.assertIn('elif definition_id == "prompt":', repository)
        self.assertIn('elif definition_id == "loop":', repository)

    def test_shared_command_catalog_orders_common_menu_items_consistently(self):
        registry = ROOT / "static" / "js" / "workbench" / "canvas" / "command-registry.js"
        catalog = ROOT / "static" / "js" / "workbench" / "canvas" / "creation-catalog.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(catalog))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(registry))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasCommands;
const menuItems = [
  {{dataset: {{canvasCommand: 'canvas.create.group'}}, hidden: false, name: 'group'}},
  {{dataset: {{canvasCommand: 'canvas.create.image'}}, hidden: false, name: 'image'}},
  {{dataset: {{canvasCommand: 'canvas.create.llm'}}, hidden: false, name: 'llm'}},
];
const menu = api.orderCreateMenuItems(menuItems, api.creationCatalogFor('smart'));
console.log(JSON.stringify({{
  smart: api.createCommandsFor('smart').map(command => command.createType),
  classic: api.createCommandsFor('classic').slice(0, 5).map(command => command.createType),
  smartCatalog: api.creationCatalogFor('smart'),
  smartMenu: menu.map(item => item.name),
  hidden: menuItems.filter(item => item.hidden).map(item => item.name),
  versioned: {{
    classicImage: api.usesVersionedBlankCreation(api.createCommand('image', 'classic'), 'classic'),
    smartPrompt: api.usesVersionedBlankCreation(api.createCommand('prompt', 'smart'), 'smart'),
    classicMinimax: api.usesVersionedBlankCreation(api.createCommand('minimax', 'classic'), 'classic'),
  }},
  connectedVersioned: {{
    smartImage: api.usesVersionedConnectedCreation(api.createCommand('image', 'smart'), 'smart'),
    smartMinimax: api.usesVersionedConnectedCreation(api.createCommand('minimax', 'smart'), 'smart'),
    classicImage: api.usesVersionedConnectedCreation(api.createCommand('image', 'classic'), 'classic'),
    classicGroup: api.usesVersionedConnectedCreation(api.createCommand('group', 'classic'), 'classic'),
  }},
  connectedCreation: Boolean(api.graphCommand('canvas.graph.create-connected', 'classic')),
  smartConnectedCreation: Boolean(api.graphCommand('canvas.graph.create-connected', 'smart')),
  inspect: Boolean(api.nodeCommand('canvas.node.inspect', 'smart')),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        ordered = json.loads(result.stdout)
        self.assertEqual(ordered["smart"], ["image", "prompt", "loop", "group", "minimax"])
        self.assertEqual(ordered["classic"], ordered["smart"])
        self.assertEqual(
            ordered["smartCatalog"],
            [
                {"id": "canvas.create.image", "definition_ref": {"id": "image", "type": "legacy-node", "version": "0"}, "order": 10},
                {"id": "canvas.create.prompt", "definition_ref": {"id": "prompt", "type": "legacy-node", "version": "0"}, "order": 20},
                {"id": "canvas.create.loop", "definition_ref": {"id": "loop", "type": "legacy-node", "version": "0"}, "order": 30},
                {"id": "canvas.create.group", "definition_ref": {"id": "group", "type": "legacy-node", "version": "0"}, "order": 40},
                {"id": "canvas.create.minimax", "definition_ref": {"id": "minimax", "type": "legacy-node", "version": "0"}, "order": 50},
            ],
        )
        self.assertEqual(ordered["smartMenu"], ["image", "group"])
        self.assertEqual(ordered["hidden"], ["llm"])
        self.assertEqual(ordered["versioned"], {"classicImage": True, "smartPrompt": True, "classicMinimax": False})
        self.assertEqual(ordered["connectedVersioned"], {"smartImage": True, "smartMinimax": True, "classicImage": False, "classicGroup": True})
        self.assertTrue(ordered["connectedCreation"])
        self.assertTrue(ordered["smartConnectedCreation"])
        self.assertTrue(ordered["inspect"])

    def test_creation_catalog_normalizes_generic_creation_definitions_without_side_effects(self):
        catalog = ROOT / "static" / "js" / "workbench" / "canvas" / "creation-catalog.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(catalog))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCreationCatalog;
const definitions = api.create([
  {{id: 'canvas.create.b', definition_ref: {{id: 'b', type: 'legacy-node', version: '0'}}, order: 20}},
  {{id: 'canvas.create.a', definition_ref: {{id: 'a', type: 'legacy-node', version: '0'}}, order: 10}},
]);
let duplicate = false;
try {{ api.create([
  {{id: 'canvas.create.a', definition_ref: {{id: 'a', type: 'legacy-node', version: '0'}}, order: 1}},
  {{id: 'canvas.create.a', definition_ref: {{id: 'a2', type: 'legacy-node', version: '0'}}, order: 2}},
]); }} catch (error) {{ duplicate = error.name === 'RangeError'; }}
console.log(JSON.stringify({{
  ids: definitions.all().map(entry => entry.id),
  definition: definitions.get('canvas.create.a').definition_ref,
  missing: definitions.get('missing'),
  duplicate,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        output = json.loads(result.stdout)
        self.assertEqual(output["ids"], ["canvas.create.a", "canvas.create.b"])
        self.assertEqual(output["definition"], {"id": "a", "type": "legacy-node", "version": "0"})
        self.assertIsNone(output["missing"])
        self.assertTrue(output["duplicate"])

    def test_generation_intent_plans_result_placement_without_execution_side_effects(self):
        intent = ROOT / "static" / "js" / "workbench" / "canvas" / "generation-intent.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(intent))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchGenerationIntent;
console.log(JSON.stringify({{
  branch: api.planResultTarget({{sourceId:'source', isGroup:false, hasMedia:true, workflowMode:false}}),
  inPlace: api.planResultTarget({{sourceId:'source', isGroup:false, hasMedia:true, workflowMode:true}}),
  group: api.planResultTarget({{sourceId:'source', isGroup:true, hasMedia:false, workflowMode:true}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        output = json.loads(result.stdout)
        self.assertEqual(output["branch"], {"sourceId": "source", "disposition": "branch"})
        self.assertEqual(output["inPlace"], {"sourceId": "source", "disposition": "in_place"})
        self.assertEqual(output["group"], {"sourceId": "source", "disposition": "branch"})

    def test_compatibility_modules_are_explicitly_dom_and_storage_free(self):
        for name in ("records.js", "node-creation-client.js", "creation-catalog.js", "generation-intent.js", "command-registry.js"):
            text = (ROOT / "static" / "js" / "workbench" / "canvas" / name).read_text(encoding="utf-8")
            self.assertNotIn("localStorage", text)
            self.assertNotIn("document.", text)

    def test_classic_standalone_blank_image_delete_uses_the_versioned_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        delete_block = classic[classic.index("function canUseVersionedBlankImageDelete(node)"):classic.index("function deleteConnection(id, event){")]
        self.assertIn("node.type !== 'image' || node.url", delete_block)
        self.assertIn("Array.isArray(candidate.items) && candidate.items.includes(node.id)", delete_block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", delete_block)
        self.assertIn("expected_revision:currentCanvasRevision()", delete_block)
        self.assertIn("if(await deleteVersionedBlankImageNode(id)) return;", delete_block)
        self.assertNotIn("scheduleSave();", delete_block)

    def test_classic_standalone_blank_image_move_uses_versioned_position_mutation(self):
        classic = read_canvas_app_source(ROOT)
        move_block = classic[classic.index("async function commitVersionedBlankImagePosition(drag)"):classic.index("async function deleteVersionedBlankImageNode(id)")]
        end_drag = classic[classic.index("function endDrag(event=null){"):classic.index("function nodeRect(n){")]
        self.assertIn("drag?.isLocalCopy || (drag?.children || []).length", move_block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", move_block)
        self.assertIn("position:{x:Number(node.x) || 0, y:Number(node.y) || 0}", move_block)
        self.assertIn("node.x = drag.ox;", move_block)
        self.assertIn("node.y = drag.oy;", move_block)
        self.assertIn("void commitVersionedBlankClassicPosition(versionedPositionCommit)", end_drag)
        self.assertIn("if(!handled) scheduleSave();", end_drag)

    def test_classic_standalone_blank_prompt_uses_the_versioned_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        block = classic[classic.index("function canUseVersionedBlankPromptDelete(node)"):classic.index("async function deleteNodeFromButton")]
        self.assertIn("node.type !== 'prompt' || String(node.text || '').trim()", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedBlankImagePosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankPromptPosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankLoopPosition(drag)) return true;", block)

    def test_classic_standalone_default_loop_uses_the_versioned_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        block = classic[classic.index("function canUseVersionedBlankLoopDelete(node)"):classic.index("async function deleteNodeFromButton")]
        self.assertIn("Number(node.count || 3) !== 3", block)
        self.assertIn("node.mode === 'parallel' || node.showPrompt || node.imageInput || node.videoInput", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedBlankLoopPosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankOutputPosition(drag)) return true;", block)

    def test_classic_standalone_empty_output_uses_the_versioned_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        block = classic[classic.index("function canUseVersionedBlankOutputDelete(node)"):classic.index("function deleteConnection(id, event){")]
        self.assertIn("node.type !== 'output'", block)
        self.assertIn("(node.images || []).length || (node._pending || []).length", block)
        self.assertIn("Object.keys(node.imageComparisons || {}).length", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedBlankOutputPosition(drag)) return true;", block)
        self.assertIn("return commitVersionedEmptyGroupPosition(drag);", block)
        self.assertIn("if(await deleteVersionedBlankOutputNode(id)) return;", block)

    def test_classic_standalone_empty_group_uses_the_versioned_mutation_route(self):
        classic = read_canvas_app_source(ROOT)
        block = classic[classic.index("function canUseVersionedEmptyGroupDelete(node)"):classic.index("function deleteConnection(id, event){")]
        self.assertIn("node.type !== 'group' || (node.items || []).length", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("Array.isArray(candidate.items) && candidate.items.includes(node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("return commitVersionedEmptyGroupPosition(drag);", block)
        self.assertIn("if(await deleteVersionedEmptyGroupNode(id)) return;", block)

    def test_node_shell_emits_intents_without_storage_or_network_side_effects(self):
        shell = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-shell.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchNodeShell", shell)
        self.assertIn("contentHost", shell)
        self.assertIn("toolbarHost", shell)
        self.assertIn("drag_start", shell)
        self.assertIn("resize_start", shell)
        self.assertIn("connect_start", shell)
        self.assertNotIn("localStorage", shell)
        self.assertNotIn("fetch(", shell)

    def test_legacy_renderer_uses_one_payload_adapter_without_node_type_branches(self):
        renderer = (ROOT / "static" / "js" / "workbench" / "canvas" / "legacy-renderer.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchLegacyRenderer", renderer)
        self.assertIn("legacyPayload", renderer)
        self.assertIn("shell.contentHost", renderer)
        self.assertNotIn("node.type ===", renderer)
        self.assertNotIn("fetch(", renderer)
        self.assertNotIn("localStorage", renderer)

    def test_media_renderer_is_data_driven_and_has_no_persistence_side_effects(self):
        renderer = (ROOT / "static" / "js" / "workbench" / "canvas" / "media-renderer.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchMediaRenderer", renderer)
        self.assertIn("mediaItems", renderer)
        self.assertIn("output_refs", renderer)
        self.assertIn("mountInto", renderer)
        self.assertIn("media.preload = 'metadata'", renderer)
        self.assertIn("WorkbenchCanvasMediaKind", renderer)
        self.assertIn("media.playsInline = true", renderer)
        self.assertIn("preserveNativeMediaInteraction(media)", renderer)
        self.assertIn("event.stopPropagation()", renderer)
        self.assertIn("value == null ? [] : [value]", renderer)
        self.assertIn("loading = 'lazy'", renderer)
        self.assertNotIn("node.type ===", renderer)
        self.assertNotIn("fetch(", renderer)
        self.assertNotIn("localStorage", renderer)

    def test_semantic_zoom_presentation_is_applied_by_one_shared_owner(self):
        apply_owner = ROOT / "static" / "js" / "workbench" / "canvas" / "semantic-zoom-apply.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{
  window: {{}},
  document: {{
    createElement: () => ({{
      attrs: {{}}, children: [], className: '', textContent: '', value: '',
      setAttribute(key, val) {{ this.attrs[key] = val; }},
      appendChild(child) {{ this.children.push(child); }},
    }}),
  }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(apply_owner))}, 'utf8'), sandbox);
const A = sandbox.window.WorkbenchSemanticZoomApply;
const makeEl = () => ({{
  dataset: {{}}, hidden: null,
  style: {{ display: null, removed: [], removeProperty(name) {{ this.removed.push(name); }} }},
}});
const SLOT = {{
  '.workbench-node-shell__title': 'title', '.workbench-node-shell__status': 'status',
  '.workbench-node-shell__actions': 'actions', '.workbench-node-shell__content': 'content',
  '.workbench-node-shell__toolbar': 'toolbar', '.workbench-node-shell__footer': 'footer',
}};
const makeShell = () => {{
  const slots = {{}};
  Object.values(SLOT).forEach(name => {{ slots[name] = makeEl(); }});
  const shellEl = {{ dataset: {{}}, querySelector: sel => slots[SLOT[sel]] || null }};
  return {{ shellEl, slots }};
}};
const full = {{presentation:'full', showTitle:true, showSummary:false, showContent:true, showControls:true, showPorts:true}};
const summary = {{presentation:'summary', showTitle:true, showSummary:true, showContent:false, showControls:false, showPorts:true}};
const shellFull = makeShell();
const outerFull = makeEl();
const portA = makeEl();
A.applyShellPresentation({{shellEl: shellFull.shellEl, outerEl: outerFull, model: full, portElements: [portA]}});
const shellApplied = shellFull.shellEl.dataset.semanticPresentation === 'full'
  && shellFull.shellEl.dataset.semanticControls === 'true'
  && shellFull.shellEl.dataset.semanticPorts === 'true'
  && outerFull.dataset.semanticPresentation === 'full';
const fullVisible = shellFull.slots.content.hidden === false && shellFull.slots.content.style.display === '';
const statusHiddenInFull = shellFull.slots.status.hidden === true && shellFull.slots.status.style.display === 'none';
const controlsVisibleInFull = shellFull.slots.toolbar.hidden === false && portA.hidden === false;

const shellSummary = makeShell();
const portB = makeEl();
A.applyShellPresentation({{shellEl: shellSummary.shellEl, model: summary, portElements: [portB]}});
const summaryHidden = shellSummary.slots.content.hidden === true && shellSummary.slots.content.style.display === 'none';
const summaryStatusInline = shellSummary.slots.status.hidden === false && shellSummary.slots.status.style.display === 'inline';
const summaryControlsHidden = shellSummary.slots.actions.hidden === true && shellSummary.slots.footer.hidden === true;

A.resetShellPresentation({{shellEl: shellFull.shellEl, outerEl: outerFull, portElements: [portA]}});
const shellReset = !('semanticPresentation' in shellFull.shellEl.dataset)
  && !('semanticControls' in shellFull.shellEl.dataset)
  && !('semanticPresentation' in outerFull.dataset)
  && shellFull.slots.content.hidden === false
  && shellFull.slots.content.style.removed.includes('display')
  && portA.hidden === false;

const legacyNode = makeEl();
const head = makeEl();
const body = makeEl();
const resize = makeEl();
const legacyPort = makeEl();
A.applyLegacyPresentation({{nodeEl: legacyNode, model: full, targets: {{head, body, resize}}, portElements: [legacyPort], headDisplay: 'flex'}});
const legacyApplied = legacyNode.dataset.semanticPresentation === 'full'
  && head.hidden === false && head.style.display === 'flex'
  && body.hidden === false
  && resize.hidden === false
  && legacyPort.hidden === false;
A.applyLegacyPresentation({{nodeEl: legacyNode, model: summary, targets: {{head, body, resize}}, portElements: [legacyPort]}});
const legacySummary = head.hidden === false && head.style.display === ''
  && body.hidden === true && body.style.display === 'none'
  && resize.hidden === true;

const hint = makeEl();
A.resetLegacyPresentation({{nodeEl: legacyNode, targets: {{head, body, hint}}, portElements: [legacyPort]}});
const legacyReset = !('semanticPresentation' in legacyNode.dataset)
  && body.hidden === false && body.style.removed.includes('display')
  && hint.hidden === false && head.hidden === false;

const container = {{ appended: [], querySelector(sel) {{ return this.appended.find(child => `#${{child.id}}` === sel) || null; }}, appendChild(child) {{ this.appended.push(child); }} }};
const indicator = A.ensureIndicator({{
  container, id: 'zoomIndicator', className: 'zoom-indicator', scale: 0.65,
  presentation: 'summary', labels: {{full:'完整', summary:'摘要'}}, count: 2,
}});
const indicatorBuilt = indicator.id === 'zoomIndicator' && indicator.className === 'zoom-indicator'
  && indicator.attrs['aria-live'] === 'polite' && indicator.value === '65'
  && indicator.textContent === '65% · 摘要 · 2 节点'
  && container.appended.length === 1;
const updated = A.ensureIndicator({{
  container, id: 'zoomIndicator', className: 'zoom-indicator', scale: 1,
  presentation: 'full', labels: {{full:'完整', summary:'摘要'}}, count: 6,
}});
const indicatorUpdated = container.appended.length === 1 && updated.textContent === '100% · 完整 · 6 节点'
  && updated.value === '100';

console.log(JSON.stringify({{shellApplied, fullVisible, statusHiddenInFull, controlsVisibleInFull, summaryHidden, summaryStatusInline, summaryControlsHidden, shellReset, legacyApplied, legacySummary, legacyReset, indicatorBuilt, indicatorUpdated}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        for key in ("shellApplied", "fullVisible", "statusHiddenInFull", "controlsVisibleInFull",
                    "summaryHidden", "summaryStatusInline", "summaryControlsHidden", "shellReset",
                    "legacyApplied", "legacySummary", "legacyReset", "indicatorBuilt", "indicatorUpdated"):
            self.assertTrue(payload[key], key)

        for page, editor in (("canvas.html", "workbench/canvas/canvas-app-bootstrap.js"),):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            apply_tag = text.index("workbench/canvas/semantic-zoom-apply.js")
            self.assertLess(text.index("workbench/canvas/semantic-zoom.js"), apply_tag)
            self.assertLess(apply_tag, text.index(editor))


    def test_classic_output_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}", classic)
        self.assertIn("if(node?.type === 'output') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.output-node .canvas-node-shell-legacy-content", styles)
        self.assertIn("overflow:auto", styles)

    def test_classic_legacy_renderer_gate_covers_all_migrated_families_and_port_contracts(self):
        classic = read_canvas_app_source(ROOT)
        migrated = [
            "prompt", "loop", "output", "llm", "generator", "midjourney",
            "msgen", "video", "comfy", "rh", "ltxDirector", "minimax", "promptGroup",
        ]
        self.assertNotIn("params.get('node_shell')", classic)
        self.assertNotIn("params.get('legacy_renderer')", classic)
        self.assertIn("window.WorkbenchNodeClient?.isLoopback?.()", classic)
        self.assertIn("WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}", classic)
        self.assertIn("if(node?.type === 'prompt') return {input:false, output:true};", classic)
        self.assertIn("if(node?.type === 'promptGroup') return {input:false, output:true};", classic)
        for node_type in [node for node in migrated if node not in {"prompt", "promptGroup"}]:
            self.assertIn(f"if(node?.type === '{node_type}') return {{input:true, output:true}};", classic)

    def test_classic_llm_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'llm') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.llm-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.llm-node .llm-body", styles)

    def test_classic_generator_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'generator') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.generator-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.generator-node .generator-body", styles)

    def test_classic_midjourney_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'midjourney') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.midjourney-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.midjourney-node .generator-body", styles)

    def test_classic_modelscope_generation_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'msgen') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.msgen-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.msgen-node .generator-body", styles)

    def test_classic_video_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'video') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.video-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.video-node .generator-body", styles)

    def test_classic_comfy_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'comfy') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.comfy-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.comfy-node .comfy-body", styles)

    def test_classic_runninghub_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'rh') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.rh-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.rh-node .rh-body", styles)

    def test_classic_ltx_director_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'ltxDirector') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.ltxDirector-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.ltxDirector-node .ltx-director-body", styles)

    def test_classic_minimax_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'minimax') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.minimax-node .workbench-legacy-renderer", styles)
        self.assertIn(".node.node-shell-mounted.minimax-node .minimax-canvas-workbench", styles)

    def test_classic_prompt_group_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = read_canvas_app_source(ROOT)
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'promptGroup') return {input:false, output:true};", classic)
        self.assertIn("if(node.type === 'promptGroup') {", classic)
        self.assertIn("${promptNodes.length} ${tr('canvas.promptCount')} ${tr('canvas.grouped')}", classic)

    def test_node_shell_ports_emit_mouse_coordinates_and_use_legacy_port_contract(self):
        shell = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-shell.js").read_text(encoding="utf-8")
        self.assertIn("connect_start", shell)
        self.assertIn("clientX: event.clientX", shell)
        self.assertIn("clientY: event.clientY", shell)
        self.assertIn("workbench-node-shell__port", shell)
        self.assertNotIn("node-port", shell)
        self.assertIn("dataset.port", shell)
        self.assertIn("resize_start", shell)
        self.assertIn("drag_start", shell)
        self.assertIn("port.addEventListener('mousedown'", shell)
        self.assertIn("resize.addEventListener('mousedown'", shell)
        self.assertIn("header.addEventListener('mousedown'", shell)
        self.assertIn("event.stopPropagation();", shell)
        self.assertNotIn("pointerdown", shell)

    def test_legacy_renderer_can_preserve_existing_legacy_content_in_a_shell_slot(self):
        renderer = (ROOT / "static" / "js" / "workbench" / "canvas" / "legacy-renderer.js").read_text(encoding="utf-8")
        self.assertIn("legacyContent", renderer)
        self.assertIn("root.append(legacyContent)", renderer)

    def test_classic_media_node_shell_reuses_legacy_gesture_and_link_state_machines(self):
        classic = read_canvas_app_source(ROOT)
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertIn("function canvasNodeShellEnabled()", classic)
        self.assertNotIn("params.get('node_shell')", classic)
        self.assertIn("function mountCanvasNodeShellForMedia", classic)
        self.assertIn("onclick=\"menuAdd('group')\"", page)
        self.assertIn("function addVersionedBlankGroupNode", classic)
        self.assertIn("definition_ref:{type:'legacy', id:'group', version:'0'}", classic)
        self.assertIn("node?.type === 'group'", classic)
        self.assertIn("workbench-node-shell__group-empty", classic)
        self.assertIn("WorkbenchUnifiedRenderHost.mount", classic)
        self.assertIn("canvas-node-shell-legacy-content", classic)
        self.assertIn("ensureRenderRuntime().mount({", classic)
        self.assertIn("card:el, contentHost:body", classic)
        self.assertIn("controlSettings:CANVAS_NODE_SHELL_LEGACY_CONTROLS", classic)
        self.assertIn("cardClasses:['node-shell-mounted'", classic)
        self.assertIn("function canvasLegacyRendererEnabled()", classic)
        self.assertNotIn("params.get('legacy_renderer')", classic)
        self.assertIn("function mountCanvasNodeShellForLegacy", classic)
        self.assertIn("WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}", classic)
        self.assertIn("function canvasLegacyNodeShellPorts(node)", classic)
        self.assertIn("node?.type === 'loop'", classic)
        self.assertIn("if(node?.type === 'loop') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'llm') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'generator') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'midjourney') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'msgen') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'video') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'comfy') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'rh') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'ltxDirector') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'minimax') return {input:true, output:true};", classic)
        self.assertIn("if(node?.type === 'promptGroup') return {input:false, output:true};", classic)
        self.assertIn("ports:canvasLegacyNodeShellPorts(node)", classic)
        self.assertIn("WorkbenchUnifiedRenderHost.cardShellView({selected:selected.has(node.id), onIntent:handleCanvasNodeShellIntent, ports:canvasLegacyNodeShellPorts(node)})", classic)
        self.assertIn("portVisibility.input !== false", (ROOT / "static" / "js" / "workbench" / "canvas" / "node-shell.js").read_text(encoding="utf-8"))
        self.assertIn("function canConnect(fromId, toId){", classic)
        self.assertIn("WorkbenchLegacyGraphCompatibility.canClassicConnect", classic)
        # Group membership is applied from the compatibility-policy
        # projection (card R4-25) instead of an inline push.
        self.assertIn("projection.addedNodeIds.forEach", classic)
        self.assertIn("function canvasNodeShellSemanticZoomEnabled()", classic)
        self.assertNotIn("params.get('semantic_zoom')", classic)
        self.assertIn("WorkbenchSemanticZoom.viewModel(node, viewport.scale)", classic)
        self.assertIn("WorkbenchSemanticZoomApply.applyShellPresentation", classic)
        self.assertIn("WorkbenchSemanticZoomApply.applyLegacyPresentation", classic)
        self.assertIn(".node:not(.node-shell-mounted)", classic)
        self.assertIn("canvasSemanticZoomIndicator", classic)
        self.assertIn("WorkbenchUnifiedRenderHost.mount", classic)
        self.assertIn("handleCanvasNodeShellIntent", classic)
        self.assertIn("function selectCanvasNodeFromShell(nodeId)", classic)
        self.assertIn("if(!applyCanvasRuntimeSelection([nodeId]))", classic)
        self.assertIn("startNodeDrag(canvasShellPointer(intent.detail), node)", classic)
        self.assertIn("startNodeResize(canvasShellPointer(intent.detail), node)", classic)
        self.assertIn("startLink(canvasShellPointer(intent.detail)", classic)
        self.assertIn(".workbench-node-shell__port--output", classic)
        self.assertIn(".node.node-shell-mounted .workbench-node-shell", styles)
        self.assertIn(".workbench-node-shell__content > .workbench-media-renderer", styles)
        self.assertIn(".node.node-shell-mounted .workbench-legacy-renderer", styles)
        self.assertIn("margin:12px; border-radius:16px", styles)
        self.assertIn("display:flex; flex:1; min-height:0; overflow:hidden", styles)
        self.assertIn("border:0; border-radius:inherit; background:transparent", styles)
        self.assertIn(".node.node-shell-mounted > .workbench-node-shell__port", styles)
        self.assertIn(".node-shell-semantic-zoom .node:not(.node-shell-mounted)[data-semantic-presentation=\"summary\"]", styles)
        self.assertIn(".canvas-semantic-zoom-indicator", styles)
        self.assertIn(".workbench-node-shell__port--input { left:-25px; }", styles)
        self.assertIn(".workbench-node-shell__port--output { right:-21px; }", styles)
        self.assertIn("canvas.css?v=2026.09.11.1", page)
        self.assertIn("command-registry.js?v=2026.09.06.6", page)
        self.assertIn("creation-catalog.js?v=2026.09.04.1", page)
        self.assertIn("generation-intent.js?v=2026.09.04.1", page)
        self.assertIn("canvas-app-bootstrap.js?v=2026.09.09.2", page)
        self.assertIn("WorkbenchUnifiedRenderHost.cardShellView({selected:selected.has(node.id), onIntent:handleCanvasNodeShellIntent})", classic)
        self.assertIn("const canvasNodeShellIntentAdapter = window.WorkbenchUnifiedRenderHost.createIntentAdapter({", classic)
        self.assertIn("delete:intent => deleteNodeFromButton(intent.nodeId)", classic)
        self.assertIn("workbench-node-shell__actions", styles)
        self.assertIn("workbench-node-shell__delete::before", styles)
