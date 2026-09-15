import pathlib
import json
import subprocess
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class UX14ComfyWorkflowPresentationTests(unittest.TestCase):
    def test_module_projects_only_versioned_mapped_contract(self):
        source = (ROOT / "static/js/workbench/canvas/comfy-workflow-presentation.js").read_text()
        self.assertIn("dataset.comfyInputRole", source)
        self.assertIn("dataset.comfyOutputRole", source)
        self.assertIn("requires a versioned definition", source)
        self.assertNotIn("credentials", source.lower())
        self.assertNotIn("class_type", source)

    def test_page_loads_module_before_comfy_compat_seam(self):
        html = (ROOT / "static/canvas.html").read_text()
        presentation = html.index("comfy-workflow-presentation.js")
        compat = html.index("classic-comfy-controls.js")
        self.assertLess(presentation, compat)
        host = (ROOT / "static/js/workbench/canvas/canvas-app-compat-host.js").read_text()
        self.assertIn("workflowPresentation: window.WorkbenchComfyWorkflowPresentation", host)

    def test_comfy_seam_resolves_cached_workflow_from_the_full_node(self):
        source = (ROOT / "static/js/workbench/canvas/classic-comfy-controls.js").read_text()
        self.assertIn("currentComfyWorkflow(node) || {}", source)

    def test_comfy_seam_passes_versioned_cached_definition_to_real_projection(self):
        seam = ROOT / "static/js/workbench/canvas/classic-comfy-controls.js"
        projection = ROOT / "static/js/workbench/canvas/comfy-workflow-presentation.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
let contentContainer = null;
function el() {{ return {{
  className:'', innerHTML:'', textContent:'', value:'', disabled:false, style:{{}}, dataset:{{}},
  children:[], classList:{{contains:()=>false}},
  append(...items) {{ this.children.push(...items); }}, appendChild(item) {{ this.children.push(item); return item; }},
  prepend(item) {{ this.children.unshift(item); }}, querySelector(selector) {{ if (selector === '.comfy-content') {{ contentContainer = el(); return contentContainer; }} return el(); }}, querySelectorAll() {{ return []; }},
  addEventListener() {{}}, closest() {{ return null; }}
}}; }}
const documentStub = {{ createElement: () => el() }};
const sandbox = {{window: {{}}, document: documentStub}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(projection))}, 'utf8'), sandbox);
const host = {{
 document:documentStub, escapeHtml:s=>String(s), tr:s=>s, addNode:r=>r, uid:p=>p,
 defaultPoint:()=>({{x:0,y:0}}), allImageModels:()=>[], imageApiProviders:()=>[], getModels:()=>({{gpt:'gpt'}}),
 getComfyWorkflows:()=>[], generatorSources:()=>[], orderedSources:(n,s)=>s, imageRefsOnly:r=>r,
 comfyFields:()=>[], validComfyWorkflowName:n=>n, hasComfyWorkflow:()=>true,
 currentComfyWorkflow:()=>({{id:'workflow-a', version:7, title:'Mapped', input_bindings:[{{role:'prompt',node_id:'1',input_name:'text'}}], output_mappings:[{{role:'image',node_id:'3',output_name:'images'}}]}}),
 comfyFieldKind:()=> 'setting', ensureComfyWorkflow:async()=>({{}}), render:()=>{{}}, scheduleSave:()=>{{}}, runCanvasGenerate:()=>{{}},
 renderPromptPreview:()=>{{}}, renderComfyImages:()=>{{}}, renderComfyCustomField:()=>'', toggleComfyRandom:()=>{{}},
 bindCascadeButtons:()=>{{}}, cascadeBtnHtml:()=>'', retryBarHtml:()=>'',
 workflowPresentation: sandbox.window.WorkbenchComfyWorkflowPresentation
}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(seam))}, 'utf8'), sandbox);
const seamApi = sandbox.window.WorkbenchCanvasClassicComfyControls.create(host);
const body = seamApi.renderBody({{node:{{id:'comfy-1', type:'comfy', mode:'text', comfyWorkflow:'workflow-a'}}}});
const projected = contentContainer?.children[0];
console.log(JSON.stringify({{
  className: projected?.className,
  title: projected?.children[0]?.textContent,
  ref: projected?.children[1]?.textContent,
  inputRole: projected?.children[2]?.children[0]?.dataset.comfyInputRole,
  outputRole: projected?.children[3]?.children[0]?.dataset.comfyOutputRole
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        definition = json.loads(result.stdout)
        self.assertEqual(definition["className"], "workbench-comfy-workflow-presentation")
        self.assertEqual(definition["title"], "Mapped")
        self.assertEqual(definition["ref"], "workflow-a@7")
        self.assertEqual(definition["inputRole"], "prompt")
        self.assertEqual(definition["outputRole"], "image")


if __name__ == "__main__":
    unittest.main()
