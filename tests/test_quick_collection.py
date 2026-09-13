import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QuickCollectionTests(unittest.TestCase):
    def test_builds_ordered_typed_references_and_ignores_ineligible_nodes(self):
        module = ROOT / "static/js/workbench/canvas/quick-collection.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const refs=sandbox.window.WorkbenchQuickCollection.eligibleReferences([
  {{id:'second',type:'image',url:'/two.png',name:'Two'}},
  {{id:'skip',type:'prompt',text:'not a resource'}},
  {{id:'first',type:'image',url:'/one.png',asset_version_id:'asset-1',mediaKind:'video'}}
]);
console.log(JSON.stringify({{refs,payload:sandbox.window.WorkbenchQuickCollection.buildPayload({{projectId:'project-1',canvasId:'canvas-1',title:'Shots',references:refs}})}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([item["referenceId"] for item in payload["refs"]], ["second", "asset-1"])
        self.assertEqual([item["order"] for item in payload["payload"]["items"]], [0, 1])
        self.assertEqual(payload["payload"]["schema"]["columns"][0]["value_type"], "asset_version")
        self.assertEqual(payload["payload"]["items"][1]["values"]["asset_version"]["metadata"]["url"], "/one.png")

    def test_accepts_canonical_asset_artifact_and_collection_nodes_without_media_urls(self):
        module = ROOT / "static/js/workbench/canvas/quick-collection.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchQuickCollection.eligibleReferences([
  {{id:'asset-node',kind:'asset',version_id:'asset-v2',title:'Asset'}},
  {{id:'artifact-node',kind:'artifact',version_id:'artifact-v3',title:'Artifact'}}
])));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([(item["referenceType"], item["referenceId"]) for item in json.loads(result.stdout)], [
            ("asset_version", "asset-v2"), ("artifact_version", "artifact-v3"),
        ])

    def test_create_prompts_persists_collection_then_creates_collection_node(self):
        module = ROOT / "static/js/workbench/canvas/quick-collection.js"
        script = f"""
const fs=require('fs'), vm=require('vm'); const calls=[]; const sandbox={{window:{{prompt:()=> 'My Set'}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
sandbox.window.WorkbenchQuickCollection.create({{
  projectId:'p',canvasId:'c',position:{{x:10,y:20}},nodes:[{{id:'a',type:'image',url:'/a.png'}},{{id:'b',type:'video',url:'/b.mp4'}}],
  prompt:()=> 'My Set', createCollection:async payload=>{{calls.push(['collection',payload]);return {{id:'collection-1',revision:1,...payload}};}},
  createNode:async request=>{{calls.push(['node',request]);return {{id:'node-1',...request}};}}
}}).then(result=>console.log(JSON.stringify({{result,calls}})));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["result"]["created"])
        self.assertEqual([call[0] for call in payload["calls"]], ["collection", "node"])
        self.assertEqual(payload["calls"][1][1]["collection"]["id"], "collection-1")
        self.assertEqual(payload["calls"][1][1]["position"], {"x": 10, "y": 20})

    def test_canvas_contributes_action_and_uses_creation_boundary(self):
        interaction = (ROOT / "static/js/workbench/canvas/canvas-app-interaction.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        definitions = (ROOT / "workbench/application/legacy_definitions.py").read_text(encoding="utf-8")
        repository = (ROOT / "workbench/repositories/legacy_json_node_repository.py").read_text(encoding="utf-8")
        self.assertIn("id:'quick-collection'", interaction)
        self.assertIn("source:'quick_collection'", interaction)
        self.assertIn("WorkbenchCollectionApiClient.create", interaction)
        self.assertIn("definitionRef:{type:'legacy', id:'collection', version:'0'}", interaction)
        self.assertIn("quick-collection.js", page)
        self.assertIn("COLLECTION = DefinitionRef", definitions)
        self.assertIn('"collection"', repository)
