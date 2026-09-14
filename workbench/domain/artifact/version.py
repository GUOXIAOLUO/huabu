"""Immutable versions of Workbench-produced Artifacts and their provenance."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


ARTIFACT_VERSION_SCHEMA_VERSION = "workbench.artifact-version/1"
CHECKSUM_PATTERN = r"^[a-z0-9]+:[0-9a-f]{32,128}$"


class ArtifactVersionContentRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    location: Annotated[str, Field(min_length=1, max_length=2048)]
    checksum: Annotated[str, Field(pattern=CHECKSUM_PATTERN)]
    mime_type: Annotated[str, Field(min_length=1, max_length=255)]
    size_bytes: Annotated[int, Field(ge=0)]


class ArtifactVersionLineage(BaseModel):
    """The immutable task/execution context that produced one formal version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: OpaqueId | None = None
    run_id: OpaqueId
    attempt_id: OpaqueId
    input_refs: tuple[OpaqueId, ...] = ()
    prompt_version_ref: OpaqueId | None = None
    model_ref: OpaqueId | None = None
    skill_version_ref: OpaqueId | None = None


class ArtifactVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ARTIFACT_VERSION_SCHEMA_VERSION] = ARTIFACT_VERSION_SCHEMA_VERSION
    id: OpaqueId
    artifact_id: OpaqueId
    project_id: OpaqueId
    ordinal: Annotated[int, Field(ge=1)]
    content_ref: ArtifactVersionContentRef
    lineage: ArtifactVersionLineage
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "ArtifactVersion":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self
