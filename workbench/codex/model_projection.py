"""Project Codex-discovered models into runtime ModelAvailability routes."""

from __future__ import annotations

from typing import Iterable, Protocol

from workbench.codex.protocol import CodexModel, ConfigReadResult, ModelListResult
from workbench.domain.availability import ModelAvailability
from workbench.domain.provider import ModelDefinition

CODEX_RUNTIME_ROUTE = "codex_harness"
CODEX_RUNTIME_EXECUTOR = "codex_harness"


class CodexModelSource(Protocol):
    async def list_models(self) -> ModelListResult: ...
    async def read_config(self) -> ConfigReadResult: ...


class ModelAvailabilitySink(Protocol):
    def register(self, availability: ModelAvailability) -> ModelAvailability: ...


class CodexModelProjector:
    """Build runtime availability without creating or changing model identity."""

    @staticmethod
    def project(
        models: Iterable[CodexModel],
        model_definitions: Iterable[ModelDefinition],
        config: ConfigReadResult,
    ) -> tuple[ModelAvailability, ...]:
        definitions_by_id = {definition.id: definition for definition in model_definitions}
        projected: list[ModelAvailability] = []
        seen: set[str] = set()
        for model in models:
            model_ref = (model.id or model.name or "").strip()
            if not model_ref or model_ref not in definitions_by_id or model_ref in seen:
                continue
            seen.add(model_ref)
            definition = definitions_by_id[model_ref]
            metadata = {"source": "codex_app_server"}
            if model.name and model.name != model_ref:
                metadata["display_name"] = model.name
            projected.append(
                ModelAvailability(
                    id=f"{CODEX_RUNTIME_ROUTE}:{model_ref}",
                    model_ref=model_ref,
                    route_type="runtime",
                    route_ref=CODEX_RUNTIME_ROUTE,
                    executor_type=CODEX_RUNTIME_EXECUTOR,
                    normalized_capabilities=definition.normalized_capabilities,
                    status="available",
                    native_metadata=metadata,
                )
            )
        return tuple(projected)


class CodexModelProjectionService:
    """Refresh current Codex runtime routes through the availability owner."""

    def __init__(self, availability_service: ModelAvailabilitySink):
        self._availability_service = availability_service

    async def refresh(
        self,
        bridge: CodexModelSource,
        model_definitions: Iterable[ModelDefinition],
    ) -> tuple[ModelAvailability, ...]:
        model_result = await bridge.list_models()
        config_result = await bridge.read_config()
        if not isinstance(config_result, ConfigReadResult):
            raise TypeError("Codex projection requires a typed ConfigReadResult")
        projected = CodexModelProjector.project(model_result.data, model_definitions, config_result)
        return tuple(self._availability_service.register(item) for item in projected)
