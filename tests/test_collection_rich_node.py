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
rich.transition('expanded');
rich.select('second'); rich.open('second');
const reload=sandbox.window.WorkbenchCollectionRichNode.create({{node,storage,resolveReference:resolve}}).snapshot();
console.log(JSON.stringify({{compatible:sandbox.window.WorkbenchCollectionRichNode.isCompatible(node),items,selected,opened,presentation:reload.presentation,reloadItems:reload.items}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["compatible"])
        self.assertEqual([(item["itemId"], item["kind"]) for item in payload["items"]], [("first", "image"), ("second", "video")])
        self.assertEqual((payload["selected"], payload["opened"], payload["presentation"]), ("second", "second", "expanded"))
        self.assertEqual(payload["reloadItems"], payload["items"])

    def test_collection_gallery_is_registered_and_integrated_with_node_shell(self):
        module = (ROOT / "static/js/workbench/canvas/collection-rich-node.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        editor = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        presentation = (ROOT / "static/js/workbench/canvas/node-presentation.js").read_text(encoding="utf-8")
        self.assertIn("id: 'collection-gallery'", module)
        self.assertIn("WorkbenchCollectionRichNode", host)
        self.assertIn("collectionRichNode", shell)
        self.assertIn("collection-rich-node.js", page)
        self.assertIn("node?.type === 'collection'", editor)
        self.assertIn("'collection'", editor)
        self.assertIn("collection: [320, 260]", presentation)


if __name__ == "__main__":
    unittest.main()
