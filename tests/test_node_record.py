import json
import unittest
from pathlib import Path
from typing import get_args

from pydantic import ValidationError

from workbench.domain.canvas import LegacyCanvasAdapter, NodeState, can_transition
from workbench.domain.canvas.models import EdgeRecord, NodeKind, NodeRecord


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "canvas"
SCHEMA_DIR = Path(__file__).parents[1] / "schemas" / "node-record"


class NodeRecordTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_classic_and_smart_fixtures_adapt_to_valid_records(self):
        for name in ("classic-v0.json", "smart-v0.json", "legacy-unknown-fields-v0.json"):
            canvas = self.fixture(name)
            nodes, edges = LegacyCanvasAdapter.canvas_to_records(canvas)
            self.assertEqual(len(nodes), len(canvas["nodes"]))
            self.assertEqual(len(edges), len(canvas["connections"]))
            self.assertTrue(all(record.schema_version == "workbench.node/1" for record in nodes))
            self.assertTrue(all(record.schema_version == "workbench.edge/1" for record in edges))
            self.assertTrue(all(record.ports.inputs[0].id == "legacy.in" for record in nodes))

    def test_legacy_adapter_round_trips_all_fields_without_normalization(self):
        for name in ("classic-v0.json", "smart-v0.json", "legacy-unknown-fields-v0.json"):
            canvas = self.fixture(name)
            nodes, edges = LegacyCanvasAdapter.canvas_to_records(canvas)
            self.assertEqual([LegacyCanvasAdapter.record_to_node(node) for node in nodes], canvas["nodes"])
            self.assertEqual([LegacyCanvasAdapter.record_to_connection(edge) for edge in edges], canvas["connections"])

    def test_model_binding_requires_provider_and_model_together(self):
        canvas = self.fixture("classic-v0.json")
        record = LegacyCanvasAdapter.node_to_record(canvas["nodes"][0], canvas=canvas)
        with self.assertRaises(ValidationError):
            NodeRecord.model_validate({**record.model_dump(mode="json"), "model_binding": {"selection_mode": "user", "provider_id": "provider-only"}})

    def test_edge_uses_explicit_default_legacy_ports(self):
        canvas = self.fixture("classic-v0.json")
        edge = LegacyCanvasAdapter.connection_to_record(canvas["connections"][0], canvas=canvas)
        self.assertIsInstance(edge, EdgeRecord)
        self.assertEqual(edge.from_.port_id, "legacy.out")
        self.assertEqual(edge.to.port_id, "legacy.in")

    def test_state_transitions_are_centralized(self):
        self.assertTrue(can_transition(NodeState.READY, NodeState.QUEUED))
        self.assertTrue(can_transition(NodeState.COMPLETED, NodeState.OUTDATED))
        self.assertFalse(can_transition(NodeState.FROZEN, NodeState.READY))
        self.assertFalse(can_transition(NodeState.READY, NodeState.COMPLETED))

    def test_json_schema_files_are_versioned_and_match_domain_constants(self):
        node_schema = json.loads((SCHEMA_DIR / "node-record.v1.schema.json").read_text(encoding="utf-8"))
        edge_schema = json.loads((SCHEMA_DIR / "edge-record.v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(node_schema["properties"]["schema_version"]["const"], "workbench.node/1")
        self.assertEqual(edge_schema["properties"]["schema_version"]["const"], "workbench.edge/1")
        self.assertFalse(node_schema.get("additionalProperties", True))
        self.assertFalse(edge_schema.get("additionalProperties", True))

    def test_published_node_kinds_are_exactly_the_domain_closed_set(self):
        # A consumer validating against the published schema must be able to
        # accept every node the domain can produce. Checking only the schema
        # version let `collection` and `result` drift out of this enum.
        node_schema = json.loads((SCHEMA_DIR / "node-record.v1.schema.json").read_text(encoding="utf-8"))
        published = node_schema["properties"]["kind"]["enum"]
        declared = list(get_args(NodeKind))
        self.assertEqual(sorted(published), sorted(declared))
        self.assertEqual(len(published), len(set(published)), msg="published node kinds must not repeat")
