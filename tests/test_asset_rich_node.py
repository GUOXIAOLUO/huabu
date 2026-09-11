import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AssetRichNodeTests(unittest.TestCase):
    def test_legacy_asset_payload_supports_all_four_presentations_and_reload(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/asset-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'asset-1',title:'Legacy asset',extensions:{{legacy:{{payload:{{images:[{{url:'/assets/a.png',name:'A'}},{{url:'/assets/a.png'}},{{url:'/assets/b.mp4',type:'video'}}]}}}}}}}};
const rich=sandbox.window.WorkbenchAssetRichNode.create({{node,storage}});
const states=[rich.transition('expanded').presentation,rich.transition('workspace').presentation,rich.transition('inspector').presentation,rich.transition('card').presentation];
const reload=sandbox.window.WorkbenchAssetRichNode.create({{node,storage}});
const snapshot=reload.snapshot();
console.log(JSON.stringify({{compatible:sandbox.window.WorkbenchAssetRichNode.isCompatible(node),states,reload:reload.state(),media:snapshot.media,mediaFrozen:Object.isFrozen(snapshot.media),legacy:snapshot.legacyCompatible}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "compatible": True,
            "states": ["expanded", "workspace", "inspector", "card"],
            "reload": "card",
            "media": [
                {"url": "/assets/a.png", "name": "A", "kind": "image"},
                {"url": "/assets/b.mp4", "name": "Media", "kind": "video"},
            ],
            "mediaFrozen": True,
            "legacy": True,
        })

    def test_asset_rich_node_stays_out_of_future_asset_version_and_library_concerns(self):
        source = (ROOT / "static/js/workbench/canvas/asset-rich-node.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        runtime = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchPresentationState", source)
        self.assertNotIn("assetVersion", source)
        self.assertNotIn("resourceLibrary", source)
        self.assertIn("/static/js/workbench/canvas/asset-rich-node.js", page)
        self.assertIn("WorkbenchAssetRichNode.create({node, presentation: presentationController})", runtime)
        self.assertIn("assetRichNode?.state()", runtime)

    def test_asset_rich_node_can_reuse_the_shared_presentation_owner(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/asset-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const controller=sandbox.window.WorkbenchPresentationState.create();
const rich=sandbox.window.WorkbenchAssetRichNode.create({{node:{{id:'asset-1',kind:'asset'}},presentation:controller}});
rich.transition('expanded');
const afterRich=controller.state();
controller.transition('inspector');
console.log(JSON.stringify({{afterRich,afterController:rich.state()}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"afterRich": "expanded", "afterController": "inspector"})


if __name__ == "__main__":
    unittest.main()
