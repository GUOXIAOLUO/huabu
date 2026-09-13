import unittest

from pydantic import ValidationError

from workbench.application.prompt_resolver import PromptResolver, PromptResolverError
from workbench.domain.prompt import PromptLayer, PromptRef


class PromptResolverTests(unittest.TestCase):
    def test_runtime_overrides_task_project_and_default_with_ref_and_metadata_snapshot(self):
        resolved = PromptResolver().resolve([
            PromptLayer(layer="default", content="default"),
            PromptLayer(layer="project", content="project", prompt=PromptRef(prompt_id="p", version=2)),
            PromptLayer(layer="task", content="task", metadata={"task_id": "t1"}),
            PromptLayer(layer="runtime", content="runtime", prompt=PromptRef(prompt_id="r", version=7), metadata={"request": "r1"}),
        ])
        self.assertEqual((resolved.source, resolved.content, resolved.prompt.prompt_id, resolved.prompt.version), ("runtime", "runtime", "r", 7))
        self.assertEqual(resolved.metadata, {"request": "r1"})
        with self.assertRaises(ValidationError):
            resolved.content = "mutated"

    def test_missing_higher_layers_falls_back_deterministically_and_duplicate_layers_fail(self):
        resolver = PromptResolver()
        resolved = resolver.resolve([
            PromptLayer(layer="default", content="default"),
            PromptLayer(layer="project", content="project", prompt=PromptRef(prompt_id="p", version=1)),
        ])
        self.assertEqual((resolved.source, resolved.content, resolved.prompt.model_dump()), ("project", "project", {"prompt_id": "p", "version": 1}))
        with self.assertRaisesRegex(PromptResolverError, "duplicate prompt layer"):
            resolver.resolve([PromptLayer(layer="task", content="one"), PromptLayer(layer="task", content="two")])

    def test_no_layers_is_rejected_without_model_or_provider_resolution(self):
        with self.assertRaisesRegex(PromptResolverError, "at least one"):
            PromptResolver().resolve([])


if __name__ == "__main__":
    unittest.main()
