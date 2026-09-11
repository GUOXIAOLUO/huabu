"""Typed input-binding contracts and the lossless Legacy compatibility seam."""

from copy import deepcopy
from typing import Any, Literal, Mapping, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator


InputBindingSourceType = Literal[
    "asset_version",
    "artifact_version",
    "entity_ref",
    "entity_version",
    "collection",
    "literal",
]


class InputBinding(BaseModel):
    """A typed connection from one source value to one node input port."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, max_length=255)
    target: str = Field(min_length=1, max_length=160)
    source_type: InputBindingSourceType
    source_ref: str = Field(min_length=1, max_length=255)
    role: str = Field(default="input", min_length=1, max_length=160)
    order: int = Field(default=0, ge=0)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegacyInputBinding(BaseModel):
    """An opaque old binding retained until its semantics are explicitly known."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    payload: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def wrap_legacy_object(cls, value: Any):
        if isinstance(value, Mapping) and "payload" not in value:
            return {"payload": deepcopy(dict(value))}
        return value

    @model_serializer(mode="plain")
    def serialize_payload(self) -> dict[str, Any]:
        """Keep legacy API/record JSON in its original object shape."""
        return deepcopy(self.payload)


InputBindingValue: TypeAlias = InputBinding | LegacyInputBinding


class InputBindingAdapter:
    """Convert typed and Legacy payloads without owning execution semantics."""

    _TYPED_FIELDS = frozenset({"id", "target", "source_type", "source_ref"})

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | InputBindingValue) -> InputBindingValue:
        if isinstance(payload, (InputBinding, LegacyInputBinding)):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("input binding payload must be an object")
        copied = deepcopy(dict(payload))
        if cls._TYPED_FIELDS.issubset(copied):
            try:
                return InputBinding.model_validate(copied)
            except ValueError:
                # An existing object with unknown or invalid semantics stays Legacy.
                pass
        return LegacyInputBinding(payload=copied)

    @classmethod
    def from_payloads(cls, payloads: list[Mapping[str, Any] | InputBindingValue] | tuple[Any, ...]) -> list[InputBindingValue]:
        return [cls.from_payload(payload) for payload in payloads]

    @staticmethod
    def to_payload(binding: InputBindingValue) -> dict[str, Any]:
        if isinstance(binding, LegacyInputBinding):
            return deepcopy(binding.payload)
        return binding.model_dump(mode="json")

    @classmethod
    def to_payloads(cls, bindings: list[InputBindingValue] | tuple[InputBindingValue, ...]) -> list[dict[str, Any]]:
        return [cls.to_payload(binding) for binding in bindings]
