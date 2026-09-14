import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/floating-action-bar.js"
INTERACTION = ROOT / "static/js/workbench/canvas/canvas-app-interaction.js"
CSS = ROOT / "static/css/canvas.css"


class UX05FloatingActionToolbarTests(unittest.TestCase):
    def test_toolbar_keeps_button_semantics_when_icons_are_refreshed(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
const makeClassList=()=>({{add(){{}},toggle(){{}}}});
const makeElement=tag=>({{tagName:tag,children:[],dataset:{{}},listeners:{{}},classList:makeClassList(),appendChild(child){{this.children.push(child);}},replaceChildren(){{this.children=[];}},setAttribute(){{}},addEventListener(type,cb){{this.listeners[type]=cb;}}}});
const documentRef={{createElement:tag=>makeElement(tag)}}; const container=makeElement('div'); const sandbox={{window:{{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))},'utf8'),sandbox);
const bar=sandbox.window.WorkbenchFloatingActionBar.create({{document:documentRef,container,actions:[{{id:'edit',label:'Edit',icon:'pencil',when:c=>c.capabilities.includes('edit')}}]}});
const result=bar.update({{nodeIds:['n1'],nodes:[{{id:'n1'}}],capabilities:['edit']}});
console.log(JSON.stringify({{result,tag:container.children[0].tagName,icon:container.children[0].children[0].dataset.lucide,label:container.children[0].children[1].textContent,buttonLucide:container.children[0].dataset.lucide||null}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "result": {"visible": ["edit"], "mode": "single"},
            "tag": "button", "icon": "pencil", "label": "Edit", "buttonLucide": None,
        })

    def test_selection_toolbar_is_capability_driven_and_visual_hierarchy_is_shared(self):
        source = INTERACTION.read_text(encoding="utf-8")
        styles = CSS.read_text(encoding="utf-8")
        self.assertIn("function selectionCapabilities(selectedNodes)", source)
        self.assertIn("capabilities:[...selectionCapabilities(selectedNodes)]", source)
        self.assertIn("context.capabilities.includes('edit')", source)
        self.assertIn("context.capabilities.includes('preview')", source)
        for selector in (".selection-hub", ".selection-hub .hub-action", ".selection-hub .hub-action:focus-visible", ".selection-hub .hub-action-label"):
            self.assertIn(selector, styles)
        self.assertIn("background:rgba(15,23,42,.94)", styles)
        self.assertIn("font-size:0", styles)


if __name__ == "__main__":
    unittest.main()
