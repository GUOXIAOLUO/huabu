import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectUiCutoverTests(unittest.TestCase):
    def test_project_page_uses_only_canonical_client_for_project_crud(self):
        source = (ROOT / "static/js/canvas-list.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch('/api/projects", source)
        self.assertNotIn("fetch(`/api/projects", source)
        self.assertIn("WorkbenchProjectApiClient.list()", source)
        self.assertIn("WorkbenchProjectApiClient.create(name)", source)
        self.assertIn("WorkbenchProjectApiClient.update(pid, { name })", source)
        self.assertIn("WorkbenchProjectApiClient.archive(pid)", source)

    def test_canonical_client_uses_versioned_routes_and_preserves_errors(self):
        client_file = ROOT / "static/js/workbench/project-api-client.js"
        script = f"""
const fs = require('fs'); const vm = require('vm');
const calls = [];
const responses = [
  {{ ok: true, status: 200, json: async () => [{{id:'p1'}}] }},
  {{ ok: true, status: 201, json: async () => ({{id:'p2'}}) }},
  {{ ok: true, status: 200, json: async () => ({{id:'p2'}}) }},
  {{ ok: true, status: 200, json: async () => ({{ok:true}}) }},
  {{ ok: false, status: 409, json: async () => ({{detail: {{code:'stale', message:'stale project'}}}}) }},
];
const sandbox = {{ window: {{}}, fetch: async (url, options) => {{ calls.push([url, options.method || 'GET', options.body || null]); return responses.shift(); }} }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client_file))}, 'utf8'), sandbox);
(async () => {{
  const api = sandbox.window.WorkbenchProjectApiClient;
  await api.list(); await api.create('New'); await api.update('p2', {{name:'Renamed'}}); await api.archive('p2');
  let error = null; try {{ await api.update('p2', {{name:'Conflict'}}); }} catch(e) {{ error = {{status:e.status, code:e.code, message:e.message}}; }}
  console.log(JSON.stringify({{calls, error}}));
}})();
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)
        self.assertEqual([call[0] for call in actual["calls"]], [
            "/api/v1/projects", "/api/v1/projects", "/api/v1/projects/p2",
            "/api/v1/projects/p2", "/api/v1/projects/p2",
        ])
        self.assertEqual([call[1] for call in actual["calls"]], ["GET", "POST", "PUT", "DELETE", "PUT"])
        self.assertEqual(actual["error"], {"status": 409, "code": "stale", "message": "stale project"})


if __name__ == "__main__":
    unittest.main()
