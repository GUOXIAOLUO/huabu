import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDIA_RENDERER = ROOT / "static/js/workbench/canvas/media-renderer.js"
NODE_CARD_HOST = ROOT / "static/js/workbench/canvas/node-card-host.js"
INTERACTION = ROOT / "static/js/workbench/canvas/canvas-app-interaction.js"
RECORDS = ROOT / "static/js/workbench/canvas/canvas-app-records.js"
MEDIA_EDITOR = ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js"


class Ux10AssetMediaNodeReplicaTests(unittest.TestCase):
    def test_media_card_is_content_first_and_supports_image_video_audio_and_file(self):
        script = f"""
const fs = require('fs'); const vm = require('vm');
const created = [];
function element(tag) {{
  return {{tagName: tag.toUpperCase(), className:'', dataset:{{}}, children:[], textContent:'',
    append(child) {{ this.children.push(child); }},
    addEventListener() {{}},
    classList: {{toggle() {{}}, add() {{}}, remove() {{}}}},
  }};
}}
const documentRef = {{createElement(tag) {{ const item = element(tag); created.push(item); return item; }}}};
const sandbox = {{window: {{WorkbenchCanvasMediaKind: {{kindForItem: item =>
  ['image','video','audio','file'].includes(String(item.kind || '').toLowerCase())
    ? String(item.kind).toLowerCase() : (item.url.endsWith('.mp4') ? 'video' : 'file')}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MEDIA_RENDERER))}, 'utf8'), sandbox);
const node = {{id:'asset-1', title:'House media', kind:'asset', extensions:{{legacy:{{payload:{{media:[
  {{url:'image.png', name:'Front elevation', kind:'image'}},
  {{url:'walkthrough.mp4', name:'Walkthrough', kind:'video'}},
  {{url:'voice.m4a', name:'Voice note', kind:'audio'}},
  {{url:'quote.pdf', name:'Quote PDF', kind:'file'}},
]}}}}}}}};
const host = {{ownerDocument:documentRef, replaceChildren(...children) {{ this.children = children; }}}};
const mounted = sandbox.window.WorkbenchMediaRenderer.mountInto(host, node, {{document:documentRef}});
console.log(JSON.stringify({{root:mounted.element.className, figures:mounted.element.children.map(figure => ({{
  figure:figure.className, child:figure.children[0].tagName, label:figure.children[0].dataset.url,
  caption:figure.children[1]?.textContent || '', file:figure.children[0].textContent || ''
}}))}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        payload = json.loads(result.stdout)
        self.assertIn("workbench-media-renderer--content-first", payload["root"])
        self.assertEqual([item["child"] for item in payload["figures"]], ["IMG", "VIDEO", "AUDIO", "DIV"])
        self.assertEqual([item["caption"] for item in payload["figures"]], [
            "Front elevation", "Walkthrough", "Voice note", "Quote PDF"
        ])
        self.assertEqual(payload["figures"][3]["file"], "Quote PDF")

    def test_node_card_host_marks_media_renderer_as_content_first_without_new_owner(self):
        source = NODE_CARD_HOST.read_text(encoding="utf-8")
        self.assertIn("contentFirst: renderer.id === 'media'", source)
        self.assertNotIn("WorkbenchAssetRepository", source)
        self.assertNotIn("fetch(", source)

    def test_existing_floating_preview_service_accepts_media_references(self):
        interaction = INTERACTION.read_text(encoding="utf-8")
        records = RECORDS.read_text(encoding="utf-8")
        self.assertIn("WorkbenchMediaRenderer?.mediaItems(node)?.[0]", interaction)
        self.assertIn("openImageNodePreview(intent.nodeIds[0])", interaction)
        self.assertIn("openOutputLightbox(url, {...node, url})", records)
        self.assertIn("node?.type === 'image'", interaction)

    def test_asset_and_artifact_records_enter_the_shared_media_admission_seam(self):
        source = MEDIA_EDITOR.read_text(encoding="utf-8")
        self.assertIn("node?.type === 'asset' || node?.type === 'artifact'", source)
        self.assertIn("WorkbenchMediaRenderer.canRender(canvasMediaRecord(node))", source)
        self.assertNotIn("mountCanvasNodeShellForMedia(node, body, el) && node.type === 'asset'", source)


if __name__ == "__main__":
    unittest.main()
