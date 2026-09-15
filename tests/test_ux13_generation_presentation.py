import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/generation-presentation.js"


class UX13GenerationPresentationTests(unittest.TestCase):
    def run_node(self, expression):
        script = f"const fs=require('fs'),vm=require('vm');const sandbox={{window:{{}}}};vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);{expression}"
        return subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout.strip()

    def test_projection_is_generic_and_uses_availability_contract(self):
        output = self.run_node("""
const node={model_ref:'image-model',modelAvailability:{route_ref:'provider-route',executor_type:'api',normalized_capabilities:['image','reference-image']},apiProvider:'legacy-provider',api_key:'must-not-project'};
console.log(JSON.stringify(sandbox.window.WorkbenchGenerationPresentation.projection(node)));
""")
        self.assertEqual(json.loads(output), {
            "model": "image-model", "route": "provider-route", "execution": "api",
            "capabilities": ["image", "reference-image"],
        })

    def test_projection_prefers_the_injected_canonical_availability_registry(self):
        script = f"""
const sandbox={{window:{{WorkbenchRuntimeRegistries:{{modelAvailability:{{listForModel:()=>[{{id:'route-1',model_ref:'model-x',route_ref:'codex',executor_type:'harness',status:'available',enabled:true}}]}}}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchGenerationPresentation.projection({{model:'model-x',apiProvider:'legacy-provider'}})));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["route"], "codex")
        self.assertEqual(json.loads(result.stdout)["execution"], "harness")

    def test_mount_renders_model_route_execution_and_capabilities_without_credentials(self):
        script = f"""
function E(tag,doc){{this.tagName=tag;this.ownerDocument=doc;this.children=[];this.className='';this.textContent='';this.attributes={{}};}}
E.prototype.append=function(){{this.children.push(...arguments)}};E.prototype.prepend=function(){{this.children.unshift(...arguments)}};E.prototype.replaceChildren=function(){{this.children=[...arguments]}};E.prototype.setAttribute=function(n,v){{this.attributes[n]=String(v)}};
const documentRef={{createElement:tag=>new E(tag,documentRef)}};const container=new E('div',documentRef);const node={{model:'model-x',apiProvider:'provider-x',executionProfile:'codex_harness',capabilities:['image','batch'],api_key:'secret'}};
const sandbox={{window:{{}}}};vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
const mounted=sandbox.window.WorkbenchGenerationPresentation.create({{document:documentRef,container,node}});
console.log(JSON.stringify({{root:mounted.root.className,route:mounted.root.children[1].textContent,capabilities:mounted.root.children[2].children.map(x=>x.textContent),secret:JSON.stringify(mounted.root).includes('secret')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "root": "workbench-generation-presentation",
            "route": "模型 · model-x  ·  路由 · provider-x  ·  执行 · codex_harness",
            "capabilities": ["image", "batch"],
            "secret": False,
        })

    def test_common_generation_bodies_use_shared_presentation_and_page_loads_it(self):
        body = (ROOT / "static/js/workbench/canvas/classic-card-body-renderer.js").read_text(encoding="utf-8")
        video = (ROOT / "static/js/workbench/canvas/classic-video-card-body.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/canvas-app-compat-host.js").read_text(encoding="utf-8")
        self.assertGreaterEqual(body.count("generationPresentation.create"), 2)
        self.assertIn("parameterPresentation.create", body)
        self.assertIn("generationPresentation.create", video)
        self.assertIn("parameterPresentation.create", video)
        self.assertIn("generationPresentation: window.WorkbenchGenerationPresentation", host)
        self.assertIn("/static/js/workbench/canvas/generation-presentation.js", page)
        self.assertNotIn("api_key", MODULE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
