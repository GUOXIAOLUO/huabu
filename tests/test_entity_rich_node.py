import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EntityRichNodeTests(unittest.TestCase):
    def test_definition_driven_fields_relations_and_version_aware_edit_intent(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/entity-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const makeElement = tag => {{
  const el={{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},textContent:'',value:'',className:'',
    append(...items){{this.children.push(...items);}}, replaceChildren(...items){{this.children=items;}},
    addEventListener(type,cb){{(this.listeners[type]=this.listeners[type]||[]).push(cb);}},
    setAttribute(name,value){{this['attr_'+name]=String(value);}}, remove(){{this.removed=true;}}}};
  return el;
}};
const documentRef={{createElement:makeElement}};
const sandbox={{window:{{document:documentRef}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
let edits=[];
const node={{id:'node-1',kind:'entity',title:'Generic record',entity_record:{{id:'entity-1',current_version_id:'v-3',current_version:{{id:'v-3',payload:{{properties:{{name:'Desk',count:2,active:true}}}}}}}},entity_definition:{{id:'furniture',version:'2',schema:{{properties:[{{key:'name',label:'Name',type:'string'}},{{key:'count',label:'Count',type:'number'}},{{key:'active',label:'Active',type:'boolean'}}]}}}},relations:[{{id:'rel-1',relation_type:'belongs_to',to:{{resource_type:'project',resource_id:'p-1'}}}}]}};
const rich=sandbox.window.WorkbenchEntityRichNode.create({{node,onEdit:e=>edits.push(e)}});
const shell={{contentHost:documentRef.createElement('section'),entityRichNode:rich}};
const mounted=sandbox.window.WorkbenchEntityRichNode.mount(shell,node,{{document:documentRef,richNode:rich}});
const fieldKeys=mounted.element.children.find(item=>item.className==='workbench-entity-rich-node__fields').children.filter(item=>item.tagName==='DT').map(item=>item.dataset.fieldKey);
const relationText=mounted.element.children.find(item=>item.className==='workbench-entity-rich-node__relations').children[1].children[0].textContent;
rich.transition('inspector'); mounted.element.children[2].listeners.click?.[0]?.({{stopPropagation(){{}}}});
const inspector=sandbox.window.WorkbenchEntityRichNode.mount(shell,node,{{document:documentRef,richNode:rich}});
const input=Array.from(inspector.element.children.find(item=>item.className==='workbench-entity-rich-node__fields').children).map(item=>item.children[0]).find(item=>item?.dataset?.fieldKey==='count');
input.value='3'; input.listeners.change[0]({{target:input}});
console.log(JSON.stringify({{compatible:sandbox.window.WorkbenchEntityRichNode.compatible(node),fieldKeys,relationText,version:rich.snapshot().versionId,edit:edits[0],inputMode:input.tagName}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["compatible"])
        self.assertEqual(payload["fieldKeys"], ["name", "count", "active"])
        self.assertEqual(payload["relationText"], "belongs_to · p-1")
        self.assertEqual(payload["version"], "v-3")
        self.assertEqual(payload["edit"], {
            "entityId": "entity-1", "baseVersionId": "v-3", "definitionId": "furniture",
            "definitionVersion": "2", "property": "count", "value": "3",
        })
        self.assertEqual(payload["inputMode"], "INPUT")

    def test_entity_renderer_is_registered_in_unified_canvas_without_domain_hardcoding(self):
        module = ROOT / "static/js/workbench/canvas/entity-rich-node.js"
        source = module.read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertNotIn("WholeHouse", source)
        self.assertNotIn("customer", source.lower())
        self.assertNotIn("room", source.lower())
        self.assertNotIn("fetch(", source)
        self.assertIn("id: 'entity-rich'", host)
        self.assertIn("WorkbenchEntityRichNode.mount", host)
        self.assertIn("type: 'entity_edit'", host)
        self.assertIn("settings.onIntent({type: 'entity_edit'", host)
        self.assertIn("WorkbenchEntityRichNode.create", shell)
        self.assertIn("entity-rich-node.js", page)


if __name__ == "__main__":
    unittest.main()
