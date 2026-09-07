import json
import re
import subprocess
import time
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

    def test_generic_prompt_rendering_is_cut_over_to_the_registry_on_classic(self):
        classic_page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(classic_page.index("workbench/canvas/node-card-host.js"), classic_page.index("workbench/canvas/prompt-card-renderer.js"))
        self.assertLess(classic_page.index("workbench/canvas/prompt-card-renderer.js"), classic_page.index("js/canvas.js"))
        # Smart keeps its composer-owned smart-prompt card; the module is Classic-only.
        self.assertNotIn("prompt-card-renderer.js", (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8"))
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("if(node.type === 'prompt' && !canUseCanvasNodeShellForLegacy(node))", classic)
        self.assertIn("rendererOptions = node.type === 'prompt' ?", classic)
        self.assertIn("preserveLegacyContent: node.type !== 'prompt'", classic)
        self.assertIn("onPromptInput: text =>", classic)
        # Flags-off fallback markup is preserved verbatim.
        self.assertIn('data-prompt-template-open data-prompt-template-node-id=', classic)
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

    def test_provider_rendering_lifecycle_is_owned_by_the_runtime_on_classic(self):
        classic_page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(classic_page.index("workbench/canvas/prompt-card-renderer.js"), classic_page.index("workbench/canvas/provider-compat-renderer.js"))
        self.assertLess(classic_page.index("workbench/canvas/provider-compat-renderer.js"), classic_page.index("js/canvas.js"))
        # Smart provider-shaped cards keep their composer-owned bodies for now.
        self.assertNotIn("provider-compat-renderer.js", (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8"))
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("const CANVAS_PROVIDER_SHELL_TYPES = Object.freeze(['llm', 'generator', 'midjourney', 'msgen', 'video', 'comfy', 'rh', 'ltxDirector', 'minimax'])", classic)
        self.assertIn("onCardDestroy: payloadNode => destroyLTXEditor(payloadNode)", classic)
        delete_flow = classic[classic.index("function deleteNode(id, event){") : classic.index("function deleteSelectedNodes(){")]
        self.assertIn("renderRuntime?.unmount(id)", delete_flow)
        self.assertNotIn("destroyLTXEditor(", delete_flow)
        bulk_start = classic.index("function deleteSelectedNodes(){")
        bulk_flow = classic[bulk_start : bulk_start + 900]
        self.assertIn("toDelete.forEach(id => renderRuntime?.unmount(id));", bulk_flow)
        self.assertNotIn("destroyLTXEditor(", bulk_flow[:bulk_flow.index("renderRuntime?.unmount") + 40])

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
        self.assertLess(controller_page.index("workbench/canvas/interaction-controller.js"), controller_page.index("js/canvas.js"))
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        drag_flow = classic[classic.index("function startNodeDrag(") : classic.index("function onNodeDrag(")]
        resize_flow = classic[classic.index("function startNodeResize(") : classic.index("function onNodeResize(")]
        self.assertIn("ensureInteractionController().begin({kind:'node-drag', onMove:onNodeDrag, onEnd:endDrag})", drag_flow)
        self.assertIn("ensureInteractionController().begin({kind:'node-resize', onMove:onNodeResize, onEnd:endDrag})", resize_flow)
        self.assertNotIn("window.onmousemove = onNodeDrag", drag_flow)
        self.assertNotIn("window.onmouseup = endDrag", drag_flow)
        self.assertNotIn("window.onmousemove = onNodeResize", resize_flow)
        # The controller singleton is the single wiring owner for these sessions.
        self.assertEqual(classic.count("WorkbenchInteractionController.create({windowRef: window})"), 1)
        self.assertEqual(classic.count("ensureInteractionController().begin("), 3)

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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("const selected = window.WorkbenchInteractionController.createSelectionStore();", classic)
        self.assertNotIn("selected = new Set(", classic)
        self.assertIn("selected.replace(runtime.snapshot().selectedIds);", classic)
        self.assertIn("if(!applyCanvasRuntimeSelection(selectedIds)) selected.replace(selectedIds);", classic)
        # The authority module loads on the Classic page before the adapter.
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertLess(page.index("workbench/canvas/interaction-controller.js"), page.index("js/canvas.js"))

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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        self.assertIn("function ensureCanvasViewportController(){", classic)
        self.assertEqual(classic.count("WorkbenchInteractionController.createViewportController"), 1)
        # Board pan: the pointer session is wired through the controller, not the window slot.
        self.assertIn("ensureInteractionController().begin({kind:'board-pan'", classic)
        self.assertIn("ensureInteractionController().begin({kind:'board-pan'", classic)
        # Zoom and the set flows go through the controller.
        self.assertIn("canvasViewportController.zoomAt(", classic)
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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
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

    def test_node_drag_and_resize_session_creation_is_cut_over_on_both_adapters(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        for adapter, drag_factory, resize_factory in (
            (classic, "ensureNodeDragSessionFactory()", "ensureNodeResizeSessionFactory()"),
            (smart, "ensureSmartNodeDragSessionFactory()", "ensureSmartNodeResizeSessionFactory()"),
        ):
            self.assertEqual(adapter.count("WorkbenchInteractionController.createNodeDragSessionFactory"), 1)
            self.assertEqual(adapter.count("WorkbenchInteractionController.createNodeResizeSessionFactory"), 1)
            self.assertIn(f"{drag_factory}({{", adapter)
            self.assertIn(f"{resize_factory}({{", adapter)
        # No page wires kernel session creation directly anymore.
        for adapter in (classic, smart):
            self.assertNotIn("WorkbenchCanvasRuntime?.createNodeDragSession", adapter)
            self.assertNotIn("WorkbenchCanvasRuntime?.createNodeResizeSession", adapter)

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

    def test_keyboard_listeners_are_cut_over_to_the_runtime_on_both_adapters(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        for adapter, singleton in (
            (classic, "const canvasKeyboardRuntime = window.WorkbenchInteractionController.createKeyboardRuntime({windowRef: window});"),
            (smart, "const smartKeyboardRuntime = window.WorkbenchInteractionController.createKeyboardRuntime({windowRef: window});"),
        ):
            self.assertIn(singleton, adapter)
            self.assertEqual(adapter.count("WorkbenchInteractionController.createKeyboardRuntime"), 1)
            self.assertIn("KeyboardRuntime.register(e => {", adapter)
        # The migrated main keydown blocks no longer add their own window listeners.
        self.assertNotIn("window.addEventListener('keydown', e => {\n    if(!canvas) return;", classic)
        self.assertNotIn("window.addEventListener('keyup', e => {\n    if(String(e.key || '').toLowerCase() === 'r') isRKeyDown = false;", classic)
        # Undo/redo, delete, copy/paste, group and select-all shortcuts still route
        # through their characterized page functions.
        self.assertIn("performUndo()", classic)
        self.assertIn("deleteSelectedNodes()", classic)
        self.assertIn("copySelectedNodes()", classic)
        self.assertIn("groupSelectedImages()", classic)
        self.assertIn("deleteNode(id);", smart)
        self.assertIn("copySelectedNodes();", smart)

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

    def test_connection_gestures_are_cut_over_on_both_adapters(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        for adapter, singleton in (
            (classic, "ensureClassicConnectionGesture"),
            (smart, "ensureSmartConnectionGesture"),
        ):
            self.assertEqual(adapter.count("WorkbenchInteractionController.createConnectionGestureController"), 1)
            self.assertIn("beginGesture(", adapter)
            self.assertIn("scheduleSave()", adapter)
        # Persistence is only touched through page save/application seams; the
        # controller module has no save/fetch API surface at all.
        runtime_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "interaction-controller.js").read_text(encoding="utf-8")
        self.assertNotIn("scheduleSave", runtime_module)
        self.assertNotIn("fetch(", runtime_module)
        # The duplicated page wiring is gone: Classic no longer assigns the
        # window slot inside startLink, and Smart's dispatcher lost both
        # portDragState branches.
        classic_link = classic[classic.index("function startLink(e, originId, originKind){") : classic.index("function nearestPort(clientX, clientY, kind){")]
        self.assertNotIn("window.onmousemove", classic_link)
        self.assertNotIn("window.onmouseup", classic_link)
        self.assertNotIn("if(portDragState){", smart)
        self.assertIn("function finishSmartPortDrag(drag, e){", smart)
        self.assertIn("drop: (gesture, result, e2) => finishSmartPortDrag(gesture, e2),", smart)
        self.assertIn("noTarget: (gesture, e2) => finishSmartPortDrag(gesture, e2),", smart)

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

    def test_single_node_clipboard_paste_routes_through_the_creation_controller(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        # Both adapters gate the versioned clipboard path to a single,
        # connection-free node and delegate creation to the controller with
        # the explicit clipboard provenance source.
        self.assertIn("function clipboardVersionedCandidate(clipNodes, clipConnections){", classic)
        self.assertIn("function clipboardVersionedSmartCandidate(sourceNodes, sourceConnections){", smart)
        for adapter in (classic, smart):
            self.assertEqual(adapter.count("source:'clipboard'"), 1)
        self.assertIn("await ensureCreationController().createNode({", classic[classic.index("async function createVersionedPastedNode("):])
        self.assertIn("await ensureSmartCreationController().createNode({", smart[smart.index("async function createVersionedPastedSmartPrompt("):])
        # The versioned path passes canvasId through the controller envelope —
        # pinned because the R4-21 blank creators omitted it and the controller
        # rejects a missing canvasId at runtime.
        for adapter, helper in (
            (classic, "async function createVersionedPastedNode(candidate, point){"),
            (smart, "async function createVersionedPastedSmartPrompt(candidate, point){"),
        ):
            body = adapter[adapter.index(helper):]
            body = body[:body.index("\n}\n")]
            self.assertIn("canvasId:canvas.id", body)
        # Multi-node fragments, connections and every other shape keep the
        # adapter-owned fragment path: center-anchored materialization stays.
        classic_paste = classic[classic.index("async function pasteNodes(){") : classic.index("function selectedWorkflowPayload(){")]
        smart_paste = smart[smart.index("function pasteNodes(){") : smart.index("// 跨页\"素材库")]
        for adapter in (classic_paste, smart_paste):
            self.assertIn("WorkbenchCanvasGraphFragment.materializeImportedSubgraph", adapter)
            self.assertIn("anchor:'center'", adapter)
        self.assertIn("function pasteClipboardFragmentLegacy(){", smart_paste)
        self.assertIn("scheduleSave()", smart_paste)

    def test_connect_drops_route_through_the_graph_connect_command(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        client = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js").read_text(encoding="utf-8")
        # One versioned client method targets the application connect route.
        self.assertEqual(client.count("/graph/connect-nodes"), 1)
        self.assertIn("connectNodes: (canvasId, command, actorId) => {", client)
        # Classic: the gesture drop delegates to the versioned connect with a
        # legacy fallback commit; Classic graph side effects stay page-owned.
        self.assertIn("async function createVersionedConnection(fromId, toId){", classic)
        self.assertIn("function commitClassicConnection(fromId, toId){", classic)
        self.assertIn("function applyClassicConnectionSideEffects(fromId, toId){", classic)
        self.assertIn("void createVersionedConnection(fromId, toId)", classic)
        classic_versioned = classic[classic.index("async function createVersionedConnection(fromId, toId){"):]
        classic_versioned = classic_versioned[:classic_versioned.index("\n}\n")]
        self.assertIn("window.WorkbenchNodeClient.connectNodes(canvas.id", classic_versioned)
        self.assertIn("edge_id:uid('c')", classic_versioned)
        self.assertIn("adoptRevision(canvas, result.canvas_revision, Date.now())", classic_versioned)
        self.assertNotIn("pushUndo()", classic_versioned)
        classic_effects = classic[classic.index("function applyClassicConnectionSideEffects(fromId, toId){"):]
        classic_effects = classic_effects[:classic_effects.index("\n}\n")]
        # Which Classic side effects fire is decided by the shared
        # compatibility policy (card R4-25); the page applies the projection
        # and still owns executing the page-level sync helper.
        self.assertIn("ensureLegacyGraphCompatibilityPolicy()", classic_effects)
        self.assertIn("syncLatestGeneratedOutputToConnection(fromId, toId)", classic_effects)
        policy = (ROOT / "static" / "js" / "workbench" / "canvas" / "legacy-graph-compatibility.js").read_text(encoding="utf-8")
        self.assertIn("canvas.group.add-member", policy)
        # Smart: the port drop delegates to the versioned connect; the shared
        # legacy connectInputNode stays for the non-drop callers.
        self.assertIn("async function connectInputNodeVersioned(fromId, toId){", smart)
        self.assertIn("void connectInputNodeVersioned(intent.from, intent.to)", smart)
        self.assertIn("connectInputNode(intent.from, intent.to)", smart)
        smart_versioned = smart[smart.index("async function connectInputNodeVersioned(fromId, toId){"):]
        smart_versioned = smart_versioned[:smart_versioned.index("\n}\n")]
        self.assertIn("window.WorkbenchNodeClient.connectNodes(canvas.id", smart_versioned)
        self.assertIn("kind:'input'", smart_versioned)
        # Core graph model stays industry-neutral: no Classic/Smart side
        # effects leak into the application boundary.
        service = (ROOT / "workbench" / "application" / "graph_mutation.py").read_text(encoding="utf-8")
        for adapter_detail in ("smart-loop", "imageInput", "showPrompt", "syncLatestGeneratedOutput", "group.items"):
            self.assertNotIn(adapter_detail, service)

    def test_group_membership_routes_through_the_graph_membership_command(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        client = (ROOT / "static" / "js" / "workbench" / "canvas" / "node-creation-client.js").read_text(encoding="utf-8")
        # One versioned client method targets the application group-membership route.
        self.assertEqual(client.count("/graph/group-membership"), 1)
        self.assertIn("setGroupMembership: (canvasId, command, actorId) => {", client)
        # Smart: a narrow async helper delegates the durable add through the
        # versioned membership write; image absorption / group-merge stay page-side.
        self.assertIn("async function addSmartGroupMemberVersioned(groupId, memberId){", smart)
        smart_helper = smart[smart.index("async function addSmartGroupMemberVersioned(groupId, memberId){"):]
        smart_helper = smart_helper[:smart_helper.index("\n}\n")]
        self.assertIn("window.WorkbenchNodeClient.setGroupMembership(canvas.id", smart_helper)
        self.assertIn("operation:'add'", smart_helper)
        # The drag-drop group gesture captures a single non-image/non-group member
        # and prefers the versioned write with a page save fallback.
        self.assertIn("let smartMembershipCommit = null;", smart)
        self.assertIn("void addSmartGroupMemberVersioned(smartMembershipCommit.groupId, smartMembershipCommit.memberId)", smart)
        # Core group-mutation service stays industry-neutral: no Classic/Smart
        # side effects leak into the application boundary.
        service = (ROOT / "workbench" / "application" / "group_mutation.py").read_text(encoding="utf-8")
        for adapter_detail in ("smart-loop", "imageInput", "showPrompt", "syncLatestGeneratedOutput", "inputNodeIds"):
            self.assertNotIn(adapter_detail, service)
        # Classic page keeps its geometry-driven membership on the page-owned path;
        # it does not yet route through the versioned client.
        self.assertNotIn("WorkbenchNodeClient.setGroupMembership", classic)

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

    def test_composer_lifecycle_is_loaded_before_the_smart_page_and_owned(self):
        page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        composer_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "composer.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/composer.js"), page.index("js/smart-canvas.js"))
        # The page delegates the shell lifecycle and no longer owns its timer/seq.
        self.assertIn("const composerLifecycle = window.WorkbenchCanvasComposer.create({ container: composer });", smart)
        self.assertIn("composerLifecycle.positionForRect(nodeRect(node))", smart)
        self.assertIn("composerLifecycle.scheduleUpdate(delay, updateComposer)", smart)
        self.assertIn("composerLifecycle.cancelPending()", smart)
        self.assertIn("composerLifecycle.setOpen(", smart)
        self.assertNotIn("composerUpdateTimer", smart)
        self.assertNotIn("composerUpdateSeq", smart)
        # The extracted shell is product-neutral: no Smart adapter detail leaks in.
        for adapter_detail in ("smart-minimax", "imageInput", "cascadeRunBtn", "selectedNode", "renderDynamicParams", "promptInput"):
            self.assertNotIn(adapter_detail, composer_module)

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

    def test_media_tools_is_loaded_before_the_smart_page_and_owned(self):
        page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        media_tools_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "media-tools.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/media-tools.js"), page.index("js/smart-canvas.js"))
        # The page delegates the tool math to the shared module and no longer
        # owns the raw geometry bodies (no duplicate owner).
        self.assertIn("const mediaTools = window.WorkbenchCanvasMediaTools;", smart)
        self.assertIn("mediaTools.clampResizeScale(value)", smart)
        self.assertIn("mediaTools.circledNumber(n)", smart)
        self.assertIn("mediaTools.canvasPoint(", smart)
        self.assertIn("mediaTools.gridSplitRects(width, height, rows, cols, gap)", smart)
        self.assertIn("mediaTools.gridSplitRectsCustom(width, height, [0, ...rawH, height], [0, ...rawV, width], gap)", smart)
        self.assertIn("mediaTools.parseCropRatio(", smart)
        self.assertIn("mediaTools.fitCropRectToAspect(ratio, boundsW, boundsH, rect)", smart)
        self.assertNotIn("Math.round(num * 100)", smart)          # old resize-clamp body
        self.assertNotIn("0x2460", smart)                          # old circled-number body
        self.assertNotIn("topLine + halfGap", smart)              # old uniform grid-split body
        self.assertNotIn("nextW / nextH > ratio", smart)          # old aspect-fit body
        # The extracted module is product-neutral: no Smart adapter detail leaks in.
        for adapter_detail in ("imageEditModal", "cropImage", "editDrawCanvas", "panoramaState",
                               "gridJoinLayout", "cropState", "selectedNode", "replaceEditedImage",
                               "scheduleSave", "gridCustomLines"):
            self.assertNotIn(adapter_detail, media_tools_module)

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

    def test_smart_execution_compatibility_manifest_is_grounded_in_source(self):
        doc = (ROOT / "docs" / "plans" / "R4_SMART_EXECUTION_COMPATIBILITY.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", doc, re.S)
        self.assertIsNotNone(match, "the characterization doc must embed a JSON evidence manifest")
        manifest = json.loads(match.group(1))
        self.assertEqual(manifest["source"], "static/js/smart-canvas.js")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        allowed_dispositions = {"seamed", "host-cutover", "host-candidate", "transport-only", "flag-only"}
        seen_dispositions = set()
        for entry in manifest["entry_points"]:
            self.assertIn(entry["disposition"], allowed_dispositions)
            seen_dispositions.add(entry["disposition"])
            self.assertIn(entry["function"], smart, f"{entry['function']} must exist in source")
            for evidence in entry["evidence"]:
                self.assertIn(evidence, smart, f"evidence {evidence} must exist in source")
        # The classification is non-trivial: at least the cutover, seamed, and a
        # deferred host-candidate disposition must all be present.
        for required in ("host-cutover", "seamed", "host-candidate"):
            self.assertIn(required, seen_dispositions)

    def test_execution_host_is_loaded_before_the_smart_page_and_run_prompt_llm_uses_it(self):
        page = (ROOT / "static" / "smart-canvas.html").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        execution_host_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "execution-host.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/execution-host.js"), page.index("js/smart-canvas.js"))
        # The page constructs the host handle and delegates runPromptLLMNode's
        # Canvas lifecycle/state side-effects through it (no direct node writes).
        self.assertIn("const executionHost = window.WorkbenchCanvasExecutionHost.create({", smart)
        self.assertIn("executionHost.markRunning(node, true)", smart)
        self.assertIn("executionHost.writePromptResult(node, {promptResult: result.text || '', provider, model})", smart)
        self.assertIn("executionHost.save()", smart)
        self.assertIn("executionHost.notifyError(e.message || tr('smart.promptLlmFailed'))", smart)
        self.assertIn("executionHost.markRunning(node, false)", smart)
        # The old direct Canvas writes in runPromptLLMNode are gone.
        self.assertNotIn("node.promptResult = (result.text || '').trim()", smart)
        self.assertNotIn("node.llmProvider = provider;", smart)
        # The extracted host is product-neutral: no Smart adapter detail leaks in.
        for adapter_detail in ("smart-prompt", "promptResult", "scheduleSave", "selectedNode",
                               "resolveChatProviderId", "promptNodeLLMInputText", "nodes"):
            self.assertNotIn(adapter_detail, execution_host_module)

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
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        provider_controls_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "provider-controls.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/provider-controls.js"), page.index("js/canvas.js"))
        # The page constructs the host handle and renderLLMBody delegates its
        # provider/system/mode controls through it (no direct node writes).
        self.assertIn("window.WorkbenchCanvasProviderControls.create({", classic)
        self.assertIn("const providerControls = ensureProviderControls();", classic)
        self.assertIn("providerControls.setField(node, 'llmProvider', value)", classic)
        self.assertIn("providerControls.setField(node, 'showSystem', !node.showSystem)", classic)
        self.assertIn("providerControls.setField(node, 'systemPrompt', e.target.value)", classic)
        self.assertIn("providerControls.setField(node, 'mode', btn.dataset.mode)", classic)
        # The old direct Canvas writes in renderLLMBody's handlers are gone
        # (these strings are unique to the LLM body; the Comfy body keeps its
        # own page-owned mode handler, out of scope for this card).
        self.assertNotIn("node.llmProvider = e.target.value", classic)
        self.assertNotIn("node.showSystem = !node.showSystem", classic)
        self.assertNotIn("node.systemPrompt = e.target.value", classic)
        # The extracted host is product-neutral: no Classic adapter detail leaks in.
        for adapter_detail in ("llmProvider", "llm", "generator", "midjourney", "msgen",
                               "providerChatModels", "renderLLMBody", "scheduleSave"):
            self.assertNotIn(adapter_detail, provider_controls_module)

    def test_classic_execution_host_module_owns_the_canvas_lifecycle_contract(self):
        classic_execution_host_module = ROOT / "static" / "js" / "workbench" / "canvas" / "classic-execution-host.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const sandbox = {{ window: {{}} }};
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
        self.assertEqual(manifest["source"], "static/js/canvas.js")
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        allowed_dispositions = {"seamed", "host-cutover", "host-candidate", "transport-only", "flag-only"}
        seen_dispositions = set()
        for entry in manifest["entry_points"]:
            self.assertIn(entry["disposition"], allowed_dispositions)
            seen_dispositions.add(entry["disposition"])
            self.assertIn(entry["function"], classic, f"{entry['function']} must exist in source")
            for evidence in entry["evidence"]:
                self.assertIn(evidence, classic, f"evidence {evidence} must exist in source")
        # The classification is non-trivial: the cutover, seamed, and a deferred
        # host-candidate disposition must all be present.
        for required in ("host-cutover", "seamed", "host-candidate"):
            self.assertIn(required, seen_dispositions)

    def test_classic_execution_host_is_loaded_before_the_classic_page_and_run_llm_uses_it(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        classic_execution_host_module = (ROOT / "static" / "js" / "workbench" / "canvas" / "classic-execution-host.js").read_text(encoding="utf-8")
        # The module loads ahead of the editor script.
        self.assertLess(page.index("workbench/canvas/classic-execution-host.js"), page.index("js/canvas.js"))
        # The page constructs the host handle and delegates runLLMNode's Canvas
        # lifecycle/state side-effects through it (no direct node writes).
        self.assertIn("window.WorkbenchCanvasClassicExecutionHost.create({", classic)
        self.assertIn("const executionHost = ensureClassicExecutionHost();", classic)
        self.assertIn("executionHost.markRunning(node, true)", classic)
        self.assertIn("executionHost.markRunning(node, false)", classic)
        self.assertIn("executionHost.writeOutputText(node, outputText)", classic)
        self.assertIn("executionHost.setRunStatus(node, 'done', '')", classic)
        self.assertIn("executionHost.setRunStatus(node, 'failed', err.message || String(err))", classic)
        self.assertIn("executionHost.save()", classic)
        self.assertIn("executionHost.notifyError(err.message || 'LLM 运行失败')", classic)
        # The old direct Canvas writes in runLLMNode are gone.
        self.assertNotIn("node.outputText = await callCanvasLLM", classic)
        # The extracted host is product-neutral: no Classic adapter detail leaks in.
        for adapter_detail in ("refreshNodes", "scheduleSave", "node.outputText",
                               "node.runStatus", "node.runError", "node.running",
                               "runLLMNode", "callCanvasLLM", "cascade", "generator"):
            self.assertNotIn(adapter_detail, classic_execution_host_module)

    def test_blank_creation_entry_points_route_through_the_creation_controller(self):
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        for adapter, factory in ((classic, "ensureCreationController"), (smart, "ensureSmartCreationController")):
            self.assertEqual(adapter.count("WorkbenchInteractionController.createCreationController"), 1)
            self.assertIn("create: (canvasId, command, clientId) => window.WorkbenchNodeClient.create(canvasId, command, clientId)", adapter)
            self.assertIn("applyResult: (result, apply) => window.WorkbenchNodeClient.applyCreationResult(result, apply)", adapter)
        # No page calls the versioned client create directly for blank entries anymore.
        self.assertNotIn("WorkbenchNodeClient.create(canvas.id", classic)
        self.assertNotIn("WorkbenchNodeClient.create(canvas.id", smart)

    def test_blank_create_entry_points_propagate_canvas_id(self):
        # R4-21.1 (do NOT execute next): every R4-21 blank-create helper must
        # propagate canvasId:canvas.id into the controller envelope, mirroring
        # the R4-22 file-drop / R4-23 clipboard helpers. Source-string pin
        # modeled after the existing clipboard wiring pin
        # (`test_single_node_clipboard_paste_routes_through_the_creation_controller`
        # pattern at line ~1922).
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")

        classic_helpers = (
            "async function addVersionedBlankImageNode(point){",
            "async function addVersionedBlankPromptNode(point){",
            "async function addVersionedBlankLoopNode(point){",
            "async function addVersionedBlankGroupNode(point){",
            "async function addVersionedBlankOutputNode(point){",
        )
        smart_helpers = (
            "async function createVersionedBlankSmartPrompt(x, y){",
            "async function createVersionedBlankSmartLoop(x, y){",
            "async function createVersionedBlankSmartGroup(x, y){",
            "async function createVersionedBlankSmartMinimax(point){",
            "async function createVersionedBlankSmartImageAt(point){",
        )

        def helper_body(source, header):
            start = source.index(header)
            rest = source[start:]
            end = rest.index("\n}\n")
            return rest[: end + len("\n}\n")]

        for header in classic_helpers:
            body = helper_body(classic, header)
            self.assertIn(
                "canvasId:canvas.id",
                body,
                f"Classic blank-create helper {header[:-2]} must propagate canvasId:canvas.id (R4-21.1)",
            )
        for header in smart_helpers:
            body = helper_body(smart, header)
            self.assertIn(
                "canvasId:canvas.id",
                body,
                f"Smart blank-create helper {header[:-2]} must propagate canvasId:canvas.id (R4-21.1)",
            )

        # Singleton factory / no-direct-client invariants from the original
        # R4-21 test must remain satisfied after the canvasId fix.
        for adapter, factory in ((classic, "ensureCreationController"), (smart, "ensureSmartCreationController")):
            self.assertEqual(adapter.count("WorkbenchInteractionController.createCreationController"), 1)
            self.assertNotIn("WorkbenchNodeClient.create(canvas.id", adapter)
        # The five blank-create envelopes per page are still routed through the
        # singleton (R4-21 invariant), now also carrying canvasId.
        self.assertGreaterEqual(classic.count("ensureCreationController().createNode({"), 5)
        self.assertGreaterEqual(smart.count("ensureSmartCreationController().createNode({"), 5)

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

    def test_versioned_connect_drops_land_at_the_application_command(self):
        # R4-24 end-to-end behavioral proof: drive the actual page-side
        # `createVersionedConnection` (Classic) and `connectInputNodeVersioned`
        # (Smart) through a sandbox with a stubbed `WorkbenchNodeClient`
        # and verify the page call lands with the right canvasId, revision,
        # edge id and kind, the projected edge appears in the page's
        # connections store, the canvas revision is adopted, and the helper
        # returns its success/failure value correctly.
        client_module = ROOT / "static/js/workbench/canvas/node-creation-client.js"
        client_source = client_module.read_text(encoding="utf-8")
        policy_source = (ROOT / "static/js/workbench/canvas/legacy-graph-compatibility.js").read_text(encoding="utf-8")
        classic_source = (ROOT / "static/js/canvas.js").read_text(encoding="utf-8")
        smart_source = (ROOT / "static/js/smart-canvas.js").read_text(encoding="utf-8")
        classic_helper = re.search(
            r"async function createVersionedConnection\(fromId, toId\)\{[\s\S]*?\n\}\n",
            classic_source,
        ).group(0)
        smart_helper = re.search(
            r"async function connectInputNodeVersioned\(fromId, toId\)\{[\s\S]*?\n\}\n",
            smart_source,
        ).group(0)

        script = f"""
const vm = require('vm');
const clientSource = {json.dumps(client_source)};
function bootSandbox() {{
  const s = {{window: {{}}, console}};
  vm.runInNewContext(clientSource, s);
  return s;
}}
function replaceClient(boot, onConnect) {{
  const original = boot.window.WorkbenchNodeClient;
  boot.window.WorkbenchNodeClient = {{
    isLoopback: original.isLoopback,
    isEnabled: original.isEnabled,
    applyCreationResult: original.applyCreationResult,
    applyGraphCreationResult: original.applyGraphCreationResult,
    create: original.create,
    update: original.update,
    remove: original.remove,
    createNodeAndEdge: original.createNodeAndEdge,
    connectNodes: onConnect,
  }};
}}

const calls = [];
const responses = [];
const classicBoot = bootSandbox();
replaceClient(classicBoot, async (canvasId, command, actorId) => {{
  calls.push({{canvasId, command, actorId}});
  const r = responses.shift();
  if (r && r.throw) throw new Error(r.throw);
  return {{edge: {{id: command.edge_id, from: {{node_id: command.from_node_id}}, to: {{node_id: command.to_node_id}}}}, canvas_revision: 1}};
}});
classicBoot.window.WorkbenchCanvasPersistence = {{adoptRevision: (canvas, rev, fallback) => rev}};
classicBoot.window.WorkbenchCanvasCommands = {{graphCommand: () => true}};
classicBoot.canvas = {{id: 'canvas-c1', project: 'p1', updated_at: 1}};
classicBoot.connections = [];
classicBoot.undoStack = [];
classicBoot.CLIENT_ID = 'c-local';
classicBoot.UNDO_MAX = 50;
classicBoot.pushUndo = () => {{}};
let classicSaveScheduled = 0; classicBoot.scheduleSave = () => {{classicSaveScheduled++;}};
classicBoot.render = () => {{}};
classicBoot.canUseVersionedImageCreation = () => true;
let classicSideEffectsCalled = 0;
classicBoot.applyClassicConnectionSideEffects = () => {{classicSideEffectsCalled++;}};
classicBoot.setStatus = () => {{}};
classicBoot.lastCanvasUpdatedAt = 1;
classicBoot.serializableCanvasNodes = () => [];
classicBoot.uid = (prefix) => prefix + '-test-abc';
vm.runInNewContext({json.dumps(classic_helper)} + '\\nthis.createVersionedConnection = createVersionedConnection;', classicBoot);

const smartBoot = bootSandbox();
// Reuse the mock-calls queue but with a fresh per-page counter helper
// so the smart side records correctly.
const smartCalls = [];
replaceClient(smartBoot, async (canvasId, command, actorId) => {{
  smartCalls.push({{canvasId, command, actorId}});
  return {{edge: {{id: command.edge_id, from: {{node_id: command.from_node_id}}, to: {{node_id: command.to_node_id}}}}, canvas_revision: 5}};
}});
smartBoot.window.WorkbenchCanvasPersistence = {{adoptRevision: (canvas, rev, fallback) => rev}};
smartBoot.canvas = {{id: 'canvas-s1', project: 'p1', updated_at: 4, connections: []}};
smartBoot.nodes = [{{id: 'p1', type: 'smart-prompt'}}, {{id: 'i1', type: 'smart-image', inputNodeIds: []}}];
smartBoot.smartClientId = 's-local';
smartBoot.UNDO_LIMIT = 50;
let smartSaveScheduled = 0; smartBoot.scheduleSave = () => {{smartSaveScheduled++;}};
smartBoot.render = () => {{}};
smartBoot.canUseVersionedSmartImageCreation = () => true;
smartBoot.resolveChatProviderId = () => 'mock';
smartBoot.resolveChatModel = () => 'mock-model';
smartBoot.imagesForNode = () => [];
smartBoot.promptTextItemsForNode = () => [];
smartBoot.isSmartGroupNode = () => false;
smartBoot.isSmartImageNode = () => false;
smartBoot.fitSmartLoopNode = () => {{}};
smartBoot.snapshotForUndo = () => ({{}});
smartBoot.serializableCanvasNodes = () => [];
smartBoot.toast = () => {{}};
smartBoot.uid = (prefix) => prefix + '-test-s';
// The Smart connect helper asks the shared compatibility policy (R4-25) for
// its projection. Drive the REAL policy here — wired to the same page-shaped
// mocks — so this test covers the helper and the policy together.
vm.runInNewContext({json.dumps(policy_source)}, smartBoot);
const smartPolicy = smartBoot.window.WorkbenchLegacyGraphCompatibility.create({{
  commands: smartBoot.window.WorkbenchCanvasCommands || null,
  smartGroupImageCount: node => smartBoot.imagesForNode(node).filter(img => img && img.url).length,
  smartGroupPromptCount: node => smartBoot.promptTextItemsForNode(node).filter(Boolean).length,
}});
smartBoot.ensureSmartLegacyGraphCompatibilityPolicy = () => smartPolicy;
vm.runInNewContext({json.dumps(smart_helper)} + '\\nthis.connectInputNodeVersioned = connectInputNodeVersioned;', smartBoot);

(async () => {{
  const classicOk = await classicBoot.createVersionedConnection('a', 'b');
  responses.push({{throw: 'stale revision'}});
  const classicStale = await classicBoot.createVersionedConnection('a', 'b');
  const smartOk = await smartBoot.connectInputNodeVersioned('p1', 'i1');
  const smartFail = await smartBoot.connectInputNodeVersioned('p1', 'missing');
  console.log(JSON.stringify({{
    classicOk, classicStale,
    smartOk, smartFail,
    classicConnections: classicBoot.connections,
    smartConnections: smartBoot.canvas.connections,
    smartCanvasNodes: smartBoot.nodes,
    classicCalls: calls.map(c => ({{canvasId: c.canvasId, project_id: c.command.project_id, from: c.command.from_node_id, to: c.command.to_node_id, kind: c.command.kind, expected_revision: c.command.expected_revision, edge_id_prefix: c.command.edge_id.slice(0, 2), actorId: c.actorId}})),
    smartCalls: smartCalls.map(c => ({{canvasId: c.canvasId, project_id: c.command.project_id, from: c.command.from_node_id, to: c.command.to_node_id, kind: c.command.kind, expected_revision: c.command.expected_revision, edge_id_prefix: c.command.edge_id.slice(0, 2), actorId: c.actorId}})),
    classicSideEffectsCalled, classicSaveScheduled, smartSaveScheduled,
  }}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        # Classic success path: helper returns true; calls the connect-nodes
        # client exactly once per call, with canvas.id, the from/to, an edge
        # id that starts with 'c-', and with the page's revision. Side
        # effects fire, the projected edge lands in `connections`.
        self.assertTrue(payload["classicOk"])
        self.assertEqual(payload["classicStale"], False)
        self.assertEqual(len(payload["classicConnections"]), 1)
        classicEdge = payload["classicConnections"][0]
        self.assertEqual(classicEdge["from"], "a")
        self.assertEqual(classicEdge["to"], "b")
        self.assertTrue(classicEdge["id"].startswith("c-"))
        self.assertEqual(payload["classicSideEffectsCalled"], 1)
        self.assertEqual(payload["classicSaveScheduled"], 1)
        # Smart success path: helper returns true; call carries `kind: input`
        # so the application boundary can apply inputNodeIds sync in the same
        # lock. The target's `inputNodeIds` ends up containing the from id.
        self.assertTrue(payload["smartOk"])
        self.assertEqual(payload["smartFail"], None)
        self.assertEqual(payload["smartConnections"], [{"from": "p1", "to": "i1", "kind": "input"}])
        self.assertEqual(payload["smartCanvasNodes"][1]["inputNodeIds"], ["p1"])
        # Classic calls: 2 (one ok, one that threw on stale). The smart
        # failed call short-circuits before reaching the client because the
        # helper returns null when the target is missing.
        self.assertEqual(len(payload["classicCalls"]), 2)
        self.assertEqual(len(payload["smartCalls"]), 1)
        for call in payload["classicCalls"]:
            self.assertEqual(call["canvasId"], "canvas-c1")
            self.assertEqual(call["project_id"], "p1")
            self.assertEqual(call["from"], "a")
            self.assertEqual(call["to"], "b")
            self.assertEqual(call["expected_revision"], 1)
            self.assertEqual(call["edge_id_prefix"], "c-")
            self.assertEqual(call["actorId"], "c-local")
            # Classic helper omits `kind` (the application default `flow`
            # applies). Pin the key's absence to lock the explicit Smart
            # `kind:'input'` contract below.
            self.assertNotIn("kind", call)
        smart_call = payload["smartCalls"][0]
        self.assertEqual(smart_call["canvasId"], "canvas-s1")
        self.assertEqual(smart_call["project_id"], "p1")
        self.assertEqual(smart_call["from"], "p1")
        self.assertEqual(smart_call["to"], "i1")
        self.assertEqual(smart_call["expected_revision"], 4)
        self.assertEqual(smart_call["actorId"], "s-local")
        self.assertEqual(smart_call["kind"], "input")
        # Smart `scheduleSave` only fires when `loopTouched` is true (target
        # is `smart-loop` AND its image-input / show-prompt flags moved).
        # In this test the target is `smart-image`, so loopTouched stays
        # false and the page-side save is intentionally not scheduled — the
        # service-owned revision CAS is the durable write.
        self.assertEqual(payload["smartSaveScheduled"], 0)

    def test_legacy_graph_compatibility_policy_owns_connect_side_effects(self):
        # R4-25: a single named policy module owns every Classic / Smart
        # historical connect side effect. The two-page helpers delegate to
        # it; no inline branching survives in the page code; Core
        # graph_mutation has zero adapter leak. The policy is loaded into
        # `window` exactly once and is the only writer of these fields.
        classic = (ROOT / "static/js/canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static/js/smart-canvas.js").read_text(encoding="utf-8")
        policy_source = (ROOT / "static/js/workbench/canvas/legacy-graph-compatibility.js").read_text(encoding="utf-8")
        service_source = (ROOT / "workbench/application/graph_mutation.py").read_text(encoding="utf-8")
        # Policy module exists and exposes a factory / singleton on window.
        self.assertIn("global.WorkbenchLegacyGraphCompatibility", policy_source)
        self.assertIn("createLegacyGraphCompatibilityPolicy", policy_source)
        # Page helpers consult the policy via the global; the page does not
        # own the side-effect rules itself anymore.
        self.assertIn("WorkbenchLegacyGraphCompatibility", classic)
        self.assertIn("WorkbenchLegacyGraphCompatibility", smart)
        # Core graph_mutation has zero adapter leak (preserved invariant
        # from R4-24). The policy module is allowed to mention these
        # branches — that's the whole point of the seam — but the service
        # must not.
        for adapter_detail in ("smart-loop", "imageInput", "showPrompt", "syncLatestGeneratedOutput", "group.items", "inputNodeIds"):
            self.assertNotIn(adapter_detail, service_source)
        # The RULES no longer live inline in the page helpers. Each helper
        # delegates to the policy and applies the returned projection; the
        # page keeps only the mechanically-unavoidable execution of
        # page-owned effects (group mutation, sync helpers, save/render).
        classic_effects = re.search(
            r"function applyClassicConnectionSideEffects\(fromId, toId\)\{[\s\S]*?\n\}\n",
            classic,
        ).group(0)
        # The helper reaches the policy through the page's accessor; the
        # global itself is referenced by that accessor (pinned above at
        # page level). Helper → accessor → policy is the seam.
        self.assertIn("ensureLegacyGraphCompatibilityPolicy()", classic_effects)
        # The Classic group-membership type rule is policy-owned now.
        self.assertNotIn("['image','prompt']", classic_effects)
        smart_connect = re.search(
            r"async function connectInputNodeVersioned\(fromId, toId\)\{[\s\S]*?\n\}\n",
            smart,
        ).group(0)
        self.assertIn("ensureSmartLegacyGraphCompatibilityPolicy()", smart_connect)
        # The Smart loop-input rule is policy-owned now: no adapter type
        # literal and no inline looks/looksPrompt derivation survives.
        self.assertNotIn("smart-loop", smart_connect)
        self.assertNotIn("looksImage", smart_connect)
        self.assertNotIn("looksPrompt", smart_connect)

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

    def test_classic_connect_side_effects_apply_the_policy_projection(self):
        # R4-25 behavioral proof for the Classic half: drive the REAL
        # `applyClassicConnectionSideEffects` out of canvas.js together with
        # the REAL policy module and verify the page applies exactly the
        # projection the policy returns — group membership (idempotent and
        # command-gated) plus the historically unconditional output /
        # generator syncs.
        classic_source = (ROOT / "static/js/canvas.js").read_text(encoding="utf-8")
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

    def test_minimap_projection_scaling_stays_linear_at_100_and_300_nodes(self):
        # DoD: minimap performance remains acceptable at 100/300 nodes — the
        # projection/rect math the minimap rebuild performs per frame must stay
        # linear in node count with bounded per-node work.
        runtime_state = (ROOT / "static" / "js" / "workbench" / "canvas" / "runtime-state.js").read_text(encoding="utf-8")
        self.assertIn("function worldPointFromMinimapPointer", runtime_state)
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
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

    def test_group_rendering_is_cut_over_to_the_runtime_on_both_adapters(self):
        runtime_source = (ROOT / "static" / "js" / "workbench" / "canvas" / "render-runtime.js").read_text(encoding="utf-8")
        self.assertIn("function mountGroupCard(options)", runtime_source)
        self.assertIn("output_refs", runtime_source)
        classic = (ROOT / "static" / "js" / "canvas.js").read_text(encoding="utf-8")
        smart = (ROOT / "static" / "js" / "smart-canvas.js").read_text(encoding="utf-8")
        # Classic: the group branch routes through the runtime with the page
        # supplying member resolution and the empty-state hook.
        self.assertIn("function mountCanvasGroupShell(node, body, el){", classic)
        self.assertIn("ensureRenderRuntime().mountGroupCard({", classic)
        self.assertIn("type:mediaKindForNode(item)", classic)
        self.assertIn("workbench-node-shell__group-empty", classic)
        # Smart: the record/media decision left the page; the rollback flag
        # stays page-owned via mediaEnabled.
        self.assertIn("ensureSmartRenderRuntime().mountGroupCard({", smart)
        self.assertIn("mediaEnabled:canUseMediaRendererForSmartGroup(entry.node)", smart)
        self.assertNotIn("smartGroupMediaRecord(node) : window.WorkbenchCanvas.legacyNodeView", smart)

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
        self.assertEqual(classic.count("WorkbenchCanvasPersistence.adoptRevision(canvas, result.canvas_revision, Date.now())"), 11)
        self.assertEqual(classic.count("WorkbenchCanvasPersistence.adoptRevision(canvas, revision)"), 10)
        self.assertEqual(smart.count("WorkbenchCanvasPersistence.adoptRevision(canvas, result.canvas_revision, Date.now())"), 6)
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
        self.assertIn("ensureNodeDragSessionFactory()({", classic)
        self.assertIn("isLocalCopy:Boolean(e.altKey), dragSession};", classic)
        self.assertIn("const dragPosition = (id, ox, oy) => sharedPositions?.get(id) || {x:ox + dx, y:oy + dy};", classic)
        self.assertIn("(e.clientX - dragNode.sx) / viewport.scale", classic)
        self.assertIn("ensureSmartNodeDragSessionFactory()({", smart)
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
        self.assertIn("ensureNodeResizeSessionFactory()({start:{x:e.clientX, y:e.clientY}, scale:viewport.scale, startWidth:sw, startHeight:sh})", classic)
        self.assertIn("const nextW = Math.max(Math.min(min.w, 220), resize ? resize.width : resizeNode.sw + (e.clientX - resizeNode.sx) / viewport.scale);", classic)
        self.assertIn("(e.clientY - resizeNode.sy) / viewport.scale", classic)
        self.assertIn("ensureSmartNodeResizeSessionFactory()({start:{x:pointer.clientX, y:pointer.clientY}, scale:viewport.scale, startWidth:rect.width, startHeight:rect.height})", smart)
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
        # Since R4-21 the blank-create envelope flows through the creation
        # controller; the client's apply stays injected in the page singletons.
        self.assertGreaterEqual(classic.count("ensureCreationController().createNode({"), 5)
        self.assertGreaterEqual(smart.count("ensureSmartCreationController().createNode({"), 5)
        self.assertEqual(classic.count("WorkbenchInteractionController.createCreationController"), 1)
        self.assertEqual(smart.count("WorkbenchInteractionController.createCreationController"), 1)
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
        self.assertIn("ensureCanvasViewportController().set(fitted)", classic)
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
        self.assertIn("definitionRef:{type:'legacy', id:'output', version:'0'}", classic)
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
        self.assertIn("graphCommand('canvas.group.add-member', 'smart')", smart)
        # The Classic variant of the same catalog entry is now issued by the
        # shared compatibility policy (card R4-25) rather than inline in the
        # page — same command id, single owner.
        policy = (ROOT / "static" / "js" / "workbench" / "canvas" / "legacy-graph-compatibility.js").read_text(encoding="utf-8")
        self.assertIn("graphCommand('canvas.group.add-member', 'classic')", policy)
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
        # Since R4-20 the hover validation lives in the Smart connection gesture
        # controller callbacks, not in the global mousemove dispatcher.
        hover = smart[smart.index("function ensureSmartConnectionGesture(){") : smart.index("function finishSmartPortDrag(")]
        self.assertIn("const intent = window.WorkbenchCanvasGraphInteraction?.edgeIntentFromPortDrop(", hover)
        self.assertIn("WorkbenchCanvasPortCompatibility?.isCompatible(", hover)
        self.assertIn("fromNode?.output_port_type || fromNode?.port_type || 'legacy.any'", hover)
        self.assertIn("toNode?.input_port_type || toNode?.port_type || 'legacy.any'", hover)
        # The gesture lifecycle is controller-owned: the dispatcher no longer
        # carries the portDragState branches.
        self.assertNotIn("if(portDragState){", smart)

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
        self.assertIn("if(!applyCanvasRuntimeSelection(selectedIds)) selected.replace(selectedIds);", classic_finish)
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
        self.assertIn("if(!handled) {", mouseup)
        self.assertIn("void addSmartGroupMemberVersioned(smartMembershipCommit.groupId, smartMembershipCommit.memberId)", mouseup)

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
        self.assertIn('node.promptResult = String(result?.promptResult ?? \'\').trim();', smart)
        self.assertIn('executionHost.writePromptResult(node, {promptResult: result.text || \'\', provider, model})', smart)
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
        # Group membership is applied from the compatibility-policy
        # projection (card R4-25) instead of an inline push.
        self.assertIn("projection.addedNodeIds.forEach", classic)
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
