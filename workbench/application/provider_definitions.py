"""ProviderDefinition projection boundary for legacy provider-shaped payloads."""

from __future__ import annotations

from typing import Any

from workbench.domain.provider import ProviderDefinition


class ProviderDefinitionAdapter:
    """Read only stable public metadata from legacy provider settings.

    Connection fields and credential values are intentionally not projected.
    """

    @staticmethod
    def _safe_metadata(value: dict[str, Any]) -> dict[str, Any]:
        sensitive = ("key", "secret", "token", "password", "credential", "authorization")

        def clean(item: Any) -> Any:
            if isinstance(item, dict):
                return {
                    key: clean(child) for key, child in item.items()
                    if not any(part in str(key).casefold() for part in sensitive)
                }
            if isinstance(item, list):
                return [clean(child) for child in item]
            return item

        return clean(value)

    @staticmethod
    def from_legacy(payload: dict[str, Any]) -> ProviderDefinition:
        if not isinstance(payload, dict):
            raise TypeError("legacy provider payload must be an object")
        provider_id = str(payload.get("id") or "").strip()
        if not provider_id:
            raise ValueError("legacy provider payload requires an id")
        title = str(payload.get("title") or payload.get("name") or provider_id).strip()
        protocol = str(payload.get("protocol") or "legacy").strip()
        raw_capabilities = payload.get("capabilities") or ()
        if not isinstance(raw_capabilities, (list, tuple)):
            raise TypeError("legacy provider capabilities must be a list")
        capabilities = tuple(str(item).strip() for item in raw_capabilities if str(item).strip())
        config_schema = payload.get("config_schema") or {}
        if not isinstance(config_schema, dict):
            raise TypeError("legacy provider config_schema must be an object")
        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise TypeError("legacy provider metadata must be an object")
        return ProviderDefinition(
            id=provider_id,
            title=title,
            protocol=protocol,
            capabilities=capabilities,
            config_schema=dict(config_schema),
            metadata=ProviderDefinitionAdapter._safe_metadata(metadata),
        )
