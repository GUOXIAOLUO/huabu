"""Exercise render sweeps with the real mounted-card lifecycle owner."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanvasRenderLifecycleTests(unittest.TestCase):
    def test_rebuild_remote_removal_failure_and_close_release_owned_resources(self):
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const sandbox = {window: {}, console: {error() {}}};
for (const file of ['render-runtime.js', 'render-sweep.js']) {
  vm.runInNewContext(fs.readFileSync('static/js/workbench/canvas/' + file, 'utf8'), sandbox);
}
const container = {
  children: [],
  appendChild(el) { el.parent = this; this.children.push(el); },
  querySelectorAll() { return this.children.slice(); },
  querySelector(selector) {
    const id = selector.match(/data-id="(.*)"/)[1];
    return this.children.find(el => el.dataset.id === id) || null;
  },
};
function card(id) {
  return {
    dataset: {id},
    remove() { if (this.parent) this.parent.children = this.parent.children.filter(el => el !== this); },
    replaceWith(next) {
      const index = this.parent.children.indexOf(this);
      this.parent.children[index] = next;
      next.parent = this.parent;
    },
  };
}
const events = [];
const resources = [];
let sequence = 0;
let failAfterMount = false;
const a = {id: 'a'};
const b = {id: 'b'};
let nodes = [a, b];
const runtime = sandbox.window.WorkbenchRenderRuntime.create({
  mount(request) {
    return {element: request.card, destroy() {
      events.push('destroy:' + request.node.id);
      // Same payload reference used by compatibility editors: late teardown
      // would destroy the NEW editor instead of the outgoing one.
      request.node.editor.destroyed = true;
      request.node.editor = null;
    }};
  },
});
const sweep = sandbox.window.WorkbenchCanvasRenderSweep.create({
  container, runtime, getNodes: () => nodes,
  renderNode(node) {
    events.push('build:' + node.id);
    assert.equal(node.editor || null, null, 'previous editor must be released before building');
    node.editor = {sequence: ++sequence, destroyed: false};
    resources.push(node.editor);
    const el = card(node.id);
    runtime.mount({node, card: el});
    if (failAfterMount && node.id === 'a') throw new Error('body failed after mount');
    return el;
  },
});
sweep.run();
const firstResources = resources.slice();
events.length = 0;
sweep.run();
assert.deepEqual(events, ['destroy:a', 'build:a', 'destroy:b', 'build:b']);
assert.ok(firstResources.every(editor => editor.destroyed));
assert.equal(a.editor.destroyed, false);
assert.equal(b.editor.destroyed, false);

// A remote record removes b without invoking any page delete handler.
const removedEditor = b.editor;
nodes = [a];
sweep.run();
assert.equal(removedEditor.destroyed, true);
assert.deepEqual(Array.from(runtime.mountedNodeIds()), ['a']);
assert.deepEqual(container.children.map(el => el.dataset.id), ['a']);

// A partial refresh follows the same teardown-before-build contract.
const beforeRefresh = a.editor;
sweep.refresh(['a']);
assert.equal(beforeRefresh.destroyed, true);
assert.equal(a.editor.destroyed, false);

// Failure after mounting must release the partially built resource and must
// not prevent a subsequent node from rendering.
nodes = [a, b];
failAfterMount = true;
sweep.run();
assert.equal(a.editor, null);
assert.deepEqual(Array.from(runtime.mountedNodeIds()), ['b']);
assert.deepEqual(container.children.map(el => el.dataset.id), ['b']);
assert.ok(resources.filter(editor => editor !== b.editor).every(editor => editor.destroyed));

const finalEditor = b.editor;
sweep.clear();
sweep.clear();
assert.equal(finalEditor.destroyed, true);
assert.deepEqual(Array.from(runtime.mountedNodeIds()), []);
assert.equal(container.children.length, 0);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
