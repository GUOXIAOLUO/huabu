import unittest

from pydantic import ValidationError

from workbench.application.model_availability import ModelAvailabilityService
from workbench.domain.availability import MODEL_AVAILABILITY_SCHEMA_VERSION, ModelAvailability
from workbench.repositories.availability_repository import InMemoryAvailabilityRepository


class ModelAvailabilityTests(unittest.TestCase):
    def test_same_model_can_have_provider_and_runtime_routes(self):
        repository = InMemoryAvailabilityRepository()
        service = ModelAvailabilityService(repository)
        provider = ModelAvailability(
            id="model-api",
            model_ref="openai/model-x",
            route_type="provider",
            route_ref="openai-primary",
            executor_type="model_api",
            normalized_capabilities=("reasoning",),
            status="available",
        )
        runtime = ModelAvailability(
            id="model-codex",
            model_ref=provider.model_ref,
            route_type="runtime",
            route_ref="codex-local",
            executor_type="codex_harness",
            normalized_capabilities=("reasoning", "vision"),
            status="available",
        )

        service.register(provider)
        service.register(runtime)
        self.assertEqual(provider.schema_version, MODEL_AVAILABILITY_SCHEMA_VERSION)
        self.assertEqual([item.id for item in service.list_for_model("openai/model-x")], ["model-api", "model-codex"])
        self.assertEqual({item.route_type for item in service.list_for_model("openai/model-x")}, {"provider", "runtime"})

    def test_availability_is_not_a_model_definition_or_secret_store(self):
        with self.assertRaises(ValidationError):
            ModelAvailability(
                id="a", model_ref="m", route_type="provider", route_ref="r", executor_type="e",
                provider_id="provider",
            )
        with self.assertRaises(ValidationError):
            ModelAvailability(
                id="a", model_ref="m", route_type="provider", route_ref="r", executor_type="e",
                native_metadata={"apiKey": "secret"},
            )


if __name__ == "__main__":
    unittest.main()
