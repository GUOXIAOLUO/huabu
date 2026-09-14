import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CollectionRichNodeTests(unittest.TestCase):
    def test_gallery_filters_mixed_visual_references_and_reloads_presentation(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/collection-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'collection-node',kind:'collection',title:'Moodboard',config:{{collection:{{schema:{{columns:[{{key:'cover',label:'Cover'}},{{key:'audio',label:'Audio'}}]}},items:[
  {{id:'second',order:2,values:{{cover:{{type:'reference',reference_type:'artifact_version',reference_id:'video-2'}},audio:{{type:'reference',reference_type:'asset_version',reference_id:'audio-1'}}}}}},
  {{id:'first',order:1,values:{{cover:{{type:'reference',reference_type:'asset_version',reference_id:'image-1'}},audio:{{type:'reference',reference_type:'asset_version',reference_id:'missing'}}}}}}
]}}}}}};
const resolve=(type,id)=>({{'image-1':{{url:'/assets/one.png',kind:'image'}},'video-2':{{url:'/output/two.mp4',kind:'video'}},'audio-1':{{url:'/assets/sound.mp3',kind:'audio'}}}})[id]||null;
let selected='', opened='';
const rich=sandbox.window.WorkbenchCollectionRichNode.create({{node,storage,resolveReference:resolve,onSelect:item=>selected=item.itemId,onOpen:item=>opened=item.itemId}});
const items=rich.snapshot().items;
const presentations=['expanded','workspace','inspector','card','workspace'].map(state=>rich.transition(state).presentation);
rich.select('second'); rich.open('second');
const reload=sandbox.window.WorkbenchCollectionRichNode.create({{node,storage,resolveReference:resolve}}).snapshot();
console.log(JSON.stringify({{compatible:sandbox.window.WorkbenchCollectionRichNode.isCompatible(node),items,selected,opened,presentations,presentation:reload.presentation,reloadItems:reload.items}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["compatible"])
        self.assertEqual([(item["itemId"], item["kind"]) for item in payload["items"]], [("first", "image"), ("second", "video")])
        self.assertEqual(payload["presentations"], ["expanded", "workspace", "inspector", "card", "workspace"])
        self.assertEqual((payload["selected"], payload["opened"], payload["presentation"]), ("second", "second", "workspace"))
        self.assertEqual(payload["reloadItems"], payload["items"])

    def test_canonical_reference_metadata_projects_without_page_resolver(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/collection-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'canonical-collection',type:'collection',collection:{{schema:{{columns:[{{key:'media',label:'Media'}}]}},items:[
  {{id:'image-row',order:1,values:{{media:{{type:'reference',reference_type:'asset_version',reference_id:'asset-1',metadata:{{url:'/assets/asset-1.png',kind:'image',name:'Asset 1'}}}}}}}},
  {{id:'video-row',order:2,values:{{media:{{type:'reference',reference_type:'artifact_version',reference_id:'artifact-1',metadata:{{url:'/output/artifact-1.mp4',kind:'video',name:'Artifact 1'}}}}}}}}
]}}}};
const rich=sandbox.window.WorkbenchCollectionRichNode.create({{node}});
console.log(JSON.stringify(rich.snapshot().items));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([(item["itemId"], item["kind"], item["url"]) for item in json.loads(result.stdout)], [
            ("image-row", "image", "/assets/asset-1.png"),
            ("video-row", "video", "/output/artifact-1.mp4"),
        ])

    def test_collection_grid_list_switch_persists_view_without_mutating_collection(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/collection-rich-node.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'view-collection',type:'collection',title:'Views',collection:{{schema:{{columns:[{{key:'media',label:'Media'}}]}},items:[
  {{id:'second',order:2,values:{{media:{{type:'reference',reference_type:'asset_version',reference_id:'asset-2',metadata:{{url:'/two.png',kind:'image'}}}}}}}},
  {{id:'first',order:1,values:{{media:{{type:'reference',reference_type:'asset_version',reference_id:'asset-1',metadata:{{url:'/one.png',kind:'image'}}}}}}}}
]}}}};
const before=JSON.stringify(node.collection);
const first=sandbox.window.WorkbenchCollectionRichNode.create({{node,storage}});
const switched=first.setViewMode('list');
const reload=sandbox.window.WorkbenchCollectionRichNode.create({{node,storage}}).snapshot();
console.log(JSON.stringify({{view:switched.viewMode,reloadedView:reload.viewMode,items:reload.items.map(item=>item.itemId),unchanged:JSON.stringify(node.collection)===before}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "view": "list",
            "reloadedView": "list",
            "items": ["first", "second"],
            "unchanged": True,
        })

    def test_gallery_exposes_compact_collection_summary_for_mixed_table(self):
        presentation = ROOT / "static/js/workbench/canvas/presentation-state.js"
        module = ROOT / "static/js/workbench/canvas/collection-rich-node.js"
        script = f"""
const fs=require('fs'),vm=require('vm');
function element(tag) {{ return {{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',textContent:'',
  append(...items){{this.children.push(...items);}},replaceChildren(...items){{this.children=items; }},setAttribute(){{}},addEventListener(type,callback){{(this.listeners[type]||(this.listeners[type]=[])).push(callback);}},remove(){{}} }}; }}
const documentRef={{createElement:element}},sandbox={{window:{{document:documentRef}},document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const node={{id:'mixed-table',type:'collection',title:'Campaign inputs',collection:{{schema:{{columns:[
  {{id:'image',key:'image',label:'Image',value_type:'asset_version'}},{{id:'prompt',key:'prompt',label:'Prompt',value_type:'literal'}}
]}},items:[{{id:'row-1',order:1,values:{{image:{{type:'reference',reference_type:'asset_version',reference_id:'a1',metadata:{{url:'/a.png',kind:'image'}}}},prompt:{{type:'literal',value:'A prompt'}}}}}}]}}}};
const shell={{contentHost:element('section')}};
const mounted=sandbox.window.WorkbenchCollectionRichNode.mount(shell,node,{{document:documentRef}});
const summary=mounted.element.children.find(child=>child.className==='workbench-collection-gallery__summary');
console.log(JSON.stringify({{title:summary.children[0].textContent,meta:summary.children[1].textContent,fields:summary.children[2].textContent}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"title": "Campaign inputs", "meta": "1 rows · 2 fields", "fields": "Image · Prompt"})

    def test_collection_gallery_is_registered_and_integrated_with_node_shell(self):
        module = (ROOT / "static/js/workbench/canvas/collection-rich-node.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        adapter = (ROOT / "static/js/workbench/canvas/collection-gallery-canvas-adapter.js").read_text(encoding="utf-8")
        css = (ROOT / "static/css/canvas.css").read_text(encoding="utf-8")
        presentation = (ROOT / "static/js/workbench/canvas/node-presentation.js").read_text(encoding="utf-8")
        self.assertNotIn("registry.register", module)
        self.assertIn("id: 'collection-gallery'", host)
        self.assertIn("WorkbenchCollectionRichNode", host)
        self.assertIn("collectionRichNode", shell)
        self.assertIn("collection-rich-node.js", page)
        self.assertIn("collection-gallery-canvas-adapter.js", page)
        self.assertIn("WorkbenchCollectionGalleryCanvasAdapter", adapter)
        self.assertIn("node?.type === 'collection'", editor)
        self.assertIn("canvasCollectionRendererOptions(node)", editor)
        self.assertIn("storage:localStorage", editor)
        self.assertIn("storage:viewStorage", adapter)
        self.assertIn("viewStorageKey", adapter)
        self.assertIn(".node.node-shell-mounted .workbench-collection-gallery.workbench-collection-gallery--list", css)
        self.assertIn(".node.node-shell-mounted .workbench-collection-gallery--list .workbench-collection-gallery__media", css)
        self.assertIn("if(!collectionGallery && !window.WorkbenchMediaRenderer.canRender(record))", editor)
        self.assertIn("collection: [320, 260]", presentation)

    def test_canvas_media_editor_collection_entry_passes_adapter_options_to_shared_mount(self):
        canvas_dir = ROOT / "static/js/workbench/canvas"
        rich_node = canvas_dir / "collection-rich-node.js"
        adapter = canvas_dir / "collection-gallery-canvas-adapter.js"
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const calls=[];
const selected=new Set();
const fakeDocument={{}};
const node={{id:'production-collection',type:'collection',collection:{{schema:{{columns:[]}},items:[]}}}};
const sandbox={{console,document:fakeDocument,localStorage:storage,canvas:null,nodes:[node],selected:new Set(),handleCanvasNodeShellIntent:()=>{{}},
  WorkbenchCollectionRichNode:null,WorkbenchCollectionGalleryCanvasAdapter:null,
  WorkbenchCollectionApiClient:{{update:()=>Promise.resolve({{}})}},
  ensureCanvasWorkspaceSession:()=>({{id:'canvas-session'}}),
  WorkbenchMediaRenderer:{{canRender:()=>false}},WorkbenchNodeShell:{{}},
  WorkbenchNodeClient:{{isLoopback:()=>true}},
  WorkbenchCanvas:{{legacyNodeView:candidate=>candidate}},
  WorkbenchRenderRuntime:{{create:()=>({{mount:options=>{{calls.push(options);return {{shell:{{}}}};}}}})}},
  WorkbenchUnifiedRenderHost:{{createIntentAdapter:()=>()=>{{}},cardShellView:()=>({{}})}},
  addEventListener:()=>{{}},
  addVersionedBlankImageNode:()=>{{}},addVersionedBlankPromptNode:()=>{{}},
  addVersionedBlankLoopNode:()=>{{}},addVersionedBlankGroupNode:()=>{{}},
  addVersionedBlankOutputNode:()=>{{}},
  outputUrlValue:value=>typeof value === 'string' ? value : value?.url || '',
  mediaKindForOutputItem:item=>item?.kind || 'image',
  outputImageName:url=>String(url).split('/').pop(),
  openOutputLightbox:()=>{{}},
}};
sandbox.window=sandbox;
sandbox.node=node;
sandbox.calls=calls;
vm.runInNewContext(fs.readFileSync({json.dumps(str(rich_node))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(adapter))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT / 'static/js/workbench/canvas/canvas-app-media-editor.js'))},'utf8'),sandbox);
vm.runInNewContext(`const mounted=mountCanvasNodeShellForMedia(node,{{}},{{}});
const rendererOptions=calls[0].rendererOptions;
console.log(JSON.stringify({{mounted,calls:calls.length,hasStorage:rendererOptions.storage===localStorage,viewStorageKey:rendererOptions.viewStorageKey,hasPersistCollection:typeof rendererOptions.persistCollection==='function',workspaceSession:rendererOptions.workspaceSession?.id}}));`,sandbox);
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "mounted": True,
            "calls": 1,
            "hasStorage": True,
            "viewStorageKey": "workbench.collection.view:production-collection",
            "hasPersistCollection": True,
            "workspaceSession": "canvas-session",
        })

    def test_collection_gallery_mounts_through_real_registry_with_resolver_and_intents(self):
        canvas_dir = ROOT / "static/js/workbench/canvas"
        modules = [
            canvas_dir / "presentation-state.js",
            canvas_dir / "collection-rich-node.js",
            canvas_dir / "node-shell.js",
            canvas_dir / "renderer-registry.js",
            canvas_dir / "node-card-host.js",
            canvas_dir / "collection-gallery-canvas-adapter.js",
        ]
        module_loads = "\n".join(
            f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))}, 'utf8'), sandbox);"
            for path in modules
        )
        script = """
const fs=require('fs'), vm=require('vm');
function makeClassList(element) {
  return {
    add(...names) { names.forEach(name => { if (name && !element.className.split(/\\s+/).includes(name)) element.className += ` ${name}`; }); },
    remove(...names) { element.className = element.className.split(/\\s+/).filter(name => name && !names.includes(name)).join(' '); },
    toggle(name, force) { if (force === false) this.remove(name); else if (force === true || !element.className.split(/\\s+/).includes(name)) this.add(name); else this.remove(name); },
  };
}
const fakeDocument = {createElement(tag) {
  const element = {
    tagName: tag.toUpperCase(), children: [], dataset: {}, listeners: {}, className: '',
    textContent: '', type: '', src: '', alt: '', controls: false, preload: '', playsInline: false,
    append(...children) { this.children.push(...children); },
    appendChild(child) { this.children.push(child); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this.dataset[`attr-${name}`] = String(value); },
    addEventListener(type, callback) { (this.listeners[type] = this.listeners[type] || []).push(callback); },
    querySelector() { return null; }, querySelectorAll() { return []; },
    remove() { this.removed = true; },
  };
  element.classList = makeClassList(element);
  return element;
}};
const values={}; const storage={getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value};
const sandbox={window:{document:fakeDocument,WorkbenchCanvas:{STATES:['ready']}}};
__MODULES__
const node={id:'collection-node',kind:'collection',title:'Gallery',state:'ready',collection:{schema:{columns:[{key:'cover',label:'Cover'}]},items:[
  {id:'first',order:1,values:{cover:{type:'reference',reference_type:'asset_version',reference_id:'asset-1'}}},
  {id:'second',order:2,values:{cover:{type:'reference',reference_type:'artifact_version',reference_id:'artifact-2'}}},
]}};
const resolved={
  'asset_version:asset-1':{url:'/assets/one.png',kind:'image',name:'One'},
  'artifact_version:artifact-2':{url:'/output/two.mp4',kind:'video',name:'Two'},
};
let resolveCalls=0, selected='', opened='';
const adapter=sandbox.window.WorkbenchCollectionGalleryCanvasAdapter.create({
  storage,
  getNodes:()=>[],
  resolveReference:(type,id)=>{ resolveCalls += 1; return resolved[`${type}:${id}`] || null; },
  openOutputLightbox:()=>{},
  onSelect:item=>selected=item.itemId,
  onOpen:item=>opened=item.itemId,
});
const mountOptions=()=>({
  ...adapter.optionsFor(node),
});
const mounted=sandbox.window.WorkbenchNodeCardHost.mount({
  node,document:fakeDocument,viewState:{presentation:'expanded'},
  rendererOptions:mountOptions(),
});
const gallery=mounted.shell.contentHost.children[0];
const initialResolveCalls=resolveCalls;
const firstTile=gallery.children.find(tile=>tile.dataset.itemId==='first');
firstTile.listeners.click[0]({stopPropagation(){}});
firstTile.listeners.dblclick[0]({stopPropagation(){}});
let viewControls=gallery.children[gallery.children.length-1];
viewControls.children[1].listeners.click[0]({stopPropagation(){}});
viewControls=gallery.children[gallery.children.length-1];
const listTileOrder=gallery.children.filter(tile=>tile.dataset.itemId).map(tile=>tile.dataset.itemId);
const selectedAfterList=gallery.children.filter(tile=>tile.dataset.itemId && tile.className.includes('is-selected')).map(tile=>tile.dataset.itemId);
const viewModeAfterList=gallery.dataset.viewMode;
mounted.destroy();
const reloaded=sandbox.window.WorkbenchNodeCardHost.mount({
  node,document:fakeDocument,viewState:{presentation:'expanded'},rendererOptions:mountOptions(),
});
const reloadedGallery=reloaded.shell.contentHost.children[0];
const reloadedView=reloadedGallery.dataset.viewMode;
const reloadedTileOrder=reloadedGallery.children.filter(tile=>tile.dataset.itemId).map(tile=>tile.dataset.itemId);
const reloadedSelected=reloadedGallery.children.filter(tile=>tile.dataset.itemId && tile.className.includes('is-selected')).map(tile=>tile.dataset.itemId);
const reloadedControls=reloadedGallery.children[reloadedGallery.children.length-1];
reloadedControls.children[0].listeners.click[0]({stopPropagation(){}});
const reloadedViewAfterGrid=reloadedGallery.dataset.viewMode;
reloaded.destroy();
viewControls.children[0].listeners.click[0]({stopPropagation(){}});
const gridTileOrder=gallery.children.filter(tile=>tile.dataset.itemId).map(tile=>tile.dataset.itemId);
const selectedAfterGrid=gallery.children.filter(tile=>tile.dataset.itemId && tile.className.includes('is-selected')).map(tile=>tile.dataset.itemId);
console.log(JSON.stringify({
  rendererId:mounted.renderer.id,
  presentation:mounted.shell.presentationState(),
  viewMode:viewModeAfterList,
  viewControls:viewControls.children.map(control=>[control.dataset.viewMode || control.dataset.presentation,control.dataset['attr-aria-pressed']]),
  tileTags:gallery.children.filter(tile=>tile.dataset.itemId).map(tile=>tile.children[0].tagName),
  listTileOrder,gridTileOrder,selectedAfterList,selectedAfterGrid,
  reloadedView,reloadedViewAfterGrid,reloadedTileOrder,reloadedSelected,
  initialResolveCalls,selected,opened,
}));
""".replace("__MODULES__", module_loads)
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "rendererId": "collection-gallery",
            "presentation": "expanded",
            "viewMode": "list",
            "viewControls": [["grid", "false"], ["list", "true"], ["workspace", None]],
            "tileTags": ["IMG", "VIDEO"],
            "listTileOrder": ["first", "second"],
            "gridTileOrder": ["first", "second"],
            "selectedAfterList": ["first"],
            "selectedAfterGrid": ["first"],
            "reloadedView": "list",
            "reloadedViewAfterGrid": "grid",
            "reloadedTileOrder": ["first", "second"],
            "reloadedSelected": ["first"],
            "initialResolveCalls": 2,
            "selected": "first",
            "opened": "first",
        })

    def test_canvas_collection_adapter_resolves_standalone_references_and_opens_media(self):
        adapter = ROOT / "static/js/workbench/canvas/collection-gallery-canvas-adapter.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const nodes=[{{id:'image-owner',type:'image',url:'/mirrored.png',output_refs:[{{type:'asset_version',id:'mirrored-1'}}]}}];
const opened=[];
const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(adapter))},'utf8'),sandbox);
const canvasNode={{id:'collection-node',type:'collection',collection:{{metadata:{{resolved_references:{{
  'asset_version:standalone-1':{{url:'/standalone.png',kind:'image',name:'Standalone'}},
  'artifact_version:standalone-2':{{url:'/standalone.mp4',kind:'video',name:'Clip'}}
}}}}}}}};
const adapterInstance=sandbox.window.WorkbenchCollectionGalleryCanvasAdapter.create({{
  getNodes:()=>nodes,
  openOutputLightbox:(url,source)=>opened.push([url,source?.id||'']),
  mediaKindForNode:node=>node.type === 'image' ? 'image' : 'file',
  mediaKindForOutputItem:item=>item.kind || 'image',
  outputUrlValue:item=>typeof item === 'string' ? item : item?.url || '',
  outputImageName:url=>url.split('/').pop(),
}});
const options=adapterInstance.optionsFor(canvasNode);
const standaloneImage=options.resolveReference('asset_version','standalone-1');
const standaloneVideo=options.resolveReference('artifact_version','standalone-2');
const mirrored=options.resolveReference('asset_version','mirrored-1');
options.onOpen({{url:standaloneVideo.url,referenceId:'standalone-2'}});
let workspaceOpens=0;
options.registerWorkspaceOpen(()=>{{workspaceOpens++;return true;}});
const workspaceOpened=adapterInstance.openWorkspace('collection-node');
console.log(JSON.stringify({{standaloneImage,standaloneVideo,mirrored,opened,workspaceOpens,workspaceOpened}}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "standaloneImage": {"url": "/standalone.png", "kind": "image", "name": "Standalone"},
            "standaloneVideo": {"url": "/standalone.mp4", "kind": "video", "name": "Clip"},
            "mirrored": {"url": "/mirrored.png", "kind": "image", "name": "mirrored.png"},
            "opened": [["/standalone.mp4", ""]],
            "workspaceOpens": 1,
            "workspaceOpened": True,
        })


if __name__ == "__main__":
    unittest.main()
