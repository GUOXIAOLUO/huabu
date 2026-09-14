import unittest
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "static/css/canvas.css"
HTML = ROOT / "static/canvas.html"
SHELL = ROOT / "static/js/workbench/canvas/node-shell.js"


class UX03NodeShellVisualTests(unittest.TestCase):
    def test_shared_nodeshell_owns_visual_states_and_presentation_sizes(self):
        styles = CSS.read_text(encoding="utf-8")
        page = HTML.read_text(encoding="utf-8")
        for selector in (
            ".node.node-shell-mounted .workbench-node-shell.is-selected",
            '.workbench-node-shell[data-state="running"]',
            '.workbench-node-shell[data-state="failed"]',
            ".workbench-node-shell.is-presentation-expanded",
            ".workbench-node-shell.is-presentation-workspace",
            ".workbench-node-shell.is-presentation-inspector",
        ):
            self.assertIn(selector, styles)
        self.assertIn("var(--wb-radius-card)", styles)
        self.assertIn("var(--wb-selection)", styles)
        self.assertIn("canvas.css?v=2026.09.11.1&ux02=2026.09.14.3&ux03=2026.09.14.2&ux04=2026.09.14.1", page)

    def test_nodeshell_projects_state_and_selection_without_provider_ownership(self):
        source = SHELL.read_text(encoding="utf-8")
        self.assertIn("root.dataset.state = state", source)
        self.assertIn("root.classList.toggle('is-selected', selected)", source)
        self.assertNotIn("provider_id", source)
        self.assertNotIn("model_id", source)

    def test_nodeshell_state_projection_covers_selected_running_and_error_states(self):
        script = f"""
const fs=require('fs'), vm=require('vm');
const makeElement=tag=>{{
  const classes=new Set();
  const el={{tagName:tag.toUpperCase(),children:[],dataset:{{}},listeners:{{}},attrs:{{}},className:'',textContent:'',
    append(...items){{this.children.push(...items);}},
    addEventListener(type,cb){{(this.listeners[type]=this.listeners[type]||[]).push(cb);}},
    setAttribute(name,value){{this.attrs[name]=String(value);}},
    classList:{{toggle(name,on){{if(on===undefined){{on=!classes.has(name);}} if(on) classes.add(name); else classes.delete(name);}},add(...names){{names.forEach(name=>classes.add(name));}},remove(...names){{names.forEach(name=>classes.delete(name));}},has(name){{return classes.has(name);}}}},
    remove(){{this.removed=true;}},closest(){{return null;}}
  }};
  Object.defineProperty(el,'className',{{get:()=>[...classes].join(' '),set:value=>{{classes.clear();String(value).split(/\\s+/).filter(Boolean).forEach(name=>classes.add(name));}}}});
  return el;
}};
const documentRef={{createElement:makeElement}};
const sandbox={{window:{{document:documentRef,WorkbenchCanvas:{{STATES:['ready','running','done','failed','error']}}}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(SHELL))},'utf8'),sandbox);
const shell=sandbox.window.WorkbenchNodeShell.create({{document:documentRef,node:{{id:'n1',title:'Task',state:'ready'}},viewState:{{selected:true}}}});
const snapshots=[];
for (const state of ['ready','running','failed','error']) {{
  shell.update({{id:'n1',title:'Task',state}}, {{selected:state !== 'ready'}});
  snapshots.push({{state:shell.element.dataset.state,selected:shell.element.classList.has('is-selected'),status:shell.slots.status.textContent,aria:shell.element.attrs['aria-label']}});
}}
console.log(JSON.stringify(snapshots));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), [
            {"state": "ready", "selected": False, "status": "ready", "aria": "Task, ready"},
            {"state": "running", "selected": True, "status": "running", "aria": "Task, running"},
            {"state": "failed", "selected": True, "status": "failed", "aria": "Task, failed"},
            {"state": "error", "selected": True, "status": "error", "aria": "Task, error"},
        ])

    def test_shared_shell_css_carries_hover_selection_and_terminal_visuals(self):
        styles = CSS.read_text(encoding="utf-8")
        block = re.search(
            r"/\* UX-03 NodeShell visual replica:.*?(?=\.node\.media-renderer-mounted)",
            styles,
            re.S,
        )
        self.assertIsNotNone(block)
        shared = block.group(0)
        for selector in (
            ".node.node-shell-mounted:hover",
            ".node.node-shell-mounted:hover .workbench-node-shell__actions",
            ".node.node-shell-mounted .workbench-node-shell.is-selected .workbench-node-shell__actions",
            '.node.node-shell-mounted .workbench-node-shell[data-state="running"]',
            '.node.node-shell-mounted .workbench-node-shell[data-state="failed"]',
            '.node.node-shell-mounted .workbench-node-shell[data-state="error"]',
        ):
            self.assertIn(selector, shared)
        self.assertRegex(shared, r"\.node\.node-shell-mounted:hover\s*\{[^}]*border-color:")
        self.assertIn("outline:2px solid var(--wb-selection)", shared)
        self.assertIn("box-shadow:inset 0 0 0 1px", shared)
        self.assertIn("opacity:1", shared)


if __name__ == "__main__":
    unittest.main()
