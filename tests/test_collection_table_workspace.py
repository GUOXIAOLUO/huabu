import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CollectionTableWorkspaceTests(unittest.TestCase):
    def test_table_edits_use_typed_cells_and_workspace_dirty_save_lifecycle(self):
        module = ROOT / "static/js/workbench/canvas/collection-table-workspace.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const saved=[], changes=[]; let dirty=0, saves=0;
const session={{markDirty:()=>dirty++,save:()=>saves++}};
const node={{id:'collection-node',type:'collection',collection:{{schema:{{columns:[
  {{id:'name',key:'name',label:'Name',value_type:'literal'}},
  {{id:'asset',key:'asset',label:'Asset',value_type:'asset_version'}}
]}},items:[
  {{id:'row-2',order:2,values:{{name:{{type:'literal',value:'Second'}},asset:{{type:'reference',reference_type:'asset_version',reference_id:'asset-2',metadata:{{label:'Keep'}}}}}}}},
  {{id:'row-1',order:1,values:{{name:{{type:'literal',value:'First'}},asset:{{type:'reference',reference_type:'asset_version',reference_id:'asset-1'}}}}}}
]}}}};
const before=JSON.stringify(node.collection);
const workspace=sandbox.window.WorkbenchCollectionTableWorkspace.create({{node,session,onChange:state=>changes.push(state.dirty),persist:collection=>{{saved.push(collection); return {{...collection,revision:(collection.revision||1)+1}}; }}}});
workspace.setCell('row-1','name','Updated');
workspace.setCell('row-1','asset',{{type:'reference',reference_type:'asset_version',reference_id:'asset-9'}});
workspace.addRow({{id:'row-3',values:{{name:'Third'}}}});
workspace.addColumn({{id:'note',key:'note',label:'Note',value_type:'literal'}});
workspace.setCell('row-3','note','New');
const filtered=workspace.setFilter('updated');
workspace.setFilter('');
const sorted=workspace.sortBy('name','desc');
const savedState=workspace.save();
workspace.setCell('row-1','name','Saved twice');
const savedAgain=workspace.save();
const noPersistence=sandbox.window.WorkbenchCollectionTableWorkspace.create({{node,session}});
noPersistence.setCell('row-1','name','Unsaved');
let noBoundaryError='';
try {{ noPersistence.save(); }} catch(error) {{ noBoundaryError=error.message; }}
console.log(JSON.stringify({{dirty,saves,saved:saved.length,changes,filtered:filtered.rows.map(row=>row.id),sorted:sorted.rows.map(row=>row.id),savedName:saved[0].items.find(row=>row.id==='row-1').values.name.value,savedAgainName:savedAgain.collection.items.find(row=>row.id==='row-1').values.name.value,savedRevision:savedAgain.collection.revision,savedRef:saved[0].items.find(row=>row.id==='row-1').values.asset.reference_id,refType:saved[0].items.find(row=>row.id==='row-1').values.asset.type,unchanged:JSON.stringify(node.collection)===before,clean:!savedState.dirty,noBoundaryError,noBoundaryDirty:noPersistence.snapshot().dirty}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "dirty": 7, "saves": 2, "saved": 2,
            "changes": [True, True, True, True, True, False, True, False],
            "filtered": ["row-1"], "sorted": ["row-1", "row-3", "row-2"],
            "savedName": "Updated", "savedRef": "asset-9", "refType": "reference",
            "savedAgainName": "Saved twice", "savedRevision": 3,
            "unchanged": True, "clean": True,
            "noBoundaryError": "collection workspace persistence is unavailable", "noBoundaryDirty": True,
        })

    def test_table_workspace_mounts_as_collection_rich_node_workspace(self):
        canvas_dir = ROOT / "static/js/workbench/canvas"
        modules = [
            canvas_dir / "presentation-state.js",
            canvas_dir / "collection-table-workspace.js",
            canvas_dir / "collection-rich-node.js",
        ]
        module_loads = "\n".join(
            f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))}, 'utf8'), sandbox);"
            for path in modules
        )
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',
  append(...items){{this.children.push(...items);}},appendChild(item){{this.children.push(item);}},replaceChildren(...items){{this.children=items; }},
  setAttribute(name,value){{this.dataset['attr-'+name]=String(value);}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{this.removed=true;}} }}; }}
