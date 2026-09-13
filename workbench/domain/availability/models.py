"""Provider/runtime route availability, separate from ModelDefinition."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata


MODEL_AVAILABILITY_SCHEMA_VERSION = "workbench.model-availability/2"
RouteType = Literal["provider", "runtime"]
AvailabilityStatus = Literal["available", "unavailable", "error", "unknown"]


class ModelAvailability(BaseModel):
    """One executable route for a ModelDefinition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[MODEL_AVAILABILITY_SCHEMA_VERSION] = MODEL_AVAILABILITY_SCHEMA_VERSION
    id: OpaqueId
    model_ref: OpaqueId
    route_type: RouteType
    route_ref: OpaqueId
    executor_type: OpaqueId
    normalized_capabilities: tuple[OpaqueId, ...] = ()
    constraints: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    status: AvailabilityStatus = "unknown"
    native_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_capabilities_and_safe_metadata(self):
        if len(self.normalized_capabilities) != len(set(self.normalized_capabilities)):
            raise ValueError("model availability capabilities must be unique")
        assert_safe_metadata(self.constraints, path="constraints")
        assert_safe_metadata(self.native_metadata, path="native_metadata")
        return self
