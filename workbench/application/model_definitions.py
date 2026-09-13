"""ModelDefinition projection boundary for legacy provider model lists."""

from __future__ import annotations

from typing import Any

from workbench.domain.provider import ModelDefinition


class ModelDefinitionAdapter:
    """Project model identity metadata without provider or connection state."""

    @staticmethod
    def from_legacy(value: str | dict[str, Any], *, capability: str = "") -> ModelDefinition:
        if isinstance(value, str):
            model_id = value.strip()
            payload: dict[str, Any] = {}
        elif isinstance(value, dict):
            payload = value
            model_id = str(payload.get("id") or payload.get("name") or payload.get("model") or "").strip()
        else:
            raise TypeError("legacy model value must be a string or object")
        if not model_id:
            raise ValueError("legacy model value requires an id")
        display_name = str(payload.get("display_name") or payload.get("displayName") or payload.get("label") or model_id).strip()
        family = str(payload.get("family") or "generic").strip() or "generic"
        capabilities = _string_tuple(payload.get("normalized_capabilities") or payload.get("capabilities"))
        if capability and capability not in capabilities:
            capabilities = (*capabilities, capability)
        input_modalities = _string_tuple(payload.get("input_modalities"))
        output_modalities = _string_tuple(payload.get("output_modalities"))
        context_window = payload.get("context_window") or payload.get("context_length")
        if context_window is not None:
            context_window = int(context_window)
        native_metadata = payload.get("native_metadata") or {}
        if not isinstance(native_metadata, dict):
            raise TypeError("legacy model native_metadata must be an object")
        return ModelDefinition(
            id=model_id,
            family=family,
            display_name=display_name,
            normalized_capabilities=capabilities,
            input_modalities=input_modalities,
            output_modalities=output_modalities,
            context_window=context_window,
            parameter_schema=dict(payload.get("parameter_schema") or {}),
            native_metadata=dict(native_metadata),
        )

    @staticmethod
    def from_legacy_list(values: list[str | dict[str, Any]], *, capability: str = "") -> tuple[ModelDefinition, ...]:
        """Project one legacy model list while preserving its first-seen order."""
        definitions: list[ModelDefinition] = []
        seen: set[str] = set()
        for value in values:
            definition = ModelDefinitionAdapter.from_legacy(value, capability=capability)
            if definition.id not in seen:
                seen.add(definition.id)
                definitions.append(definition)
        return tuple(definitions)


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise TypeError("legacy model metadata must be a list")
    return tuple(item for item in (str(item).strip() for item in value) if item)
