"""Versioned, provider-neutral execution profile records."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata


EXECUTION_PROFILE_SCHEMA_VERSION = "workbench.execution-profile/1"
EXECUTION_PROFILE_REF_SCHEMA_VERSION = "workbench.execution-profile-ref/1"


class ExecutionProfileRef(BaseModel):
    """Exact reference to one immutable execution profile version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_PROFILE_REF_SCHEMA_VERSION] = EXECUTION_PROFILE_REF_SCHEMA_VERSION
    profile_id: OpaqueId
    version: Annotated[int, Field(ge=1)]


class ExecutionProfile(BaseModel):
    """Reusable execution configuration without executor implementation details."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_PROFILE_SCHEMA_VERSION] = EXECUTION_PROFILE_SCHEMA_VERSION
    id: OpaqueId
    version: Annotated[int, Field(ge=1)]
    name: Annotated[str, Field(min_length=1, max_length=500)]
    description: str = ""
    executor_ref: OpaqueId
    runtime_connection_ref: OpaqueId | None = None
    model_availability_ref: OpaqueId | None = None
    default_params: dict[str, Any] = Field(default_factory=dict)
    safety_policy_ref: OpaqueId | None = None
    timeout_seconds: Annotated[float, Field(gt=0)] = 30.0
    cancel_timeout_seconds: Annotated[float, Field(gt=0)] = 10.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def ref(self) -> ExecutionProfileRef:
        return ExecutionProfileRef(profile_id=self.id, version=self.version)

    @model_validator(mode="after")
    def require_secret_free_configuration(self):
        assert_safe_metadata(self.default_params, path="default_params")
        assert_safe_metadata(self.metadata)
        return self
