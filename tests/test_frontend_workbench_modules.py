import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendWorkbenchModulesTests(unittest.TestCase):
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

    def test_renderer_admission_loads_before_canvas_adapters(self):
        classic = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        for page in (classic, smart):
            self.assertLess(page.index("renderer-registry.js"), page.index("renderer-admission.js"))
            self.assertLess(page.index("renderer-admission.js"), page.index("node-card-host.js"))

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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertLess(page_source.index("workbench/canvas/media-result-normalizer.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaResultNormalizer.extract", editor_source)

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
  mime:api.kindForFile({{type:'video/mp4', name:'ignored'}}), fallback:api.kindForFile({{type:'', name:'unknown.bin'}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "video": "video", "audio": "audio", "text": "text", "workflow": "workflow", "file": "file",
            "classicFlv": "video", "smartFlv": "image", "mime": "video", "fallback": "image",
        })
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertLess(page_source.index("workbench/canvas/media-preview-controls.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasMediaPreviewControls.bindVideoOverlay", editor_source)

    def test_media_preview_controls_bind_image_fallbacks_without_adapter_dom_logic(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-preview-controls.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const listeners = {{}};
const fallback = {{id:'fallback'}};
const template = {{content:{{firstElementChild:fallback}}, set innerHTML(value) {{ this.html = value; }}}};
const video = {{dataset:{{inlineVideoActive:'1'}}}};
const image = {{
  dataset:{{previewSrc:'/api/media-preview', originalSrc:'/assets/video.mp4', previewKind:'video', videoFallbackAttrs:'muted'}},
  ownerDocument:{{createElement:type => type === 'template' ? template : null}},
  addEventListener:(type, listener) => {{ listeners[type] = listener; }},
  getAttribute:() => '/api/media-preview', replaceWith:value => {{ image.replaced = value; }},
}};
const imageOnly = {{
  dataset:{{previewSrc:'/api/media-preview', originalSrc:'/assets/image.png'}},
  addEventListener:(type, listener) => {{ imageOnly.listener = listener; }},
  getAttribute:() => '/api/media-preview', src:'',
}};
const root = {{querySelectorAll:selector => selector.startsWith('img') ? [image, imageOnly] : [video]}};
const bound = [];
sandbox.window.WorkbenchCanvasMediaPreviewControls.bindPreviewImageFallbacks(root, {{
  videoFallbackHtml:(url, attrs) => `<video data-url="${{url}}" ${{attrs}}></video>`,
  bindVideoOverlay:item => bound.push(item.id || 'inline'),
}});
listeners.error();
imageOnly.listener();
console.log(JSON.stringify({{markers:[image.dataset.previewFallbackBound, imageOnly.dataset.previewFallbackBound], html:template.html, replaced:image.replaced.id, imageSrc:imageOnly.src, bound}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "markers": ["1", "1"],
            "html": '<video data-url="/assets/video.mp4" muted></video>',
            "replaced": "fallback",
            "imageSrc": "/assets/image.png",
            "bound": ["inline", "fallback"],
        })
        for editor in ("canvas.js", "smart-canvas.js"):
            source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertIn("WorkbenchCanvasMediaPreviewControls.bindPreviewImageFallbacks", source)

    def test_media_preview_controls_preload_image_decodes_and_reports_failure(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-preview-controls.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const createImage = kind => () => {{
  const image = {{decoding:'', decode:async () => {{ image.decoded = true; }}}};
  Object.defineProperty(image, 'src', {{set: value => {{ image.value = value; queueMicrotask(() => kind === 'ok' ? image.onload() : image.onerror()); }}}});
  return image;
}};
(async () => {{
  const api = sandbox.window.WorkbenchCanvasMediaPreviewControls;
  const ok = await api.preloadImage('/assets/image.png', {{createImage:createImage('ok')}});
  const failed = await api.preloadImage('/assets/missing.png', {{createImage:createImage('fail')}});
  const empty = await api.preloadImage('', {{createImage:createImage('ok')}});
  console.log(JSON.stringify({{ok, failed, empty}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "failed": False, "empty": False})
        for editor in ("canvas.js", "smart-canvas.js"):
            source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertIn("WorkbenchCanvasMediaPreviewControls.preloadImage", source)

    def test_media_preview_controls_collect_high_res_candidates_preserves_preview_states(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-preview-controls.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const makeImage = (original, preview, src, kind='') => ({{
  dataset:{{originalSrc:original, previewSrc:preview, previewKind:kind, selectedHighResTarget:'old'}},
  getAttribute:() => src, src:'',
}});
const pending = makeImage('/assets/pending.png', '/preview/pending.png', '/preview/pending.png');
const loaded = makeImage('/assets/loaded.png', '/preview/loaded.png', '/preview/loaded.png');
const far = makeImage('/assets/far.png', '/preview/far.png', '/assets/far.png');
const video = makeImage('/assets/video.png', '/preview/video.png', '/preview/video.png', 'video');
const root = {{querySelectorAll:() => [pending, loaded, far, video]}};
const candidates = sandbox.window.WorkbenchCanvasMediaPreviewControls.collectHighResCandidates({{
  root, wantHighRes:true, isNearViewport:image => image !== far,
  resolveTarget:original => `high:${{original}}`, isLoaded:target => target.includes('loaded'),
}});
console.log(JSON.stringify({{candidates:candidates.map(item => item.target), pending:pending.dataset.selectedHighResTarget, loadedSrc:loaded.src, farSrc:far.src, farTarget:far.dataset.selectedHighResTarget || '', videoTarget:video.dataset.selectedHighResTarget}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "candidates": ["high:/assets/pending.png"],
            "pending": "high:/assets/pending.png",
            "loadedSrc": "high:/assets/loaded.png",
            "farSrc": "/preview/far.png",
            "farTarget": "",
            "videoTarget": "old",
        })
        for editor in ("canvas.js", "smart-canvas.js"):
            source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertIn("WorkbenchCanvasMediaPreviewControls.collectHighResCandidates", source)

    def test_smart_adapter_delegates_pure_media_grid_fitting_to_shared_canvas_module(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-grid-layout.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaGridLayout;
console.log(JSON.stringify({{
  fitted:api.fitSquareGrid(4, 400, 300, 100, {{pad:32, gap:8, maxVisibleRows:4}}),
  fallback:api.fitSquareGrid(3, 1, 1, 100, {{pad:32, gap:8, maxVisibleRows:2, fallbackMaxVisibleRows:4}}),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "fitted": {"cols": 3, "rows": 2, "visibleRows": 2, "thumb": 100, "score": [1, 100, 3, -73, -2]},
            "fallback": {"cols": 2, "rows": 2, "visibleRows": 2, "thumb": 28},
        })
        smart_page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        classic_page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(smart_page.index("workbench/canvas/media-grid-layout.js"), smart_page.index("smart-canvas.js"))
        self.assertLess(classic_page.index("workbench/canvas/media-grid-layout.js"), classic_page.index("canvas.js"))
        layout = smart[smart.index("function groupImageGridLayout(") : smart.index("function smartNodeInputThumbRows(")]
        self.assertIn("WorkbenchCanvasMediaGridLayout.fitSquareGrid", layout)
        self.assertNotIn("for(let cols", layout)

    def test_smart_adapter_delegates_pure_media_intrinsic_and_thumbnail_sizing(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-layout.js"
        script = f"""
const fs = require('fs'); const vm = require('vm'); const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaLayout;
console.log(JSON.stringify({{
  intrinsic:api.intrinsicSize({{natural_w:1200, natural_h:800, width:1, height:1}}),
  fallback:api.intrinsicSize({{width:0, height:40}}),
  contain:api.contain({{width:1200, height:800}}, 260, 220, {{minWidth:72, minHeight:72}}),
  thumbnail:api.thumbnailSize({{layout_w:200, layout_h:100}}, 96),
  unknown:api.thumbnailSize({{}}, 64),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "intrinsic": {"width": 1200, "height": 800}, "fallback": {"width": 0, "height": 0},
            "contain": {"width": 260, "height": 173}, "thumbnail": {"width": 96, "height": 48},
            "unknown": {"width": 64, "height": 64},
        })
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        smart_page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        classic_page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(smart_page.index("workbench/canvas/media-layout.js"), smart_page.index("smart-canvas.js"))
        self.assertLess(classic_page.index("workbench/canvas/media-layout.js"), classic_page.index("canvas.js"))
        self.assertIn("WorkbenchCanvasMediaLayout.intrinsicSize", smart)
        self.assertIn("WorkbenchCanvasMediaLayout.contain", smart)
        self.assertIn("WorkbenchCanvasMediaLayout.thumbnailSize", smart)

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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
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
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertLess(page_source.index("workbench/canvas/canvas-http-error.js"), page_source.index(editor))
            self.assertIn("WorkbenchCanvasHttpError.message", editor_source)
            self.assertIn("WorkbenchCanvasHttpError.responseMessage", editor_source)
            self.assertNotIn("const detail = data.detail ?? data.error ?? data.message", editor_source)

    def test_editor_adapters_share_the_workflow_transfer_transport_boundary(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "workflow-transfer-client.js"
        graph = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-graph-fragment.js"
        http_error = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-http-error.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const downloads = [];
const revoked = [];
const sandbox = {{
  window: {{}}, Blob, FormData,
  URL: {{createObjectURL: () => 'blob:workflow', revokeObjectURL: url => revoked.push(url)}},
  document: {{
    body: {{appendChild: link => downloads.push({{event:'append', href:link.href, download:link.download}})}},
    createElement: () => ({{
      href:'', download:'',
      click: function() {{ downloads.push({{event:'click', href:this.href, download:this.download}}); }},
      remove: function() {{ downloads.push({{event:'remove'}}); }},
    }}),
  }},
  setTimeout: (callback, delay) => {{ downloads.push({{event:'timeout', delay}}); callback(); }},
  fetch: async (path, options={{}}) => {{
    requests.push({{path, options}});
    return path.endsWith('/export')
      ? {{ok:true, json: async () => ({{}}), blob: async () => new Blob(['archive'])}}
      : {{ok:true, json: async () => ({{workflow:{{nodes:[{{id:'n1'}}], connections:[]}}}})}};
  }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(graph))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(http_error))}, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
(async () => {{
  const archive = await sandbox.window.WorkbenchCanvasWorkflowTransfer.exportArchive({{nodes:[{{id:'n1'}}]}}, 'flow.zip');
  const imported = await sandbox.window.WorkbenchCanvasWorkflowTransfer.importArchive(new Blob(['flow']));
  const jsonExport = await sandbox.window.WorkbenchCanvasWorkflowTransfer.jsonExportBlob({{nodes:[{{id:'json'}}]}}).text();
  sandbox.window.WorkbenchCanvasWorkflowTransfer.downloadBlob(new Blob(['download']), '', {{fallbackFilename:'fallback.json', revokeAfterMs:800}});
  const errors = [
    sandbox.window.WorkbenchCanvasWorkflowTransfer.errorMessage('raw failure', 'fallback'),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.errorMessage({{detail:'plain'}}, 'fallback'),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.errorMessage({{detail:[{{loc:['body', 'nodes', 0], msg:'invalid'}}]}}, 'fallback'),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.errorMessage({{detail:{{message:'nested'}}}}, 'fallback'),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.errorMessage({{}}, 'fallback'),
  ];
  const normalized = [
    sandbox.window.WorkbenchCanvasWorkflowTransfer.normalizeImported(imported),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.normalizeImported([{{id:'legacy'}}]),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.normalizeImported({{nodes:[{{id:'direct'}}]}}),
    sandbox.window.WorkbenchCanvasWorkflowTransfer.normalizeImported({{invalid:true}}),
  ];
  const selected = sandbox.window.WorkbenchCanvasGraphFragment.selectedSubgraph({{
    nodes:[{{id:'a'}}, {{id:'b'}}, {{id:'c'}}],
    connections:[{{from:'a', to:'b', state:{{live:true}}}}, {{from:'b', to:'c'}}, {{from:'c', to:'a'}}],
    selectedIds:['b', 'missing', 'a', 'b'],
    serializeNode:node => ({{...node, exported:true}}),
    order:'selection',
  }});
  const sourceOrder = sandbox.window.WorkbenchCanvasGraphFragment.selectedSubgraph({{
    nodes:[{{id:'a'}}, {{id:'b'}}, {{id:'c'}}], selectedIds:['c', 'a'],
  }});
  let nextId = 0;
  const materialized = sandbox.window.WorkbenchCanvasGraphFragment.materializeImportedSubgraph({{
    nodes:[{{id:'a', x:10, y:20}}, {{id:'b', x:30, y:25}}],
    connections:[{{from:'a', to:'b', metadata:{{source:true}}}}, {{from:'b', to:'missing'}}],
    target:{{x:100, y:200}},
    serializeNode:node => ({{...node}}),
    createNodeId:type => `${{type}}-${{++nextId}}`,
    prepareNode:node => ({{...node, prepared:true}}),
    createConnection:(connection, endpoints) => ({{...connection, ...endpoints, copied:true}}),
  }});
  const centered = sandbox.window.WorkbenchCanvasGraphFragment.materializeImportedSubgraph({{
    nodes:[{{id:'left', x:10, y:20}}, {{id:'right', x:30, y:40}}],
    target:{{x:100, y:200}}, anchor:'center',
    serializeNode:node => ({{...node}}), createNodeId:type => `center-${{type}}`,
  }});
  const expanded = sandbox.window.WorkbenchCanvasGraphFragment.expandNodeIds({{
    nodes:[{{id:'group', items:['child', 'nested']}}, {{id:'child'}}, {{id:'nested', items:['leaf']}}, {{id:'leaf'}}],
    initialIds:['group'], childIds:node => node.items || [],
  }});
  const removed = sandbox.window.WorkbenchCanvasGraphFragment.removeGraphRecords({{
    nodes:[{{id:'group'}}, {{id:'child'}}, {{id:'keep'}}],
    connections:[{{from:'group', to:'child'}}, {{from:'keep', to:'child'}}, {{from:'keep', to:'keep'}}],
    removeIds:expanded,
  }});
  console.log(JSON.stringify({{archiveSize:archive.size, imported, jsonExport, errors, normalized, selected, sourceOrder, materialized:{{nodes:materialized.nodes, connections:materialized.connections, idMap:[...materialized.idMap.entries()]}}, centered:{{nodes:centered.nodes, connections:centered.connections}}, expanded:[...expanded], removed, downloads, revoked, requests:requests.map(item => ({{path:item.path, method:item.options.method, body:item.options.body}}))}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["archiveSize"], 7)
        self.assertEqual(payload["imported"]["workflow"]["nodes"], [{"id": "n1"}])
        self.assertEqual(json.loads(payload["jsonExport"]), {"nodes": [{"id": "json"}]})
        self.assertEqual(
            payload["errors"],
            ["raw failure", "plain", "nodes.0: invalid", "nested", "{}"],
        )
        self.assertEqual(payload["downloads"], [
            {"event": "append", "href": "blob:workflow", "download": "fallback.json"},
            {"event": "click", "href": "blob:workflow", "download": "fallback.json"},
            {"event": "remove"},
            {"event": "timeout", "delay": 800},
        ])
        self.assertEqual(payload["revoked"], ["blob:workflow"])
        self.assertEqual(payload["normalized"], [
            {"nodes": [{"id": "n1"}], "connections": []},
            {"nodes": [{"id": "legacy"}], "connections": []},
            {"nodes": [{"id": "direct"}], "connections": []},
            {"nodes": [], "connections": []},
        ])
        self.assertEqual(payload["selected"], {
            "nodes": [{"id": "b", "exported": True}, {"id": "a", "exported": True}],
            "connections": [{"from": "a", "to": "b", "state": {"live": True}}],
        })
        self.assertEqual(payload["sourceOrder"], {
            "nodes": [{"id": "a"}, {"id": "c"}],
            "connections": [],
        })
        self.assertEqual(payload["materialized"], {
            "nodes": [
                {"id": "node-1", "x": 100, "y": 200, "prepared": True},
                {"id": "node-2", "x": 120, "y": 205, "prepared": True},
            ],
            "connections": [{
                "from": "node-1", "to": "node-2", "metadata": {"source": True}, "copied": True,
            }],
            "idMap": [["a", "node-1"], ["b", "node-2"]],
        })
        self.assertEqual(payload["centered"], {
            "nodes": [{"id": "center-node", "x": 90, "y": 190}, {"id": "center-node", "x": 110, "y": 210}],
            "connections": [],
        })
        self.assertEqual(payload["expanded"], ["group", "child", "nested", "leaf"])
        self.assertEqual(payload["removed"], {
            "nodes": [{"id": "keep"}],
            "connections": [{"from": "keep", "to": "keep"}],
        })
        self.assertEqual(payload["requests"][0]["path"], "/api/canvas-workflows/export")
        self.assertEqual(payload["requests"][0]["method"], "POST")
        self.assertEqual(json.loads(payload["requests"][0]["body"]), {
            "nodes": [{"id": "n1"}], "include_resources": True, "filename": "flow.zip",
        })
        self.assertEqual(payload["requests"][1]["path"], "/api/canvas-workflows/import")
        self.assertEqual(payload["requests"][1]["method"], "POST")

        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            page_source = (ROOT / "static" / page).read_text(encoding="utf-8")
            editor_source = (ROOT / "static" / "js" / editor).read_text(encoding="utf-8")
            self.assertLess(page_source.index("workbench/canvas/workflow-transfer-client.js"), page_source.index(editor))
            self.assertLess(page_source.index("workbench/canvas/canvas-graph-fragment.js"), page_source.index("workbench/canvas/workflow-transfer-client.js"))
            self.assertIn("WorkbenchCanvasWorkflowTransfer.exportArchive", editor_source)
            self.assertIn("WorkbenchCanvasWorkflowTransfer.importArchive", editor_source)
            self.assertIn("WorkbenchCanvasWorkflowTransfer.normalizeImported", editor_source)
            self.assertIn("WorkbenchCanvasWorkflowTransfer.jsonExportBlob", editor_source)
            self.assertIn("WorkbenchCanvasWorkflowTransfer.downloadBlob", editor_source)
            self.assertIn("WorkbenchCanvasGraphFragment.selectedSubgraph", editor_source)
            self.assertIn("WorkbenchCanvasGraphFragment.materializeImportedSubgraph", editor_source)
        graph_source = graph.read_text(encoding="utf-8")
        client_source = client.read_text(encoding="utf-8")
        self.assertIn("WorkbenchCanvasGraphFragment", graph_source)
        self.assertNotIn("fetch(", graph_source)
        self.assertNotIn("document.", graph_source)
        self.assertNotIn("localStorage", graph_source)
        self.assertIn("WorkbenchCanvasHttpError", client_source)
        self.assertNotIn("const detail = payload.detail", client_source)
        classic_source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchCanvasGraphFragment.expandNodeIds", classic_source)
        self.assertIn("WorkbenchCanvasGraphFragment.removeGraphRecords", classic_source)
        self.assertIn(
            "WorkbenchCanvasGraphFragment.removeGraphRecords",
            (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8"),
        )
        classic_export = editor_source = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        classic_export = classic_export[classic_export.index("async function exportSelectedWorkflow(") : classic_export.index("function defaultWorkflowAssetTarget(")]
        classic_import = editor_source[editor_source.index("async function importWorkflowFile(") : editor_source.index("function startNodeDrag(")]
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        smart_export = smart[smart.index("async function exportSelectedSmartWorkflow(") : smart.index("function insertSmartWorkflowIntoCanvas(")]
        smart_import = smart[smart.index("async function importSmartWorkflowFile(") : smart.index("const RECENT_SMART_SETTINGS_KEY")]
        for adapter in (classic_export, classic_import, smart_export, smart_import):
            self.assertNotIn("/api/canvas-workflows/export", adapter)
            self.assertNotIn("/api/canvas-workflows/import", adapter)
        self.assertNotIn("function normalizeImportedWorkflow", editor_source)
        self.assertNotIn("function normalizeImportedSmartWorkflow", smart)
        self.assertNotIn("function downloadBlob", editor_source)
        self.assertNotIn("function downloadBlob", smart)
        self.assertNotIn("new Blob([JSON.stringify(payload, null, 2)]", classic_export)
        self.assertNotIn("new Blob([JSON.stringify(payload, null, 2)]", smart_export)
        classic_copy = editor_source[editor_source.index("function copySelectedNodes(){") : editor_source.index("function clipboardNodeCount(){")]
        smart_copy = smart[smart.index("function copySelectedNodes(){") : smart.index("function pasteNodes(){")]
        for adapter in (classic_copy, smart_copy):
            self.assertIn("WorkbenchCanvasGraphFragment.selectedSubgraph", adapter)
            self.assertNotIn("filter(c => ids.has(c.from) && ids.has(c.to))", adapter)
        classic_paste = editor_source[editor_source.index("function pasteNodes(){") : editor_source.index("function selectedWorkflowPayload(){")]
        smart_paste = smart[smart.index("function pasteNodes(){") : smart.index("// 跨页\"素材库")]
        for adapter in (classic_paste, smart_paste):
            self.assertIn("WorkbenchCanvasGraphFragment.materializeImportedSubgraph", adapter)
            self.assertIn("anchor:'center'", adapter)

    def test_editor_adapters_share_the_canvas_record_persistence_boundary(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const requests = [];
const responses = [
  {{ok:true, status:200, json: async () => ({{canvas:{{id:'canvas/1', updated_at:7}}}})}},
  {{ok:false, status:409, json: async () => ({{detail:{{canvas:{{id:'canvas/1', updated_at:8}}, updated_at:8}}}})}},
  {{ok:true, status:200, json: async () => ({{updated_at:9}})}},
];
const sandbox = {{window: {{}}, fetch: async (path, options={{}}) => {{
  requests.push({{path, options}});
  return responses.shift();
}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
(async () => {{
  const loaded = await sandbox.window.WorkbenchCanvasPersistence.load('canvas/1');
  const stale = await sandbox.window.WorkbenchCanvasPersistence.save('canvas/1', {{title:'Shared'}});
  const metadata = await sandbox.window.WorkbenchCanvasPersistence.metadata('canvas/1');
  console.log(JSON.stringify({{loaded, stale, metadata, requests}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["loaded"]["canvas"]["id"], "canvas/1")
        self.assertEqual(payload["stale"]["status"], 409)
        self.assertEqual(payload["stale"]["canvas"]["updated_at"], 8)
        self.assertEqual(payload["stale"]["updatedAt"], 8)
        self.assertEqual(payload["metadata"]["updatedAt"], 9)
        # Canonical-first load: a revision-less canonical response carries no cursor,
        # so the save falls back to the legacy transport with the record as body.
        self.assertEqual(payload["requests"][0]["path"], "/api/v1/canvases/canvas%2F1")
        self.assertEqual(payload["requests"][0]["options"]["method"], "GET")
        self.assertEqual(payload["requests"][1]["options"]["method"], "PUT")
        self.assertEqual(payload["requests"][1]["path"], "/api/canvases/canvas%2F1")
        self.assertEqual(json.loads(payload["requests"][1]["options"]["body"]), {"title": "Shared"})
        self.assertEqual(payload["requests"][2]["path"], "/api/v1/canvases/canvas%2F1/meta")

        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            self.assertLess(text.index("workbench/canvas/canvas-persistence-client.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/canvas-remote-sync.js"), text.index(editor))
            self.assertLess(text.index("workbench/canvas/canvas-update-message.js"), text.index(editor))
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        classic_save = classic[classic.index("async function saveCanvas(){") : classic.index("async function loadConfig(){")]
        classic_open = classic[classic.index("async function openCanvas(id){") : classic.index("function applyRemoteCanvasData(remote){")]
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        smart_load = smart[smart.index("async function loadCanvas(){") : smart.index("function scheduleSave(){")]
        smart_save = smart[smart.index("async function saveCanvas(){") : smart.index("function imageMetaFromNode")]
        classic_remote_sync = classic[classic.index("async function syncRemoteCanvasNow(){") : classic.index("function startCanvasRemotePolling(){")]
        smart_remote_sync = smart[smart.index("async function mergeReloadCanvasNow(){") : smart.index("function connectAssetLibrarySyncSocket(){")]
        for adapter in (classic_save, classic_open, smart_load, smart_save, classic_remote_sync, smart_remote_sync):
            self.assertIn("WorkbenchCanvasPersistence", adapter)
            self.assertNotIn("fetch(`/api/canvases/", adapter)

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
        # Canonical GET then three canonical CAS PUTs whose expected_revision follows
        # load -> save -> conflict -> recovery, with transport fields stripped.
        self.assertEqual(payload["requests"][0]["path"], "/api/v1/canvases/c1")
        self.assertEqual(payload["requests"][1]["path"], "/api/v1/canvases/c1")
        self.assertEqual(json.loads(payload["requests"][1]["options"]["body"]), {"payload": {"title": "A"}, "expected_revision": 5, "client_id": "editor-1"})
        self.assertEqual(json.loads(payload["requests"][2]["options"]["body"])["expected_revision"], 6)
        self.assertEqual(json.loads(payload["requests"][3]["options"]["body"])["expected_revision"], 9)
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

    def test_rendering_ownership_map_shared_seams_are_load_order_stable_and_mounted_once(self):
        # R4-08 characterization: the shared render pipeline loads before both
        # adapters, the registry prefers media over source-payload, both adapters
        # mount through the unified host, and neither adapter ever tears a mounted
        # card down (DOM dies by omission from the next render sweep).
        order = [
            "renderer-registry.js", "renderer-admission.js", "node-shell.js",
            "legacy-renderer.js", "media-renderer.js", "node-card-host.js",
            "unified-render-host.js",
        ]
        for page, adapter in (("canvas.html", "js/canvas.js"), ("smart-canvas.html", "js/smart-canvas.js")):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            positions = [text.index(f"workbench/canvas/{name}") for name in order]
            self.assertEqual(positions, sorted(positions), page)
            self.assertLess(positions[-1], text.index(adapter), page)
        host = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-card-host.js").read_text(encoding="utf-8")
        self.assertLess(host.index("id: 'media'"), host.index("id: 'source-payload'"))
        self.assertIn("priority: 100", host[:host.index("id: 'source-payload'")])
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchUnifiedRenderHost.mountAdapterCard", classic)
        self.assertIn("ensureSmartRenderRuntime().mountAll(entries)", smart)
        for adapter_source in (classic, smart):
            self.assertIn("WorkbenchCanvasMediaPlaybackState.capture", adapter_source)
            self.assertNotIn(".destroy()", adapter_source)

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

    def test_render_runtime_is_wired_as_the_single_card_lifecycle_owner(self):
        runtime_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "render-runtime.js").read_text(encoding="utf-8")
        self.assertIn("global.WorkbenchRenderRuntime", runtime_source)
        for page, adapter in (("canvas.html", "js/canvas.js"), ("smart-canvas.html", "js/smart-canvas.js")):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            self.assertLess(text.index("workbench/canvas/unified-render-host.js"), text.index("workbench/canvas/render-runtime.js"), page)
            self.assertLess(text.index("workbench/canvas/render-runtime.js"), text.index(adapter), page)
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        # The UnifiedRenderHost mount is injected once per page; every card mount
        # goes through the runtime, and delete/refresh flows unmount through it.
        self.assertEqual(classic.count("WorkbenchUnifiedRenderHost.mountAdapterCard("), 1)
        self.assertEqual(smart.count("WorkbenchUnifiedRenderHost.mountAdapterCard("), 1)
        self.assertNotIn("mountAdapterCards(entries)", smart)
        for adapter, expected_reset in ((classic, "renderRuntime?.unmountAll()"), (smart, "smartRenderRuntime?.unmountAll()")):
            self.assertIn("WorkbenchRenderRuntime.create", adapter)
            self.assertIn(expected_reset, adapter)
        self.assertIn("renderRuntime?.unmount(id)", classic)
        self.assertIn("smartRenderRuntime?.unmount(deleteId)", smart)

    def test_versioned_writes_adopt_revisions_through_one_shared_owner(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-persistence-client.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const adopt = sandbox.window.WorkbenchCanvasPersistence.adoptRevision;
const newer = {{updated_at: 400}};
const kept = {{updated_at: 400}};
const seeded = {{}};
const revisionless = {{}};
console.log(JSON.stringify({{
  newer: adopt(newer, 500),
  newerStored: newer.updated_at,
  keptCurrent: adopt(kept, 0, 12345),
  keptStored: kept.updated_at,
  seededValue: adopt(seeded, 0, 12345),
  seededStored: seeded.updated_at,
  revisionless: adopt(revisionless, 0, 0),
  revisionlessStored: revisionless.updated_at,
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["newer"], 500)
        self.assertEqual(payload["newerStored"], 500)
        self.assertEqual(payload["keptCurrent"], 400)
        self.assertEqual(payload["keptStored"], 400)
        self.assertEqual(payload["seededValue"], 12345)
        self.assertEqual(payload["seededStored"], 12345)
        self.assertEqual(payload["revisionless"], 0)

        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertNotIn("canvas.updated_at = Number(result.canvas_revision", classic)
        self.assertNotIn("canvas.updated_at = Number(result.canvas_revision", smart)
        self.assertEqual(classic.count("WorkbenchCanvasPersistence.adoptRevision(canvas, result.canvas_revision, Date.now())"), 10)
        self.assertEqual(classic.count("WorkbenchCanvasPersistence.adoptRevision(canvas, revision)"), 8)
        self.assertEqual(smart.count("WorkbenchCanvasPersistence.adoptRevision(canvas, result.canvas_revision, Date.now())"), 4)
        self.assertEqual(smart.count("WorkbenchCanvasPersistence.adoptRevision(canvas, result.canvas_revision, 0)"), 4)

    def test_editor_saves_share_one_scheduler(self):
        scheduler = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-save-scheduler.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const timers = [];
const sandbox = {{
  window: {{}},
  setTimeout: (callback, delay) => {{ timers.push({{callback, delay, cleared: false}}); return timers.length; }},
  clearTimeout: handle => {{ if (timers[handle - 1]) timers[handle - 1].cleared = true; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(scheduler))}, 'utf8'), sandbox);
const S = sandbox.window.WorkbenchCanvasSaveScheduler;
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
(async () => {{
  const runsA = [];
  const schedA = S.create({{debounceMs: 500, run: async () => {{ runsA.push(1); }}}});
  schedA.schedule();
  const pending = timers[timers.length - 1];
  const debouncedOnly = pending.delay === 500 && !pending.cleared && runsA.length === 0;
  pending.callback();
  await tick();
  const firedAfterDebounce = runsA.length === 1;

  const runsB = [];
  const retries = [];
  let releaseB;
  const gateB = new Promise(resolve => {{ releaseB = resolve; }});
  const schedB = S.create({{debounceMs: 100, run: async () => {{ runsB.push(1); await gateB; }}, onRetry: () => retries.push(1)}});
  const first = schedB.flush();
  await tick();
  const second = await schedB.flush();
  schedB.schedule();
  const coalesced = {{second, noTimer: !schedB.hasScheduled(), again: schedB.hasPendingAgain()}};
  releaseB();
  const firstDone = await first;
  const retryTimer = timers[timers.length - 1];
  const retryScheduled = retries.length === 1 && retryTimer.delay === 0 && !retryTimer.cleared;
  retryTimer.callback();
  await tick();
  const retried = runsB.length === 2;

  const runsC = [];
  let releaseC;
  const gateC = new Promise(resolve => {{ releaseC = resolve; }});
  const schedC = S.create({{debounceMs: 100, allowOverlap: true, run: async () => {{ runsC.push(1); await gateC; }}}});
  const overlap1 = schedC.flush();
  await tick();
  const overlap2 = schedC.flush();
  releaseC();
  const overlapDone = (await Promise.all([overlap1, overlap2])) && runsC.length === 2;

  const runsD = [];
  const schedD = S.create({{debounceMs: 50, run: async () => {{ runsD.push(1); }}}});
  schedD.schedule();
  schedD.cancel();
  const canceled = !schedD.hasScheduled();
  await tick();
  console.log(JSON.stringify({{debouncedOnly, firedAfterDebounce, coalesced, firstDone, retryScheduled, retried, overlapDone, canceled, runsD: runsD.length}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["debouncedOnly"])
        self.assertTrue(payload["firedAfterDebounce"])
        self.assertEqual(payload["coalesced"], {"second": False, "noTimer": True, "again": True})
        self.assertTrue(payload["firstDone"])
        self.assertTrue(payload["retryScheduled"])
        self.assertTrue(payload["retried"])
        self.assertTrue(payload["overlapDone"])
        self.assertTrue(payload["canceled"])
        self.assertEqual(payload["runsD"], 0)

        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            self.assertLess(text.index("workbench/canvas/canvas-save-scheduler.js"), text.index(editor))
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        for legacy_state in ("savingCanvasNow", "saveCanvasAgain", "saveTimer"):
            self.assertNotIn(legacy_state, classic)
        self.assertIn("WorkbenchCanvasSaveScheduler.create", classic)
        for legacy_state in ("canvasSyncInFlight", "saveTimer"):
            self.assertNotIn(legacy_state, smart)
        self.assertIn("WorkbenchCanvasSaveScheduler.create", smart)
        self.assertIn("allowOverlap: true", smart)

    def test_remote_apply_retries_share_one_scheduler_owner(self):
        scheduler = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-save-scheduler.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const timers = [];
const sandbox = {{
  window: {{}},
  setTimeout: (callback, delay) => {{ timers.push({{callback, delay, cleared: false}}); return timers.length; }},
  clearTimeout: handle => {{ if (timers[handle - 1]) timers[handle - 1].cleared = true; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(scheduler))}, 'utf8'), sandbox);
const S = sandbox.window.WorkbenchCanvasSaveScheduler;
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
(async () => {{
  const applied = [];
  const remote = S.createRemoteApply({{apply: () => applied.push(1), defaultDelayMs: 1000}});
  remote.schedule();
  const first = timers[timers.length - 1];
  const defaulted = first.delay === 1000 && !first.cleared && applied.length === 0;
  remote.schedule(700);
  const replaced = first.cleared && applied.length === 0;
  const second = timers[timers.length - 1];
  second.callback();
  await tick();
  const fired = applied.length === 1 && !remote.hasPending();

  remote.schedule(50);
  remote.cancel();
  const canceled = !remote.hasPending();
  await tick();

  const bare = S.createRemoteApply({{apply: () => applied.push(2)}});
  bare.schedule();
  const fallbackDefault = timers[timers.length - 1].delay === 200;
  let rejected = false;
  try {{ S.createRemoteApply({{ }}); }} catch (e) {{ rejected = true; }}
  console.log(JSON.stringify({{defaulted, replaced, fired, canceled, applied: applied.length, fallbackDefault, rejected}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["defaulted"])
        self.assertTrue(payload["replaced"])
        self.assertTrue(payload["fired"])
        self.assertTrue(payload["canceled"])
        self.assertEqual(payload["applied"], 1)
        self.assertTrue(payload["fallbackDefault"])
        self.assertTrue(payload["rejected"])

        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertNotIn("remoteSyncTimer", classic)
        self.assertIn("WorkbenchCanvasSaveScheduler.createRemoteApply", classic)
        self.assertIn("defaultDelayMs: 1000", classic)
        self.assertEqual(classic.count("remoteApplyTimer.schedule("), 2)
        self.assertNotIn("canvasSyncTimer", smart)
        self.assertNotIn("scheduleCanvasMergeReload", smart)
        self.assertIn("WorkbenchCanvasSaveScheduler.createRemoteApply", smart)
        self.assertIn("defaultDelayMs: 200", smart)
        self.assertEqual(smart.count("mergeReloadTimer.schedule("), 2)

    def test_remote_sync_polls_canvas_metadata_through_adapter_callbacks(self):
        remote_sync = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-remote-sync.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const timers = [];
let metadataCalls = 0;
const sandbox = {{
  window: {{WorkbenchCanvasPersistence: {{metadata: async canvasId => {{
    metadataCalls += 1;
    return {{ok:true, updatedAt: metadataCalls === 1 ? 8 : 9, canvasId}};
  }}}}}},
  setInterval: (callback, intervalMs) => {{ timers.push({{callback, intervalMs}}); return timers.length; }},
  clearInterval: handle => {{ timers[handle - 1].cleared = true; }},
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(remote_sync))}, 'utf8'), sandbox);
(async () => {{
  let current = 7;
  const newer = [];
  const sync = sandbox.window.WorkbenchCanvasRemoteSync.create({{
    canvasId: () => 'canvas-1', currentUpdatedAt: () => current,
    isEligible: () => true, onNewer: result => newer.push(result.updatedAt), intervalMs: 2500,
  }});
  const first = await sync.check();
  current = 9;
  const second = await sync.check();
  sync.start(); sync.start(); sync.stop();
  console.log(JSON.stringify({{first, second, newer, metadataCalls, interval:timers[0].intervalMs, timerCount:timers.length, cleared:timers[0].cleared, running:sync.isRunning()}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["first"])
        self.assertFalse(payload["second"])
        self.assertEqual(payload["newer"], [8])
        self.assertEqual(payload["metadataCalls"], 2)
        self.assertEqual(payload["interval"], 2500)
        self.assertEqual(payload["timerCount"], 1)
        self.assertTrue(payload["cleared"])
        self.assertFalse(payload["running"])

        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("function ensureCanvasRemoteSync(){", classic)
        self.assertIn("intervalMs:2500", classic)
        self.assertIn("window.WorkbenchCanvasRemoteSync.create", classic)
        self.assertIn("intervalMs:8000", smart)
        self.assertIn("window.WorkbenchCanvasRemoteSync.create", smart)

    def test_canvas_update_messages_are_filtered_before_adapter_sync_policy(self):
        update_message = ROOT / "static" / "js" / "workbench" / "canvas" / "canvas-update-message.js"
        script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(update_message))}, 'utf8'), sandbox);
const match = sandbox.window.WorkbenchCanvasUpdateMessage.newerForCanvas(
  {{type:'canvas_updated', canvas_id:'canvas-1', client_id:'other', updated_at:8}},
  {{canvasId:'canvas-1', clientId:'local', currentUpdatedAt:7}},
);
const own = sandbox.window.WorkbenchCanvasUpdateMessage.newerForCanvas(
  {{type:'canvas_updated', canvas_id:'canvas-1', client_id:'local', updated_at:8}},
  {{canvasId:'canvas-1', clientId:'local', currentUpdatedAt:7}},
);
const stale = sandbox.window.WorkbenchCanvasUpdateMessage.newerForCanvas(
  {{type:'canvas_updated', canvas_id:'canvas-1', client_id:'other', updated_at:7}},
  {{canvasId:'canvas-1', clientId:'local', currentUpdatedAt:7}},
);
const wrongCanvas = sandbox.window.WorkbenchCanvasUpdateMessage.newerForCanvas(
  {{type:'canvas_updated', canvas_id:'canvas-2', client_id:'other', updated_at:8}},
  {{canvasId:'canvas-1', clientId:'local', currentUpdatedAt:7}},
);
console.log(JSON.stringify({{match, own, stale, wrongCanvas}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["match"], {"canvasId": "canvas-1", "clientId": "other", "updatedAt": 8})
        self.assertIsNone(payload["own"])
        self.assertIsNone(payload["stale"])
        self.assertIsNone(payload["wrongCanvas"])

        for source in (ROOT / "static" / "js" / "canvas.js", ROOT / "static" / "js" / "smart-canvas.js"):
            text = source.read_text(encoding="utf-8")
            start = text.index("function handleCanvasUpdatedMessage")
            handler = text[start : start + 700]
            self.assertIn("WorkbenchCanvasUpdateMessage.newerForCanvas", handler)

    def test_opening_a_classic_canvas_does_not_issue_a_touch_write(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        opening = classic[classic.index("async function openCanvas(id){") : classic.index("function applyRemoteCanvasData(remote){")]
        self.assertNotIn("touchCanvasOpened", classic)
        self.assertNotIn("/touch", opening)

    def test_canvas_selection_paths_do_not_schedule_persistence(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        classic_selection = classic[classic.index("el.onclick = (e) => {") : classic.index("el.oncontextmenu = e => {")]
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        smart_selection = smart[smart.index("function applySmartNodeSelection(") : smart.index("function smartSelectionToggleRequested(")]
        smart_shell_selection = smart[smart.index("function selectSmartNodeFromShell(") : smart.index("function startSmartPortDrag(")]
        for selection_path in (classic_selection, smart_selection, smart_shell_selection):
            self.assertNotIn("scheduleSave(", selection_path)

    def test_both_canvas_pages_load_compatibility_modules_before_editor(self):
        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
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
        self.assertIn("const rendererFlags = [", harness)
        self.assertIn("'node_shell', 'legacy_renderer', 'media_renderer', 'semantic_zoom'", harness)
        self.assertIn("'screen_space_controls', 'unified_canvas'", harness)
        self.assertIn(".filter(name => params.get(name) === '1')", harness)
        self.assertIn("const benchmarkNonce = Date.now();", harness)
        self.assertIn("&benchmark=1&benchmark_nonce=${benchmarkNonce}${rendererQuery}", harness)
        self.assertIn("renderer_flags=${rendererFlags.length ? rendererFlags.join(',') : 'none'}", harness)
        self.assertIn("const visibleTarget = params.get('visible') === '1';", harness)
        self.assertIn("document.body.classList.toggle('visible-target', visibleTarget);", harness)
        self.assertIn("target_visibility=${visibleTarget ? 'visible' : 'offscreen'}", harness)

    def test_classic_minimap_updates_the_viewport_box_without_rebuilding_nodes(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        harness = (ROOT / "static" / "canvas-performance-harness.html").read_text(encoding="utf-8")
        apply_viewport = classic[classic.index("function applyViewport()") : classic.index("function canvasNodeShellSemanticZoomEnabled()")]
        self.assertIn("scheduleMinimapViewportUpdate();", apply_viewport)
        self.assertNotIn("scheduleMinimapRender();", apply_viewport)
        self.assertIn("function scheduleMinimapViewportUpdate(){", classic)
        self.assertIn("updateMinimapViewport();", classic)
        self.assertIn("if(!enabled){\n        existingIndicator?.remove();\n        return;\n    }", classic)
        self.assertIn("const oldViewportStyle = oldViewport?.getAttribute('style') || '';", harness)
        self.assertIn("nextViewport.getAttribute('style') !== oldViewportStyle", harness)

    def test_shared_viewport_pan_session_preserves_adapter_thresholds(self):
        runtime = ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime))}, 'utf8'), sandbox);
const shared = sandbox.window.WorkbenchCanvasRuntime;
const classic = shared.createViewportPanSession({{start:{{x:10,y:20}}, viewport:{{x:5,y:6,scale:2}}, threshold:4}}).move({{x:13,y:24}});
const smart = shared.createViewportPanSession({{start:{{x:0,y:0}}, viewport:{{x:1,y:2,scale:1}}, threshold:3, metric:'manhattan'}}).move({{x:2,y:2}});
const classicZoom = shared.viewportScaleForWheel({{x:0,y:0,scale:1}}, 4, {{strategy:'step', outFactor:.92, inFactor:1.08}});
const smartZoom = shared.viewportScaleForWheel({{x:0,y:0,scale:1}}, -1000, {{strategy:'exponential', deltaLimit:240, sensitivity:.001, minScale:.06, maxScale:3}});
const minimapViewport = shared.viewportCenteredOnWorldPoint({{x:4,y:5,scale:2}}, {{x:30,y:40}}, {{width:200,height:120}});
const minimapPoint = shared.worldPointFromMinimapPointer({{x:62,y:88}}, {{screenOrigin:{{x:10,y:20}}, worldOrigin:{{x:-100,y:50}}, offset:{{x:2,y:4}}, scale:2}});
console.log(JSON.stringify({{classic, smart, classicZoom, smartZoom, minimapViewport, minimapPoint}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "classic": {"moved": True, "viewport": {"x": 8, "y": 10, "scale": 2}},
            "smart": {"moved": True, "viewport": {"x": 3, "y": 4, "scale": 1}},
            "classicZoom": 0.92,
            "smartZoom": 1.2712491503214047,
            "minimapViewport": {"x": 40, "y": -20, "scale": 2},
            "minimapPoint": {"x": -75, "y": 82},
        })
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("canvasUnifiedRuntimeEnabled", classic)
        self.assertIn("createViewportPanSession", classic)
        self.assertIn("viewportScaleForWheel", classic)
        self.assertIn("viewportCenteredOnWorldPoint", classic)
        self.assertIn("worldPointFromMinimapPointer", classic)
        self.assertIn("let restoredViewport = {x:prev.x, y:prev.y, scale:restoredScale};", classic)
        self.assertIn("const targetViewport = (canvasUnifiedRuntimeEnabled", classic)
        self.assertIn("smartUnifiedRuntimeEnabled", smart)
        self.assertIn("metric:'manhattan'", smart)
        self.assertIn("strategy:'exponential'", smart)
        self.assertIn("viewportCenteredOnWorldPoint", smart)
        self.assertIn("worldPointFromMinimapPointer", smart)
        self.assertIn("let restoredViewport = {x:prev.x, y:prev.y, scale:prev.scale};", smart)
        self.assertIn("const targetViewport = (smartUnifiedRuntimeEnabled", smart)

    def test_shared_node_drag_session_projects_member_positions(self):
        runtime = ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime))}, 'utf8'), sandbox);
const shared = sandbox.window.WorkbenchCanvasRuntime;
const session = shared.createNodeDragSession({{
  start:{{x:10, y:20}}, scale:2,
  members:[{{id:'a', ox:100, oy:50}}, {{id:'b', ox:0, oy:0}}, null, {{ox:1, oy:1}}],
}});
const moved = session.move({{x:30, y:60}});
const rescaled = session.move({{x:30, y:60}}, {{scale:1}});
const fallbackSession = shared.createNodeDragSession({{start:{{x:0, y:0}}, members:[{{id:'m', ox:5, oy:6}}]}});
const fallbackMoved = fallbackSession.move({{x:4, y:8}});
console.log(JSON.stringify({{
  members: session.members.map(member => ({{id:member.id, ox:member.ox, oy:member.oy}})),
  moved,
  rescaled,
  fallbackMoved,
  frozen: Object.isFrozen(session) && Object.isFrozen(moved) && Object.isFrozen(moved.positions) && Object.isFrozen(moved.positions[0]),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "members": [{"id": "a", "ox": 100, "oy": 50}, {"id": "b", "ox": 0, "oy": 0}],
            "moved": {"dx": 10, "dy": 20, "positions": [{"id": "a", "x": 110, "y": 70}, {"id": "b", "x": 10, "y": 20}]},
            "rescaled": {"dx": 20, "dy": 40, "positions": [{"id": "a", "x": 120, "y": 90}, {"id": "b", "x": 20, "y": 40}]},
            "fallbackMoved": {"dx": 4, "dy": 8, "positions": [{"id": "m", "x": 9, "y": 14}]},
            "frozen": True,
        })
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("window.WorkbenchCanvasRuntime?.createNodeDragSession?.({", classic)
        self.assertIn("isLocalCopy:Boolean(e.altKey), dragSession};", classic)
        self.assertIn("const dragPosition = (id, ox, oy) => sharedPositions?.get(id) || {x:ox + dx, y:oy + dy};", classic)
        self.assertIn("(e.clientX - dragNode.sx) / viewport.scale", classic)
        self.assertIn("window.WorkbenchCanvasRuntime?.createNodeDragSession?.({", smart)
        self.assertIn("const dragSession = smartUnifiedRuntimeEnabled", smart)
        self.assertIn("dragSession:detachSession", smart)
        self.assertIn("const pos = sharedPositions?.get(item.id) || {x:item.ox + moveDx, y:item.oy + moveDy};", smart)
        self.assertIn("(e.clientX - dragState.startX) / viewport.scale", smart)

    def test_shared_node_resize_session_projects_proposed_sizes(self):
        runtime = ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(runtime))}, 'utf8'), sandbox);
const shared = sandbox.window.WorkbenchCanvasRuntime;
const session = shared.createNodeResizeSession({{start:{{x:10, y:20}}, scale:2, startWidth:260, startHeight:160}});
const moved = session.move({{x:40, y:50}});
const rescaled = session.move({{x:40, y:50}}, {{scale:4}});
const fallbackSession = shared.createNodeResizeSession({{start:{{x:0, y:0}}, startWidth:100}});
const fallbackMoved = fallbackSession.move({{x:-6, y:3}});
console.log(JSON.stringify({{
  moved, rescaled, fallbackMoved,
  frozen: Object.isFrozen(session) && Object.isFrozen(moved) && Object.isFrozen(rescaled),
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "moved": {"dx": 15, "dy": 15, "width": 275, "height": 175},
            "rescaled": {"dx": 7.5, "dy": 7.5, "width": 267.5, "height": 167.5},
            "fallbackMoved": {"dx": -6, "dy": 3, "width": 94, "height": 3},
            "frozen": True,
        })
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("window.WorkbenchCanvasRuntime?.createNodeResizeSession?.({start:{x:e.clientX, y:e.clientY}, scale:viewport.scale, startWidth:sw, startHeight:sh})", classic)
        self.assertIn("const nextW = Math.max(Math.min(min.w, 220), resize ? resize.width : resizeNode.sw + (e.clientX - resizeNode.sx) / viewport.scale);", classic)
        self.assertIn("(e.clientY - resizeNode.sy) / viewport.scale", classic)
        self.assertIn("window.WorkbenchCanvasRuntime?.createNodeResizeSession?.({start:{x:pointer.clientX, y:pointer.clientY}, scale:viewport.scale, startWidth:rect.width, startHeight:rect.height})", smart)
        self.assertIn("const proposedW = resize ? resize.width : resizeState.startW + dx;", smart)
        self.assertIn("const proposedH = resize ? resize.height : resizeState.startH + dy;", smart)
        self.assertIn("(e.clientY - resizeState.startY) / viewport.scale", smart)
        self.assertNotIn("Math.round(resizeState.startW + dx)", smart)

    def test_canvas_state_swaps_reset_the_unified_runtime(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("function adoptCanvasRuntimeState(nextViewport){", classic)
        self.assertIn("    canvasUnifiedRuntime = null;", classic)
        self.assertEqual(classic.count("adoptCanvasRuntimeState(localViewportForCanvas(canvas.id, canvas.viewport || {x:0, y:0, scale:1}));"), 2)
        self.assertEqual(classic.count("adoptCanvasRuntimeState({x: -1800, y: -1000, scale: 1});"), 2)
        self.assertIn("connections = canvas.connections || [];\n        adoptCanvasRuntimeState(localViewport);", classic)
        self.assertEqual(classic.count("viewport = localViewport;"), 1)
        self.assertIn("function adoptSmartRuntimeState(nextViewport){", smart)
        self.assertIn("    smartUnifiedRuntime = null;", smart)
        self.assertIn("adoptSmartRuntimeState(mergedViewport);", smart)
        self.assertNotIn("viewport = {...viewport, ...(canvas.viewport || {})};", smart)
        self.assertNotIn("viewport.scale = safeScale(viewport.scale);", smart)

    def test_node_creation_client_projects_service_results_without_page_specific_shapes(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchNodeClient;
const nodes = []; const undo = []; const canvas = {{updated_at:2}}; let revision = 0; let selected = '';
const node = api.applyCreationResult({{node:{{id:'created', title:'Created'}}, canvas_revision:7}}, {{
  nodes, undoStack:undo, undoSnapshot:{{before:true}}, undoLimit:1, canvas,
  projectNode:source => ({{id:source.id, title:source.title, compatibility:true}}),
  onRevision:value => revision = value, onSelected:value => selected = value.id,
}});
const graphNodes = [{{id:'existing'}}]; const graphConnections = []; const graphUndo = [];
const graphCanvas = {{updated_at:7}}; let graphSelected = '';
const graphNode = api.applyGraphCreationResult({{
  node:{{id:'connected', title:'Connected'}},
  edge:{{id:'edge', from:{{node_id:'connected'}}, to:{{node_id:'existing'}}}},
  canvas_revision:8,
}}, {{
  nodes:graphNodes, connections:graphConnections, undoStack:graphUndo, undoSnapshot:{{beforeGraph:true}}, undoLimit:1, canvas:graphCanvas,
  projectNode:source => ({{id:source.id, title:source.title, compatibility:true}}),
  projectEdge:edge => ({{id:edge.id, from:edge.from.node_id, to:edge.to.node_id, kind:'input'}}),
  syncTargetInput:true, onSelected:value => graphSelected = value.id,
}});
console.log(JSON.stringify({{node, nodes, undo, revision, selected, canvas, graph:{{graphNode, graphNodes, graphConnections, graphUndo, graphCanvas, graphSelected}}}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "node": {"id": "created", "title": "Created", "compatibility": True},
            "nodes": [{"id": "created", "title": "Created", "compatibility": True}],
            "undo": [{"before": True}], "revision": 7, "selected": "created", "canvas": {"updated_at": 7},
            "graph": {
                "graphNode": {"id": "connected", "title": "Connected", "compatibility": True},
                "graphNodes": [
                    {"id": "existing", "inputNodeIds": ["connected"]},
                    {"id": "connected", "title": "Connected", "compatibility": True},
                ],
                "graphConnections": [{"id": "edge", "from": "connected", "to": "existing", "kind": "input"}],
                "graphUndo": [{"beforeGraph": True}], "graphCanvas": {"updated_at": 8}, "graphSelected": "connected",
            },
        })
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertGreaterEqual(classic.count("WorkbenchNodeClient.applyCreationResult(result"), 5)
        self.assertGreaterEqual(smart.count("WorkbenchNodeClient.applyCreationResult(result"), 5)
        self.assertGreaterEqual(classic.count("WorkbenchNodeClient.applyGraphCreationResult(result"), 2)
        self.assertIn("WorkbenchNodeClient.applyGraphCreationResult(result", smart)

    def test_media_drop_payload_traverses_directory_entries_and_preserves_adapter_filtering(self):
        client = ROOT / "static" / "js" / "workbench" / "canvas" / "media-drop-payload.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchCanvasMediaDrop;
const image = {{name:'image.png', allowed:true}}; const ignored = {{name:'notes.txt', allowed:false}};
const fileEntry = file => ({{isFile:true, file:resolve => resolve(file)}});
const directory = {{
  isDirectory:true,
  createReader:() => {{ let pass = 0; return {{readEntries:resolve => resolve(pass++ ? [] : [fileEntry(image), fileEntry(ignored)])}}; }},
}};
(async () => {{
  const fromDirectory = await api.filesFromDataTransfer({{items:[{{webkitGetAsEntry:() => directory}}]}}, file => file.allowed);
  const fromFiles = await api.filesFromDataTransfer({{files:[image, ignored]}}, file => file.allowed);
  const textPayload = await api.resolvePayload({{
    files:[], types:['text/plain'], getData:() => '/tmp/input.png\\nhttps://example.test/remote.png',
  }}, {{
    textTypes:['text/plain'], isSupportedFile:file => file.allowed,
    isLocalValue:value => value.startsWith('/tmp/'), isRemoteValue:value => value.startsWith('https://'),
  }});
  class FakeFormData {{ constructor() {{ this.parts = []; }} append(field, file, name) {{ this.parts.push({{field, file:file.name, name:name || null}}); }} }}
  sandbox.window.FormData = FakeFormData;
  sandbox.window.fetch = async () => ({{ok:true, status:200, json:async () => ({{files:[{{url:'/output/image.png'}}]}})}});
  const uploaded = await api.uploadFiles([image], {{fileName:file => `stored-${{file.name}}`}});
  console.log(JSON.stringify({{fromDirectory:fromDirectory.map(file => file.name), fromFiles:fromFiles.map(file => file.name), textPayload, uploaded}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {
            "fromDirectory": ["image.png"], "fromFiles": ["image.png"],
            "textPayload": {"type": "localPaths", "localPaths": ["/tmp/input.png"]},
            "uploaded": [{"url": "/output/image.png"}],
        })
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchCanvasMediaDrop.filesFromDataTransfer(dataTransfer, isSupportedUploadFile)", classic)
        self.assertIn("WorkbenchCanvasMediaDrop.filesFromDataTransfer(dataTransfer, isSupportedUploadFile)", smart)
        self.assertIn("WorkbenchCanvasMediaDrop.resolvePayload(dataTransfer", classic)
        self.assertIn("WorkbenchCanvasMediaDrop.resolvePayload(dataTransfer", smart)
        self.assertIn("WorkbenchCanvasMediaDrop.uploadFiles(supported)", classic)
        self.assertIn("WorkbenchCanvasMediaDrop.uploadFiles(supported", smart)

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

    def test_smart_canvas_cache_busts_current_node_shell_assets(self):
        page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        self.assertIn("smart-canvas.css?v=2026.09.04.2", page)
        self.assertIn("node-shell.js?v=2026.09.04.2", page)
        self.assertIn("records.js?v=2026.08.28.1788439786", page)
        self.assertIn("node-inspector.js?v=2026.08.28.1788441997", page)
        self.assertIn("legacy-renderer.js?v=2026.08.28.1788438695", page)
        self.assertIn("media-renderer.js?v=2026.08.28.1788438695", page)
        self.assertIn("semantic-zoom.js?v=2026.08.28.1788370356", page)
        self.assertIn("command-registry.js?v=2026.09.06.6", page)
        self.assertIn("creation-catalog.js?v=2026.09.04.1", page)
        self.assertIn("generation-intent.js?v=2026.09.04.1", page)
        self.assertIn("smart-canvas.js?v=2026.09.06.15", page)

    def test_smart_node_inspector_sections_are_ephemeral_and_collapsible(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        self.assertIn("const smartNodeInspectorCollapsedSections = new Map();", smart)
        self.assertIn("sectionId !== 'identity'", smart)
        self.assertIn("label.setAttribute('aria-expanded'", smart)
        self.assertIn("label.setAttribute('aria-controls'", smart)
        self.assertIn("smartNodeInspector?.addEventListener('keydown'", smart)
        self.assertIn("target?.closest?.('#smartNodeInspector')", smart)
        self.assertIn("if(event.key === 'Tab' && !event.shiftKey && !insideInspector", smart)
        self.assertIn("firstToggle.focus();", smart)
        self.assertIn("smartNodeInspectorTabEntryNodeId = '';", smart)
        self.assertIn("function toggleSmartNodeInspectorSection(nodeId, sectionId, options={})", smart)
        self.assertIn("toggleSmartNodeInspectorSection(toggle.dataset.inspectorNodeId", smart)
        self.assertIn("restoredToggle?.focus({preventScroll:true});", smart)
        self.assertIn("function smartNodeInspectorSelectionIdentity()", smart)
        self.assertIn("inspector.selectionViewModel(records)", smart)
        self.assertIn("function applySmartNodeSelection(nodeId, options={})", smart)
        self.assertIn("smartSelectionToggleRequested(e)", smart)
        smart_event_bindings = smart[smart.index("function bindNodeEvents()") :]
        smart_media_selection = smart_event_bindings[smart_event_bindings.index("el.querySelectorAll('.thumb-item,.image-wrap')") : smart_event_bindings.index("el.querySelectorAll('.thumb-item,.smart-group-single-thumb')")]
        self.assertGreaterEqual(smart_media_selection.count("applySmartNodeSelection(id);"), 4)
        self.assertNotIn("selectedId = id;", smart_media_selection)
        smart_upload_target = smart_event_bindings[smart_event_bindings.index("nodeDrop?.addEventListener('click'") : smart_event_bindings.index("el.querySelectorAll('.node-delete')")]
        self.assertIn("applySmartNodeSelection(id);", smart_upload_target)
        self.assertNotIn("selectedId = id;", smart_upload_target)
        smart_group_menu_selection = smart[smart.index("shell.oncontextmenu = e =>") : smart.index("shell.ondblclick = e =>")]
        self.assertIn("applySmartNodeSelection(groupEl.dataset.id);", smart_group_menu_selection)
        self.assertNotIn("selectedId = groupEl.dataset.id;", smart_group_menu_selection)
        self.assertIn("const CANVAS_SCALE_MIN = 0.06;", smart)
        self.assertIn("const CANVAS_SCALE_MAX = 3;", smart)
        self.assertIn("const CANVAS_WHEEL_DELTA_LIMIT = 240;", smart)
        self.assertIn("const nextScale = sharedNextScale || safeScale(viewport.scale * factor);", smart)
        self.assertIn("viewportScaleForWheel?.(viewport, e.deltaY", smart)
        self.assertIn("applyCanvasRuntimeViewport({type:window.WorkbenchCanvasRuntime.COMMANDS.VIEWPORT_SET, viewport:fitted})", classic)
        self.assertIn("applySmartRuntimeViewport({type:window.WorkbenchCanvasRuntime.COMMANDS.VIEWPORT_SET, viewport:fitted})", smart)
        self.assertIn("function recoverSmartViewportIfCorrupt()", smart)
        self.assertIn("function restoreSmartViewportToVisibleNodes()", smart)
        self.assertIn("if(key === 'f'){", smart)
        self.assertIn("nodeCommand('canvas.node.inspect', 'smart')", smart)
        self.assertIn("function focusSmartNodeInspector(nodeId)", smart)
        self.assertIn(".workbench-node-shell__menu::before { content:'⋯';", styles)
        self.assertIn("padding:0 84px 0 18px", styles)
        self.assertIn("right:16px; min-height:64px", styles)
        self.assertIn("workbench-node-shell__actions", styles)
        self.assertIn("workbench-node-shell__delete::before", styles)
        self.assertIn("right:10px; min-height:32px", styles)
        self.assertIn("WorkbenchUnifiedRenderHost.cardShellView({selected:isNodeSelected(node.id), onIntent:handleSmartNodeShellIntent})", smart)
        self.assertIn("const smartNodeShellIntentAdapter = window.WorkbenchUnifiedRenderHost.createIntentAdapter({", smart)
        self.assertIn("delete:intent => deleteNodeFromButton(intent.nodeId)", smart)
        self.assertIn("function ordinarySmartViewportNodes()", smart)
        self.assertIn("if(recoveredSpatialViewport) toast('检测到异常视口，已恢复到可见节点');", smart)
        self.assertIn("event.stopImmediatePropagation();", smart)
        self.assertIn("}, true);", smart)
        self.assertIn("fields.hidden = collapsed", smart)
        self.assertIn("smart-node-inspector__toggle", styles)
        self.assertIn("smart-node-inspector__toggle:focus-visible", styles)
        self.assertIn("smart-node-inspector__section.is-collapsed", styles)

    def test_smart_canvas_context_menu_matches_the_classic_single_column_treatment(self):
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("width:190px", styles)
        self.assertIn("border-radius:18px", styles)
        self.assertIn(".create-menu-grid { display:flex; flex-direction:column; gap:0; }", styles)
        self.assertIn("min-height:38px", styles)
        self.assertIn(".create-card-sub { display:none; }", styles)
        self.assertIn("const w = 190;", smart)
        self.assertIn("const h = 206;", smart)

    def test_common_create_and_group_intents_use_the_shared_command_catalog(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        registry = (ROOT / "static" / "js" / "workbench" / "canvas" / "command-registry.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchCanvasCommands", registry)
        self.assertIn("canvas.create.group", registry)
        self.assertIn("canvas.selection.group", registry)
        self.assertIn("canvas.graph.connect", registry)
        self.assertIn("canvas.graph.create-connected", registry)
        self.assertIn("canvas.group.add-member", registry)
        self.assertIn("creationCatalogFor", registry)
        self.assertIn("usesVersionedBlankCreation", registry)
        self.assertIn("usesVersionedConnectedCreation", registry)
        self.assertIn("orderCreateMenuItems", registry)
        self.assertIn("WorkbenchCanvasCommands?.createCommand(type, 'classic')", classic)
        self.assertIn("WorkbenchCanvasCommands?.createCommand(type, 'smart')", smart)
        self.assertIn("canvas.selection.group', 'classic'", classic)
        self.assertIn("canvas.selection.group', 'smart'", smart)
        self.assertIn("syncClassicCreateMenuCommands", classic)
        self.assertIn("syncSmartCreateMenuCommands", smart)
        self.assertIn("creationCatalogFor('classic')", classic)
        self.assertIn("creationCatalogFor('smart')", smart)
        self.assertIn("const classicVersionedBlankNodeCreators = Object.freeze({", classic)
        self.assertIn("output: addVersionedBlankOutputNode", classic)
        self.assertIn("definition_ref:{type:'legacy', id:'output', version:'0'}", classic)
        self.assertIn("function createClassicMenuNode(command, point){", classic)
        self.assertIn("usesVersionedBlankCreation(command, 'classic')", classic)
        self.assertIn("const classicVersionedConnectedNodeCreators = Object.freeze({", classic)
        self.assertIn("image: createVersionedLinkedImage", classic)
        self.assertIn("prompt: createVersionedLinkedPrompt", classic)
        self.assertIn("loop: createVersionedLinkedLoop", classic)
        self.assertIn("usesVersionedConnectedCreation(command, 'classic')", classic)
        self.assertIn("function quickAdd(type){", classic)
        self.assertIn("return createClassicMenuNode(command, point);", classic)

        self.assertIn("const smartVersionedBlankNodeCreators = Object.freeze({", smart)
        self.assertIn("minimax: point => createVersionedBlankSmartMinimax(point)", smart)
        self.assertIn("definition_ref:{type:'legacy', id:'smart-minimax', version:'0'}", smart)
        self.assertIn("function createVersionedSmartTopLevelMenuNode(command, point){", smart)
        self.assertIn("usesVersionedBlankCreation(command, 'smart')", smart)
        self.assertIn("WorkbenchGenerationIntent?.planResultTarget({", smart)
        self.assertIn("const smartVersionedConnectedNodeCreators = Object.freeze({", smart)
        self.assertIn("usesVersionedConnectedCreation(command, 'smart')", smart)
        self.assertIn("graphCommand('canvas.graph.connect', 'classic')", classic)
        self.assertIn("graphCommand('canvas.graph.connect', 'smart')", smart)
        self.assertIn("graphCommand('canvas.graph.create-connected', 'smart')", smart)
        self.assertIn("graphCommand('canvas.group.add-member', 'classic')", classic)
        self.assertIn("graphCommand('canvas.group.add-member', 'smart')", smart)
        self.assertIn("openSmartPortCreateMenu(drag, e)", smart)
        self.assertIn("createSmartConnectedNodeFromMenu(command, portCreate)", smart)
        self.assertIn("group: createVersionedConnectedSmartGroup", smart)
        self.assertIn("prompt: createVersionedConnectedSmartPrompt", smart)
        self.assertIn("loop: createVersionedConnectedSmartLoop", smart)
        self.assertIn("image: createVersionedConnectedSmartImage", smart)
        self.assertIn("minimax: createVersionedConnectedSmartMinimax", smart)
        self.assertIn("applyVersionedSmartConnectedNode", smart)
        self.assertIn("WorkbenchNodeClient.createNodeAndEdge", smart)
        connected_apply = smart[smart.index("function applyVersionedSmartConnectedNode"):smart.index("async function createVersionedConnectedSmartPrompt")]
        client = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchNodeClient.applyGraphCreationResult", connected_apply)
        self.assertIn("syncTargetInput:true", connected_apply)
        self.assertIn("target.inputNodeIds = Array.from", client)
        self.assertNotIn("scheduleSave();", connected_apply)
        self.assertIn("connectInputNode(fromId, toId)", smart)

    def test_classic_connected_blank_image_uses_the_versioned_graph_mutation_route(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        create_block = classic[classic.index("async function createVersionedLinkedImage"):classic.index("function createNodeByType")]
        self.assertIn("definition_ref:{type:'legacy', id:'image', version:'0'}", create_block)
        self.assertIn("await window.WorkbenchNodeClient.createNodeAndEdge(canvas.id", create_block)
        self.assertIn("type:'image'", create_block)
        self.assertIn("mediaKind:'image'", create_block)
        self.assertNotIn("scheduleSave();", create_block)

    def test_classic_connected_blank_prompt_and_loop_use_the_versioned_graph_mutation_route(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
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

    def test_smart_port_hover_uses_the_shared_data_type_compatibility_contract(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        on_mouse_move = smart.index("window.onmousemove = e =>")
        hover = smart[smart.index("if(portDragState){", on_mouse_move) : smart.index("if(promptResizeState){", on_mouse_move)]
        self.assertIn("const hoverIntent = window.WorkbenchCanvasGraphInteraction?.edgeIntentFromPortDrop(", hover)
        self.assertIn("WorkbenchCanvasPortCompatibility.isCompatible(", hover)
        self.assertIn("fromNode?.output_port_type || fromNode?.port_type || 'legacy.any'", hover)
        self.assertIn("toNode?.input_port_type || toNode?.port_type || 'legacy.any'", hover)

    def test_classic_and_smart_generation_entries_delegate_to_compatibility_execution(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        classic_entry = classic[classic.index("async function runCanvasGenerate(nodeId){") : classic.index("function computeCascadeOrder", classic.index("async function runCanvasGenerate(nodeId){"))]
        smart_entry = smart[smart.index("async function runGeneration(){") : smart.index("async function runPromptLLMNode", smart.index("async function runGeneration(){"))]
        self.assertIn("WorkbenchCanvasExecutionCompatibility?.run({", classic_entry)
        self.assertIn("canvasKind:'classic', sourceNodeId:nodeId", classic_entry)
        self.assertIn("execute:() => runCanvasGenerateLegacy(nodeId)", classic_entry)
        self.assertIn("?? runCanvasGenerateLegacy(nodeId)", classic_entry)
        self.assertIn("WorkbenchCanvasExecutionCompatibility?.run({", smart_entry)
        self.assertIn("canvasKind:'smart', sourceNodeId:node.id", smart_entry)
        self.assertIn("execute:() => runGenerationLegacy()", smart_entry)
        self.assertIn("?? runGenerationLegacy()", smart_entry)

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

    def test_top_level_blank_image_menus_use_versioned_client_only_on_loopback(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        client = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js").read_text(encoding="utf-8")
        self.assertIn("addVersionedBlankImageNode", classic)
        self.assertIn("canUseVersionedImageCreation()", classic)
        self.assertIn("createVersionedBlankSmartImageAt", smart)
        self.assertIn("canUseVersionedSmartImageCreation()", smart)
        self.assertIn("isLoopback", client)
        self.assertIn("isEnabled", client)
        self.assertIn("versioned_nodes", client)
        self.assertIn("undoStack.push(undoSnapshot)", classic)
        self.assertIn("undoStack.push(undoSnapshot)", smart)
        self.assertIn("addVersionedBlankPromptNode", classic)
        self.assertIn("createVersionedLinkedGroup", classic)
        self.assertIn("createNodeAndEdge", client)
        self.assertIn("createVersionedBlankSmartPrompt", smart)
        self.assertIn("createVersionedBlankSmartLoop", smart)
        self.assertIn("createVersionedBlankSmartGroup", smart)
        self.assertIn("function createVersionedSmartTopLevelMenuNode(command, point){", smart)
        self.assertIn("if(!groupId && createVersionedSmartTopLevelMenuNode(command, p))", smart)
        self.assertIn("const shouldCreateBranchOutput = resultTarget?.disposition === 'branch';", smart)
        self.assertIn("quickAdd('image')", (ROOT / "static" / "canvas.html").read_text(encoding="utf-8"))
        toolbar = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8").split('<div class="toolbar-items">', 1)[1].split('</div>', 1)[0]
        for create_type in ("llm", "generator", "msgen", "video", "minimax", "rh", "comfy", "ltxDirector", "output"):
            self.assertIn(f"quickAdd('{create_type}')", toolbar)
        self.assertNotIn("onclick=\"addLLMNode()\"", toolbar)
        self.assertIn("function quickAdd(type)", classic)

    def test_completed_box_selection_commits_through_the_shared_runtime_on_both_adapters(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        classic_finish = classic[classic.index("function finishSelection(){"):classic.index("function renderSelectionHub(){")]
        smart_finish = smart[smart.index("function finishSelection(event){"):smart.index("function groupSelectedNodes(){")]
        self.assertIn("const selectedIds = []", classic_finish)
        self.assertIn("if(!applyCanvasRuntimeSelection(selectedIds)) selected = new Set(selectedIds);", classic_finish)
        self.assertIn("const nextSelectedIds = nodes.filter", smart_finish)
        self.assertIn("if(!applySmartRuntimeSelection(nextSelectedIds))", smart_finish)

    def test_classic_standalone_blank_image_delete_uses_the_versioned_mutation_route(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        delete_block = classic[classic.index("function canUseVersionedBlankImageDelete(node)"):classic.index("function deleteConnection(id, event){")]
        self.assertIn("node.type !== 'image' || node.url", delete_block)
        self.assertIn("Array.isArray(candidate.items) && candidate.items.includes(node.id)", delete_block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", delete_block)
        self.assertIn("expected_revision:Number(lastCanvasUpdatedAt || canvas.updated_at || 0)", delete_block)
        self.assertIn("if(await deleteVersionedBlankImageNode(id)) return;", delete_block)
        self.assertNotIn("scheduleSave();", delete_block)

    def test_classic_standalone_blank_image_move_uses_versioned_position_mutation(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        block = classic[classic.index("function canUseVersionedBlankPromptDelete(node)"):classic.index("async function deleteNodeFromButton")]
        self.assertIn("node.type !== 'prompt' || String(node.text || '').trim()", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedBlankImagePosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankPromptPosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankLoopPosition(drag)) return true;", block)

    def test_classic_standalone_default_loop_uses_the_versioned_mutation_route(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        block = classic[classic.index("function canUseVersionedBlankLoopDelete(node)"):classic.index("async function deleteNodeFromButton")]
        self.assertIn("Number(node.count || 3) !== 3", block)
        self.assertIn("node.mode === 'parallel' || node.showPrompt || node.imageInput || node.videoInput", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedBlankLoopPosition(drag)) return true;", block)
        self.assertIn("if(await commitVersionedBlankOutputPosition(drag)) return true;", block)

    def test_classic_standalone_empty_output_uses_the_versioned_mutation_route(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        block = classic[classic.index("function canUseVersionedEmptyGroupDelete(node)"):classic.index("function deleteConnection(id, event){")]
        self.assertIn("node.type !== 'group' || (node.items || []).length", block)
        self.assertIn("connections.some(connection => connection.from === node.id || connection.to === node.id)", block)
        self.assertIn("Array.isArray(candidate.items) && candidate.items.includes(node.id)", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("return commitVersionedEmptyGroupPosition(drag);", block)
        self.assertIn("if(await deleteVersionedEmptyGroupNode(id)) return;", block)

    def test_smart_standalone_blank_image_delete_uses_the_versioned_mutation_route(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        delete_block = smart[smart.index("function canUseVersionedBlankSmartImageDelete(node)"):smart.index("function disconnectConnection(index){")]
        self.assertIn("node?.type !== 'smart-image'", delete_block)
        self.assertIn("node.pending || node.queued || node.jimengPending || node.running", delete_block)
        self.assertIn("smartGroupContainingNode(node.id)", delete_block)
        self.assertIn("candidate.historyFor === node.id", delete_block)
        self.assertIn("candidate?.inputNodeIds", delete_block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", delete_block)
        self.assertIn("expected_revision:Number(canvas.updated_at || 0)", delete_block)
        self.assertIn("if(await deleteVersionedBlankSmartImageNode(id)) return;", delete_block)
        self.assertNotIn("scheduleSave();", delete_block)

    def test_smart_standalone_blank_image_move_uses_the_versioned_mutation_route(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        move_block = smart[smart.index("async function commitVersionedBlankSmartImagePosition(drag)"):smart.index("async function deleteVersionedBlankSmartImageNode(id)")]
        mouseup = smart[smart.index("window.onmouseup = e => {"):smart.index("shell.addEventListener('wheel'")]
        self.assertIn("drag?.isLocalCopy || drag?.ctrlGroup || drag?.thumbDetached", move_block)
        self.assertIn("(drag?.group || []).length !== 1", move_block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", move_block)
        self.assertIn("position:{x:Number(node.x) || 0, y:Number(node.y) || 0}", move_block)
        self.assertIn("node.x = drag.ox;", move_block)
        self.assertIn("node.y = drag.oy;", move_block)
        self.assertIn("isLocalCopy:Boolean(pointer.altKey)", smart)
        self.assertIn("void commitVersionedSmartPosition(versionedPositionCommit)", mouseup)
        self.assertIn("if(!handled) scheduleSave();", mouseup)

    def test_smart_standalone_empty_group_uses_the_versioned_mutation_route(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        block = smart[smart.index("function canUseVersionedEmptySmartGroupDelete(node)"):smart.index("function disconnectConnection(index){")]
        self.assertIn("(node.items || []).length || (node.images || []).length || (node.inputNodeIds || []).length", block)
        self.assertIn("(canvas?.connections || []).some", block)
        self.assertIn("return !smartGroupContainingNode(node.id);", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("void commitVersionedSmartPosition(versionedPositionCommit)", smart)
        self.assertIn("if(await deleteVersionedEmptySmartGroupNode(id)) return;", block)

    def test_smart_standalone_default_loop_uses_the_versioned_mutation_route(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        block = smart[smart.index("function canUseVersionedDefaultSmartLoopDelete(node)"):smart.index("function disconnectConnection(index){")]
        self.assertIn("Number(node.count || 1) !== 1 || node.mode === 'parallel'", block)
        self.assertIn("String(node.variablePrompt || '').trim()", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("if(await commitVersionedDefaultSmartLoopPosition(drag)) return true;", block)
        self.assertIn("if(await deleteVersionedDefaultSmartLoopNode(id)) return;", block)

    def test_smart_standalone_blank_prompt_uses_the_versioned_mutation_route(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        block = smart[smart.index("function canUseVersionedBlankSmartPromptDelete(node)"):smart.index("function disconnectConnection(index){")]
        self.assertIn("node?.type !== 'smart-prompt'", block)
        self.assertIn("String(node.text || '').trim() || String(node.promptResult || '').trim()", block)
        self.assertIn("node.llmEnabled || node.llmSystemEnabled", block)
        self.assertIn("(node.promptAttachments || []).length || (node.inputNodeIds || []).length", block)
        self.assertIn("(canvas?.connections || []).some", block)
        self.assertIn("return !smartGroupContainingNode(node.id);", block)
        self.assertIn("await window.WorkbenchNodeClient.update(canvas.id, node.id", block)
        self.assertIn("await window.WorkbenchNodeClient.remove(canvas.id, node.id", block)
        self.assertIn("return commitVersionedBlankSmartPromptPosition(drag);", block)
        self.assertIn("if(await deleteVersionedBlankSmartPromptNode(id)) return;", block)

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

    def test_legacy_video_overlays_follow_the_real_playback_state(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        controls = (ROOT / "static" / "js" / "workbench" / "canvas" / "media-preview-controls.js").read_text(encoding="utf-8")
        self.assertIn("function bindSmartVideoOverlay(video)", smart)
        self.assertIn("WorkbenchCanvasMediaPreviewControls.bindVideoOverlay", smart)
        self.assertIn("function bindCanvasVideoOverlay(video)", classic)
        self.assertIn("WorkbenchCanvasMediaPreviewControls.bindVideoOverlay", classic)
        self.assertIn("['play', 'playing', 'pause', 'ended']", controls)
        self.assertIn("['pointerdown', 'pointerup', 'mousedown', 'mouseup', 'click', 'dblclick', 'contextmenu', 'wheel']", controls)

    def test_semantic_zoom_application_is_shared_and_screen_space_controls_stay_smart_local(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        apply_owner = (ROOT / "static" / "js" / "workbench" / "canvas" / "semantic-zoom-apply.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        policy = (ROOT / "static" / "js" / "workbench" / "canvas" / "semantic-zoom.js").read_text(encoding="utf-8")
        self.assertIn("function nodeShellSemanticZoomEnabled()", smart)
        self.assertIn("params.get('semantic_zoom') !== '0'", smart)
        self.assertIn("params.get('node_shell') !== '0'", smart)
        self.assertIn("WorkbenchSemanticZoom.viewModel(node, viewport.scale)", smart)
        self.assertIn("applyNodeShellSemanticZoom();", smart)
        self.assertIn("semanticZoomIndicator", smart)
        self.assertIn("count: shells.length", smart)
        self.assertIn("WorkbenchSemanticZoomApply.ensureIndicator", smart)
        self.assertIn("WorkbenchSemanticZoomApply.applyShellPresentation", smart)
        self.assertIn("WorkbenchSemanticZoomApply.resetShellPresentation", smart)
        self.assertIn("WorkbenchSemanticZoomApply.applyLegacyPresentation", smart)
        self.assertIn("WorkbenchSemanticZoomApply.resetLegacyPresentation", smart)
        self.assertIn("function applyLegacySmartSemanticZoom(enabled)", smart)
        self.assertIn(".image-node:not(.node-shell-mounted)", smart)
        self.assertIn("smartActions:nodeEl.querySelector(':scope > .smart-node-floating-menu')", smart)
        self.assertIn("shellEl.closest('.image-node')?.querySelectorAll(':scope > .smart-node-floating-menu, :scope > .floating-node-actions')", smart)
        self.assertIn("dataset.semanticPresentation = model.presentation", apply_owner)
        self.assertIn("Math.round(Number(settings.scale) * 100)", apply_owner)
        self.assertIn("setVisible(slots.status, model.showSummary, 'inline')", apply_owner)
        self.assertIn("setVisible(slots.content, model.showContent)", apply_owner)
        self.assertIn("Object.freeze(['full', 'summary'])", policy)
        self.assertIn("scale >= 0.75 ? 'full' : 'summary'", policy)
        self.assertIn('width:190px', styles)
        self.assertIn(".node-shell-semantic-zoom", styles)
        self.assertIn(".semantic-zoom-indicator", styles)
        self.assertNotIn("data-semantic-presentation=\"icon\"", styles)
        self.assertIn("function nodeShellScreenSpaceControlsEnabled()", smart)
        self.assertIn("params.get('screen_space_controls') !== '0'", smart)
        self.assertIn("WorkbenchScreenSpaceControls.controlViewModel", smart)
        self.assertIn("--screen-space-port-size", styles)
        self.assertIn("--screen-space-toolbar-scale", styles)

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

        for page, editor in (("canvas.html", "canvas.js"), ("smart-canvas.html", "smart-canvas.js")):
            text = (ROOT / "static" / page).read_text(encoding="utf-8")
            apply_tag = text.index("workbench/canvas/semantic-zoom-apply.js")
            self.assertLess(text.index("workbench/canvas/semantic-zoom.js"), apply_tag)
            self.assertLess(apply_tag, text.index(editor))


    def test_node_shell_mount_is_explicit_and_supports_smart_groups(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("node_shell", smart)
        self.assertIn("canUseNodeShellForSmartGroup", smart)
        self.assertNotIn("!smartGroupMembers(node).length", smart)
        self.assertIn("mountNodeShellForSmartGroups();", smart)
        self.assertIn("handleSmartNodeShellIntent", smart)

    def test_legacy_renderer_has_an_opt_in_non_media_smart_canvas_adapter(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        self.assertIn("function canUseNodeShellForSmartLegacy(node)", smart)
        self.assertIn("params.get('legacy_renderer') !== '0'", smart)
        self.assertIn("function mountNodeShellForSmartLegacyNodes()", smart)
        self.assertIn("mountNodeShellForSmartLegacyNodes();", smart)
        self.assertIn("preserveLegacyContent:true", smart)
        self.assertIn("function adoptLegacyContent(settings)", (ROOT / "static" / "js" / "workbench" / "canvas" / "unified-render-host.js").read_text(encoding="utf-8"))
        admission = (ROOT / "static" / "js" / "workbench" / "canvas" / "renderer-admission.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", smart)
        self.assertIn("accepts:candidate => !isSmartImageNode(candidate) && !isSmartGroupNode(candidate) && candidate.type !== 'group'", smart)
        self.assertIn("function admits(policy, node)", admission)
        self.assertIn("renderer-admission.js?v=2026.09.06.1", page)
        self.assertIn(".image-node.legacy-renderer-mounted > .floating-node-actions", styles)
        self.assertIn("smart-canvas.js?v=2026.09.06.15", page)

    def test_classic_output_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}", classic)
        self.assertIn("if(node?.type === 'output') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.output-node .canvas-node-shell-legacy-content", styles)
        self.assertIn("overflow:auto", styles)

    def test_classic_legacy_renderer_gate_covers_all_migrated_families_and_port_contracts(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        migrated = [
            "prompt", "loop", "output", "llm", "generator", "midjourney",
            "msgen", "video", "comfy", "rh", "ltxDirector", "minimax", "promptGroup",
        ]
        self.assertIn("params.get('node_shell') !== '0'", classic)
        self.assertIn("params.get('legacy_renderer') !== '0'", classic)
        self.assertIn("window.WorkbenchNodeClient?.isLoopback?.()", classic)
        self.assertIn("WorkbenchRendererAdmission?.admits({enabled:canvasLegacyRendererEnabled(), types:['prompt', 'loop', 'output', 'llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax', 'promptGroup']}", classic)
        self.assertIn("if(node?.type === 'prompt') return {input:false, output:true};", classic)
        self.assertIn("if(node?.type === 'promptGroup') return {input:false, output:true};", classic)
        for node_type in [node for node in migrated if node not in {"prompt", "promptGroup"}]:
            self.assertIn(f"if(node?.type === '{node_type}') return {{input:true, output:true}};", classic)

    def test_classic_llm_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'llm') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.llm-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.llm-node .llm-body", styles)

    def test_classic_generator_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'generator') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.generator-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.generator-node .generator-body", styles)

    def test_classic_midjourney_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'midjourney') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.midjourney-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.midjourney-node .generator-body", styles)

    def test_classic_modelscope_generation_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'msgen') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.msgen-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.msgen-node .generator-body", styles)

    def test_classic_video_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'video') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.video-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.video-node .generator-body", styles)

    def test_classic_comfy_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'comfy') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.comfy-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.comfy-node .comfy-body", styles)

    def test_classic_runninghub_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'rh') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.rh-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.rh-node .rh-body", styles)

    def test_classic_ltx_director_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'ltxDirector') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.ltxDirector-node .canvas-node-shell-legacy-content", styles)
        self.assertIn(".node.node-shell-mounted.ltxDirector-node .ltx-director-body", styles)

    def test_classic_minimax_node_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'minimax') return {input:true, output:true};", classic)
        self.assertIn(".node.node-shell-mounted.minimax-node .workbench-legacy-renderer", styles)
        self.assertIn(".node.node-shell-mounted.minimax-node .minimax-canvas-workbench", styles)

    def test_classic_prompt_group_can_use_the_opt_in_shared_legacy_renderer(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchRendererAdmission?.admits", classic)
        self.assertIn("if(node?.type === 'promptGroup') return {input:false, output:true};", classic)
        self.assertIn("if(node.type === 'promptGroup') {", classic)
        self.assertIn("${promptNodes.length} ${tr('canvas.promptCount')} ${tr('canvas.grouped')}", classic)

    def test_prompt_node_uses_the_compact_llm_card_hierarchy(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        self.assertIn('class="prompt-node-studio-head"', smart)
        self.assertIn('class="prompt-node-models"', smart)
        self.assertIn('class="prompt-node-tools prompt-node-footer ${node.promptSkillEnabled', smart)
        self.assertIn('class="prompt-node-run prompt-node-control"', smart)
        self.assertIn(".prompt-node-studio-head", styles)
        self.assertIn(".prompt-node-models", styles)
        self.assertIn(".prompt-node-footer", styles)
        self.assertIn('promptSkillPack', smart)
        self.assertIn('promptSkillDefinition', smart)
        self.assertIn('function openPromptNodeUpload(nodeId)', smart)
        self.assertIn('function attachFilesToPromptNode(files, nodeId)', smart)
        self.assertIn('function promptNodeSkillSystemPrompt(node)', smart)
        self.assertIn('const PROMPT_SKILL_VISUAL_CATALOG', smart)
        self.assertIn('function promptSkillVisual(pack, definition)', smart)
        self.assertIn('聘才猫简历优化', smart)
        self.assertIn('Pincaimiao Skills', smart)
        self.assertIn('node.title = visual.definition;', smart)
        self.assertIn('function promptNodeContextChipsHtml(node, upstreamItems=[])', smart)
        self.assertIn('class="prompt-node-context-row"', smart)
        self.assertIn('data-lucide="brain"', smart)
        self.assertIn("node.title = node.promptSkillEnabled ? promptSkillVisual", smart)
        self.assertIn('.prompt-node-footer .prompt-skill-toggle:not(.active)', styles)
        self.assertIn('.image-node.prompt-smart-node.node-shell-mounted .workbench-node-shell__header', styles)
        self.assertIn('.image-node.prompt-smart-node.node-shell-mounted .workbench-node-shell__footer', styles)
        self.assertIn('.image-node.prompt-smart-node.node-shell-mounted .workbench-node-shell__resize', styles)
        self.assertIn('container-name:prompt-card; overflow:visible; border:1px solid #e8edf3; border-radius:18px; background:rgba(255,255,255,.96)', styles)
        self.assertIn('box-sizing:border-box; gap:0; padding:0; overflow:hidden; border:0; border-radius:inherit; background:transparent; box-shadow:none;', styles)
        self.assertIn('margin:0 18px 18px; padding-right:32px;', styles)
        self.assertIn('@container prompt-card (max-width: 420px)', styles)
        self.assertIn('.image-node.prompt-smart-node.node-shell-mounted .workbench-node-shell__port--input', styles)
        self.assertIn('.image-node.prompt-smart-node.node-shell-mounted .workbench-node-shell__port--output', styles)
        self.assertIn('visibility\n   still follows the shared selected/hover/connection interaction contract', styles)
        self.assertIn('ensureSmartRenderRuntime().mountAll(entries);', smart)
        self.assertIn('card:el, contentHost,', smart)
        self.assertIn('function nodeShellPortElements(shellEl)', smart)
        self.assertIn('w:340, h:286', smart)
        self.assertIn('function promptNodeOutputItems(node)', smart)
        self.assertIn('node.promptResult = (result.text || \'\').trim();', smart)
        self.assertIn('node.promptResultOutdated = false;', smart)
        self.assertIn("node?.promptResultOutdated === true", smart)
        self.assertIn('prompt-node-result ${node.promptResultOutdated', smart)
        self.assertIn("node?.promptOutputMode === 'list'", smart)
        self.assertIn('system_prompt:systemPrompt', smart)
        self.assertIn('function smartMinimaxUpstreamScript(node)', smart)
        self.assertIn('function smartMinimaxApplyUpstreamScript(node)', smart)
        self.assertIn('class="minimax-upstream-script"', smart)
        self.assertIn('未填写片段 Prompt 时将用于生成', smart)
        self.assertIn('data-minimax-apply-upstream="1"', smart)
        self.assertIn("if(node?.type === 'smart-prompt'){", smart)
        self.assertIn('return promptNodeInputMediaForLLM(node)', smart)
        self.assertIn("selectSmartNodeFromShell", smart)
        self.assertIn("startSmartPortDrag", smart)
        self.assertIn("startSmartNodeDrag", smart)
        self.assertIn("startSmartNodeResize", smart)

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

    def test_node_shell_mount_removes_legacy_controls_owned_by_the_shell(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("controlSettings:{selectors:SMART_NODE_SHELL_LEGACY_CONTROLS}", smart)
        self.assertIn("removeControlsBeforeMount:true", smart)

    def test_node_shell_ports_override_legacy_port_geometry(self):
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        self.assertIn(".image-node.node-shell-mounted .workbench-node-shell__port", styles)
        self.assertIn(".image-node.node-shell-mounted.selected > .workbench-node-shell__port", styles)
        self.assertIn(".image-node.node-shell-mounted.port-dragging > .workbench-node-shell__port", styles)
        self.assertIn(".workbench-node-shell__port--input { left:-8px; right:auto; }", styles)
        self.assertIn(".workbench-node-shell__port--output { right:-8px; left:auto; }", styles)
        self.assertIn(".shell.port-dragging .workbench-node-shell__port", styles)
        self.assertIn(".image-node.node-shell-mounted.dragging .workbench-node-shell__port", styles)

    def test_smart_group_node_shell_uses_classic_group_card_treatment(self):
        styles = (ROOT / "static" / "css" / "smart-canvas.css").read_text(encoding="utf-8")
        self.assertIn("Smart Group NodeShell adopts the established Classic Canvas group card", styles)
        self.assertIn(".image-node.smart-group-node.node-shell-mounted .workbench-node-shell__header", styles)
        self.assertIn("min-height:66px", styles)
        self.assertIn(".workbench-node-shell__menu::before { content:'⋯'", styles)

    def test_smart_canvas_accepts_both_legacy_and_node_shell_ports(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn(".node-port, .workbench-node-shell__port", smart)
        self.assertIn('querySelector(`[data-port="${portDragState.hoverPort}"]`)', smart)

    def test_media_renderer_mount_is_explicit_and_limited_to_top_level_smart_images(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        self.assertIn("canUseMediaRendererForSmartImage", smart)
        self.assertIn("media_renderer", smart)
        self.assertIn("mountNodeShellForSmartImages();", smart)
        self.assertIn("smart-group-member-node", smart)
        self.assertIn("WorkbenchUnifiedRenderHost.mount", smart)

    def test_media_renderer_has_opt_in_group_and_classic_canvas_adapters(self):
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("canUseMediaRendererForSmartGroup", smart)
        self.assertIn("smartGroupMediaRecord", smart)
        self.assertIn("const ownMedia = (node.images || [])", smart)
        self.assertIn("canUseCanvasMediaRenderer", classic)
        self.assertIn("canvasMediaRecord", classic)
        self.assertIn("WorkbenchUnifiedRenderHost.mountAdapterContent", classic)
        self.assertIn("cardClasses:['media-renderer-mounted']", classic)

    def test_classic_media_node_shell_reuses_legacy_gesture_and_link_state_machines(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "css" / "canvas.css").read_text(encoding="utf-8")
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertIn("function canvasNodeShellEnabled()", classic)
        self.assertIn("params.get('node_shell') !== '0'", classic)
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
        self.assertIn("params.get('legacy_renderer') !== '0'", classic)
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
        self.assertIn("if(to.type === 'group') return ['image','prompt'].includes(from.type)", classic)
        self.assertIn("group.items.push(fromId)", classic)
        self.assertIn("function canvasNodeShellSemanticZoomEnabled()", classic)
        self.assertIn("params.get('semantic_zoom') !== '0'", classic)
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
        self.assertIn("canvas.css?v=2026.09.04.1", page)
        self.assertIn("command-registry.js?v=2026.09.06.6", page)
        self.assertIn("creation-catalog.js?v=2026.09.04.1", page)
        self.assertIn("generation-intent.js?v=2026.09.04.1", page)
        self.assertIn("canvas.js?v=2026.09.06.15", page)
        self.assertIn("WorkbenchUnifiedRenderHost.cardShellView({selected:selected.has(node.id), onIntent:handleCanvasNodeShellIntent})", classic)
        self.assertIn("const canvasNodeShellIntentAdapter = window.WorkbenchUnifiedRenderHost.createIntentAdapter({", classic)
        self.assertIn("delete:intent => deleteNodeFromButton(intent.nodeId)", classic)
        self.assertIn("workbench-node-shell__actions", styles)
        self.assertIn("workbench-node-shell__delete::before", styles)
