import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanvasRevisionCursorTests(unittest.TestCase):
    def test_creation_and_graph_results_keep_updated_at_as_timestamp_metadata(self):
        client = ROOT / "static/js/workbench/canvas/node-creation-client.js"
        script = f"""
const fs = require('fs'), vm = require('vm');
const sandbox = {{window: {{}}}};
vm.runInNewContext(fs.readFileSync({json.dumps(str(client))}, 'utf8'), sandbox);
const api = sandbox.window.WorkbenchNodeClient;
const revisions = [], canvas = {{updated_at: 1700000000000}};
const projectNode = node => ({{id: node.id}});
const projectEdge = edge => ({{id: edge.id, from: edge.from, to: edge.to}});
api.applyCreationResult({{node: {{id: 'node-1'}}, canvas_revision: 7}}, {{nodes: [], canvas, projectNode, onRevision: value => revisions.push(value)}});
api.applyGraphCreationResult({{node: {{id: 'node-2'}}, edge: {{id: 'edge-1', from: 'source', to: 'node-2'}}, canvas_revision: 8}}, {{nodes: [{{id: 'source'}}], connections: [], canvas, projectNode, projectEdge, onRevision: value => revisions.push(value)}});
api.applyConnectionResult({{edge: {{id: 'edge-2', from: 'source', to: 'node-2'}}, canvas_revision: 9}}, {{connections: [], canvas, fromId: 'source', toId: 'node-2', onRevision: value => revisions.push(value)}});
console.log(JSON.stringify({{updated_at: canvas.updated_at, revisions}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"updated_at": 1700000000000, "revisions": [7, 8, 9]})


if __name__ == "__main__":
    unittest.main()
