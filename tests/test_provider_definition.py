import unittest

from pydantic import ValidationError

from workbench.application.provider_definitions import ProviderDefinitionAdapter
from workbench.domain.provider import PROVIDER_DEFINITION_SCHEMA_VERSION, ProviderDefinition


class ProviderDefinitionTests(unittest.TestCase):
    def test_provider_definition_exists_without_connection_or_credentials(self):
        definition = ProviderDefinition(
            id="generic.openai-compatible",
            title="OpenAI-compatible provider",
            protocol="openai-compatible",
            capabilities=("text.generate", "image.generate"),
            config_schema={"type": "object", "properties": {"base_url": {"type": "string"}}},
        )
        self.assertEqual(definition.schema_version, PROVIDER_DEFINITION_SCHEMA_VERSION)
        self.assertEqual(definition.protocol, "openai-compatible")
        self.assertIsNone(getattr(definition, "connection", None))
        self.assertNotIn("api_key", definition.model_dump(mode="json"))

    def test_provider_definition_is_immutable_and_rejects_duplicate_or_unknown_fields(self):
        definition = ProviderDefinition(id="p", title="P", protocol="http")
        with self.assertRaises(ValidationError):
            definition.title = "changed"
        with self.assertRaises(ValidationError):
            ProviderDefinition(id="p", title="P", protocol="http", api_key="secret")
        with self.assertRaises(ValidationError):
            ProviderDefinition(id="p", title="P", protocol="http", metadata={"nested": {"api_key": "secret"}})
        with self.assertRaises(ValidationError):
            ProviderDefinition(id="p", title="P", protocol="http", capabilities=("text", "text"))

    def test_legacy_adapter_projects_public_metadata_without_connection_values(self):
        definition = ProviderDefinitionAdapter.from_legacy({
            "id": "legacy-provider", "name": "Legacy Provider", "protocol": "openai",
            "capabilities": ["text.generate"],
            "base_url": "https://example.invalid", "api_key": "must-not-project",
            "metadata": {"label": "legacy", "api_key": "must-not-project"},
            "config_schema": {"type": "object", "properties": {"base_url": {"type": "string"}}},
        })
        payload = definition.model_dump(mode="json")
        self.assertEqual(payload["id"], "legacy-provider")
        self.assertEqual(payload["title"], "Legacy Provider")
        self.assertEqual(payload["capabilities"], ["text.generate"])
        self.assertEqual(payload["metadata"], {"label": "legacy"})
        self.assertNotIn("base_url", payload["metadata"])
        self.assertNotIn("api_key", str(payload))


if __name__ == "__main__":
    unittest.main()
