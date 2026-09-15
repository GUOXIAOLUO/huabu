import unittest

from workbench.comfyui import ComfyUIWorkflowDefinitionBuilder


class ComfyUIWorkflowDefinitionBuilderTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "2": {"class_type": "KSampler", "inputs": {"seed": 1, "steps": 20}},
            "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "prompt"}},
            "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0]}},
        }

    def test_builds_version_pinned_definition_with_selected_outputs(self):
        definition = ComfyUIWorkflowDefinitionBuilder.build({
            "workflow_ref": "demo@4", "title": "Demo", "graph": self.graph,
            "input_bindings": [{"role": "prompt", "node_id": "1", "input_name": "text"}],
            "output_mappings": [{"role": "image", "node_id": "3", "output_name": "images"}],
        })
        self.assertEqual(definition.ref.ref, "demo@4")
        self.assertEqual(definition.input_bindings[0].node_id, "1")
        self.assertEqual(definition.output_mappings[0].output_name, "images")

    def test_requires_explicit_version_and_never_infers_latest(self):
        with self.assertRaisesRegex(ValueError, "positive integer version"):
            ComfyUIWorkflowDefinitionBuilder.build({"workflow_id": "demo", "graph": self.graph})

    def test_discovers_deterministic_semantic_candidates_and_skips_links(self):
        candidates = ComfyUIWorkflowDefinitionBuilder.discover_inputs(self.graph)
        self.assertEqual([(item.role, item.node_id, item.input_name) for item in candidates], [
            ("prompt", "1", "text"), ("seed", "2", "seed")
        ])

    def test_rejects_mappings_to_unknown_graph_slots(self):
        with self.assertRaisesRegex(ValueError, "unknown input"):
            ComfyUIWorkflowDefinitionBuilder.build({
                "workflow_ref": "demo@1", "graph": self.graph,
                "input_bindings": [{"role": "prompt", "node_id": "1", "input_name": "missing"}],
            })


if __name__ == "__main__":
    unittest.main()
