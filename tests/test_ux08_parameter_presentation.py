import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "static/js/workbench/canvas/parameter-presentation.js"


class UX08ParameterPresentationTests(unittest.TestCase):
    def test_summary_is_compact_and_uses_generation_parameter_labels(self):
        script = f"""
const fs = require('fs'), vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))}, 'utf8'), sandbox);
console.log(JSON.stringify(sandbox.window.WorkbenchParameterPresentation.summary({{
  ratio: 'square', resolution: '4k', count: 3, model: 'gpt-image-1'
}})));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "items": [
                {"id": "ratio", "label": "比例", "value": "square", "display": "1:1"},
                {"id": "resolution", "label": "分辨率", "value": "4k", "display": "4K"},
                {"id": "count", "label": "数量", "value": "3", "display": "×3"},
            ],
            "text": "1:1 · 4K · ×3",
        })

    def test_popover_edits_delegate_and_advanced_fields_are_collapsed_by_default(self):
        script = f"""
const fs = require('fs'), vm = require('vm');
function element(tag) {{
  return {{tag, children:[], dataset:{{}}, hidden:false, value:'', listeners:{{}}, className:'',
    append(...items){{this.children.push(...items)}}, prepend(item){{this.children.unshift(item)}},
    setAttribute(){{}}, addEventListener(type, fn){{this.listeners[type]=fn}},
    querySelector(selector){{const wanted=selector.startsWith('.') ? selector.slice(1) : ''; return this.children.flatMap(child => [child, ...(child.children || [])]).find(child => child.className === wanted) || null;}}
  }};
}}
const documentRef={{createElement:element}}; const container=element('div'); const advanced=element('div'); advanced.className='gen-settings'; container.append(advanced);
const sandbox={{window:{{}}, document:documentRef}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(MODULE))}, 'utf8'), sandbox);
const node={{ratio:'square',resolution:'1k',count:1}}; const changes=[];
const mounted=sandbox.window.WorkbenchParameterPresentation.create({{document:documentRef,container,node,onChange:(field,value)=>{{changes.push([field,value]); node[field]=value;}}}});
const summaryButton=mounted.root.children[0]; const ratio=mounted.root.children[1].children[1].children[0].children[1];
summaryButton.listeners.click({{stopPropagation(){{}}}});
ratio.listeners.change({{target:{{value:'wide'}},stopPropagation(){{}}}});
mounted.root.children[2].listeners.click({{stopPropagation(){{}}}});
console.log(JSON.stringify({{summary:mounted.summary().text,changes,popoverHidden:mounted.popover.hidden,advancedHidden:mounted.advanced.hidden}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {
            "summary": "16:9 · 1K · ×1",
            "changes": [["ratio", "wide"]],
            "popoverHidden": True,
            "advancedHidden": False,
        })

    def test_generator_uses_shared_parameter_presentation_without_new_canvas_owner(self):
        renderer = (ROOT / "static/js/workbench/canvas/classic-card-body-renderer.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/canvas-app-compat-host.js").read_text(encoding="utf-8")
        page = (ROOT / "static/canvas.html").read_text(encoding="utf-8")
        self.assertIn("host.parameterPresentation.create", renderer)
        self.assertIn("parameterPresentation: window.WorkbenchParameterPresentation", host)
        self.assertIn("/static/js/workbench/canvas/parameter-presentation.js", page)
        self.assertNotIn("WholeHouse", (ROOT / "static/js/workbench/canvas/parameter-presentation.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
