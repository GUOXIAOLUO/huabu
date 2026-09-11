import unittest

from workbench.domain.canvas import InputBinding, InputBindingAdapter, LegacyInputBinding, NodeRecord


class InputBindingTests(unittest.TestCase):
    def test_typed_binding_round_trips_through_json(self):
        binding = InputBinding(
            id="binding-1",
            target="prompt.image",
            source_type="asset_version",
            source_ref="asset-version-1",
            role="reference",
            order=2,
            enabled=False,
            metadata={"label": "reference image"},
        )
        restored = InputBinding.model_validate(binding.model_dump(mode="json"))
        self.assertEqual(restored, binding)

    def test_legacy_payload_is_readable_and_serializes_losslessly(self):
        payload = {"node_id": "legacy-source", "port": "image", "custom": {"keep": True}}
        binding = InputBindingAdapter.from_payload(payload)
        self.assertIsInstance(binding, LegacyInputBinding)
        self.assertEqual(InputBindingAdapter.to_payload(binding), payload)
        self.assertEqual(binding.model_dump(mode="json"), payload)

    def test_node_record_accepts_legacy_binding_objects_without_guessing_semantics(self):
        record = NodeRecord.model_validate({
            "id": "node-1", "project_id": "project-1", "canvas_id": "canvas-1",
            "kind": "legacy", "definition_ref": {"type": "legacy", "id": "image", "version": "0"},
            "renderer": {"id": "legacy", "version": "1"}, "state": "ready", "title": "Image",
            "position": {"x": 0, "y": 0}, "size": {"width": 280, "height": 180},
            "input_bindings": [{"node_id": "legacy-source", "port": "image"}],
            "created_by": "user-1", "created_at": "2026-09-10T00:00:00Z",
            "updated_at": "2026-09-10T00:00:00Z",
        })
        self.assertIsInstance(record.input_bindings[0], LegacyInputBinding)
        self.assertEqual(InputBindingAdapter.to_payloads(record.input_bindings), [{"node_id": "legacy-source", "port": "image"}])
        self.assertEqual(record.model_dump(mode="json")["input_bindings"], [{"node_id": "legacy-source", "port": "image"}])
