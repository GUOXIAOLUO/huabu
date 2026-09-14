import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/task-card-presentation.js"
MODEL_SELECTOR = ROOT / "static/js/workbench/canvas/model-selector.js"
SKILL_SELECTOR = ROOT / "static/js/workbench/canvas/skill-selector.js"
NODE_SHELL = ROOT / "static/js/workbench/canvas/node-shell.js"
TASK_RICH_NODE = ROOT / "static/js/workbench/canvas/task-rich-node.js"


class Ux09TaskLlmNodeReplicaTests(unittest.TestCase):
    def run_node(self, expression):
        script = f"const fs=require('fs'),vm=require('vm');{self.fake_dom()}const sandbox={{window:{{}}}};vm.runInNewContext(fs.readFileSync({json.dumps(str(MODEL_SELECTOR))},'utf8'),sandbox);vm.runInNewContext(fs.readFileSync({json.dumps(str(SKILL_SELECTOR))},'utf8'),sandbox);vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);{expression}"
        return subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout.strip()

    @staticmethod
    def fake_dom():
        return """
function E(tag,doc){this.tagName=tag;this.ownerDocument=doc;this.children=[];this.dataset={};this.attributes={};this.listeners={};this.className='';this.textContent='';this.value='';this.checked=false;this.disabled=false;}
E.prototype.append=function(){this.children.push(...arguments);return this};E.prototype.prepend=function(){this.children.unshift(...arguments);return this};
E.prototype.replaceChildren=function(){this.children=[...arguments]};E.prototype.addEventListener=function(name,fn){this.listeners[name]=fn};
E.prototype.setAttribute=function(name,value){this.attributes[name]=String(value)};E.prototype.remove=function(){this.removed=true};
const documentRef={createElement:tag=>new E(tag,documentRef)};const host=new E('section',documentRef);
function find(root,klass){if(String(root.className).split(' ').includes(klass))return root;for(const child of root.children){const hit=find(child,klass);if(hit)return hit}return null}
"""

    def test_card_renders_reference_hierarchy_and_delegates_state(self):
        output = self.run_node("""
const changes=[];const state={nodeId:'task-1',title:'品牌宣传短片生成器',status:'ready',inputs:[{name:'产品图'}],definition:{title:'品牌宣传 Skill'},skillBinding:{skill_id:'brand.copy',enabled:true},modelSelection:{resolved:{model_ref:'gpt-5.6-sol'}},prompt:'保持产品结构不变',outputMode:'text'};
const task={state:()=>state,update:patch=>{Object.assign(state,patch);changes.push(patch)}};
const card=sandbox.window.WorkbenchTaskCardPresentation.create({task,document:documentRef,routeLabel:'公司'});card.mount(host);
const root=host.children[0],prompt=find(root,'workbench-task-card__prompt'),list=find(root,'workbench-task-card__output-mode').children[0];
prompt.value='生成三种文案';prompt.listeners.input();list.listeners.click({preventDefault(){},stopPropagation(){}});
console.log(JSON.stringify({root:root.className,title:find(root,'workbench-task-card__title').textContent,input:find(root,'workbench-task-card__input-chip').textContent,route:find(root,'workbench-task-card__route').textContent,changes,run:find(root,'workbench-task-card__run').textContent}));
""")
        payload = json.loads(output)
        self.assertEqual(payload["root"], "workbench-task-card")
        self.assertEqual(payload["title"], "品牌宣传短片生成器")
        self.assertEqual(payload["input"], "产品图")
        self.assertIn("gpt-5.6-sol", payload["route"])
        self.assertEqual(payload["changes"][0], {"prompt": "生成三种文案"})
        self.assertEqual(payload["run"], "生成")

    def test_output_mode_and_skill_toggle_update_task_without_execution_ownership(self):
        output = self.run_node("""
const updates=[];const state={nodeId:'task-2',title:'Task',status:'draft',inputs:[],skillBinding:{skill_id:'skill',enabled:true},outputMode:'text'};
const task={state:()=>state,update:patch=>{Object.assign(state,patch);updates.push(patch)}};
sandbox.window.WorkbenchTaskCardPresentation.create({task,document:documentRef,modelSelectorOptions:{availabilities:[]}}).mount(host);
const root=host.children[0],toggle=find(root,'workbench-task-card__skill-label').children[0],modes=find(root,'workbench-task-card__output-mode').children;
toggle.checked=false;toggle.listeners.change();modes[2].listeners.click({preventDefault(){},stopPropagation(){}});
console.log(JSON.stringify({updates,hasExecutor:Object.prototype.hasOwnProperty.call(sandbox.window.WorkbenchTaskCardPresentation,'executor')}));
""")
        payload = json.loads(output)
        self.assertEqual(payload["updates"], [{"skillBinding": {"skill_id": "skill", "enabled": False}}, {"outputMode": "structured"}])
        self.assertFalse(payload["hasExecutor"])

    def test_model_selector_stays_inside_task_card_presentation(self):
        output = self.run_node("""
const state={nodeId:'task-3',title:'Task',status:'ready',inputs:[],modelSelection:{selection:{mode:'auto',availabilityId:''}},outputMode:'text'};
const task={state:()=>state,update:patch=>Object.assign(state,patch),mountModelSelector:(target,options)=>sandbox.window.WorkbenchModelSelector.create({...options,task:{update:patch=>task.update(patch)}}).mount(target)};
sandbox.window.WorkbenchTaskCardPresentation.create({task,document:documentRef,modelSelectorOptions:{availabilities:[]}}).mount(host);
const selector=find(host,'workbench-task-card__model-selector'),available=find(selector,'workbench-model-selector__select');
console.log(JSON.stringify({selector:selector.className,available:available.tagName}));
""")
        self.assertEqual(json.loads(output), {"selector": "workbench-task-card__model-selector", "available": "select"})

    def test_skill_selector_requires_injected_canonical_registry(self):
        output = self.run_node("""
const state={nodeId:'task-4',title:'Task',status:'ready',inputs:[],skillBinding:{skill_id:'brand.copy',version:'1.0.0',enabled:true},outputMode:'text'};
const registry={discover:({query})=>query?[{skill:{id:'brand.copy',version:'1.0.0',title:'Brand Copy'}}]:[{skill:{id:'brand.copy',version:'1.0.0',title:'Brand Copy'}}]};
const task={state:()=>state,update:patch=>Object.assign(state,patch),mountSkillSelector:(target,options)=>sandbox.window.WorkbenchSkillSelector.create({...options,task:{update:patch=>task.update(patch)}}).mount(target)};
const card=sandbox.window.WorkbenchTaskCardPresentation.create({task,document:documentRef,skillSelectorOptions:{registry}});
card.mount(host);
console.log(JSON.stringify({selector:Boolean(find(host,'workbench-task-card__skill-selector')),skillButton:find(host,'workbench-skill-selector__skill').textContent}));
""")
        self.assertEqual(json.loads(output), {"selector": True, "skillButton": "Brand Copy · 1.0.0"})

    def test_production_task_composition_mounts_each_injected_selector_once(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
function E(tag,doc){{this.tagName=tag;this.ownerDocument=doc;this.children=[];this.dataset={{}};this.attributes={{}};this.listeners={{}};this.className='';this.textContent='';this.value='';this.checked=false;this.disabled=false;this.tabIndex=0;}}
E.prototype.append=function(){{this.children.push(...arguments);return this}};E.prototype.prepend=function(){{this.children.unshift(...arguments);return this}};E.prototype.replaceChildren=function(){{this.children=[...arguments]}};E.prototype.addEventListener=function(n,f){{this.listeners[n]=f}};E.prototype.setAttribute=function(n,v){{this.attributes[n]=String(v)}};E.prototype.remove=function(){{this.removed=true}};E.prototype.closest=function(){{return null}};E.prototype.classList={{toggle(){{}},add(){{}},remove(){{}}}};
const documentRef={{createElement:tag=>new E(tag,documentRef)}};const sandbox={{window:{{document:documentRef,WorkbenchCanvas:{{STATES:['ready','running','done']}}}}}};
for(const file of [{json.dumps(str(MODEL_SELECTOR))},{json.dumps(str(SKILL_SELECTOR))},{json.dumps(str(MODULE))},{json.dumps(str(TASK_RICH_NODE))},{json.dumps(str(NODE_SHELL))}]) vm.runInNewContext(fs.readFileSync(file,'utf8'),sandbox);
const registry={{discover:()=>[{{skill:{{id:'brand.copy',version:'1.0.0',title:'Brand Copy'}}}}]}};
const routes=[{{id:'route-1',model_ref:'model-1',route_type:'provider',route_ref:'provider-1',executor_type:'api',normalized_capabilities:[],status:'available'}}];
const selectorOptions={{registry}},modelOptions={{availabilities:routes}};
const mounted=sandbox.window.WorkbenchNodeShell.create({{document:documentRef,node:{{id:'task-6',type:'task',title:'Task',state:'ready',skillBinding:{{skill_id:'brand.copy',version:'1.0.0'}},modelSelection:{{selection:{{mode:'auto',availabilityId:''}}}}}},taskNode:{{id:'task-6',type:'task'}},taskPresentationOptions:{{routeLabel:'平台',skillSelectorOptions:selectorOptions,modelSelectorOptions:modelOptions}},skillSelectorOptions:selectorOptions,modelSelectorOptions:modelOptions}});
function count(root,klass){{let total=String(root.className).split(' ').includes(klass)?1:0;for(const child of root.children)total+=count(child,klass);return total}}
console.log(JSON.stringify({{skill:count(mounted.element,'workbench-skill-selector'),model:count(mounted.element,'workbench-model-selector'),task:count(mounted.element,'workbench-task-card')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"skill": 1, "model": 1, "task": 1})

    def test_skill_selector_keeps_honest_placeholder_without_registry(self):
        output = self.run_node("""
const state={nodeId:'task-5',title:'Task',status:'ready',inputs:[],skillBinding:{skill_id:'brand.copy',version:'1.0.0',enabled:true},outputMode:'text'};
const task={state:()=>state,update:patch=>Object.assign(state,patch)};
sandbox.window.WorkbenchTaskCardPresentation.create({task,document:documentRef}).mount(host);
const select=find(host,'workbench-task-card__skill-selector-select');
console.log(JSON.stringify({disabled:select.disabled,label:select.children[0].textContent}));
""")
        self.assertEqual(json.loads(output), {"disabled": True, "label": "brand.copy · 等待 Skill Registry"})

    def test_production_renderer_reuses_canonical_registry_aliases_without_creating_owners(self):
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("window.WorkbenchRuntimeRegistries || window.WorkbenchRegistries", editor)
        self.assertIn("window.WorkbenchTaskSkillRegistry", editor)
        self.assertIn("window.WorkbenchSkillRegistry", editor)
        self.assertIn("window.WorkbenchModelAvailabilityRegistry", editor)
        self.assertIn("listForModel", editor)
        self.assertNotIn("new SkillRegistry", editor)
        self.assertNotIn("new ModelAvailability", editor)

    def test_production_wiring_uses_shared_shell_and_existing_save_boundary(self):
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("taskPresentationOptions", editor)
        self.assertIn("storage: null", editor)
        self.assertIn("scheduleSave();", editor)
        self.assertIn("data-task-card-presentation-host", shell)
        self.assertIn("mountTaskPresentation", shell)
        self.assertIn("taskRichNodeOptions", host)
        self.assertIn("const taskCandidate = resolvedRendererOptions.taskNode || node", host)
        self.assertIn("modelSelectorOptions,", host)
        self.assertIn("skillSelectorOptions: resolvedRendererOptions.skillSelectorOptions", host)
        self.assertIn("taskPresentationOptions", host)
        self.assertIn("mountModelSelector,", (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8"))
        self.assertIn("WorkbenchTaskSkillRegistry", editor)
        self.assertIn("modelAvailabilities", editor)
        self.assertLess(page.index("task-rich-node.js"), page.index("task-card-presentation.js"))
        self.assertLess(page.index("task-card-presentation.js"), page.index("node-shell.js"))

    def test_inline_task_presentation_is_the_single_selector_owner(self):
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("const inlineTaskPresentation = Boolean(taskRichNode && settings.taskPresentationOptions)", shell)
        self.assertIn("settings.skillSelectorOptions && !inlineTaskPresentation", shell)
        self.assertIn("settings.modelSelectorOptions && !inlineTaskPresentation", shell)


if __name__ == "__main__":
    unittest.main()
