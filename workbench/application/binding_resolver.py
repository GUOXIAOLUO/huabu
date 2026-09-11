"""Deterministic, Canvas-edge-independent input binding resolution."""

import json
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from workbench.domain.canvas.input_bindings import InputBinding, InputBindingSourceType


BindingSourceResolver = Callable[[str], Any | None]
ResolutionStatus = Literal["resolved", "unresolved", "disabled"]


class BindingResolutionError(ValueError):
    """A typed error for invalid binding input or a failed normalization step."""

    def __init__(self, code: str, message: str, *, binding_id: str | None = None):
        self.code = code
        self.binding_id = binding_id
        super().__init__(message)


class ResolvedInput(BaseModel):
    """The normalized, non-executable result of resolving one binding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    binding_id: str = Field(min_length=1, max_length=255)
    target: str = Field(min_length=1, max_length=160)
    source_type: str = Field(min_length=1, max_length=80)
    source_ref: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=160)
    order: int = Field(ge=0)
    status: ResolutionStatus
    value: Any | None = None
    reason: str | None = None


class BindingResolver:
    """Resolve typed references through injected resource adapters.

    The resolver only normalizes references. It does not invoke models, inspect
    Canvas edges, or mutate project state. Missing adapters and missing records
    are represented explicitly as unresolved results.
    """

    def __init__(self, resolvers: Mapping[InputBindingSourceType, BindingSourceResolver] | None = None):
        self._resolvers = dict(resolvers or {})

    def resolve(self, bindings: Iterable[InputBinding]) -> tuple[ResolvedInput, ...]:
        materialized = tuple(bindings)
        self._validate_unique_ids(materialized)
        return tuple(self._resolve_one(binding) for binding in sorted(materialized, key=lambda item: (item.order, item.id)))

    @staticmethod
    def _validate_unique_ids(bindings: tuple[InputBinding, ...]) -> None:
        seen: set[str] = set()
        for binding in bindings:
            if not isinstance(binding, InputBinding):
                raise BindingResolutionError("invalid_binding", "BindingResolver accepts typed InputBinding values")
            if binding.id in seen:
                raise BindingResolutionError("duplicate_binding_id", f"duplicate input binding id: {binding.id}", binding_id=binding.id)
            seen.add(binding.id)

    def _resolve_one(self, binding: InputBinding) -> ResolvedInput:
        base = {
            "binding_id": binding.id,
            "target": binding.target,
            "source_type": binding.source_type,
            "source_ref": binding.source_ref,
            "role": binding.role,
            "order": binding.order,
        }
        if not binding.enabled:
            return ResolvedInput(**base, status="disabled", reason="binding_disabled")
        if binding.source_type == "literal":
            try:
                value = json.loads(binding.source_ref)
            except json.JSONDecodeError as error:
                raise BindingResolutionError("invalid_literal", "literal source_ref must be valid JSON", binding_id=binding.id) from error
            return ResolvedInput(**base, status="resolved", value=value)

        resolver = self._resolvers.get(binding.source_type)
        if resolver is None:
            return ResolvedInput(**base, status="unresolved", reason="resolver_unavailable")
        value = resolver(binding.source_ref)
        if value is None:
            return ResolvedInput(**base, status="unresolved", reason="source_not_found")
        return ResolvedInput(**base, status="resolved", value=value)
