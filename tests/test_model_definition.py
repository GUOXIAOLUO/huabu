import unittest

from pydantic import ValidationError

from workbench.application.model_definitions import ModelDefinitionAdapter
from workbench.domain.provider import MODEL_DEFINITION_SCHEMA_VERSION, ModelDefinition


class ModelDefinitionTests(unittest.TestCase):
    def test_model_identity_is_route_free_and_preserves_context_and_io_metadata(self):
        model = ModelDefinition(
            id="openai/gpt-x",
            family="gpt",
            display_name="GPT X",
            normalized_capabilities=("reasoning", "vision"),
            input_modalities=("text", "image"),
            output_modalities=("text",),
            context_window=128_000,
            parameter_schema={"type": "object"},
        )
        payload = model.model_dump(mode="json")
        self.assertEqual(model.schema_version, MODEL_DEFINITION_SCHEMA_VERSION)
        self.assertNotIn("provider_id", payload)
        self.assertNotIn("connection_id", payload)
        self.assertEqual(payload["context_window"], 128_000)

    def test_legacy_model_projection_has_no_provider_or_credential_ownership(self):
        model = ModelDefinitionAdapter.from_legacy(
            {"id": "vendor/model-x", "display_name": "Model X", "capabilities": ["text.generate"],
             "input_modalities": ["text"], "output_modalities": ["text"], "context_length": 32_000},
            capability="reasoning",
        )
        self.assertEqual(model.normalized_capabilities, ("text.generate", "reasoning"))
        self.assertEqual(model.context_window, 32_000)
        self.assertIsNone(getattr(model, "provider_id", None))
        self.assertIsNone(getattr(model, "credential_ref", None))

        projected = ModelDefinitionAdapter.from_legacy_list(["vendor/model-x", "vendor/model-y", "vendor/model-x"])
        self.assertEqual(tuple(item.id for item in projected), ("vendor/model-x", "vendor/model-y"))

    def test_model_definition_rejects_routes_credentials_and_duplicate_metadata(self):
        with self.assertRaises(ValidationError):
            ModelDefinition(id="m", family="f", display_name="M", connection_id="connection")
        with self.assertRaises(ValidationError):
            ModelDefinition(id="m", family="f", display_name="M", native_metadata={"apiKey": "secret"})
        with self.assertRaises(ValidationError):
            ModelDefinition(id="m", family="f", display_name="M", input_modalities=("text", "text"))


if __name__ == "__main__":
    unittest.main()
