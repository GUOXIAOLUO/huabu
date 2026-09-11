import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NodeShellV2Tests(unittest.TestCase):
    def test_contract_exposes_generic_slots_and_intents_without_provider_logic(self):
        source_path = ROOT / "static/js/workbench/canvas/node-shell.js"
        source = source_path.read_text(encoding="utf-8")
        self.assertNotIn("provider_id", source)
        self.assertNotIn("model_id", source)
        self.assertIn("const slots = Object.freeze", source)

        script = f"""
const fs = require('fs'); const vm = require('vm');
const makeElement = tag => {{
  const el = {{tagName: tag.toUpperCase(), children: [], dataset: {{}}, listeners: {{}}, className:'', textContent:'', hidden:false,
    append(...items) {{ this.children.push(...items); }},
    addEventListener(type, cb) {{ (this.listeners[type] = this.listeners[type] || []).push(cb); }},
    setAttribute(name, value) {{ this['attr_' + name] = String(value); }},
    classList: {{toggle(){{}}, add(){{}}, remove(){{}}}},
    remove() {{ this.removed = true; }},
    closest() {{ return null; }} }};
  return el;
}};
const documentRef = {{createElement: makeElement}};
const sandbox = {{window: {{document: documentRef, WorkbenchCanvas: {{STATES: ['ready', 'running', 'done']}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(source_path))}, 'utf8'), sandbox);
const events = [];
const shell = sandbox.window.WorkbenchNodeShell.create({{document: documentRef, node: {{id:'n1', title:'Generic', state:'ready'}}, showDelete:true, onIntent:e => events.push(e)}});
shell.slots.title.textContent = 'Generic';
shell.slots.header.listeners.mousedown?.[0]?.({{button:0, preventDefault(){{}}, stopPropagation(){{}}, target:{{closest:()=>null}}, clientX:4, clientY:5}});
shell.slots.ports.input.listeners.mousedown[0]({{button:0, preventDefault(){{}}, stopPropagation(){{}}, clientX:8, clientY:9}});
shell.slots.resize.listeners.mousedown[0]({{button:0, preventDefault(){{}}, stopPropagation(){{}}, clientX:10, clientY:11}});
shell.slots.actions.children[0].listeners.click[0]({{preventDefault(){{}}, stopPropagation(){{}}}});
console.log(JSON.stringify({{slotKeys:Object.keys(shell.slots), contentAlias:shell.contentHost===shell.slots.content, intents:events.map(e=>e.type), providerModelDataset:shell.slots.footer.dataset.model || null}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["slotKeys"], ["header", "title", "status", "ports", "content", "actions", "toolbar", "footer", "resize"])
        self.assertTrue(payload["contentAlias"])
        self.assertEqual(payload["intents"], ["drag_start", "connect_start", "resize_start", "menu"])
        self.assertIsNone(payload["providerModelDataset"])


if __name__ == "__main__":
    unittest.main()
