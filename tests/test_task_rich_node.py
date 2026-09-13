import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TaskRichNodeTests(unittest.TestCase):
    def test_generic_task_exercises_presentations_and_reloads_generic_state(self):
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const T=sandbox.window.WorkbenchTaskRichNode;
const node={{id:'task-1',type:'task',title:'Draft task',status:'ready',inputs:[{{type:'literal',value:'x'}}],definition_ref:{{id:'legacy-definition'}}}};
const task=T.create({{node,storage}});
const states=['expanded','workspace','inspector','card'].map(p=>task.update({{presentation:p}}).presentation);
task.update({{status:'ready',inputs:[{{type:'literal',value:'saved'}}],definition:{{id:'task-definition',version:'1'}},skill:'placeholder',skillBinding:{{skill_id:'common.image-analysis',version:'1.0.0',enabled:true,parameters:{{detail:'high'}},prompt_override:{{prompt_id:'task.prompt',version:2}},execution_profile_ref:'local.default'}},workspace:'placeholder',inspector:'placeholder'}});
const reload=T.create({{node,storage}}).snapshot();
console.log(JSON.stringify({{compatible:T.compatible(node),presentations:T.PRESENTATIONS,states,reload}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["presentations"], ["card", "expanded", "workspace", "inspector"])
        self.assertEqual(payload["states"], ["expanded", "workspace", "inspector", "card"])
        self.assertTrue(payload["compatible"])
        self.assertEqual(payload["reload"]["fields"]["status"], "ready")
        self.assertEqual(payload["reload"]["fields"]["inputs"], [{"type": "literal", "value": "saved"}])
        self.assertEqual(payload["reload"]["fields"]["skill"], "placeholder")
        self.assertEqual(payload["reload"]["fields"]["skillBinding"]["version"], "1.0.0")
        self.assertEqual(payload["reload"]["fields"]["skillBinding"]["parameters"], {"detail": "high"})
        self.assertEqual(payload["reload"]["kind"], "task")

    def test_task_skeleton_does_not_claim_skill_or_execution_ownership(self):
        source = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertNotIn("SkillRegistry", source)
        self.assertNotIn("ModelDefinition", source)
        self.assertNotIn("execute", source.lower())
        self.assertIn("/static/js/workbench/canvas/task-rich-node.js", page)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("WorkbenchTaskRichNode.create({node, presentationController})", shell)
        self.assertIn("taskRichNode?.state().presentation", shell)

    def test_task_rich_node_reuses_shared_presentation_owner(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const controller=sandbox.window.WorkbenchPresentationState.create();
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}},presentationController:controller}});
task.update({{presentation:'expanded'}});
const afterTask=controller.state();
controller.transition('inspector');
console.log(JSON.stringify({{afterTask,afterController:task.state().presentation}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"afterTask": "expanded", "afterController": "inspector"})

    def test_skill_selector_changes_binding_without_changing_task_kind(self):
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        selector = ROOT / "static/js/workbench/canvas/skill-selector.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const skills=[
  {{skill:{{id:'common.summary',version:'1.0.0',title:'Summary'}},source:'package'}},
  {{skill:{{id:'common.summary',version:'2.0.0',title:'Summary v2'}},source:'package'}},
  {{skill:{{id:'common.image',version:'1.0.0',title:'Image'}},source:'system'}}
];
const registry={{discover:({{query}}={{}})=>skills.filter(item=>!query||item.skill.title.toLowerCase().includes(query.toLowerCase())),list_packs:({{enabled}})=>enabled?[{{id:'common-pack',version:'1',skills:[{{skill_id:'common.summary',version:'1.0.0'}}]}}]:[]}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(selector))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}}}});
const picker=sandbox.window.WorkbenchSkillSelector.create({{registry,task,recommended:[{{skill_id:'common.summary',version:'1.0.0'}}]}});
const chosen=picker.select(skills[1],{{parameters:{{tone:'brief'}}}});
const view=picker.snapshot('summary');
console.log(JSON.stringify({{chosen,kind:task.snapshot().kind,binding:task.snapshot().fields.skillBinding,recent:picker.recent(),recommended:view.recommended.map(item=>item.skill.version),packs:view.packs}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "task")
        self.assertEqual(payload["binding"]["skill_id"], "common.summary")
        self.assertEqual(payload["binding"]["version"], "2.0.0")
        self.assertEqual(payload["binding"]["parameters"], {"tone": "brief"})
        self.assertEqual(payload["recent"][0], {"skill_id": "common.summary", "version": "2.0.0"})
        self.assertEqual(payload["recommended"], ["1.0.0"])
        self.assertEqual(payload["packs"][0]["id"], "common-pack")

    def test_skill_selector_mounts_inside_task_content_host(self):
        selector = ROOT / "static/js/workbench/canvas/skill-selector.js"
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tagName:tag,children:[],dataset:{{}},append(...items){{this.children.push(...items)}},replaceChildren(...items){{this.children=[...items]}},addEventListener(name,fn){{this[name]=fn}},remove(){{this.removed=true}}}}; }}
const documentRef={{createElement:element}}; const host=element('section');
const skills=[{{skill:{{id:'common.summary',version:'1.0.0',title:'Summary'}}}}];
const registry={{discover:({{query}}={{}})=>skills,list_packs:()=>[]}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(selector))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}}}});
const mounted=task.mountSkillSelector(host,{{registry,document:documentRef}});
const search=host.children[0].children[0];
console.log(JSON.stringify({{root:host.children[0].className,search:search.className,groups:host.children[0].children[1].children.length,kind:task.snapshot().kind}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"root": "workbench-skill-selector", "search": "workbench-skill-selector__search", "groups": 1, "kind": "task"})

    def test_two_skill_definitions_produce_different_task_presentation(self):
        presentation = ROOT / "static/js/workbench/canvas/skill-driven-presentation.js"
        module = ROOT / "static/js/workbench/canvas/task-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tagName:tag,children:[],dataset:{{}},append(...items){{this.children.push(...items)}},replaceChildren(...items){{this.children=[...items]}},addEventListener(name,fn){{this[name]=fn}},remove(){{}},}}; }}
const documentRef={{createElement:element}};
const definition=(id,type)=>({{id,version:'1',title:id,parameter_schema:{{type:'object',properties:{{value:{{type}}}}}},ports:{{inputs:[{{id:type,required:true,accepts:['asset.image']}}],outputs:[{{id:'result',produces:['artifact.file']}}]}},output_schema:{{type:'object',properties:{{result:{{type:'string'}}}}}}}});
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox); vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const task=sandbox.window.WorkbenchTaskRichNode.create({{node:{{id:'task-1',kind:'task'}}}}); const host=element('section');
const a=task.mountSkillPresentation(host,{{definition:definition('skill-a','string'),document:documentRef}}); const first=host.children[0].className;
const b=sandbox.window.WorkbenchSkillDrivenPresentation.create({{definition:definition('skill-b','boolean'),document:documentRef}}); const secondHost=element('section'); b.mount(secondHost,{{document:documentRef}});
console.log(JSON.stringify({{first,second:secondHost.children[0].className,firstControls:host.children[0].children[1].children.length,secondControl:secondHost.children[0].children[1].children[0].children[0].type,kind:task.snapshot().kind}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"first": "workbench-skill-driven-presentation", "second": "workbench-skill-driven-presentation", "firstControls": 1, "secondControl": "checkbox", "kind": "task"})

    def test_selector_and_definition_presentation_have_separate_task_hosts(self):
        selector = ROOT / "static/js/workbench/canvas/skill-selector.js"
        presentation = ROOT / "static/js/workbench/canvas/skill-driven-presentation.js"
        shell = ROOT / "static/js/workbench/canvas/node-shell.js"
        source = shell.read_text(encoding="utf-8")
        self.assertIn("data-task-skill-selector-host", source)
        self.assertIn("data-task-skill-presentation-host", source)
        self.assertIn("mountSkillSelector(skillSelectorHost", source)
        self.assertIn("mountSkillPresentation(skillPresentationHost", source)
        self.assertIn("/static/js/workbench/canvas/skill-selector.js", (ROOT / "static/canvas.html").read_text(encoding="utf-8"))
        self.assertIn("/static/js/workbench/canvas/skill-driven-presentation.js", (ROOT / "static/canvas.html").read_text(encoding="utf-8"))
        self.assertTrue(selector.exists())
        self.assertTrue(presentation.exists())

    def test_skill_inspector_projects_definition_binding_and_only_safe_actions(self):
        inspector = ROOT / "static/js/workbench/canvas/skill-inspector.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
function element(tag) {{ return {{tagName:tag,children:[],dataset:{{}},append(...items){{this.children.push(...items)}},replaceChildren(...items){{this.children=[...items]}},addEventListener(name,fn){{this[name]=fn}},remove(){{this.removed=true}}}}; }}
const documentRef={{createElement:element}}; const host=element('section'); const calls=[];
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(inspector))},'utf8'),sandbox);
const definition={{id:'common.render',version:'2.1.0',title:'Render',package:{{package_id:'common-pack',version:'3.0.0'}},ports:{{inputs:[{{id:'source',required:true,accepts:['asset.image']}}],outputs:[{{id:'result',produces:['artifact.image']}}]}},parameter_schema:{{properties:{{quality:{{title:'Quality',type:'string',default:'high'}}}}}},capability_requirements:[{{id:'media.render',version:'1'}}],prompt:{{prompt_id:'render.prompt',version:4}},execution_routes:[{{route_type:'runtime',route_ref:'hidden.route',executor_type:'hidden.executor'}}]}};
const binding={{skill_id:'common.render',version:'2.1.0',parameters:{{quality:'draft'}},prompt_override:{{prompt_id:'override.prompt',version:5}}}};
const view=sandbox.window.WorkbenchSkillInspector.create({{definition,binding,onChangeSkill:payload=>calls.push(['change',payload.definition.id]),onOpenResource:payload=>calls.push(['open',payload.binding.version])}});
const snapshot=view.snapshot(); const mounted=view.mount(host,{{document:documentRef}});
host.children[0].children.at(-1).children[0].click();
console.log(JSON.stringify({{skill:snapshot.skill,package:snapshot.package,input:snapshot.inputs[0],parameter:snapshot.parameters[0],capabilities:snapshot.capabilities,prompts:snapshot.promptRefs,actions:snapshot.actions.map(item=>item.id),hasExecutor:Object.prototype.hasOwnProperty.call(snapshot,'executor'),root:mounted.element.className,calls}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["skill"], {"id": "common.render", "version": "2.1.0", "title": "Render"})
        self.assertEqual(payload["package"], {"id": "common-pack", "version": "3.0.0"})
        self.assertEqual(payload["input"]["accepts"], ["asset.image"])
        self.assertEqual(payload["parameter"]["value"], "draft")
        self.assertEqual(payload["capabilities"], ["media.render"])
        self.assertEqual(payload["prompts"], [{"id": "render.prompt", "version": "4"}, {"id": "override.prompt", "version": "5", "source": "override"}])
        self.assertEqual(payload["actions"], ["change", "open_resource"])
        self.assertFalse(payload["hasExecutor"])
        self.assertEqual(payload["root"], "workbench-skill-inspector")
        self.assertEqual(payload["calls"], [["change", "common.render"]])

    def test_task_skill_inspector_has_separate_host_and_no_runtime_ownership(self):
        task = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("mountSkillInspector", task)
        self.assertIn("data-task-skill-inspector-host", shell)
        self.assertIn("mountSkillInspector(skillInspectorHost", shell)
        self.assertIn("/static/js/workbench/canvas/skill-inspector.js", page)
        self.assertNotIn("ExecutorRegistry", task)
        self.assertNotIn("ProviderConnection", task)
        self.assertNotIn("execution_profile", (ROOT / "static/js/workbench/canvas/skill-inspector.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
