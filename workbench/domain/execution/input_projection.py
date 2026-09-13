"""Immutable execution input snapshot envelopes."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.canvas.models import DefinitionRef
from workbench.domain.prompt import PromptRef
from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_INPUT_PROJECTION_SCHEMA_VERSION = "workbench.execution-input-projection/1"


class ProjectionError(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    code: OpaqueId
    message: str = Field(min_length=1, max_length=2_000)
    binding_id: str | None = None


class ProjectedExecutionInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    input_id: OpaqueId
    binding_id: OpaqueId
    target: OpaqueId
    role: OpaqueId
    order: int = Field(ge=0)
    source_type: OpaqueId
    source_ref: OpaqueId
    value: Any
    source_snapshot: Any

    @model_validator(mode="after")
    def freeze_values(self):
        object.__setattr__(self, "value", freeze_value(self.value))
        object.__setattr__(self, "source_snapshot", freeze_value(self.source_snapshot))
        return self


class ExecutionInputProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: str = EXECUTION_INPUT_PROJECTION_SCHEMA_VERSION
    inputs: tuple[ProjectedExecutionInput, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    skill_ref: DefinitionRef | None = None
    prompt_ref: PromptRef | None = None
    model_availability_ref: OpaqueId | None = None
    execution_profile_ref: OpaqueId | None = None
    errors: tuple[ProjectionError, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors

    @model_validator(mode="after")
    def validate_snapshot(self):
        assert_safe_metadata(self.parameters, path="parameters")
        object.__setattr__(self, "parameters", freeze_value(self.parameters))
        if self.errors and self.inputs:
            raise ValueError("invalid input projections cannot contain executable inputs")
        return self
