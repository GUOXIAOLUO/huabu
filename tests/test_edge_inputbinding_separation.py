import unittest
from datetime import UTC, datetime

from workbench.application.binding_resolver import BindingResolver
from workbench.domain.canvas import EdgeRecord, InputBinding, NodeRecord
from workbench.domain.canvas.models import Position, RendererRef, Size
from workbench.domain.canvas.ports import PortSet
from workbench.domain.canvas.states import NodeState


def node(*, bindings=()):
    return NodeRecord(
        id="node-1", project_id="project-1", canvas_id="canvas-1", kind="legacy",
        definition_ref={"type": "legacy", "id": "image", "version": "0"},
        renderer=RendererRef(id="legacy", version="1"), state=NodeState.READY,
        title="Image", position=Position(x=0, y=0), size=Size(width=280, height=180),
        ports=PortSet(), input_bindings=list(bindings), created_by="user-1",
        created_at=datetime(2026, 9, 10, tzinfo=UTC), updated_at=datetime(2026, 9, 10, tzinfo=UTC),
    )


def edge():
    return EdgeRecord(
        id="edge-1", canvas_id="canvas-1",
        **{"from": {"node_id": "source", "port_id": "legacy.out"}, "to": {"node_id": "node-1", "port_id": "legacy.in"}},
    )


class EdgeInputBindingSeparationTests(unittest.TestCase):
    def test_graph_relation_can_exist_without_an_input_binding(self):
        relation = edge()
        record = node()
        self.assertIsInstance(relation, EdgeRecord)
        self.assertEqual(record.input_bindings, [])

    def test_input_binding_can_resolve_without_a_graph_relation(self):
        binding = InputBinding(id="binding-1", target="image", source_type="literal", source_ref='{"value": 1}')
        result = BindingResolver().resolve([binding])
        self.assertEqual(result[0].status, "resolved")
        self.assertEqual(result[0].value, {"value": 1})

    def test_edge_and_binding_are_independent_records(self):
        binding = InputBinding(id="binding-1", target="image", source_type="asset_version", source_ref="asset-1")
        record = node(bindings=(binding,))
        relation = edge()
        self.assertEqual(record.input_bindings, [binding])
        self.assertEqual((relation.from_.node_id, relation.to.node_id), ("source", "node-1"))
        self.assertIsNone(next((item for item in record.input_bindings if item.id == relation.id), None))
