import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/artifact-inspector.js"


class ArtifactInspectorTests(unittest.TestCase):
    def test_inspector_renders_history_lineage_comparison_and_actions(self):
        source = MODULE.read_text(encoding="utf-8")
        script = f"""
const vm = require('vm');
const sandbox = {{window: {{}}, globalThis: {{}}}};
vm.createContext(sandbox);
vm.runInContext({json.dumps(source)}, sandbox);
const I = sandbox.window.WorkbenchArtifactInspector;
const inspector = I.createInspector({{escapeHtml: value => String(value).replace(/[&<>\\\"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\\\"':'&quot;',\"'\":'&#39;'}}[c]))}});
const history = {{current_version_id:'v2', versions:[
  {{id:'v1', ordinal:1, created_at:'2026-09-14T10:00:00Z', content_ref:{{location:'/a.txt', mime_type:'text/plain', checksum:'sha256:aaa'}}, lineage:{{run_id:'r1', attempt_id:'a1', input_refs:['i1']}}}},
  {{id:'v2', ordinal:2, created_at:'2026-09-14T11:00:00Z', content_ref:{{location:'https://example.test/a.txt', mime_type:'text/plain', checksum:'sha256:bbb'}}, lineage:{{run_id:'r2', attempt_id:'a2', input_refs:['i2'], prompt_version_ref:'p2', model_ref:'m2', skill_version_ref:'s2'}}}}
]}};
const html = inspector.render({{id:'art-1', title:'结果 <x>', type:'analysis', state:'ready'}}, history, {{selectedVersionId:'v1', compareVersionId:'v2'}});
const defaultCompare = inspector.render({{id:'art-1', title:'结果', type:'analysis', state:'ready'}}, history, {{compareVersionId:'v1'}});
const result = {{escaped:html.includes('结果 &lt;x&gt;'), history:html.includes('v2') && html.includes('v1'), lineage:html.includes('r1') && html.includes('a1') && html.includes('p2'), compare:html.includes('版本比较') && html.includes('data-artifact-compare=\"v2\"') && defaultCompare.includes('版本比较'), actions:html.includes('data-artifact-open=') && html.includes('data-artifact-materialize=\"v1\"'), noFileSrc:!html.includes('src=\"/a.txt\"'), active:inspector.activeVersion(history, 'v1').id === 'v1'}};
if (!Object.values(result).every(Boolean)) throw new Error(JSON.stringify(result));
console.log(JSON.stringify(result));
"""
        completed = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["compare"])

    def test_page_mounts_artifact_surface_without_canvas_runtime(self):
        page = (ROOT / "static/asset-manager.html").read_text(encoding="utf-8")
        source = (ROOT / "static/js/asset-manager.js").read_text(encoding="utf-8")
        self.assertIn("artifact-inspector.js", page)
        self.assertIn("id=\"artifactInspector\"", page)
        self.assertIn("kind:'artifact'", source)
        self.assertIn("/api/v1/artifacts?project_id=", source)
        self.assertIn("function renderArtifactManager()", source)
        self.assertIn("artifact-materialize-request", source)
        shell = (ROOT / "static/index.html").read_text(encoding="utf-8")
        canvas_state = (ROOT / "static/js/workbench/canvas/canvas-app-state.js").read_text(encoding="utf-8")
        self.assertIn("artifact-materialize-request", shell)
        self.assertIn("pendingArtifactMaterialization", canvas_state)
        interaction = (ROOT / "static/js/workbench/canvas/canvas-app-interaction.js").read_text(encoding="utf-8")
        self.assertIn("workbench-artifact-materialization-request", canvas_state)
        self.assertIn("ensureCreationController().createNode", interaction)
        self.assertIn("source:'result_materialization'", interaction)
        self.assertIn("artifact_version_ref", interaction)
        self.assertIn("initialOutputRefs", interaction)
        creation = (ROOT / "static/js/workbench/canvas/interaction-controller.js").read_text(encoding="utf-8")
        self.assertIn("initial_output_refs", creation)
        api = (ROOT / "workbench/api/canvas_nodes.py").read_text(encoding="utf-8")
        self.assertIn("initial_output_refs: list[ArtifactOrAssetVersionRef]", api)
        self.assertIn("initial_output_refs=tuple(payload.initial_output_refs)", api)
        self.assertNotIn("canvasRuntime", MODULE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
