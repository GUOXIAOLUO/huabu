import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArtifactRichNodeTests(unittest.TestCase):
    def test_legacy_outputs_support_all_presentations_and_version_ready_projection(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/artifact-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'artifact-1',title:'Generated output',extensions:{{legacy:{{payload:{{outputs:[{{id:'out-1',url:'/output/a.png',type:'image',revision:2}},{{id:'out-1',url:'/output/duplicate.png'}},{{artifact_id:'out-2',src:'/output/b.txt',kind:'text'}}]}}}}}}}};
const artifact=sandbox.window.WorkbenchArtifactRichNode.create({{node,storage}});
const states=['expanded','workspace','inspector','card'].map(p=>artifact.transition(p).presentation);
const reload=sandbox.window.WorkbenchArtifactRichNode.create({{node,storage}}).snapshot();
console.log(JSON.stringify({{compatible:sandbox.window.WorkbenchArtifactRichNode.compatible(node),states,reload,outputsFrozen:Object.isFrozen(reload.outputs)}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["compatible"])
        self.assertEqual(payload["states"], ["expanded", "workspace", "inspector", "card"])
        self.assertEqual(payload["reload"]["presentation"], "card")
        self.assertTrue(payload["reload"]["versionReady"])
        self.assertEqual(payload["reload"]["approvals"], "deferred")
        self.assertEqual(payload["reload"]["outputs"], [
            {"id": "out-1", "url": "/output/a.png", "kind": "image", "version": "2"},
            {"id": "out-2", "url": "/output/b.txt", "kind": "text", "version": "unversioned"},
        ])
        self.assertTrue(payload["outputsFrozen"])

    def test_artifact_skeleton_stays_generic_and_does_not_persist_future_domain_objects(self):
        source = (ROOT / "static/js/workbench/canvas/artifact-rich-node.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertNotIn("ApprovalService", source)
        self.assertNotIn("artifactVersion", source)
        self.assertIn("WorkbenchPresentationState", source)
        self.assertIn("/static/js/workbench/canvas/artifact-rich-node.js", page)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchArtifactRichNode.create({node, presentation: presentationController})", shell)
        self.assertIn("artifactRichNode?.state()", shell)

    def test_artifact_rich_node_can_reuse_the_shared_presentation_owner(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/artifact-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const controller=sandbox.window.WorkbenchPresentationState.create();
const artifact=sandbox.window.WorkbenchArtifactRichNode.create({{node:{{id:'artifact-1',kind:'artifact'}},presentation:controller}});
artifact.transition('expanded');
const afterArtifact=controller.state();
controller.transition('inspector');
console.log(JSON.stringify({{afterArtifact,afterController:artifact.state()}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"afterArtifact": "expanded", "afterController": "inspector"})


if __name__ == "__main__":
    unittest.main()
