import asyncio
import unittest
from unittest.mock import AsyncMock

from workbench.codex.model_projection import (
    CODEX_RUNTIME_EXECUTOR,
    CODEX_RUNTIME_ROUTE,
    CodexModelProjectionService,
    CodexModelProjector,
)
from workbench.application.model_availability import ModelAvailabilityService
from workbench.codex.protocol import CodexModel, ConfigReadResult, ModelListResult
from workbench.domain.provider import ModelDefinition
from workbench.repositories.availability_repository import InMemoryAvailabilityRepository


class CodexModelProjectionTests(unittest.TestCase):
    def test_projects_known_codex_models_as_runtime_routes(self):
        definitions = (
            ModelDefinition(
                id="gpt-x",
                family="gpt",
                display_name="GPT X",
                normalized_capabilities=("reasoning", "vision"),
            ),
        )
        projected = CodexModelProjector.project(
            (CodexModel(id="gpt-x", name="GPT X"), CodexModel(id="unknown"), CodexModel(id="gpt-x")),
            definitions,
            ConfigReadResult(config={}),
        )
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0].model_ref, "gpt-x")
        self.assertEqual(projected[0].route_type, "runtime")
        self.assertEqual(projected[0].route_ref, CODEX_RUNTIME_ROUTE)
        self.assertEqual(projected[0].executor_type, CODEX_RUNTIME_EXECUTOR)
        self.assertEqual(projected[0].normalized_capabilities, ("reasoning", "vision"))
        self.assertNotEqual(projected[0].model_ref, CODEX_RUNTIME_ROUTE)

    def test_refresh_reads_typed_sources_and_registers_only_current_projection(self):
        bridge = type("Bridge", (), {})()
        bridge.list_models = AsyncMock(return_value=ModelListResult(data=(CodexModel(id="gpt-x"),)))
        bridge.read_config = AsyncMock(return_value=ConfigReadResult(config={"profile": "safe"}))
        service = CodexModelProjectionService(ModelAvailabilityService(InMemoryAvailabilityRepository()))
        definitions = (ModelDefinition(id="gpt-x", family="gpt", display_name="GPT X"),)

        projected = asyncio.run(service.refresh(bridge, definitions))

        self.assertEqual([item.id for item in projected], [f"{CODEX_RUNTIME_ROUTE}:gpt-x"])
        bridge.list_models.assert_awaited_once()
        bridge.read_config.assert_awaited_once()

    def test_projection_does_not_accept_untyped_config(self):
        bridge = type("Bridge", (), {})()
        bridge.list_models = AsyncMock(return_value=ModelListResult(data=()))
        bridge.read_config = AsyncMock(return_value={})
        service = CodexModelProjectionService(ModelAvailabilityService(InMemoryAvailabilityRepository()))
        with self.assertRaises(TypeError):
            asyncio.run(service.refresh(bridge, ()))
