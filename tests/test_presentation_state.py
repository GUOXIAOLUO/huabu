import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PresentationStateTests(unittest.TestCase):
    def test_state_machine_transitions_and_reload_restore_only_presentation_state(self):
        module = ROOT / "static/js/workbench/canvas/presentation-state.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const values={{}}; const storage={{getItem:key=>values[key]||null, setItem:(key,value)=>values[key]=value}};
const sandbox={{window:{{}}}}; vm.runInNewContext(fs.readFileSync({json.dumps(str(module))},'utf8'),sandbox);
const P=sandbox.window.WorkbenchPresentationState;
const first=P.create({{initial:'card',storage,storageKey:'node:p1'}});
const states=[first.transition('expanded'),first.transition('workspace'),first.transition('inspector'),first.transition('card')];
const reloaded=P.create({{initial:'workspace',storage,storageKey:'node:p1'}});
let invalid=false; try {{ reloaded.transition('unknown'); }} catch(e) {{ invalid=e.name==='RangeError'; }}
console.log(JSON.stringify({{states,reloaded:reloaded.state(),snapshot:reloaded.snapshot(),stored:values['node:p1'],invalid,all:P.STATES}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "states": ["expanded", "workspace", "inspector", "card"],
            "reloaded": "card", "snapshot": {"state": "card"}, "stored": "card",
            "invalid": True, "all": ["card", "expanded", "workspace", "inspector"],
        })

    def test_nodeshell_consumes_presentation_state_without_owning_selection(self):
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("presentationState", shell)
        self.assertIn("root.dataset.presentationState", shell)
        self.assertNotIn("selected.add", shell)
        self.assertNotIn("selected.delete", shell)
        host = (ROOT / "static/js/workbench/canvas/unified-render-host.js").read_text(encoding="utf-8")
        self.assertIn("presentation: settings.presentation || 'card'", host)

    def test_nodeshell_exposes_the_shared_presentation_transition_seam(self):
        shell_path = ROOT / "static/js/workbench/canvas/node-shell.js"
        presentation_path = ROOT / "static/js/workbench/canvas/presentation-state.js"
        script = f"""
const fs=require('fs'), vm=require('vm');
const makeElement=tag=>{{const el={{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},className:'',classList:{{toggle(){{}},add(){{}},remove(){{}}}},append(...items){{this.children.push(...items)}},addEventListener(type,cb){{(this.listeners[type]=this.listeners[type]||[]).push(cb)}},setAttribute(){{}},remove(){{}},closest(){{return null}}}};return el;}};
const documentRef={{createElement:makeElement}}; const sandbox={{window:{{document:documentRef,WorkbenchCanvas:{{STATES:['ready']}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(presentation_path))},'utf8'),sandbox);
vm.runInNewContext(fs.readFileSync({json.dumps(str(shell_path))},'utf8'),sandbox);
const shell=sandbox.window.WorkbenchNodeShell.create({{document:documentRef,node:{{id:'n1',title:'Generic',state:'ready'}},viewState:{{presentation:'card'}}}});
const states=[shell.transitionPresentation('expanded'),shell.transitionPresentation('workspace'),shell.transitionPresentation('inspector'),shell.transitionPresentation('card')];
console.log(JSON.stringify({{states,dom:shell.presentationState(),selected:shell.element.className.includes('is-selected')}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "states": ["expanded", "workspace", "inspector", "card"],
            "dom": "card", "selected": False,
        })


if __name__ == "__main__":
    unittest.main()