const documentRef={{createElement:element}};
const sandbox={{window:{{document:documentRef}},document:documentRef}};
{module_loads}
const node={{id:'table-node',type:'collection',collection:{{schema:{{columns:[{{id:'name',key:'name',label:'Name',value_type:'literal'}}]}},items:[{{id:'row-1',order:1,values:{{name:{{type:'literal',value:'Hello'}}}}}}]}}}};
const shell={{contentHost:element('section')}};
const rich=sandbox.window.WorkbenchCollectionRichNode.create({{node,presentation:sandbox.window.WorkbenchPresentationState.create({{initial:'workspace'}})}});
const mounted=sandbox.window.WorkbenchCollectionRichNode.mount(shell,node,{{richNode:rich,document:documentRef}});
console.log(JSON.stringify({{className:mounted.element.className,table:mounted.element.children[1].tagName,headers:mounted.element.children[1].children[0].children[0].children.length,inputs:mounted.element.children[1].children[1].children[0].children.length}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"className": "workbench-collection-table-workspace", "table": "TABLE", "headers": 1, "inputs": 1})

    def test_gallery_workspace_entry_opens_canvas_session_before_table_editing(self):
        canvas_dir = ROOT / "static/js/workbench/canvas"
        modules = [canvas_dir / "presentation-state.js", canvas_dir / "collection-table-workspace.js", canvas_dir / "collection-rich-node.js"]
        module_loads = "\n".join(f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))},'utf8'),sandbox);" for path in modules)
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',
  append(...items){{this.children.push(...items);}},appendChild(item){{this.children.push(item);}},replaceChildren(...items){{this.children=items; }},
  setAttribute(name,value){{this.dataset['attr-'+name]=String(value);}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{}} }}; }}
const documentRef={{createElement:element}}; let opened=0;
const session={{openFromSelection:id=>{{if(id==='table-node') opened++;}}}};
const sandbox={{window:{{document:documentRef}},document:documentRef}};
{module_loads}
const node={{id:'table-node',type:'collection',collection:{{schema:{{columns:[]}},items:[]}}}};
const shell={{contentHost:element('section')}};
const rich=sandbox.window.WorkbenchCollectionRichNode.create({{node,workspaceSession:session,presentation:sandbox.window.WorkbenchPresentationState.create({{initial:'card'}})}});
sandbox.window.WorkbenchCollectionRichNode.mount(shell,node,{{richNode:rich,document:documentRef,workspaceSession:session}});
const controls=shell.contentHost.children[0].children.find(child=>child.children?.some(item=>item.dataset.presentation==='workspace'));
const workspaceButton=controls.children.find(item=>item.dataset.presentation==='workspace');
workspaceButton.listeners.click[0]({{stopPropagation(){{}}}});
console.log(JSON.stringify({{opened,table:shell.contentHost.children[0].className}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"opened": 1, "table": "workbench-collection-table-workspace"})

    def test_mounted_workspace_actions_add_rows_columns_and_save_through_boundary(self):
        module = ROOT / "static/js/workbench/canvas/collection-table-workspace.js"
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',
  append(...items){{this.children.push(...items);}},appendChild(item){{this.children.push(item);}},replaceChildren(...items){{this.children=items; }},
  setAttribute(name,value){{this.dataset['attr-'+name]=String(value);}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{}} }}; }}
