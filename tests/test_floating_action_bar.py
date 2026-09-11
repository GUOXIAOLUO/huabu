import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FloatingActionBarTests(unittest.TestCase):
    def test_action_registry_filters_selection_context_and_emits_intents(self):
        module = ROOT / "static/js/workbench/canvas/floating-action-bar.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const makeClassList = () => {{ const values = new Set(); return {{add:x=>values.add(x), toggle:(x,on)=>on?values.add(x):values.delete(x), has:x=>values.has(x)}}; }};
const makeElement = () => ({{children:[], dataset:{{}}, listeners:{{}}, classList:makeClassList(), appendChild(child){{this.children.push(child);}}, replaceChildren(){{this.children=[];}}, addEventListener(type, cb){{(this.listeners[type]=this.listeners[type]||[]).push(cb);}}, setAttribute(){{}}}});
const container = makeElement(); const documentRef = {{createElement:makeElement}}; const intents=[];
const sandbox = {{window:{{}}}}; vm.runInNewContext(fs.readFileSync({json.dumps(str(module))}, 'utf8'), sandbox);
const bar = sandbox.window.WorkbenchFloatingActionBar.create({{document:documentRef, container, onIntent:intent=>intents.push(intent), actions:[
  {{id:'open', label:'Open', order:10, when:c=>c.count===1}},
  {{id:'copy', label:'Copy', order:20, when:c=>c.count>0}},
  {{id:'group', label:'Group', order:30, when:c=>c.count>1}},
]}});
const empty=bar.update({{nodeIds:[],nodes:[]}});
const single=bar.update({{nodeIds:['a','a'],nodes:[{{id:'a'}}]}});
container.children[0].listeners.click[0]({{preventDefault(){{}},stopPropagation(){{}}}});
const multiple=bar.update({{nodeIds:['a','b'],nodes:[{{id:'a'}},{{id:'b'}}]}});
container.children[1].listeners.click[0]({{preventDefault(){{}},stopPropagation(){{}}}});
console.log(JSON.stringify({{empty,single,multiple,intents,open:container.classList.has('open')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["empty"], {"visible": [], "mode": "empty"})
        self.assertEqual(actual["single"], {"visible": ["open", "copy"], "mode": "single"})
        self.assertEqual(actual["multiple"], {"visible": ["copy", "group"], "mode": "multiple"})
        self.assertEqual([item["actionId"] for item in actual["intents"]], ["open", "group"])
        self.assertTrue(actual["open"])


if __name__ == "__main__":
    unittest.main()