const documentRef={{createElement:element}}, sandbox={{window:{{document:documentRef}},document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const host=element('section'), saved=[];
const node={{id:'table-node',type:'collection',collection:{{schema:{{columns:[{{id:'name',key:'name',label:'Name',value_type:'literal'}}]}},items:[{{id:'row-1',order:1,values:{{name:{{type:'literal',value:'Before'}}}}}}]}}}};
const workspace=sandbox.window.WorkbenchCollectionTableWorkspace.create({{node,persist:collection=>{{saved.push(collection);return collection;}}}});
sandbox.window.WorkbenchCollectionTableWorkspace.mount(host,workspace,{{document:documentRef}});
const actions=Object.fromEntries(host.children[0].children[0].children.filter(item=>item.dataset.action).map(item=>[item.dataset.action,item]));
actions['add-row'].listeners.click[0]({{preventDefault(){{}}}});
actions['add-column'].listeners.click[0]({{preventDefault(){{}}}});
workspace.setCell('row-1','name','After');
actions.save.listeners.click[0]({{preventDefault(){{}}}});
Promise.resolve().then(()=>console.log(JSON.stringify({{rows:workspace.snapshot().collection.items.length,columns:workspace.snapshot().collection.schema.columns.length,saved:saved.length,value:saved[0].items[0].values.name.value,dirty:workspace.snapshot().dirty}})));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"rows": 2, "columns": 2, "saved": 1, "value": "After", "dirty": False})

    def test_collection_api_client_uses_versioned_application_save_boundary(self):
        module = ROOT / "static/js/workbench/canvas/collection-api-client.js"
        script = f"""
const fs=require('fs'),vm=require('vm');
const requests=[];
const response={{ok:true,status:200,json:async()=>({{id:'collection-1',revision:2}})}};
const sandbox={{window:{{fetch:async (url,options)=>{{requests.push({{url,options}});return response;}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
sandbox.window.WorkbenchCollectionApiClient.update({{id:'collection-1',revision:1,name:'Rows',schema:{{columns:[]}},items:[],default_view:{{}},metadata:{{}}}},{{actorId:'canvas-user'}}).then(result=>console.log(JSON.stringify({{result,request:requests[0]}})));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], {"id": "collection-1", "revision": 2})
        self.assertEqual(payload["request"]["url"], "/api/v1/collections/collection-1")
        self.assertEqual(payload["request"]["options"]["method"], "PUT")
        self.assertEqual(payload["request"]["options"]["headers"]["X-User-ID"], "canvas-user")
        self.assertEqual(json.loads(payload["request"]["options"]["body"])["expected_revision"], 1)

    def test_binding_table_projects_each_ordered_row_to_typed_input_bindings(self):
        binding = ROOT / "static/js/workbench/canvas/binding-table.js"
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(binding))},'utf8'),sandbox);
const collection={{schema:{{columns:[
  {{id:'image',key:'image',label:'Image',value_type:'asset_version',required:true,metadata:{{input_role:'reference',input_target:'image'}}}},
  {{id:'prompt',key:'prompt',label:'Prompt',value_type:'literal',required:true,metadata:{{input_role:'prompt'}}}}
]}},items:[
  {{id:'row-2',order:2,values:{{image:{{type:'reference',reference_type:'asset_version',reference_id:'asset-2'}},prompt:{{type:'literal',value:'Second'}}}}}},
  {{id:'row-1',order:1,values:{{image:{{type:'reference',reference_type:'asset_version',reference_id:'asset-1'}},prompt:{{type:'literal',value:'First'}}}}}},
  {{id:'row-3',order:3,values:{{image:{{type:'reference',reference_type:'asset_version',reference_id:'asset-3'}}}}}}
]}};
const result=sandbox.window.WorkbenchBindingTable.projectCollection(collection);
console.log(JSON.stringify({{valid:result.valid,rows:result.rows.map(row=>({{rowId:row.rowId,valid:row.valid,missing:row.missingRequired,bindings:row.bindings}})),flat:result.bindings.map(binding=>[binding.id,binding.target,binding.role,binding.source_type,binding.source_ref,binding.order])}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertEqual([row["rowId"] for row in payload["rows"]], ["row-1", "row-2", "row-3"])
        self.assertEqual(payload["rows"][2]["missing"], ["prompt"])
        self.assertEqual(payload["flat"][:2], [
            ["row-1:image", "image", "reference", "asset_version", "asset-1", 0],
            ["row-1:prompt", "prompt", "prompt", "literal", '"First"', 1],
        ])

    def test_collection_table_workspace_exposes_binding_projection_and_required_validation(self):
        canvas_dir = ROOT / "static/js/workbench/canvas"
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(canvas_dir / 'binding-table.js'))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(canvas_dir / 'collection-table-workspace.js'))},'utf8'),sandbox);
const node={{id:'binding-node',type:'collection',collection:{{schema:{{columns:[{{id:'input',key:'input',label:'Input',value_type:'asset_version',required:true}}]}},items:[{{id:'row-1',order:1,values:{{}}}}]}}}};
const workspace=sandbox.window.WorkbenchCollectionTableWorkspace.create({{node}});
console.log(JSON.stringify({{projection:workspace.bindingProjection(),row:workspace.rowBindings('row-1')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["projection"]["valid"])
        self.assertEqual(payload["row"]["missingRequired"], ["input"])
        self.assertEqual(payload["row"]["bindings"], [])

    def test_table_rows_share_selection_state_without_mutating_collection(self):
        module = ROOT / "static/js/workbench/canvas/collection-table-workspace.js"
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',
  append(...items){{this.children.push(...items);}},replaceChildren(...items){{this.children=items; }},setAttribute(name,value){{this.dataset['attr-'+name]=String(value);}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{}} }}; }}
const documentRef={{createElement:element}},sandbox={{window:{{document:documentRef}},document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'selectable',type:'collection',collection:{{schema:{{columns:[{{id:'prompt',key:'prompt',label:'Prompt',value_type:'literal'}}]}},items:[
  {{id:'row-1',order:1,values:{{prompt:{{type:'literal',value:'one'}}}}}},{{id:'row-2',order:2,values:{{prompt:{{type:'literal',value:'two'}}}}}}
]}}}};
let selected=''; const workspace=sandbox.window.WorkbenchCollectionTableWorkspace.create({{node,onSelectRow:id=>selected=id}});
const host=element('section'); const mounted=sandbox.window.WorkbenchCollectionTableWorkspace.mount(host,workspace,{{document:documentRef}});
const rows=mounted.element.children[1].children[1].children; rows[1].listeners.click[0]();
const rerenderedRows=mounted.element.children[1].children[1].children;
console.log(JSON.stringify({{selected,selectedRowId:workspace.snapshot().selectedRowId,selectedClass:rerenderedRows[1].className,ariaSelected:rerenderedRows[1].dataset['attr-aria-selected'],unchanged:node.collection.items[1].values.prompt.value==='two'}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"selected": "row-2", "selectedRowId": "row-2", "selectedClass": "is-selected", "ariaSelected": "true", "unchanged": True})

    def test_binding_table_rejects_reference_type_mismatch(self):
        binding = ROOT / "static/js/workbench/canvas/binding-table.js"
        script = f"""
const fs=require('fs'),vm=require('vm'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(binding))},'utf8'),sandbox);
const row={{id:'row-1',values:{{asset:{{type:'reference',reference_type:'artifact_version',reference_id:'wrong-type'}}}}}};
console.log(JSON.stringify(sandbox.window.WorkbenchBindingTable.projectRow(row,{{columns:[{{key:'asset',value_type:'asset_version',required:true}}]}})));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["invalidCells"], ["asset"])
        self.assertEqual(payload["bindings"], [])


if __name__ == "__main__":
    unittest.main()
